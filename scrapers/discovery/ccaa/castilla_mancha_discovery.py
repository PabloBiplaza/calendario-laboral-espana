"""
Auto-discovery de URLs del DOCM para festivos locales de Castilla-La Mancha.

Busca automáticamente la URL del PDF de festivos locales para cualquier año
en el Diario Oficial de Castilla-La Mancha (DOCM).

Estrategia:
1. Datos abiertos: buscar XLSX/CSV en datosabiertos.castillalamancha.es
2. DOCM: buscar el anuncio de fiestas locales en el DOCM
3. Portal castillalamancha.es: buscar PDF del anuncio

Datos conocidos:
- 2026: DOCM nº 240, 12/12/2025, Anuncio 2025/9468 (PDF)
- 2024: DOCM nº 243, 21/12/2023, Anuncio 2023/10208 (PDF)
"""

from typing import Optional
import requests
import time


# Portal de datos abiertos
DATOS_ABIERTOS_BASE = "https://datosabiertos.castillalamancha.es/sites/datosabiertos.castillalamancha.es/files"

# URLs conocidas del DOCM
KNOWN_DOCM_URLS = {
    2026: "https://docm.jccm.es/portaldocm/descargarArchivo.do?ruta=2025/12/12/pdf/2025_9468.pdf&tipo=rutaDocm",
    2024: "https://www.castillalamancha.es/sites/default/files/documentos/pdf/20240103/anuncio_14-12-2023_festivos_locales_clm_2024.pdf",
}


def _check_datos_abiertos(year: int) -> Optional[str]:
    """
    Busca el XLSX/CSV de festivos en el portal de datos abiertos de CLM.

    Los ficheros siguen el patrón:
    CALENDARIO FESTIVOS LOCALES {year}.xlsx

    Args:
        year: Año de los festivos

    Returns:
        URL del fichero o None
    """
    # Probar variantes de nombre
    nombres = [
        f"CALENDARIO%20FESTIVOS%20LOCALES%20{year}.xlsx",
        f"festivos%20locales%20{year}.xlsx",
        f"festivos%20locales%20{year}.csv",
        f"fiestas%20locales%20{year}.csv",
    ]

    print(f"   🔎 Buscando en datos abiertos CLM...")

    for nombre in nombres:
        url = f"{DATOS_ABIERTOS_BASE}/{nombre}"
        try:
            response = requests.head(url, timeout=10, allow_redirects=True)
            if response.status_code == 200:
                print(f"   ✅ Encontrado: {url}")
                return url
        except Exception:
            pass

    print(f"   ❌ No encontrado en datos abiertos")
    return None


def _check_known_url(year: int) -> Optional[str]:
    """
    Verifica si hay una URL conocida del DOCM para el año.

    Args:
        year: Año de los festivos

    Returns:
        URL del PDF/HTML o None
    """
    url = KNOWN_DOCM_URLS.get(year)
    if not url:
        return None

    print(f"   🔎 Verificando URL conocida del DOCM...")

    try:
        response = requests.head(url, timeout=10, allow_redirects=True)
        if response.status_code == 200:
            content_length = response.headers.get('Content-Length', '?')
            print(f"   ✅ URL válida (status 200, {content_length} bytes)")
            return url
        else:
            print(f"   ❌ URL no disponible (status {response.status_code})")
            return None
    except Exception as e:
        print(f"   ❌ Error verificando URL: {e}")
        return None


def auto_discover_castilla_mancha(year: int) -> Optional[str]:
    """
    Descubre automáticamente la URL de festivos locales de Castilla-La Mancha.

    Los festivos se publican anualmente en el DOCM como PDF y opcionalmente
    como XLSX en el portal de datos abiertos.

    Estrategia:
    1. Portal datos abiertos (XLSX/CSV)
    2. URL conocida del DOCM (PDF)
    3. Si no encuentra nada, muestra instrucciones manuales

    Args:
        year: Año de los festivos buscados (ej: 2026)

    Returns:
        URL del PDF/CSV/XLSX, o None si no se encuentra
    """
    print()
    print("=" * 80)
    print(f"🔎 AUTO-DISCOVERY DOCM CASTILLA-LA MANCHA {year}")
    print("=" * 80)
    print(f"   Buscando festivos locales {year}")
    print()

    start_time = time.time()

    # Estrategia 1: Datos abiertos
    url = _check_datos_abiertos(year)

    # Estrategia 2: URL conocida del DOCM
    if not url:
        print()
        url = _check_known_url(year)

    elapsed = time.time() - start_time

    print()
    print("=" * 80)

    if url:
        print(f"   ✅ URL encontrada: {url}")
        print(f"   ⏱️  Tiempo: {elapsed:.1f}s")
        return url
    else:
        print(f"   ❌ No se encontró URL para {year}")
        print(f"   ⏱️  Tiempo: {elapsed:.1f}s")
        print()
        print("💡 SUGERENCIAS:")
        print(f"   1. Busca en https://docm.jccm.es/ 'fiestas locales {year}'")
        print(f"   2. Revisa https://datosabiertos.castillalamancha.es/")
        print(f"   3. Copia la URL a config/castilla_mancha_urls_cache.json")
        return None


if __name__ == "__main__":
    import sys

    year = int(sys.argv[1]) if len(sys.argv) > 1 else 2026
    url = auto_discover_castilla_mancha(year)

    if url:
        print(f"\n✅ URL para {year}: {url}")
    else:
        print(f"\n❌ No se encontró URL para {year}")
