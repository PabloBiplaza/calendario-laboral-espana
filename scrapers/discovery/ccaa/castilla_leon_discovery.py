"""
Auto-discovery de URLs de OpenData Castilla y León.

Busca automáticamente las URLs del CSV de festivos locales
para cualquier año en el portal de transparencia de la JCyL.

Estrategia:
1. URL predecible: https://transparencia.jcyl.es/empresas/FIESTAS-LOCALES-INE-{year}.csv
2. Validación con HEAD request
3. Fallback: Opendatasoft API

Datos conocidos:
- 2026: FIESTAS-LOCALES-INE-2026.csv (confirmado)
- 2025: FIESTAS-LOCALES-INE-2025.csv (confirmado)
"""

from typing import Optional
import requests
import time


BASE_URL = "https://transparencia.jcyl.es/empresas/FIESTAS-LOCALES-INE-{year}.csv"

# URLs de Opendatasoft como fallback
OPENDATASOFT_API = "https://analisis.datosabiertos.jcyl.es/api/explore/v2.1/catalog/datasets"


def _check_predictable_url(year: int) -> Optional[str]:
    """
    Verifica si la URL predecible del CSV existe.

    La JCyL publica CSVs con patrón de URL predecible:
    https://transparencia.jcyl.es/empresas/FIESTAS-LOCALES-INE-{year}.csv

    Args:
        year: Año de los festivos

    Returns:
        URL del CSV si existe (HEAD 200), o None
    """
    url = BASE_URL.format(year=year)
    print(f"   🔎 Verificando URL predecible: {url}")

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


def _search_opendatasoft(year: int) -> Optional[str]:
    """
    Busca el CSV en el portal Opendatasoft de Castilla y León.

    Como fallback cuando la URL predecible no funciona.

    Args:
        year: Año de los festivos

    Returns:
        URL de exportación CSV o None
    """
    print(f"   🔎 Buscando en Opendatasoft: fiestas locales {year}")

    try:
        # Buscar datasets que contengan "fiestas locales"
        search_url = f"{OPENDATASOFT_API}"
        params = {
            'where': f'search(default, "fiestas locales {year}")',
            'limit': 5
        }

        response = requests.get(search_url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        results = data.get('results', [])
        print(f"   📊 {len(results)} datasets encontrados")

        for dataset in results:
            dataset_id = dataset.get('dataset_id', '')
            title = dataset.get('metas', {}).get('default', {}).get('title', '')

            if str(year) in dataset_id or str(year) in str(title):
                print(f"   ✅ Dataset encontrado: {title}")
                # Construir URL de exportación CSV
                export_url = (
                    f"https://analisis.datosabiertos.jcyl.es/api/explore/v2.1/"
                    f"catalog/datasets/{dataset_id}/exports/csv"
                    f"?delimiter=;"
                )
                return export_url

    except Exception as e:
        print(f"   ❌ Error en Opendatasoft: {e}")

    return None


def auto_discover_castilla_leon(year: int) -> Optional[str]:
    """
    Descubre automáticamente la URL del CSV de festivos locales de Castilla y León.

    Los festivos se publican anualmente en el portal de transparencia de la JCyL
    con URLs predecibles por año.

    Estrategia:
    1. URL predecible (transparencia.jcyl.es) + HEAD request
    2. Fallback: Opendatasoft API
    3. Si no encuentra nada, muestra instrucciones manuales

    Args:
        year: Año de los festivos buscados (ej: 2026)

    Returns:
        URL del CSV, o None si no se encuentra
    """
    print()
    print("=" * 80)
    print(f"🔎 AUTO-DISCOVERY OPENDATA CASTILLA Y LEÓN {year}")
    print("=" * 80)
    print(f"   Buscando festivos locales {year} en transparencia.jcyl.es")
    print()

    start_time = time.time()

    # Estrategia 1: URL predecible
    url = _check_predictable_url(year)

    # Estrategia 2: Opendatasoft
    if not url:
        print()
        url = _search_opendatasoft(year)

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
        print(f"   1. Visita https://transparencia.jcyl.es/ manualmente")
        print(f"   2. Busca 'fiestas locales {year}' en el catálogo")
        print(f"   3. Copia la URL del CSV a config/castilla_leon_urls_cache.json")
        return None


if __name__ == "__main__":
    import sys

    year = int(sys.argv[1]) if len(sys.argv) > 1 else 2026
    url = auto_discover_castilla_leon(year)

    if url:
        print(f"\n✅ URL para {year}: {url}")
    else:
        print(f"\n❌ No se encontró URL para {year}")
