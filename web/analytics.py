"""
Módulo de analytics interno para el Calendario Laboral.

Registra generaciones de calendario y descargas en SQLite.
Diseñado para ser best-effort: un error aquí NUNCA rompe la app.

Uso:
    from web.analytics import log_generation, log_download, get_stats

    log_generation(ccaa, municipio, year, session_id, request)
    log_download(session_id, 'pdf', has_empresa=True)
    stats = get_stats()
"""

import os
import sqlite3
import hashlib
import threading
from pathlib import Path


# ---------------------------------------------------------------------------
# Database path (con fallbacks)
# ---------------------------------------------------------------------------

def _get_db_path() -> str:
    """
    Determina dónde guardar la base de datos SQLite.

    Orden de prioridad:
    1. ANALYTICS_DB_PATH env var (Railway Volume)
    2. /data/ si existe y es escribible (Railway Volume convencional)
    3. web/data/analytics.db (desarrollo local)
    4. :memory: (último recurso)
    """
    # 1. Variable de entorno explícita
    env_path = os.environ.get('ANALYTICS_DB_PATH')
    if env_path:
        # Asegurar que el directorio padre existe
        parent = Path(env_path).parent
        if parent.exists() and os.access(str(parent), os.W_OK):
            return env_path

    # 2. Railway Volume convencional
    railway_volume = Path('/data')
    if railway_volume.exists() and os.access(str(railway_volume), os.W_OK):
        return str(railway_volume / 'analytics.db')

    # 3. Desarrollo local
    local_dir = Path(__file__).parent / 'data'
    try:
        local_dir.mkdir(exist_ok=True)
        return str(local_dir / 'analytics.db')
    except OSError:
        pass

    # 4. In-memory (datos efímeros, pero la app no falla)
    return ':memory:'


# ---------------------------------------------------------------------------
# Inicialización
# ---------------------------------------------------------------------------

_db_path = _get_db_path()
_db_lock = threading.Lock()

print(f"[analytics] Database: {_db_path}")


def _get_connection() -> sqlite3.Connection:
    """Abre una conexión nueva con configuración óptima."""
    conn = sqlite3.connect(_db_path, timeout=5, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def _init_db():
    """Crea tablas e índices si no existen."""
    conn = _get_connection()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS generations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL DEFAULT (datetime('now')),
                ccaa TEXT NOT NULL,
                municipio TEXT NOT NULL,
                year INTEGER NOT NULL,
                ip_hash TEXT,
                user_agent TEXT,
                session_id TEXT
            );

            CREATE TABLE IF NOT EXISTS downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL DEFAULT (datetime('now')),
                session_id TEXT NOT NULL,
                format TEXT NOT NULL,
                has_empresa INTEGER NOT NULL DEFAULT 0
            );

            CREATE INDEX IF NOT EXISTS idx_gen_timestamp ON generations(timestamp);
            CREATE INDEX IF NOT EXISTS idx_gen_ccaa ON generations(ccaa);
            CREATE INDEX IF NOT EXISTS idx_dl_timestamp ON downloads(timestamp);
            CREATE INDEX IF NOT EXISTS idx_dl_format ON downloads(format);
        """)
        conn.commit()
    finally:
        conn.close()


# Inicializar al importar el módulo
try:
    _init_db()
except Exception as e:
    print(f"[analytics] Error inicializando DB: {e}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _hash_ip(ip: str) -> str:
    """Hash de IP con salt. Devuelve 16 chars hex, nunca la IP real."""
    salt = os.environ.get('IP_HASH_SALT', 'calendario-laboral-default-salt')
    return hashlib.sha256(f"{salt}:{ip}".encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# API pública: logging
# ---------------------------------------------------------------------------

def log_generation(ccaa: str, municipio: str, year: int,
                   session_id: str, request) -> None:
    """
    Registra una generación de calendario.
    Llamar desde la ruta /generar tras crear la sesión.
    """
    try:
        ip_hash = _hash_ip(request.remote_addr or '0.0.0.0')
        user_agent = (request.headers.get('User-Agent', '') or '')[:500]

        with _db_lock:
            conn = _get_connection()
            try:
                conn.execute(
                    """INSERT INTO generations
                       (ccaa, municipio, year, ip_hash, user_agent, session_id)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (ccaa, municipio, year, ip_hash, user_agent, session_id)
                )
                conn.commit()
            finally:
                conn.close()
    except Exception as e:
        print(f"[analytics] Error logging generation: {e}")


def log_download(session_id: str, format: str,
                 has_empresa: bool = False) -> None:
    """
    Registra una descarga (PDF o CSV).
    Llamar desde las rutas /download y /download-csv.
    """
    try:
        with _db_lock:
            conn = _get_connection()
            try:
                conn.execute(
                    """INSERT INTO downloads
                       (session_id, format, has_empresa)
                       VALUES (?, ?, ?)""",
                    (session_id, format, 1 if has_empresa else 0)
                )
                conn.commit()
            finally:
                conn.close()
    except Exception as e:
        print(f"[analytics] Error logging download: {e}")


# ---------------------------------------------------------------------------
# API pública: consultas
# ---------------------------------------------------------------------------

def get_stats() -> dict:
    """
    Devuelve estadísticas agregadas para el endpoint /admin/stats.

    Returns:
        dict con totales, rankings, tendencias diarias, conversión, etc.
    """
    conn = _get_connection()
    try:
        stats = {}

        # --- Totales ---
        stats['total_generations'] = conn.execute(
            "SELECT COUNT(*) FROM generations"
        ).fetchone()[0]

        stats['total_downloads'] = conn.execute(
            "SELECT COUNT(*) FROM downloads"
        ).fetchone()[0]

        # --- Top CCAA ---
        stats['by_ccaa'] = [dict(r) for r in conn.execute(
            """SELECT ccaa, COUNT(*) as count
               FROM generations
               GROUP BY ccaa
               ORDER BY count DESC
               LIMIT 10"""
        ).fetchall()]

        # --- Descargas por formato ---
        stats['by_format'] = [dict(r) for r in conn.execute(
            """SELECT format, COUNT(*) as count
               FROM downloads
               GROUP BY format
               ORDER BY count DESC"""
        ).fetchall()]

        # --- Últimos 7 días: generaciones ---
        stats['daily_generations'] = [dict(r) for r in conn.execute(
            """SELECT DATE(timestamp) as day, COUNT(*) as count
               FROM generations
               WHERE timestamp >= datetime('now', '-7 days')
               GROUP BY day
               ORDER BY day"""
        ).fetchall()]

        # --- Últimos 7 días: descargas ---
        stats['daily_downloads'] = [dict(r) for r in conn.execute(
            """SELECT DATE(timestamp) as day, COUNT(*) as count
               FROM downloads
               WHERE timestamp >= datetime('now', '-7 days')
               GROUP BY day
               ORDER BY day"""
        ).fetchall()]

        # --- Top 10 municipios ---
        stats['top_municipios'] = [dict(r) for r in conn.execute(
            """SELECT municipio, ccaa, COUNT(*) as count
               FROM generations
               GROUP BY municipio, ccaa
               ORDER BY count DESC
               LIMIT 10"""
        ).fetchall()]

        # --- Visitantes únicos (30 días) ---
        stats['unique_visitors_30d'] = conn.execute(
            """SELECT COUNT(DISTINCT ip_hash)
               FROM generations
               WHERE timestamp >= datetime('now', '-30 days')"""
        ).fetchone()[0]

        # --- Tasa de conversión ---
        if stats['total_generations'] > 0:
            stats['conversion_rate'] = round(
                stats['total_downloads'] / stats['total_generations'] * 100, 1
            )
        else:
            stats['conversion_rate'] = 0

        # --- Últimas 10 generaciones ---
        stats['recent'] = [dict(r) for r in conn.execute(
            """SELECT timestamp, ccaa, municipio, year
               FROM generations
               ORDER BY id DESC
               LIMIT 10"""
        ).fetchall()]

        # --- Info ---
        stats['db_path'] = _db_path

        return stats

    finally:
        conn.close()
