"""
Scraper de festivos locales para Extremadura.

Extrae festivos del DOE (Diario Oficial de Extremadura) en formato PDF.
Los datos provienen de la Resolución anual de la Dirección General de Trabajo,
publicada típicamente en octubre del año anterior.

Formato PDF:
    MUNICIPIO.- fecha1 y fecha2.

Estrategia de obtención de datos (4 niveles):
1. Cache de festivos pre-generado (instantáneo, fiable en cloud)
2. URL en cache (extremadura_urls_cache.json)
3. URL conocida en ccaa_registry.yaml
4. Auto-discovery vía datos abiertos + DOE
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


def _title_case_municipio(name: str) -> str:
    """Convierte MAYÚSCULAS → Title Case."""
    exceptions = {'DE', 'DEL', 'LA', 'LAS', 'LOS', 'EL', 'Y', 'EN', 'AL', 'A'}
    words = name.split()
    result = []
    for i, w in enumerate(words):
        if i == 0 or w.upper() not in exceptions:
            result.append(w.capitalize())
        else:
            result.append(w.lower())
    return ' '.join(result)


class ExtremaduraLocalesScraper(BaseScraper):
    """
    Scraper para festivos locales de Extremadura desde el DOE (PDF).

    Extremadura publica festivos locales en el DOE como PDF con
    las fiestas por provincia y municipio.

    Provincias: Badajoz, Cáceres
    Municipios: ~388 oficiales (440 incluyendo pedanías)
    Total esperado: 8 nacionales + 4 autonómicos + 2 locales = 14 festivos
    """

    CACHE_FILE = "config/extremadura_urls_cache.json"

    def __init__(self, year: int = 2026, municipio: Optional[str] = None):
        super().__init__(year=year, ccaa='extremadura', tipo='locales')
        self._load_cache()

        if municipio:
            from utils.normalizer import find_municipio
            try:
                with open('config/extremadura_municipios.json', 'r', encoding='utf-8') as f:
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
                self.municipio = municipio
        else:
            self.municipio = None

    def _load_cache(self):
        self.cached_urls = {}
        if os.path.exists(self.CACHE_FILE):
            try:
                with open(self.CACHE_FILE, 'r', encoding='utf-8') as f:
                    self.cached_urls = json.load(f)
                print(f"📦 Cache cargado: {len(self.cached_urls)} URLs")
            except Exception:
                self.cached_urls = {}

    def _save_to_cache(self, year_str: str, url: str):
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
        cache_path = Path(__file__).parent.parent.parent.parent / 'config' / f'extremadura_festivos_locales_{self.year}.json'
        if not cache_path.exists():
            return {}
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Error cargando cache de festivos de Extremadura: {e}")
            return {}

    def _resolve_from_cache(self, cache: Dict[str, list]):
        if self.municipio:
            festivos_muni = cache.get(self.municipio)

            if not festivos_muni:
                municipio_upper = self.municipio.upper()
                for muni_cache, fests in cache.items():
                    if muni_cache.upper() == municipio_upper:
                        festivos_muni = fests
                        break

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
        cache = self._load_festivos_cache()
        if cache:
            print(f"📦 Usando cache de festivos locales de Extremadura {self.year} ({len(cache)} municipios)")
            return self._resolve_from_cache(cache)

        print(f"⚠️  No hay cache de festivos para Extremadura {self.year}, descargando PDF...")
        return super().scrape()

    def get_source_url(self) -> str:
        year_str = str(self.year)

        if year_str in self.cached_urls:
            url = self.cached_urls[year_str]
            print(f"📦 URL en cache para {self.year}: {url}")
            return url

        url = registry.get_url('extremadura', self.year, 'locales')
        if url:
            print(f"✅ URL oficial (registry) para {self.year}: {url}")
            return url

        print(f"🔍 Auto-discovery para Extremadura {self.year}...")
        try:
            from scrapers.discovery.ccaa.extremadura_discovery import auto_discover_extremadura
            url = auto_discover_extremadura(self.year)
            if url:
                print(f"✅ URL encontrada via discovery: {url}")
                self._save_to_cache(year_str, url)
                return url
        except Exception as e:
            print(f"⚠️  Error en auto-discovery: {e}")

        raise ValueError(
            f"No se encontró URL para Extremadura {self.year}.\n"
            f"Añade la URL a {self.CACHE_FILE}"
        )

    def fetch_content(self, url: str) -> str:
        try:
            print(f"📥 Descargando PDF: {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            import pdfplumber
            import io

            pdf_bytes = io.BytesIO(response.content)
            full_text = ""

            with pdfplumber.open(pdf_bytes) as pdf:
                print(f"   📄 PDF con {len(pdf.pages)} páginas")
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        # Quitar headers de sitios web
                        text = re.sub(r'www\.\S+', '', text)
                        full_text += text + "\n"

            print(f"✅ PDF procesado ({len(full_text)} caracteres)")
            return full_text

        except ImportError:
            print(f"❌ pdfplumber no instalado")
            return ""
        except Exception as e:
            print(f"❌ Error: {e}")
            return ""

    def parse_festivos(self, content: str) -> List[Dict]:
        print("🔍 Parseando festivos locales de Extremadura...")

        if self.municipio:
            print(f"   🎯 Filtrando por municipio: {self.municipio}")

        festivos = []
        provincia_actual = None

        for line in content.split('\n'):
            line = line.strip()

            if 'provincia de Badajoz' in line:
                provincia_actual = 'Badajoz'
                continue
            elif 'provincia de Cáceres' in line:
                provincia_actual = 'Cáceres'
                continue

            if not provincia_actual or not line:
                continue

            # MUNICIPIO.- fecha1 y fecha2.
            m = re.match(r'^([A-ZÁÉÍÓÚÑÜ][A-ZÁÉÍÓÚÑÜ\s\(\)]+)\.\-\s*(.+?)\.?$', line)
            if not m:
                continue

            municipio_raw = m.group(1).strip()
            fechas_str = m.group(2).strip().rstrip('.')
            municipio = _title_case_municipio(municipio_raw)

            # Filtrar por municipio
            if self.municipio:
                if self.municipio.upper() != municipio.upper():
                    from utils.normalizer import MunicipioNormalizer
                    if not MunicipioNormalizer.are_equivalent(self.municipio, municipio, threshold=85):
                        continue

            if ' y ' in fechas_str:
                partes = fechas_str.split(' y ', 1)
                fecha1 = self._parse_fecha_texto(partes[0].strip())
                fecha2 = self._parse_fecha_texto(partes[1].strip())
            else:
                fecha1 = self._parse_fecha_texto(fechas_str.strip())
                fecha2 = None

            if fecha1:
                festivos.append({
                    'fecha': fecha1,
                    'fecha_texto': _iso_to_fecha_texto(fecha1),
                    'descripcion': 'Fiesta local',
                    'tipo': 'local',
                    'ambito': 'local',
                    'municipio': municipio,
                    'provincia': provincia_actual,
                    'year': self.year
                })
            if fecha2:
                festivos.append({
                    'fecha': fecha2,
                    'fecha_texto': _iso_to_fecha_texto(fecha2),
                    'descripcion': 'Fiesta local',
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
        texto = texto.strip().lower()
        m = re.match(r'(\d{1,2})\s+de\s+(\w+)', texto)
        if m:
            dia = int(m.group(1))
            mes = MESES.get(m.group(2))
            if mes:
                return f"{self.year}-{mes:02d}-{dia:02d}"
        return None


if __name__ == "__main__":
    import sys
    municipio = sys.argv[1] if len(sys.argv) > 1 else None
    year = int(sys.argv[2]) if len(sys.argv) > 2 else 2026
    scraper = ExtremaduraLocalesScraper(year=year, municipio=municipio)
    festivos = scraper.scrape()
    if festivos:
        print(f"\n📅 Festivos encontrados: {len(festivos)}")
        for f in festivos:
            print(f"   {f['fecha']} - {f['descripcion']} ({f.get('municipio', 'N/A')})")
    else:
        print("\n❌ No se encontraron festivos")
