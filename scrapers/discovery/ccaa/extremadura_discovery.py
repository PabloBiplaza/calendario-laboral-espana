"""
Auto-discovery de URLs del DOE para festivos locales de Extremadura.

Busca la URL del PDF/XLSX de festivos locales en el portal de datos abiertos
y en el Diario Oficial de Extremadura (DOE).

Estrategia:
1. Portal datos.gob.es: XLSX en juntaex.es
2. DOE: buscar PDF del anuncio de fiestas locales
3. Fallback: URLs conocidas

Datos conocidos:
- 2026: DOE nº 204, 23/10/2025, Resolución de 15 de octubre de 2025
- 2025: XLSX en juntaex.es/documents/77055/5801338/FestivosLocales2025.xlsx
"""

from typing import Optional
import requests
import time


# Portal datos abiertos XLSX
JUNTAEX_BASE = "https://www.juntaex.es/documents/77055/5801338"

# URLs conocidas
KNOWN_URLS = {
    2026: "https://www.laboral-social.com/sites/laboral-social.com/files/Calendario-fiestas-locales-extremadura-2026.pdf",
}


def _check_juntaex_xlsx(year: int) -> Optional[str]:
    """Busca el XLSX de festivos en la web de la Junta de Extremadura."""
    url = f"{JUNTAEX_BASE}/FestivosLocales{year}.xlsx"
    print(f"   🔎 Verificando XLSX en juntaex.es: FestivosLocales{year}.xlsx")

    try:
        response = requests.head(url, timeout=10, allow_redirects=True)
        if response.status_code == 200:
            print(f"   ✅ XLSX encontrado")
            return url
        else:
            print(f"   ❌ XLSX no disponible (status {response.status_code})")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    return None


def _check_known_url(year: int) -> Optional[str]:
    """Verifica si hay una URL conocida del DOE."""
    url = KNOWN_URLS.get(year)
    if not url:
        return None

    print(f"   🔎 Verificando URL conocida...")

    try:
        response = requests.head(url, timeout=10, allow_redirects=True)
        if response.status_code == 200:
            print(f"   ✅ URL válida")
            return url
        else:
            print(f"   ❌ URL no disponible (status {response.status_code})")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    return None


def auto_discover_extremadura(year: int) -> Optional[str]:
    """
    Descubre automáticamente la URL de festivos locales de Extremadura.

    Estrategia:
    1. XLSX en juntaex.es (datos abiertos)
    2. URL conocida del DOE (PDF)
    3. Instrucciones manuales

    Args:
        year: Año de los festivos buscados

    Returns:
        URL del PDF/XLSX, o None
    """
    print()
    print("=" * 80)
    print(f"🔎 AUTO-DISCOVERY DOE EXTREMADURA {year}")
    print("=" * 80)
    print(f"   Buscando festivos locales {year}")
    print()

    start_time = time.time()

    # Estrategia 1: XLSX datos abiertos
    url = _check_juntaex_xlsx(year)

    # Estrategia 2: URL conocida
    if not url:
        print()
        url = _check_known_url(year)

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
        print(f"   1. Busca en https://doe.juntaex.es/ 'fiestas locales {year}'")
        print(f"   2. Revisa https://datos.gob.es/ para Extremadura")
        print(f"   3. Copia la URL a config/extremadura_urls_cache.json")
        return None


if __name__ == "__main__":
    import sys
    year = int(sys.argv[1]) if len(sys.argv) > 1 else 2026
    url = auto_discover_extremadura(year)
    if url:
        print(f"\n✅ URL para {year}: {url}")
    else:
        print(f"\n❌ No se encontró URL para {year}")
