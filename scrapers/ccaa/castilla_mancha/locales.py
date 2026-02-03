"""
Scraper de festivos locales para Castilla-La Mancha.

Extrae festivos del DOCM (Diario Oficial de Castilla-La Mancha) en formato PDF.
Los datos provienen del Anuncio anual de la Dirección General de Autónomos,
Trabajo y Economía Social, publicado típicamente en diciembre del año anterior.

Formato PDF:
    Relación de Fiestas Locales de {Provincia}
    Municipio  dd de mes y dd de mes

Estrategia de obtención de datos (4 niveles):
1. Cache de festivos pre-generado (instantáneo, fiable en cloud)
2. URL en cache (castilla_mancha_urls_cache.json)
3. URL conocida en ccaa_registry.yaml
4. Auto-discovery vía datos abiertos + DOCM
"""

from scrapers.core.base_scraper import BaseScraper
from config.config_manager import CCAaRegistry
from typing import List, Dict, Optional
from pathlib import Path
import requests
import json
import re
import os


registry = CCAaRegistry()

# Meses en español
MESES = {
    'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
    'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
    'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
}

MESES_INV = {v: k for k, v in MESES.items()}


def _iso_to_fecha_texto(fecha_iso: str) -> str:
    """Convierte '2026-06-04' → '4 de junio'."""
    try:
        partes = fecha_iso.split('-')
        mes = int(partes[1])
        dia = int(partes[2])
        return f"{dia} de {MESES_INV.get(mes, str(mes))}"
    except (IndexError, ValueError):
        return fecha_iso


class CastillaLaManchaLocalesScraper(BaseScraper):
    """
    Scraper para festivos locales de Castilla-La Mancha desde el DOCM (PDF).

    Castilla-La Mancha publica festivos locales en el DOCM como PDF con
    las fiestas por provincia y municipio.

    Provincias: Albacete, Ciudad Real, Cuenca, Guadalajara, Toledo
    Municipios: ~919 oficiales (1024 incluyendo entidades locales)
    Total esperado: 8 nacionales + 4 autonómicos + 2 locales = 14 festivos
    """

    CACHE_FILE = "config/castilla_mancha_urls_cache.json"

    def __init__(self, year: int = 2026, municipio: Optional[str] = None):
        super().__init__(year=year, ccaa='castilla_mancha', tipo='locales')
        self._load_cache()

        # Fuzzy matching del municipio
        if municipio:
            from utils.normalizer import find_municipio

            try:
                with open('config/castilla_mancha_municipios.json', 'r', encoding='utf-8') as f:
                    provincias_data = json.load(f)

                todos_municipios = []
                for munis in provincias_data.values():
                    todos_municipios.extend(munis)

                mejor_match = find_municipio(municipio, todos_municipios, threshold=85)

                if mejor_match:
                    self.municipio = mejor_match
                    if mejor_match.lower() != municipio.lower():
                        print(f"   🔍 Fuzzy match: '{municipio}' → '{mejor_match}'")
                else:
                    self.municipio = municipio
            except FileNotFoundError:
                print(f"   ⚠️  Archivo de municipios no encontrado, usando nombre tal cual")
                self.municipio = municipio
        else:
            self.municipio = None

    def _load_cache(self):
        """Carga URLs del cache."""
        self.cached_urls = {}

        if os.path.exists(self.CACHE_FILE):
            try:
                with open(self.CACHE_FILE, 'r', encoding='utf-8') as f:
                    self.cached_urls = json.load(f)
                print(f"📦 Cache cargado: {len(self.cached_urls)} URLs")
            except Exception:
                self.cached_urls = {}

    def _save_to_cache(self, year_str: str, url: str):
        """Guarda URL en el cache."""
        cache = {}
        if os.path.exists(self.CACHE_FILE):
            try:
                with open(self.CACHE_FILE, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
            except Exception:
                pass

        cache[year_str] = url

        with open(self.CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)

        print(f"💾 URL guardada en cache: {self.CACHE_FILE}")

    def _load_festivos_cache(self) -> Dict[str, list]:
        """
        Carga cache de festivos pre-generado.

        Archivo: config/castilla_mancha_festivos_locales_{year}.json
        Estructura: {municipio: [{fecha, descripcion, provincia}]}

        Returns:
            Dict con festivos por municipio, o {} si no hay cache.
        """
        cache_path = Path(__file__).parent.parent.parent.parent / 'config' / f'castilla_mancha_festivos_locales_{self.year}.json'
        if not cache_path.exists():
            return {}
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Error cargando cache de festivos de Castilla-La Mancha: {e}")
            return {}

    def _resolve_from_cache(self, cache: Dict[str, list]):
        """
        Resuelve festivos desde el cache pre-generado.

        Args:
            cache: Dict {municipio: [{fecha, descripcion, ...}]}

        Returns:
            List[Dict] de festivos del municipio
        """
        if self.municipio:
            festivos_muni = cache.get(self.municipio)

            # Si no hay match exacto, buscar con normalización
            if not festivos_muni:
                municipio_upper = self.municipio.upper()
                for muni_cache, fests in cache.items():
                    if muni_cache.upper() == municipio_upper:
                        festivos_muni = fests
                        break

            # Fuzzy match como último recurso
            if not festivos_muni:
                from utils.normalizer import MunicipioNormalizer
                for muni_cache, fests in cache.items():
                    if MunicipioNormalizer.are_equivalent(self.municipio, muni_cache, threshold=85):
                        festivos_muni = fests
                        print(f"   🔍 Fuzzy match en cache: '{self.municipio}' → '{muni_cache}'")
                        break

            if festivos_muni:
                result = []
                for f in festivos_muni:
                    result.append({
                        'fecha': f['fecha'],
                        'fecha_texto': _iso_to_fecha_texto(f['fecha']),
                        'descripcion': f['descripcion'],
                        'tipo': 'local',
                        'ambito': 'local',
                        'municipio': self.municipio,
                        'provincia': f.get('provincia', ''),
                        'year': self.year
                    })
                print(f"   ✅ {len(result)} festivos locales desde cache para {self.municipio}")
                return result
            else:
                print(f"   ⚠️  Municipio '{self.municipio}' no encontrado en cache")
                return []
        else:
            return []

    def scrape(self):
        """
        Extrae festivos locales de Castilla-La Mancha.

        Estrategia de 4 niveles:
        1. Cache de festivos pre-generado (instantáneo, fiable en cloud)
        2-4. Flujo estándar BaseScraper

        Returns:
            List[Dict] de festivos del municipio
        """
        # Nivel 1: Cache de festivos pre-generado
        cache = self._load_festivos_cache()
        if cache:
            print(f"📦 Usando cache de festivos locales de Castilla-La Mancha {self.year} ({len(cache)} municipios)")
            return self._resolve_from_cache(cache)

        # Niveles 2-4: Flujo estándar BaseScraper
        print(f"⚠️  No hay cache de festivos para Castilla-La Mancha {self.year}, descargando PDF...")
        return super().scrape()

    def get_source_url(self) -> str:
        """
        Devuelve la URL del PDF del DOCM.

        Estrategia de 3 niveles:
        1. Cache de URLs
        2. URL en ccaa_registry.yaml
        3. Auto-discovery
        """
        year_str = str(self.year)

        # Nivel 1: Cache
        if year_str in self.cached_urls:
            url = self.cached_urls[year_str]
            print(f"📦 URL en cache para {self.year}: {url}")
            return url

        # Nivel 2: Registry
        url = registry.get_url('castilla_mancha', self.year, 'locales')
        if url:
            print(f"✅ URL oficial (registry) para {self.year}: {url}")
            return url

        # Nivel 3: Auto-discovery
        print(f"🔍 Auto-discovery para Castilla-La Mancha {self.year}...")
        try:
            from scrapers.discovery.ccaa.castilla_mancha_discovery import auto_discover_castilla_mancha
            url = auto_discover_castilla_mancha(self.year)

            if url:
                print(f"✅ URL encontrada via discovery: {url}")
                self._save_to_cache(year_str, url)
                return url
        except Exception as e:
            print(f"⚠️  Error en auto-discovery: {e}")

        raise ValueError(
            f"No se encontró URL para Castilla-La Mancha {self.year}.\n"
            f"Añade la URL a {self.CACHE_FILE}"
        )

    def fetch_content(self, url: str) -> str:
        """
        Descarga y extrae texto del PDF del DOCM.

        El PDF contiene texto plano extraíble con pdfplumber.
        """
        try:
            print(f"📥 Descargando PDF: {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # Extraer texto del PDF
            import pdfplumber
            import io

            pdf_bytes = io.BytesIO(response.content)
            full_text = ""

            with pdfplumber.open(pdf_bytes) as pdf:
                print(f"   📄 PDF con {len(pdf.pages)} páginas")
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        full_text += text + "\n"

            print(f"✅ PDF procesado ({len(full_text)} caracteres de texto)")
            return full_text

        except ImportError:
            print(f"❌ pdfplumber no instalado. Instala con: pip install pdfplumber")
            return ""
        except Exception as e:
            print(f"❌ Error descargando/procesando {url}: {e}")
            return ""

    def parse_festivos(self, content: str) -> List[Dict]:
        """
        Parsea festivos desde el texto extraído del PDF del DOCM.

        Formato:
            Relación de Fiestas Locales de {Provincia}
            Municipio dd de mes y dd de mes

        Returns:
            List[Dict] con festivos (filtrados por municipio si se especificó)
        """
        print("🔍 Parseando festivos locales de Castilla-La Mancha...")

        if self.municipio:
            print(f"   🎯 Filtrando por municipio: {self.municipio}")

        festivos = []
        provincia_actual = None

        lines = content.split('\n')

        for line in lines:
            line = line.strip()

            # Detectar cambio de provincia
            m_prov = re.match(r'Relación de Fiestas Locales de (.+)', line)
            if m_prov:
                provincia_actual = m_prov.group(1).strip()
                continue

            if not provincia_actual or not line:
                continue
            if 'AÑO XL' in line or line == 'Municipios Fiestas':
                continue

            # Parsear: "Municipio dd de mes y dd de mes"
            fecha_pattern = r'(\d{1,2}\s+(?:de\s+)?\w+)\s+y\s+(?:de\s+)?(\d{1,2}\s+(?:de\s+)?\w+)'
            m_fecha = re.search(fecha_pattern, line)

            if not m_fecha:
                continue

            municipio = line[:m_fecha.start()].strip()
            fecha1_str = m_fecha.group(1).strip()
            fecha2_str = m_fecha.group(2).strip()

            if not municipio:
                continue

            # Parsear fechas
            fecha1 = self._parse_fecha_texto(fecha1_str)
            fecha2 = self._parse_fecha_texto(fecha2_str)

            if not fecha1 or not fecha2:
                continue

            # Filtrar por municipio si se especificó
            if self.municipio:
                if self.municipio.upper() != municipio.upper():
                    from utils.normalizer import MunicipioNormalizer
                    if not MunicipioNormalizer.are_equivalent(
                        self.municipio, municipio, threshold=85
                    ):
                        continue

            festivos.append({
                'fecha': fecha1,
                'fecha_texto': _iso_to_fecha_texto(fecha1),
                'descripcion': f'Fiesta local ({fecha1_str})',
                'tipo': 'local',
                'ambito': 'local',
                'municipio': municipio,
                'provincia': provincia_actual,
                'year': self.year
            })
            festivos.append({
                'fecha': fecha2,
                'fecha_texto': _iso_to_fecha_texto(fecha2),
                'descripcion': f'Fiesta local ({fecha2_str})',
                'tipo': 'local',
                'ambito': 'local',
                'municipio': municipio,
                'provincia': provincia_actual,
                'year': self.year
            })

        if self.municipio:
            print(f"   ✅ {len(festivos)} festivos locales para {self.municipio}")
        else:
            print(f"   ✅ {len(festivos)} festivos locales parseados")

        return festivos

    def _parse_fecha_texto(self, texto: str) -> Optional[str]:
        """Parsea '24 de junio' → '2026-06-24'"""
        texto = texto.strip().lower()
        m = re.match(r'(\d{1,2})\s+(?:de\s+)?(\w+)', texto)
        if m:
            dia = int(m.group(1))
            mes_str = m.group(2)
            mes = MESES.get(mes_str)
            if mes:
                return f"{self.year}-{mes:02d}-{dia:02d}"
        return None


if __name__ == "__main__":
    import sys

    municipio = sys.argv[1] if len(sys.argv) > 1 else None
    year = int(sys.argv[2]) if len(sys.argv) > 2 else 2026

    scraper = CastillaLaManchaLocalesScraper(year=year, municipio=municipio)
    festivos = scraper.scrape()

    if festivos:
        print(f"\n📅 Festivos encontrados: {len(festivos)}")
        for f in festivos:
            print(f"   {f['fecha']} - {f['descripcion']} ({f.get('municipio', 'N/A')})")
    else:
        print("\n❌ No se encontraron festivos")
