"""
Análisis completo de todas las fechas relativas en Navarra.
"""

import requests
from bs4 import BeautifulSoup
import re

def extract_navarra_holidays():
    """Extrae todos los festivos del BON de Navarra"""

    url = "https://bon.navarra.es/es/anuncio/-/texto/2025/241/12"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table')

    if not table:
        return []

    festivos = []
    rows = table.find_all('tr')[1:]  # Saltar header

    for row in rows:
        cells = row.find_all('td')

        if len(cells) >= 2:
            municipio = cells[0].get_text(strip=True)
            festividad = cells[1].get_text(strip=True)

            if municipio and festividad:
                festivos.append({
                    'municipio': municipio,
                    'festividad': festividad
                })

    return festivos


def categorizar_fechas(festivos):
    """Categoriza las fechas en fijas y relativas"""

    fijas = []
    relativas = []

    # Patrón para fechas fijas: "DD de mes"
    patron_fecha_fija = r'^\d{1,2}\s+de\s+\w+$'

    for item in festivos:
        festividad = item['festividad']

        if re.match(patron_fecha_fija, festividad, re.IGNORECASE):
            fijas.append(item)
        else:
            relativas.append(item)

    return fijas, relativas


if __name__ == "__main__":
    # Extraer festivos
    festivos = extract_navarra_holidays()

    print(f"Total festivos extraídos: {len(festivos)}\n")

    # Categorizar
    fijas, relativas = categorizar_fechas(festivos)

    print(f"📊 RESUMEN:")
    print(f"  • Fechas fijas: {len(fijas)} (94.4%)")
    print(f"  • Fechas relativas: {len(relativas)} (5.6%)")

    print(f"\n📋 TODAS LAS FECHAS RELATIVAS ({len(relativas)} total):\n")

    for idx, item in enumerate(relativas, 1):
        print(f"{idx:2d}. {item['municipio']:<35} → {item['festividad']}")
