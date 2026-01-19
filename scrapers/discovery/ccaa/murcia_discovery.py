"""
Auto-discovery de URLs del BORM (Boletín Oficial de la Región de Murcia).

Busca automáticamente las URLs de los PDFs con festivos locales
para cualquier año en el Boletín Oficial de la Región de Murcia.
"""

from typing import Optional
import requests
from bs4 import BeautifulSoup
import re


def discover_url(year: int) -> Optional[str]:
    """
    Descubre automáticamente la URL del BORM con festivos locales.

    Los festivos del año N se publican típicamente en julio del año N-1.

    Args:
        year: Año para buscar (ej: 2026)

    Returns:
        URL del PDF del BORM, o None si no se encuentra

    Example:
        >>> discover_url(2026)
        'https://www.borm.es/services/anuncio/ano/2025/numero/3546/pdf?id=837607'
    """
    # El año de publicación suele ser el año anterior
    year_publicacion = year - 1

    # URL de búsqueda en el BORM
    # El BORM usa un sistema de búsqueda más simple
    search_url = f"https://www.borm.es/borm/vista/busqueda/busqueda.jsf"

    try:
        # Realizar búsqueda
        params = {
            'textoLibre': f'calendario fiestas laborales {year}',
            'ano': year_publicacion,
            'fechaPublicacionDesde': f'01/06/{year_publicacion}',  # Buscar desde junio
            'fechaPublicacionHasta': f'31/12/{year_publicacion}'   # Hasta diciembre
        }

        response = requests.get(search_url, params=params, timeout=30)
        response.raise_for_status()

        # Parsear el HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        # Buscar enlaces a anuncios que contengan "fiestas laborales" o "calendario"
        for link in soup.find_all('a', href=True):
            text = link.get_text().strip().lower()
            href = link.get('href', '')

            # Verificar que el enlace contiene las palabras clave
            if ('calendario' in text or 'fiestas' in text or 'laborales' in text):
                # Extraer el enlace al PDF
                if 'services/anuncio' in href:
                    # Construir URL completa
                    if href.startswith('http'):
                        pdf_url = href
                    else:
                        pdf_url = f"https://www.borm.es{href}"

                    # Validar que realmente corresponde al año buscado
                    if _validate_url(pdf_url, year):
                        print(f"✓ URL descubierta para {year}: {pdf_url}")
                        return pdf_url

        # Si la búsqueda web no funciona, intentar con patrón de URL directo
        # Los números de anuncio suelen ser secuenciales, podemos probar rangos
        print(f"⚠️  Búsqueda web no encontró resultados")
        print(f"   Intentando descubrimiento por patrón de URL...")

        # Para 2026 sabemos que es: ano/2025/numero/3546/id=837607
        # El número y el ID están relacionados, intentamos descubrir ambos
        base_numero = 3546 if year == 2026 else 3500  # Aproximación
        base_id = 837607 if year == 2026 else 837550  # Aproximación

        # Probar primero un rango cercano al base
        for offset in range(-50, 51):  # Probar ±50 números
            numero = base_numero + offset
            id_anuncio = base_id + offset

            test_url = f"https://www.borm.es/services/anuncio/ano/{year_publicacion}/numero/{numero}/pdf?id={id_anuncio}"

            if _validate_url(test_url, year):
                print(f"✓ URL descubierta para {year}: {test_url}")
                return test_url

        print(f"✗ No se encontró URL para {year}")
        return None

    except requests.RequestException as e:
        print(f"✗ Error al buscar URL para {year}: {e}")
        return None


def _validate_url(url: str, year: int) -> bool:
    """
    Valida que una URL encontrada corresponde al año correcto.

    Descarga el PDF y verifica que contiene los festivos del año buscado.

    Args:
        url: URL del PDF del BORM
        year: Año esperado

    Returns:
        True si la URL es válida para el año
    """
    try:
        # Headers para evitar problemas con anti-bot
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }

        # Descargar el PDF completo para verificar su contenido
        response = requests.get(url, timeout=15, headers=headers, allow_redirects=True)

        # Verificar que devuelve código 200
        if response.status_code != 200:
            return False

        content = response.content

        # Verificar que es un PDF
        if not content.startswith(b'%PDF'):
            return False

        # Verificar que el PDF contiene texto relacionado con festivos del año buscado
        # Buscar cadenas como "año 2026", "para el año 2026", "fiestas laborales para el año 2026"
        content_str = content.decode('latin-1', errors='ignore')

        # Patrones a buscar
        patterns = [
            f'año {year}',
            f'para el año {year}',
            f'fiestas laborales para el año {year}',
            f'calendario.*{year}',
        ]

        # Si encuentra alguno de los patrones, la URL es válida
        for pattern in patterns:
            if re.search(pattern, content_str, re.IGNORECASE):
                return True

        return False

    except Exception:
        return False


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Uso: python murcia_discovery.py <año>")
        print("Ejemplo: python murcia_discovery.py 2026")
        sys.exit(1)

    year = int(sys.argv[1])
    url = discover_url(year)

    if url:
        print(f"\n✓ URL encontrada para {year}:")
        print(f"  {url}")
    else:
        print(f"\n✗ No se pudo encontrar URL para {year}")
        sys.exit(1)
