"""
Análisis de fechas relativas en el BON de Navarra.

Extrae todos los festivos locales y los categoriza en:
- Fechas fijas (día y mes específicos)
- Fechas relativas/calculadas (segundo viernes de septiembre, etc.)
"""

import requests
from bs4 import BeautifulSoup
from collections import Counter
import re

def extract_navarra_holidays():
    """Extrae todos los festivos del BON de Navarra"""

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
        return []

    festivos = []

    # Extraer filas de la tabla (saltar header)
    rows = table.find_all('tr')[1:]  # Saltar primera fila (header)

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


def analizar_patrones_relativos(relativas):
    """Analiza los patrones de fechas relativas"""

    patrones = []

    for item in relativas:
        festividad = item['festividad'].lower()

        # Identificar tipo de patrón
        if 'primer' in festividad or 'segundo' in festividad or 'tercer' in festividad:
            patron = 'ordinal_dia_semana'  # "segundo viernes de septiembre"
        elif 'siguiente' in festividad or 'anterior' in festividad:
            patron = 'relativo_a_santo'  # "viernes de la siguiente semana a San Lucas"
        elif 'carnaval' in festividad or 'pascua' in festividad or 'corpus' in festividad:
            patron = 'liturgico'  # "Viernes de carnaval"
        elif 'san ' in festividad or 'santa ' in festividad:
            patron = 'santoral'  # Referencia a día del santo
        else:
            patron = 'otro'

        patrones.append(patron)

    return patrones


if __name__ == "__main__":
    # Extraer festivos
    festivos = extract_navarra_holidays()

    print(f"\n✓ Total festivos extraídos: {len(festivos)}")

    # Categorizar
    fijas, relativas = categorizar_fechas(festivos)

    print(f"\n📊 CATEGORIZACIÓN:")
    print(f"  • Fechas fijas: {len(fijas)} ({len(fijas)/len(festivos)*100:.1f}%)")
    print(f"  • Fechas relativas: {len(relativas)} ({len(relativas)/len(festivos)*100:.1f}%)")

    # Analizar patrones de fechas relativas
    if relativas:
        print(f"\n📋 FECHAS RELATIVAS (primeros 20 ejemplos):")
        for item in relativas[:20]:
            print(f"  • {item['municipio']:<30} → {item['festividad']}")

        # Analizar patrones
        patrones = analizar_patrones_relativos(relativas)
        contador = Counter(patrones)

        print(f"\n🔍 TIPOS DE PATRONES RELATIVOS:")
        for patron, count in contador.most_common():
            print(f"  • {patron:<25} {count:>3} ({count/len(relativas)*100:.1f}%)")

    # Mostrar algunos ejemplos de fechas fijas
    print(f"\n📅 FECHAS FIJAS (primeros 10 ejemplos):")
    for item in fijas[:10]:
        print(f"  • {item['municipio']:<30} → {item['festividad']}")
