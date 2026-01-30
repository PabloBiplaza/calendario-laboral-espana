"""
Auto-discovery de URLs del BON (Boletín Oficial de Navarra).

Busca automáticamente las URLs de los HTMLs con festivos locales
para cualquier año en el Boletín Oficial de Navarra.

Usa búsqueda paralela para acelerar el descubrimiento.
"""

from typing import Optional
import requests
from bs4 import BeautifulSoup
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import time


def _validate_url(url: str, year: int) -> bool:
    """
    Valida que una URL encontrada corresponde al año correcto.

    Verifica que la página contiene festivos locales del año buscado.

    Args:
        url: URL del BON
        year: Año esperado

    Returns:
        True si la URL es válida para el año
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }

        response = requests.get(url, timeout=10, headers=headers)

        # Verificar que devuelve código 200
        if response.status_code != 200:
            return False

        content = response.text.lower()

        # Verificar que contiene palabras clave relacionadas con festivos locales
        keywords_required = ['fiestas', 'locales', str(year)]
        keywords_optional = [f'para el año {year}', f'calendario.*{year}', 'festividades']

        # Debe contener todas las required
        if not all(keyword in content for keyword in keywords_required):
            return False

        # Y al menos 1 de las opcionales
        if not any(re.search(keyword, content, re.IGNORECASE) for keyword in keywords_optional):
            return False

        # Verificar que tiene una tabla (formato HTML estructurado)
        soup = BeautifulSoup(content, 'html.parser')
        table = soup.find('table')

        if table:
            # Contar filas para asegurarse de que tiene suficientes municipios
            rows = table.find_all('tr')
            if len(rows) > 600:  # Navarra tiene 694 municipios
                return True

        return False

    except Exception:
        return False


def _probar_rango_bon(year_publicacion: int, inicio_bon: int, fin_bon: int, year: int) -> Optional[str]:
    """
    Prueba un rango de números de BON en paralelo.

    Args:
        year_publicacion: Año de publicación
        inicio_bon: Número BON inicial
        fin_bon: Número BON final
        year: Año de festivos buscado

    Returns:
        URL encontrada o None
    """
    # Para cada BON, probar varios números de anuncio
    for numero_bon in range(inicio_bon, fin_bon + 1):
        for numero_anuncio in range(1, 25):  # Probar anuncios 1-24
            test_url = f"https://bon.navarra.es/es/anuncio/-/texto/{year_publicacion}/{numero_bon}/{numero_anuncio}"

            if _validate_url(test_url, year):
                print(f"   ✅ Encontrado: BON {numero_bon}/{year_publicacion}, anuncio {numero_anuncio}")
                return test_url

    return None


def discover_url(year: int) -> Optional[str]:
    """
    Descubre automáticamente la URL del BON con festivos locales.

    Los festivos del año N se publican típicamente en noviembre-diciembre del año N-1.

    Usa búsqueda paralela para acelerar el proceso:
    - Divide el rango de búsqueda en chunks
    - Ejecuta búsquedas en paralelo (hasta 4 workers)
    - Retorna en cuanto encuentra la primera coincidencia

    Args:
        year: Año para buscar (ej: 2026)

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
    print(f"   Rango esperado: BON 230-250 (noviembre-diciembre)")
    print()

    start_time = time.time()

    # El patrón de URL es: /anuncio/-/texto/AÑO_PUBLICACION/NUMERO_BON/NUMERO_ANUNCIO
    # Los festivos suelen publicarse en BON 230-250 (noviembre-diciembre)

    # Dividir el rango en chunks para búsqueda paralela
    rangos = [
        (235, 240),  # Rango 1: BON 235-240 (más probable)
        (241, 245),  # Rango 2: BON 241-245
        (230, 234),  # Rango 3: BON 230-234
        (246, 250),  # Rango 4: BON 246-250
    ]

    url_encontrada = None

    with ThreadPoolExecutor(max_workers=4) as executor:
        print(f"   🔄 Lanzando 4 búsquedas paralelas...")

        # Lanzar búsquedas en paralelo
        futures = {
            executor.submit(_probar_rango_bon, year_publicacion, inicio, fin, year): (inicio, fin)
            for inicio, fin in rangos
        }

        # Recoger el primer resultado exitoso
        for future in as_completed(futures):
            rango = futures[future]
            try:
                resultado = future.result()
                if resultado:
                    url_encontrada = resultado
                    print(f"   ✓ URL descubierta en rango BON {rango[0]}-{rango[1]}")
                    # Cancelar búsquedas restantes
                    for f in futures:
                        f.cancel()
                    break
            except Exception as e:
                print(f"   ⚠️  Error en rango {rango}: {e}")

    elapsed = time.time() - start_time

    print()
    print("=" * 80)
    print("📋 RESULTADOS:")

    if url_encontrada:
        print(f"   ✅ URL encontrada: {url_encontrada}")
        print(f"   ⏱️  Tiempo: {elapsed:.2f}s")
        return url_encontrada
    else:
        print(f"   ✗ No se encontró URL para {year}")
        print(f"   ⏱️  Tiempo: {elapsed:.2f}s")
        print()
        print("💡 SUGERENCIAS:")
        print(f"   1. Visita https://bon.navarra.es/ manualmente")
        print(f"   2. Busca 'fiestas locales {year}' en el buscador")
        print(f"   3. Busca en boletines de noviembre-diciembre {year_publicacion}")
        print(f"   4. Copia la URL encontrada al archivo ccaa_registry.yaml")
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
