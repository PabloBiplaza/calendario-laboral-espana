"""
Scraper de festivos locales para la Comunidad Foral de Navarra.

Extrae festivos del BON (Boletín Oficial de Navarra) en formato HTML.
"""

from typing import List, Dict
import json
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

from scrapers.core.base_scraper import BaseScraper
from config.config_manager import registry
from scrapers.utils.date_calculator import calcular_fecha_relativa


class NavarraLocalesScraper(BaseScraper):
    """
    Scraper para festivos locales de Navarra.

    Navarra tiene 694 municipios/localidades, cada uno con 1 festivo local.
    Los festivos se publican en el BON (Boletín Oficial de Navarra).

    Particularidades:
    - Formato HTML (no PDF)
    - 94.4% fechas fijas, 5.6% fechas relativas/calculadas
    - Estructura: 8 nacionales + 4 autonómicos + 1 local = 14 festivos totales
    """

    def __init__(self, year: int = 2026, municipio: str = None):
        super().__init__(year, ccaa='navarra', tipo='locales')
        self.municipio = municipio
        self.municipios = self._load_municipios()

    def _load_municipios(self) -> Dict[str, str]:
        """
        Carga la lista de municipios de Navarra.

        Returns:
            Dict con {NOMBRE_NORMALIZADO: nombre_display}
        """
        municipios_file = registry.get_municipios_file('navarra')

        if not municipios_file:
            print("No se encontró archivo de municipios para Navarra")
            return {}

        municipios_path = Path(municipios_file)

        if not municipios_path.exists():
            print(f"Archivo de municipios no existe: {municipios_path}")
            return {}

        with open(municipios_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_source_url(self) -> str:
        """Obtiene la URL del BON para el año actual"""
        url = registry.get_url('navarra', self.year, 'locales')
        return url or ""

    def parse_festivos(self, content: str) -> List[Dict]:
        """
        Implementa método abstracto de BaseScraper.
        Para Navarra, retorna lista vacía ya que usamos parse_festivos_html.

        Args:
            content: Contenido (no usado)

        Returns:
            Lista vacía
        """
        return []

    def parse_festivos_html(self, html_content: str) -> Dict[str, List[Dict]]:
        """
        Parsea el contenido HTML del BON.

        Args:
            html_content: Contenido HTML de la página del BON

        Returns:
            Dict con {municipio: [festivos]}
        """
        soup = BeautifulSoup(html_content, 'html.parser')

        # Buscar la tabla
        table = soup.find('table')

        if not table:
            print("⚠️  No se encontró tabla en el HTML")
            return {}

        festivos_por_municipio = {}

        # Extraer filas de la tabla (saltar header)
        rows = table.find_all('tr')[1:]  # Saltar primera fila (header)

        for row in rows:
            cells = row.find_all('td')

            if len(cells) >= 2:
                municipio_raw = cells[0].get_text(strip=True)
                festividad_raw = cells[1].get_text(strip=True)

                if not municipio_raw or not festividad_raw:
                    continue

                # Normalizar municipio
                municipio = self._normalizar_municipio(municipio_raw)

                if not municipio:
                    continue

                # Parsear la fecha
                festivo = self._parsear_festividad(festividad_raw)

                if festivo:
                    festivos_por_municipio[municipio] = [festivo]

        return festivos_por_municipio

    def _parsear_festividad(self, texto: str) -> Dict:
        """
        Parsea una festividad, puede ser fecha fija o relativa.

        Args:
            texto: Texto de la festividad (ej: "22 de enero", "Segundo viernes de septiembre")

        Returns:
            Dict con el festivo o None si no se puede parsear
        """
        # Intentar fecha fija primero: "DD de mes"
        patron_fija = r'^(\d{1,2})\s+de\s+(\w+)$'
        match = re.match(patron_fija, texto, re.IGNORECASE)

        if match:
            # Fecha fija
            dia = int(match.group(1))
            mes_nombre = match.group(2).lower()

            # Meses en español
            meses = {
                'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
                'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
                'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
            }

            mes = meses.get(mes_nombre)

            if mes:
                try:
                    fecha = datetime(self.year, mes, dia)
                    return {
                        'fecha': fecha.strftime('%Y-%m-%d'),
                        'descripcion': 'Fiesta local',
                        'fecha_original': texto,
                        'calculada': False,
                        'tipo': 'local',
                        'ambito': 'local',
                        'year': self.year
                    }
                except ValueError:
                    print(f"⚠️  Fecha inválida: {dia}/{mes}/{self.year}")
                    return None

        # Si no es fecha fija, intentar calcular fecha relativa
        resultado = calcular_fecha_relativa(self.year, texto)

        if resultado:
            fecha, metodo = resultado
            return {
                'fecha': fecha.strftime('%Y-%m-%d'),
                'descripcion': 'Fiesta local',
                'fecha_original': texto,
                'calculada': True,
                'metodo_calculo': metodo,
                'tipo': 'local',
                'ambito': 'local',
                'year': self.year
            }

        # No se pudo parsear
        print(f"⚠️  No se pudo parsear festividad: '{texto}'")
        return None

    def _normalizar_municipio(self, nombre: str) -> str:
        """
        Normaliza el nombre del municipio.

        Args:
            nombre: Nombre del municipio

        Returns:
            Nombre normalizado en mayúsculas
        """
        # Limpiar espacios
        nombre = nombre.strip()

        # Ignorar líneas vacías o muy cortas
        if len(nombre) < 2:
            return None

        # Normalizar a mayúsculas
        return nombre.upper()

    def _load_cache(self) -> Dict[str, Dict]:
        """
        Carga el cache de festivos locales pre-generado.

        El BON puede no ser accesible desde servidores cloud (Streamlit Cloud),
        así que mantenemos un cache estático como fallback.

        Returns:
            Dict con {MUNICIPIO: {fecha, descripcion, ...}} o {} si no hay cache
        """
        cache_path = Path(__file__).parent.parent.parent.parent / 'config' / f'navarra_festivos_locales_{self.year}.json'

        if not cache_path.exists():
            return {}

        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Error cargando cache de Navarra: {e}")
            return {}

    def _festivo_from_cache(self, cache_entry: Dict) -> Dict:
        """
        Construye un dict de festivo a partir de una entrada del cache.

        Args:
            cache_entry: Dict con {fecha, descripcion, fecha_original, calculada, ...}

        Returns:
            Dict con formato estándar de festivo
        """
        festivo = {
            'fecha': cache_entry['fecha'],
            'descripcion': cache_entry.get('descripcion', 'Fiesta local'),
            'fecha_original': cache_entry.get('fecha_original', ''),
            'calculada': cache_entry.get('calculada', False),
            'tipo': 'local',
            'ambito': 'local',
            'year': self.year
        }
        if cache_entry.get('metodo_calculo'):
            festivo['metodo_calculo'] = cache_entry['metodo_calculo']
        return festivo

    def scrape(self):
        """
        Extrae festivos locales de Navarra.

        Estrategia cache-first: usa el cache pre-generado si existe (es más
        rápido y fiable). Solo descarga del BON en vivo si no hay cache
        disponible para el año solicitado.

        Returns:
            Si self.municipio está definido: List[Dict] de festivos del municipio
            Si no: Dict[str, List[Dict]] con {municipio: [festivos]}
        """
        # 1. Intentar cache primero (rápido y fiable)
        cache = self._load_cache()
        if cache:
            print(f"📦 Usando cache de festivos locales de Navarra {self.year} ({len(cache)} municipios)")
            return self._resolve_from_cache(cache)

        # 2. Si no hay cache, descargar del BON en vivo
        print(f"⚠️  No hay cache para Navarra {self.year}, descargando del BON...")
        return self._scrape_from_bon()

    def _resolve_from_cache(self, cache: Dict[str, Dict]):
        """
        Resuelve festivos desde el cache cargado.

        Args:
            cache: Dict con {MUNICIPIO: {fecha, descripcion, ...}}

        Returns:
            Si self.municipio: List[Dict] | Si no: Dict[str, List[Dict]]
        """
        if self.municipio:
            municipio_upper = self.municipio.upper()
            entry = cache.get(municipio_upper)

            if entry:
                festivo = self._festivo_from_cache(entry)
                print(f"✅ Festivo local desde cache: {festivo['fecha']} ({festivo.get('fecha_original', '')})")
                return [festivo]
            else:
                print(f"⚠️  '{self.municipio}' no encontrado en cache")
                return []
        else:
            result = {}
            for mun, entry in cache.items():
                result[mun] = [self._festivo_from_cache(entry)]
            print(f"✅ {len(result)} municipios cargados desde cache")
            return result

    def _scrape_from_bon(self):
        """
        Descarga y parsea festivos del BON en vivo.

        Returns:
            Si self.municipio: List[Dict] | Si no: Dict[str, List[Dict]]
        """
        url = registry.get_url('navarra', self.year, 'locales')

        if not url:
            print(f"❌ No hay URL configurada para Navarra {self.year}")
            return [] if self.municipio else {}

        print(f"Scraping festivos locales de Navarra {self.year}")
        print(f"URL: {url}")

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            print(f"📥 Descargando desde: {url}")
            response = requests.get(url, timeout=30, headers=headers)
            response.raise_for_status()
            print(f"✅ Descarga exitosa: {len(response.text)} caracteres")

            festivos_todos = self.parse_festivos_html(response.text)
            print(f"📊 Municipios parseados del HTML: {len(festivos_todos)}")

            if not festivos_todos:
                print(f"⚠️  El BON devolvió HTML pero sin tabla de festivos")
                return [] if self.municipio else {}

            if self.municipio:
                print(f"🎯 Filtrando por municipio: {self.municipio}")
                festivos_municipio = self.get_festivos_municipio_from_dict(festivos_todos, self.municipio)

                if festivos_municipio:
                    print(f"✅ Festivos locales extraídos: {len(festivos_municipio)}")
                else:
                    print(f"⚠️  NO se encontraron festivos para '{self.municipio}'")
                    print(f"   Municipios disponibles (muestra): {list(festivos_todos.keys())[:5]}")

                return festivos_municipio
            else:
                total_fijos = sum(1 for fests in festivos_todos.values() for f in fests if not f.get('calculada', False))
                total_calculados = sum(1 for fests in festivos_todos.values() for f in fests if f.get('calculada', False))

                print(f"✅ Extraídos festivos de {len(festivos_todos)} municipios")
                print(f"   • Fechas fijas: {total_fijos}")
                print(f"   • Fechas calculadas: {total_calculados}")
                return festivos_todos

        except requests.RequestException as e:
            print(f"❌ Error descargando el BON: {e}")
            return [] if self.municipio else {}
        except Exception as e:
            print(f"❌ Error parseando el BON: {e}")
            return [] if self.municipio else {}

    def get_festivos_municipio_from_dict(self, festivos_dict: Dict[str, List[Dict]], municipio: str) -> List[Dict]:
        """
        Busca festivos de un municipio en un diccionario.

        Args:
            festivos_dict: Dict con {municipio: [festivos]}
            municipio: Nombre del municipio

        Returns:
            Lista de festivos del municipio
        """
        municipio_upper = municipio.upper()

        for key, festivos in festivos_dict.items():
            if key.upper() == municipio_upper:
                return festivos

        return []

    def get_festivos_municipio(self, municipio: str) -> List[Dict]:
        """
        Obtiene festivos de un municipio específico.

        Args:
            municipio: Nombre del municipio

        Returns:
            Lista de festivos del municipio
        """
        festivos_todos = self.scrape()

        # Búsqueda case-insensitive
        municipio_upper = municipio.upper()

        for key, festivos in festivos_todos.items():
            if key.upper() == municipio_upper:
                return festivos

        return []


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Uso: python locales.py <año> [municipio]")
        print("Ejemplo: python locales.py 2026 PAMPLONA")
        sys.exit(1)

    year = int(sys.argv[1])
    municipio = sys.argv[2] if len(sys.argv) > 2 else None

    scraper = NavarraLocalesScraper(year=year, municipio=municipio)

    try:
        if municipio:
            festivos = scraper.scrape()
            print(f"\nFestivos de {municipio} en {year}:")
            for f in festivos:
                calculada_info = f" [calculada: {f.get('metodo_calculo', '')}]" if f.get('calculada') else ""
                print(f"  - {f['fecha']}: {f['descripcion']} (original: '{f.get('fecha_original', '')}')" + calculada_info)
        else:
            festivos_todos = scraper.scrape()
            print(f"\nTotal municipios: {len(festivos_todos)}")
            print("\nPrimeros 20 municipios:")
            for idx, (mun, fests) in enumerate(list(festivos_todos.items())[:20]):
                festivo = fests[0] if fests else {}
                calculada_info = " [calculada]" if festivo.get('calculada') else ""
                print(f"  {idx+1:2d}. {mun:<35} {festivo.get('fecha', 'N/A')}" + calculada_info)
    except Exception as e:
        print(f"\n⚠️  Error: {e}")
        import traceback
        traceback.print_exc()
