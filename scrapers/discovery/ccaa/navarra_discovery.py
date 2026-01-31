"""
Auto-discovery de URLs del BON (Boletín Oficial de Navarra).

Busca automáticamente las URLs de los HTMLs con festivos locales
para cualquier año en el Boletín Oficial de Navarra.

Usa búsqueda masivamente paralela (20 workers) para descubrir URLs
en menos de 30 segundos.

Datos conocidos:
- 2026: BON 241/2025, anuncio 12 → /texto/2025/241/12
- 2025: BON 260/2024, anuncio 4  → /texto/2024/260/4

Rango de búsqueda: BON 200-270 (octubre-diciembre del año anterior).
"""

from typing import Optional
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import time


def _check_url(args: tuple) -> Optional[str]:
    """
    Verifica si una URL específica contiene festivos locales del año buscado.

    Hace una única petición HTTP y valida el contenido:
    - Contiene keywords "fiestas", "locales" y el año
    - Tiene una tabla HTML con >600 filas (694 municipios de Navarra)

    Args:
        args: Tupla (year_publicacion, bon_num, anuncio_num, target_year)

    Returns:
        URL si es válida, None si no
    """
    year_pub, bon_num, anuncio_num, target_year = args
    url = f"https://bon.navarra.es/es/anuncio/-/texto/{year_pub}/{bon_num}/{anuncio_num}"

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, timeout=10, headers=headers)

        if response.status_code != 200:
            return None

        content = response.text.lower()

        # Verificar keywords básicas (rápido, sin parsing)
        if not ('fiestas' in content and 'locales' in content and str(target_year) in content):
            return None

        # Verificar tabla con suficientes municipios
        soup = BeautifulSoup(content, 'html.parser')
        table = soup.find('table')

        if not table:
            return None

        rows = table.find_all('tr')
        if len(rows) > 600:  # Navarra tiene 694 municipios
            return url

    except Exception:
        pass

    return None


def discover_url(year: int) -> Optional[str]:
    """
    Descubre automáticamente la URL del BON con festivos locales.

    Los festivos del año N se publican en octubre-diciembre del año N-1.
    Busca en BON 200-270 con 20 workers paralelos, probando anuncios 1-20
    por cada número de BON.

    Args:
        year: Año de los festivos buscados (ej: 2026)

    Returns:
        URL del HTML del BON, o None si no se encuentra

    Example:
        >>> discover_url(2026)
        'https://bon.navarra.es/es/anuncio/-/texto/2025/241/12'
    """
    year_publicacion = year - 1

    print(f"🔎 AUTO-DISCOVERY BON NAVARRA {year}")
    print("=" * 80)
    print(f"   Buscando festivos locales {year} en BON {year_publicacion}")
    print(f"   Rango: BON 200-270, anuncios 1-20")

    start_time = time.time()

    # Generar todas las combinaciones de URL a probar
    # Rango BON 200-270 cubre octubre-diciembre (donde se publican)
    tasks = []
    for bon_num in range(200, 271):
        for anuncio_num in range(1, 21):
            tasks.append((year_publicacion, bon_num, anuncio_num, year))

    print(f"   📊 {len(tasks)} URLs a probar con 20 workers paralelos")
    print()

    url_encontrada = None

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(_check_url, t): t for t in tasks}

        for future in as_completed(futures):
            result = future.result()
            if result:
                url_encontrada = result
                # Cancelar búsquedas restantes
                for f in futures:
                    f.cancel()
                break

    elapsed = time.time() - start_time

    print("=" * 80)

    if url_encontrada:
        print(f"   ✅ URL encontrada: {url_encontrada}")
        print(f"   ⏱️  Tiempo: {elapsed:.1f}s")
        return url_encontrada
    else:
        print(f"   ❌ No se encontró URL para {year}")
        print(f"   ⏱️  Tiempo: {elapsed:.1f}s")
        print()
        print("💡 SUGERENCIAS:")
        print(f"   1. Visita https://bon.navarra.es/ manualmente")
        print(f"   2. Busca 'fiestas locales {year}' en el buscador")
        print(f"   3. Busca en boletines de octubre-diciembre {year_publicacion}")
        return None


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Uso: python navarra_discovery.py <año>")
        print("Ejemplo: python navarra_discovery.py 2026")
        sys.exit(1)

    year = int(sys.argv[1])
    url = discover_url(year)

    if url:
        print(f"\n✓ URL encontrada para {year}:")
        print(f"  {url}")
        sys.exit(0)
    else:
        sys.exit(1)
