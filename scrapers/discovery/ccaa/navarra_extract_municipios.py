"""
Extrae la lista de municipios de Navarra desde el BON.

Genera el archivo navarra_municipios.json con todos los municipios.
"""

import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path


def extract_municipios():
    """Extrae todos los municipios del BON de Navarra"""

    url = "https://bon.navarra.es/es/anuncio/-/texto/2025/241/12"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }

    print(f"Descargando BON de Navarra...")
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')

    # Buscar la tabla
    table = soup.find('table')

    if not table:
        print("No se encontró tabla en el HTML")
        return {}

    municipios = {}

    # Extraer filas de la tabla (saltar header)
    rows = table.find_all('tr')[1:]  # Saltar primera fila (header)

    for row in rows:
        cells = row.find_all('td')

        if len(cells) >= 2:
            municipio_raw = cells[0].get_text(strip=True)

            if municipio_raw and len(municipio_raw) >= 2:
                # Key: mayúsculas, Value: formato display
                municipios[municipio_raw.upper()] = municipio_raw

    return municipios


if __name__ == "__main__":
    # Extraer municipios
    municipios = extract_municipios()

    print(f"\n✓ Total municipios extraídos: {len(municipios)}")

    # Guardar en JSON
    output_path = Path(__file__).parent.parent.parent.parent / "config" / "navarra_municipios.json"

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(municipios, f, ensure_ascii=False, indent=2)

    print(f"✓ Guardado en: {output_path}")

    # Mostrar primeros 10
    print(f"\nPrimeros 10 municipios:")
    for idx, (key, value) in enumerate(list(municipios.items())[:10], 1):
        print(f"  {idx:2d}. {key:<40} → {value}")
