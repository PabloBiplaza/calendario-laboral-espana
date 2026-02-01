"""
Auto-discovery de URLs de OpenData Aragón.

Busca automáticamente las URLs del CSV de festivos locales
para cualquier año en el catálogo CKAN de OpenData Aragón.

Estrategia:
1. CKAN API package_search → buscar dataset por año
2. Dentro del dataset, buscar recurso CSV
3. Fallback a recurso XLS si no hay CSV

Datos conocidos:
- 2026: dataset f861c5f7-5424-4b3c-90bf-a6d2c2f5b0bd (CSV disponible)
- 2025: dataset ac141fff-7507-41ea-852c-fa55c2e3a275 (solo XLS/ICS)
"""

from typing import Optional
import requests
import time


CKAN_API_BASE = "https://opendata.aragon.es/ckan/api/3/action"

# Dataset IDs conocidos (para fallback)
KNOWN_DATASETS = {
    2026: "f861c5f7-5424-4b3c-90bf-a6d2c2f5b0bd",
    2025: "ac141fff-7507-41ea-852c-fa55c2e3a275",
}


def _find_csv_resource(resources: list) -> Optional[str]:
    """
    Busca un recurso CSV en la lista de recursos de un dataset CKAN.

    Prioriza CSV sobre otros formatos. Busca por formato y por extensión de URL.

    Args:
        resources: Lista de recursos del dataset CKAN

    Returns:
        URL del CSV o None
    """
    # Prioridad 1: recurso con formato CSV explícito
    for resource in resources:
        fmt = resource.get('format', '').upper()
        url = resource.get('url', '')
        if fmt == 'CSV' or url.lower().endswith('.csv'):
            return url

    # Prioridad 2: recurso XLS/XLSX como fallback
    for resource in resources:
        fmt = resource.get('format', '').upper()
        url = resource.get('url', '')
        if fmt in ('XLS', 'XLSX') or url.lower().endswith(('.xls', '.xlsx')):
            print(f"   ⚠️  No hay CSV, usando XLS: {url}")
            return url

    return None


def _search_by_api(year: int) -> Optional[str]:
    """
    Busca el dataset de festivos en el catálogo CKAN por año.

    Args:
        year: Año de los festivos buscados

    Returns:
        URL del recurso CSV/XLS o None
    """
    search_url = f"{CKAN_API_BASE}/package_search"
    params = {
        'q': f'festivos aragon {year}',
        'rows': 10
    }

    print(f"   🔎 Buscando en CKAN API: festivos aragon {year}")

    try:
        response = requests.get(search_url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        if not data.get('success'):
            print(f"   ❌ CKAN API devolvió error")
            return None

        results = data.get('result', {}).get('results', [])
        print(f"   📊 {len(results)} datasets encontrados")

        # Buscar dataset que contenga el año en el nombre
        for dataset in results:
            name = dataset.get('name', '')
            title = dataset.get('title', '')

            if str(year) in name or str(year) in title:
                print(f"   ✅ Dataset encontrado: {title}")
                resources = dataset.get('resources', [])
                url = _find_csv_resource(resources)
                if url:
                    return url

    except Exception as e:
        print(f"   ❌ Error en CKAN API search: {e}")

    return None


def _search_by_dataset_id(year: int) -> Optional[str]:
    """
    Busca en un dataset CKAN conocido por su ID.

    Args:
        year: Año de los festivos

    Returns:
        URL del recurso CSV/XLS o None
    """
    dataset_id = KNOWN_DATASETS.get(year)
    if not dataset_id:
        return None

    show_url = f"{CKAN_API_BASE}/package_show"
    params = {'id': dataset_id}

    print(f"   🔎 Buscando por dataset ID conocido: {dataset_id[:12]}...")

    try:
        response = requests.get(show_url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        if not data.get('success'):
            return None

        resources = data.get('result', {}).get('resources', [])
        return _find_csv_resource(resources)

    except Exception as e:
        print(f"   ❌ Error en CKAN API show: {e}")

    return None


def auto_discover_aragon(year: int) -> Optional[str]:
    """
    Descubre automáticamente la URL del CSV de festivos locales de Aragón.

    Los festivos se publican anualmente en OpenData Aragón como datasets CKAN.

    Estrategia:
    1. CKAN package_search por nombre/año
    2. Fallback: CKAN package_show con dataset ID conocido
    3. Si no encuentra nada, muestra instrucciones manuales

    Args:
        year: Año de los festivos buscados (ej: 2026)

    Returns:
        URL del CSV/XLS, o None si no se encuentra
    """
    print()
    print("=" * 80)
    print(f"🔎 AUTO-DISCOVERY OPENDATA ARAGÓN {year}")
    print("=" * 80)
    print(f"   Buscando festivos locales {year} en OpenData Aragón")
    print()

    start_time = time.time()

    # Estrategia 1: CKAN API search
    url = _search_by_api(year)

    # Estrategia 2: Dataset ID conocido
    if not url:
        print()
        url = _search_by_dataset_id(year)

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
        print(f"   1. Visita https://opendata.aragon.es/ manualmente")
        print(f"   2. Busca 'festivos aragon {year}' en el catálogo")
        print(f"   3. Copia la URL del CSV a config/aragon_urls_cache.json")
        return None


if __name__ == "__main__":
    import sys

    year = int(sys.argv[1]) if len(sys.argv) > 1 else 2026
    url = auto_discover_aragon(year)

    if url:
        print(f"\n✅ URL para {year}: {url}")
    else:
        print(f"\n❌ No se encontró URL para {year}")
