"""
Frontend web Flask para el Calendario Laboral de España.

Usa el motor de scraping del proyecto principal (ScraperFactory + CCAaRegistry)
para generar calendarios laborales personalizados con las 17 CCAA.
"""

import os
import sys
import uuid
import json
import tempfile
import threading
from pathlib import Path
from datetime import datetime

# Añadir raíz del monorepo al path para acceder a scrapers/, config/, etc.
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from flask import (
    Flask, render_template, request, jsonify,
    redirect, url_for, send_file
)

from web.utils.calendar_generator import CalendarGenerator
from web.analytics import log_generation, log_download, get_stats
from scrape_municipio import scrape_festivos_completos
from config.config_manager import CCAaRegistry

# ---------------------------------------------------------------------------
# App Flask
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = os.environ.get(
    'SECRET_KEY', 'dev-secret-key-super-importante-cambiar-en-produccion'
)
app.config['UMAMI_WEBSITE_ID'] = os.environ.get('UMAMI_WEBSITE_ID', '')

# ---------------------------------------------------------------------------
# CCAA dinámicas desde el registry (17 CCAA)
# ---------------------------------------------------------------------------
_registry = CCAaRegistry()
CCAA_SOPORTADAS = _registry.list_ccaa()

CCAA_NOMBRES = {}
for _code in CCAA_SOPORTADAS:
    _info = _registry.get_ccaa_info(_code)
    CCAA_NOMBRES[_code] = _info.get('name', _code.title()) if _info else _code.title()

# ---------------------------------------------------------------------------
# Sesiones temporales
# ---------------------------------------------------------------------------
SESSION_DIR = Path(__file__).parent / 'temp_sessions'
SESSION_DIR.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Contexto global de plantillas
# ---------------------------------------------------------------------------
@app.context_processor
def inject_current_year():
    """Expone el año en curso a todas las plantillas (título, footer, etc.)."""
    return {'current_year': datetime.now().year}


# ===================================================================
# RUTAS
# ===================================================================

@app.route('/')
def landing():
    """Landing page principal"""
    ccaas = [
        {'value': ccaa, 'nombre': CCAA_NOMBRES.get(ccaa, ccaa.title())}
        for ccaa in CCAA_SOPORTADAS
    ]
    ccaas.sort(key=lambda x: x['nombre'])
    current_year = datetime.now().year
    # Años seleccionables: posterior, en curso (por defecto) y anterior
    years = [current_year + 1, current_year, current_year - 1]
    return render_template('landing.html', ccaas=ccaas, years=years)


def _write_session(session_file, session_id, municipio, ccaa, year,
                   status, data=None, error=None):
    """Escribe el fichero de sesión de forma atómica (evita lecturas parciales)."""
    payload = {
        'session_id': session_id,
        'municipio': municipio,
        'ccaa': ccaa,
        'ccaa_nombre': CCAA_NOMBRES.get(ccaa, ccaa.title()),
        'year': year,
        'status': status,
        'created_at': datetime.now().isoformat(),
    }
    if data is not None:
        payload['data'] = data
    if error is not None:
        payload['error'] = error

    tmp_file = session_file.with_suffix('.json.tmp')
    with open(tmp_file, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    tmp_file.replace(session_file)


def _run_generation(session_id, municipio, ccaa, year):
    """Ejecuta el scraping en segundo plano y actualiza el estado de la sesión."""
    session_file = SESSION_DIR / f"{session_id}.json"
    try:
        print(f"  [bg] Generando calendario: {municipio}, {ccaa}, {year}")
        data = scrape_festivos_completos(municipio, ccaa, year)

        if not data:
            _write_session(session_file, session_id, municipio, ccaa, year,
                           status='error', error='No se pudieron obtener los festivos')
            return

        _write_session(session_file, session_id, municipio, ccaa, year,
                       status='done', data=data)
        print(f"  [bg] Calendario generado: {session_id}")

    except Exception as e:
        print(f"  [bg] Error generando calendario: {e}")
        import traceback
        traceback.print_exc()
        _write_session(session_file, session_id, municipio, ccaa, year,
                       status='error', error=str(e))


@app.route('/generar', methods=['POST'])
def generar():
    """Inicia la generación en segundo plano y redirige a la pantalla de espera."""
    municipio = request.form.get('municipio', '').strip()
    ccaa = request.form.get('ccaa', '').strip()
    try:
        year = int(request.form.get('year', datetime.now().year))
    except (TypeError, ValueError):
        year = datetime.now().year

    if not municipio or not ccaa:
        return "Error: Faltan datos del formulario", 400

    if ccaa not in CCAA_SOPORTADAS:
        return f"Error: CCAA '{ccaa}' no soportada", 400

    session_id = str(uuid.uuid4())
    session_file = SESSION_DIR / f"{session_id}.json"

    # Estado inicial: procesando
    _write_session(session_file, session_id, municipio, ccaa, year,
                   status='processing')

    # Registrar la generación (aquí sí hay contexto de request)
    try:
        log_generation(ccaa, municipio, year, session_id, request)
    except Exception:
        pass

    # Lanzar el scraping en un hilo para que la petición responda al instante
    # (evita timeouts del servidor/proxy en la primera generación de un municipio)
    threading.Thread(
        target=_run_generation,
        args=(session_id, municipio, ccaa, year),
        daemon=True,
    ).start()

    return redirect(url_for('procesando', session_id=session_id))


@app.route('/procesando/<session_id>')
def procesando(session_id):
    """Pantalla de espera que consulta el estado hasta que el calendario esté listo."""
    session_file = SESSION_DIR / f"{session_id}.json"

    if not session_file.exists():
        return "Error: Sesion no encontrada o expirada", 404

    with open(session_file, 'r', encoding='utf-8') as f:
        session_data = json.load(f)

    if session_data.get('status') == 'done':
        return redirect(url_for('calendario', session_id=session_id))

    return render_template('procesando.html', **session_data)


@app.route('/status/<session_id>')
def status(session_id):
    """Devuelve el estado de la generación en JSON (para el polling del cliente)."""
    session_file = SESSION_DIR / f"{session_id}.json"

    if not session_file.exists():
        return jsonify({'status': 'not_found'}), 404

    try:
        with open(session_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
    except (json.JSONDecodeError, ValueError):
        # Fichero a medio escribir: tratar como "procesando"
        return jsonify({'status': 'processing'})

    return jsonify({
        'status': session_data.get('status', 'processing'),
        'error': session_data.get('error'),
    })


@app.route('/calendario/<session_id>')
def calendario(session_id):
    """Muestra el calendario generado"""
    session_file = SESSION_DIR / f"{session_id}.json"

    if not session_file.exists():
        return "Error: Sesion no encontrada o expirada", 404

    with open(session_file, 'r', encoding='utf-8') as f:
        session_data = json.load(f)

    estado = session_data.get('status', 'done')
    if estado == 'processing':
        return redirect(url_for('procesando', session_id=session_id))
    if estado == 'error':
        mensaje = session_data.get('error', 'desconocido')
        return f"Error generando el calendario: {mensaje}", 500

    return render_template('calendario.html', **session_data)


@app.route('/download-csv/<session_id>')
def download_csv(session_id):
    """Descarga festivos en formato CSV"""
    import pandas as pd

    session_file = SESSION_DIR / f"{session_id}.json"
    if not session_file.exists():
        return "Error: Sesion no encontrada", 404

    with open(session_file, 'r', encoding='utf-8') as f:
        session_data = json.load(f)

    try:
        festivos = session_data['data']['festivos']
        df = pd.DataFrame(festivos)

        columnas = ['fecha', 'fecha_texto', 'descripcion', 'tipo']
        if 'ambito' in df.columns:
            columnas.append('ambito')
        df = df[columnas]

        with tempfile.NamedTemporaryFile(
            delete=False, suffix='.csv', mode='w', encoding='utf-8'
        ) as tmp:
            csv_path = tmp.name
            df.to_csv(csv_path, index=False, encoding='utf-8')

        municipio_safe = session_data['municipio'].lower().replace(' ', '_')
        filename = f"festivos_{municipio_safe}_{session_data['year']}.csv"

        try:
            log_download(session_id, 'csv')
        except Exception:
            pass

        return send_file(
            csv_path,
            as_attachment=True,
            download_name=filename,
            mimetype='text/csv'
        )

    except Exception as e:
        print(f"  Error generando CSV: {e}")
        import traceback
        traceback.print_exc()
        return f"Error generando CSV: {str(e)}", 500


@app.route('/download/<session_id>', methods=['POST'])
def download(session_id):
    """Genera y descarga HTML con auto-print para PDF"""

    session_file = SESSION_DIR / f"{session_id}.json"
    if not session_file.exists():
        return "Error: Sesion no encontrada", 404

    with open(session_file, 'r', encoding='utf-8') as f:
        session_data = json.load(f)

    # === RECOGER DATOS DEL FORMULARIO ===
    empresa = request.form.get('empresa', '').strip()
    direccion = request.form.get('direccion', '').strip()
    horario_invierno = request.form.get('horario_invierno', '').strip()

    horario = {
        'invierno': horario_invierno,
        'tiene_verano': bool(request.form.get('tiene_verano'))
    }

    if horario['tiene_verano']:
        horario['verano'] = request.form.get('horario_verano', '').strip()
        verano_inicio = request.form.get('verano_inicio', '').strip()
        verano_fin = request.form.get('verano_fin', '').strip()
        if verano_inicio:
            horario['verano_inicio'] = datetime.strptime(verano_inicio, '%Y-%m-%d')
        if verano_fin:
            horario['verano_fin'] = datetime.strptime(verano_fin, '%Y-%m-%d')

    datos_opcionales = {'direccion': direccion}

    convenio = request.form.get('convenio', '').strip()
    if convenio:
        datos_opcionales['convenio'] = convenio

    num_patronal = request.form.get('num_patronal', '').strip()
    if num_patronal:
        datos_opcionales['num_patronal'] = num_patronal

    mutua = request.form.get('mutua', '').strip()
    if mutua:
        datos_opcionales['mutua'] = mutua

    try:
        generator = CalendarGenerator(
            year=session_data['year'],
            festivos=session_data['data']['festivos'],
            municipio=session_data['municipio'],
            ccaa=session_data['ccaa_nombre'],
            empresa=empresa,
            horario=horario,
            datos_opcionales=datos_opcionales
        )

        html_content = generator.generate_html()

        # Auto-print al abrir
        html_content = html_content.replace('</body>', '''
            <script>
            window.onload = function() {
                setTimeout(function() {
                    window.print();
                }, 500);
            };
            </script>
            </body>
        ''')

        with tempfile.NamedTemporaryFile(
            delete=False, suffix='.html', mode='w', encoding='utf-8'
        ) as tmp:
            tmp.write(html_content)
            html_path = tmp.name

        municipio_safe = session_data['municipio'].lower().replace(' ', '_')
        filename = f"calendario_{municipio_safe}_{session_data['year']}.html"

        try:
            log_download(session_id, 'pdf', has_empresa=bool(empresa))
        except Exception:
            pass

        return send_file(
            html_path,
            as_attachment=True,
            download_name=filename,
            mimetype='text/html'
        )

    except Exception as e:
        print(f"  Error generando calendario: {e}")
        import traceback
        traceback.print_exc()
        return f"Error: {str(e)}", 500


@app.route('/health')
def health():
    """Health check para Railway"""
    return jsonify({
        'status': 'ok',
        'ccaa_count': len(CCAA_SOPORTADAS),
    })


@app.route('/api/municipios/<ccaa>')
def api_municipios(ccaa):
    """API que devuelve municipios de una CCAA"""

    # Mapeo de nombres especiales de archivos
    FILENAME_MAP = {
        'canarias': 'canarias_municipios_islas.json',
    }

    filename = FILENAME_MAP.get(ccaa, f'{ccaa}_municipios.json')
    config_file = PROJECT_ROOT / 'config' / filename

    if not config_file.exists():
        return jsonify({'error': f'CCAA {ccaa} no encontrada'}), 404

    with open(config_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    municipios = []

    if isinstance(data, list):
        # Lista directa (ej. baleares)
        municipios = sorted(data)

    elif isinstance(data, dict):
        # Dict con valores string: {NORMALIZADO: display} (asturias, cantabria, rioja)
        if all(isinstance(v, str) for v in data.values()):
            municipios = sorted(data.values())

        # Dict con listas: {region: [municipios]} (canarias, madrid, cataluna, etc.)
        elif any(isinstance(v, list) for v in data.values()):
            for valores in data.values():
                if isinstance(valores, list):
                    municipios.extend(valores)
            municipios = sorted(set(municipios))

        # Dict con clave "municipios"
        elif 'municipios' in data:
            municipios = sorted(data['municipios'])

    return jsonify(municipios)


@app.route('/admin/stats')
def admin_stats():
    """Dashboard de estadísticas (protegido por ADMIN_SECRET)."""
    secret = request.args.get('key', '')
    expected = os.environ.get('ADMIN_SECRET', '')

    if not expected or secret != expected:
        return "Unauthorized", 401

    return jsonify(get_stats())


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)
