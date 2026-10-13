"""
Auto-discovery para Asturias usando OpenData y BOPA
"""

import requests
from typing import Optional


def auto_discover_asturias(year: int) -> Optional[str]:
    """
    Descubre automáticamente la URL del JSON/CSV de festivos locales de Asturias.

    Estrategia:
    1. Probar URL predecible del OpenData (CSV/JSON)
    2. Si falla, buscar en datos.gob.es
    3. Como último recurso, buscar en BOPA

    Returns:
        URL del JSON/CSV o None
    """

    print("=" * 80)
    print(f"🔎 AUTO-DISCOVERY ASTURIAS {year}")
    print("=" * 80)
    print()

    # ESTRATEGIA 1: URL predecible de OpenData (CSV es más estable)
    urls_predecibles = [
        f"https://descargas.asturias.es/asturias/opendata/CulturayOcio/calendario/dataset_calendario_festivos.csv",
        f"https://descargas.asturias.es/asturias/opendata/CulturayOcio/calendario/dataset_calendario_festivos.json",
    ]

    for url_predecible in urls_predecibles:
        formato = url_predecible.split('.')[-1].upper()
        print(f"🔍 Probando URL predecible de OpenData ({formato})...")
        print(f"   {url_predecible}")

        try:
            # GET (no HEAD): la URL es la misma todos los años, hay que comprobar
            # que el fichero ya trae fechas del año pedido (formato dd/mm/aaaa)
            r = requests.get(url_predecible, timeout=30, verify=False)  # verify=False por problemas SSL

            if r.status_code == 200 and f"/{year}".encode() not in r.content:
                print(f"   ❌ El fichero aún no contiene festivos de {year}\n")
            elif r.status_code == 200:
                print(f"   ✅ URL válida\n")
                print("=" * 80)
                print(f"✅ URL ENCONTRADA (OpenData {formato})")
                print("=" * 80)
                return url_predecible
            else:
                print(f"   ❌ No existe ({r.status_code})\n")
        except Exception as e:
            print(f"   ❌ Error de conexión: {e}\n")

    # ESTRATEGIA 2: Buscar en datos.gob.es (metadatos oficiales)
    print(f"🔍 Buscando en datos.gob.es...")

    try:
        # URL del dataset oficial en datos.gob.es
        url_dataset = "https://datos.gob.es/es/catalogo/a03002951-fiestas-locales-autonomicas-principado-asturias"

        print(f"   📄 Accediendo al catálogo: {url_dataset}")

        r_dataset = requests.get(url_dataset, timeout=15)

        if r_dataset.status_code == 200:
            print(f"   ✅ Catálogo accesible")

            # Buscar enlaces a CSV/JSON en el HTML
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(r_dataset.text, 'html.parser')

            for enlace in soup.find_all('a', href=True):
                href = enlace['href']

                if ('dataset_calendario_festivos' in href or 'calendario' in href.lower()) and \
                   (href.endswith('.csv') or href.endswith('.json')):

                    # Construir URL completa
                    if not href.startswith('http'):
                        continue

                    formato = href.split('.')[-1].upper()
                    print(f"   ✅ {formato} encontrado: {href}\n")
                    print("=" * 80)
                    print(f"✅ URL ENCONTRADA VIA DATOS.GOB.ES ({formato})")
                    print("=" * 80)

                    return href

            print(f"   ⚠️  No se encontraron enlaces directos a archivos\n")
        else:
            print(f"   ❌ Error accediendo al catálogo: {r_dataset.status_code}\n")

    except Exception as e:
        print(f"   ❌ Error en datos.gob.es: {e}\n")

    # ESTRATEGIA 3: Buscar en BOPA (fallback)
    print(f"🔍 Buscando en BOPA (Boletín Oficial del Principado de Asturias)...")

    try:
        # URL del buscador de BOPA
        url_buscador = "https://miprincipado.asturias.es/bopa/disposiciones"

        # Buscar por término "fiestas locales" y año anterior (se publica en mayo/junio)
        year_publicacion = year - 1

        params = {
            'p_r_p_dispositionText': f'fiestas locales {year}',
            'p_r_p_dispositionDate': f'{year_publicacion}',
        }

        print(f"   🔍 Buscando 'fiestas locales {year}' en BOPA...")

        r_buscador = requests.get(url_buscador, params=params, timeout=15)

        if r_buscador.status_code == 200:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(r_buscador.text, 'html.parser')

            # Buscar enlaces a PDFs de resoluciones
            for enlace in soup.find_all('a', href=True):
                href = enlace['href']
                texto = enlace.get_text().lower()

                if 'fiestas locales' in texto and str(year) in texto and '.pdf' in href:

                    # Construir URL completa
                    if not href.startswith('http'):
                        href = f"https://miprincipado.asturias.es{href}"

                    print(f"   ✅ PDF encontrado en BOPA: {href}\n")
                    print("=" * 80)
                    print(f"✅ URL ENCONTRADA VIA BOPA (PDF)")
                    print("=" * 80)
                    print(f"⚠️  NOTA: Es un PDF, se requiere parsing adicional")

                    return href

            print(f"   ❌ No se encontró PDF para {year}\n")
        else:
            print(f"   ❌ Error en BOPA: {r_buscador.status_code}\n")

    except Exception as e:
        print(f"   ❌ Error en BOPA: {e}\n")

    # No se encontró nada
    print("=" * 80)
    print("❌ AUTO-DISCOVERY FALLIDO")
    print("=" * 80)
    print(f"\n📋 Búsqueda manual necesaria:")
    print(f"   1. OpenData: https://descargas.asturias.es/asturias/opendata/CulturayOcio/calendario/")
    print(f"   2. Datos.gob.es: https://datos.gob.es/es/catalogo/a03002951-fiestas-locales-autonomicas-principado-asturias")
    print(f"   3. BOPA: https://miprincipado.asturias.es/bopa/disposiciones")
    print(f"   4. Añade la URL a: config/asturias_urls_cache.json")

    return None


if __name__ == "__main__":
    import sys
    year = int(sys.argv[1]) if len(sys.argv) > 1 else 2026

    url = auto_discover_asturias(year)

    if url:
        print(f"\n🎯 Resultado: {url}")
    else:
        print(f"\n❌ No se pudo encontrar URL para {year}")
