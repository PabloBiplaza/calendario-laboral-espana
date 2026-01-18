"""
Auto-discovery de URLs del BOR (Boletín Oficial de La Rioja).

Busca automáticamente las URLs de los PDFs con festivos locales
para cualquier año en el Boletín Oficial de La Rioja.
"""

from typing import Optional
import requests
from bs4 import BeautifulSoup
import re


def discover_url(year: int) -> Optional[str]:
    """
    Descubre automáticamente la URL del BOR con festivos locales.

    Args:
        year: Año para buscar (ej: 2026)

    Returns:
        URL de la página del anuncio, o None si no se encuentra

    Example:
        >>> discover_url(2026)
        'https://web.larioja.org/bor-portada/boranuncio?n=anu-571537'
    """
    # URL de búsqueda en el BOR
    search_url = f"https://web.larioja.org/bor-portada/bor?q=fiestas+locales+{year}"

    try:
        # Realizar la búsqueda
        response = requests.get(search_url, timeout=30)
        response.raise_for_status()

        # Parsear el HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        # Buscar el primer resultado con el título específico
        # El título debe contener "Calendario laboral de fiestas locales" y el año
        for result in soup.find_all('a', href=True):
            text = result.get_text().strip()

            # Verificar que el título contiene las palabras clave
            if ('calendario laboral' in text.lower() and
                'fiestas locales' in text.lower() and
                str(year) in text):

                # Extraer la URL del enlace HTML (no el PDF directo)
                # Buscamos enlaces que van a /bor-portada/boranuncio
                href = result.get('href', '')

                # Si es relativo, convertir a absoluto
                if href.startswith('/bor-portada/boranuncio'):
                    full_url = f"https://web.larioja.org{href}"
                    print(f"✓ URL descubierta para {year}: {full_url}")
                    return full_url

        # También buscar directamente en el HTML por el patrón del enlace
        html_pattern = r'href="(/bor-portada/boranuncio\?n=anu-\d+)"'
        matches = re.findall(html_pattern, response.text)

        if matches:
            # Validar cada URL encontrada hasta encontrar la correcta para el año
            for relative_url in matches:
                full_url = f"https://web.larioja.org{relative_url}"

                # Validar que realmente corresponde al año buscado
                if _validate_url(full_url, year):
                    print(f"✓ URL descubierta para {year}: {full_url}")
                    return full_url

        print(f"✗ No se encontró URL para {year}")
        return None

    except requests.RequestException as e:
        print(f"✗ Error al buscar URL para {year}: {e}")
        return None


def _validate_url(url: str, year: int) -> bool:
    """
    Valida que una URL encontrada corresponde al año correcto.

    Args:
        url: URL del anuncio del BOR
        year: Año esperado

    Returns:
        True si la URL es válida para el año
    """
    try:
        # Descargar la página del anuncio
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        content = response.text

        # Buscar el título específico en la página
        # Patrón: <p class="entradilla_anuncio">Calendario laboral de fiestas locales {year}</p>
        # El título puede ser "fiestas locales 2026" o "fiestas locales del año 2026"
        soup = BeautifulSoup(content, 'html.parser')
        title_elem = soup.find('p', class_='entradilla_anuncio')

        if title_elem:
            title = title_elem.get_text().strip().lower()

            # Verificar que contiene "fiestas locales" y el año
            if 'fiestas locales' in title:
                # Debe contener el año específico
                if str(year) in title:
                    # Verificar que no es otro año (evitar falsos positivos)
                    # Por ejemplo, evitar que "2026" matchee con "2025"
                    if f' {year}' in title or f'año {year}' in title:
                        return True

        return False

    except requests.RequestException:
        return False


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Uso: python rioja_discovery.py <año>")
        print("Ejemplo: python rioja_discovery.py 2026")
        sys.exit(1)

    year = int(sys.argv[1])
    url = discover_url(year)

    if url:
        print(f"\n✓ URL encontrada para {year}:")
        print(f"  {url}")
    else:
        print(f"\n✗ No se pudo encontrar URL para {year}")
        sys.exit(1)
