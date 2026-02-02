"""
Scraper de festivos locales para Castilla y León.

Extrae festivos del portal de transparencia de la JCyL en formato CSV.
Los datos provienen de la Consejería de Industria, Comercio y Empleo,
publicados anualmente en https://transparencia.jcyl.es/

Formato CSV (separador ;, encoding latin-1):
    Provincia;Municipio;Fecha fiesta;Nombre fiesta;INE

Estrategia de obtención de datos (4 niveles):
1. Cache de festivos pre-generado (instantáneo, fiable en cloud)
2. URL en cache (castilla_leon_urls_cache.json)
3. URL conocida en ccaa_registry.yaml
4. Auto-discovery vía URL predecible + Opendatasoft API
"""

from scrapers.core.base_scraper import BaseScraper
from config.config_manager import CCAaRegistry
from typing import List, Dict, Optional
from pathlib import Path
import requests
import json
import csv
import io
import os


registry = CCAaRegistry()

# Mapa de normalización de provincias (el CSV usa MAYÚSCULAS inconsistentes)
PROVINCIA_MAP = {
    'AVILA': 'Ávila',
    'ÁVILA': 'Ávila',
    'BURGOS': 'Burgos',
    'LEON': 'León',
    'LEÓN': 'León',
    'PALENCIA': 'Palencia',
    'SALAMANCA': 'Salamanca',
    'SEGOVIA': 'Segovia',
    'SORIA': 'Soria',
    'VALLADOLID': 'Valladolid',
    'ZAMORA': 'Zamora',
}


def _title_case_municipio(name: str) -> str:
    """
    Convierte nombre de municipio de MAYÚSCULAS a Title Case.

    Respeta artículos y preposiciones (de, del, la, las, los, el, y, en, al, a)
    excepto cuando son la primera palabra.

    Ejemplos:
        ARENAS DE SAN PEDRO → Arenas de San Pedro
        ÁVILA → Ávila
        LA ADRADA → La Adrada
    """
    exceptions = {'DE', 'DEL', 'LA', 'LAS', 'LOS', 'EL', 'Y', 'EN', 'AL', 'A'}
    words = name.split()
    result = []
    for i, w in enumerate(words):
        if i == 0 or w.upper() not in exceptions:
            result.append(w.capitalize())
        else:
            result.append(w.lower())
    return ' '.join(result)


class CastillaLeonLocalesScraper(BaseScraper):
    """
    Scraper para festivos locales de Castilla y León desde OpenData JCyL.

    Castilla y León publica festivos locales como CSV en su portal de transparencia.
    Las URLs son predecibles por año: FIESTAS-LOCALES-INE-{year}.csv

    Provincias: Ávila, Burgos, León, Palencia, Salamanca, Segovia, Soria, Valladolid, Zamora
    Municipios: ~2.248 con festivos declarados
    Total esperado: 8 nacionales + 4 autonómicos + 2 locales = 14 festivos
    """

    CACHE_FILE = "config/castilla_leon_urls_cache.json"

    def __init__(self, year: int = 2026, municipio: Optional[str] = None):
        super().__init__(year=year, ccaa='castilla_leon', tipo='locales')
        self._load_cache()

        # Fuzzy matching del municipio
        if municipio:
            from utils.normalizer import find_municipio

            # Cargar todos los municipios de Castilla y León
            try:
                with open('config/castilla_leon_municipios.json', 'r', encoding='utf-8') as f:
                    provincias_data = json.load(f)

                # Crear lista plana
                todos_municipios = []
                for munis in provincias_data.values():
                    todos_municipios.extend(munis)

                # Buscar mejor match
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

        Archivo: config/castilla_leon_festivos_locales_{year}.json
        Estructura: {municipio: [{fecha, descripcion, provincia, codigo_ine}]}

        Returns:
            Dict con festivos por municipio, o {} si no hay cache.
        """
        cache_path = Path(__file__).parent.parent.parent.parent / 'config' / f'castilla_leon_festivos_locales_{self.year}.json'
        if not cache_path.exists():
            return {}
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Error cargando cache de festivos de Castilla y León: {e}")
            return {}

    def _resolve_from_cache(self, cache: Dict[str, list]):
        """
        Resuelve festivos desde el cache pre-generado.

        Args:
            cache: Dict {municipio: [{fecha, descripcion, ...}]}

        Returns:
            Si self.municipio: List[Dict] de festivos del municipio
            Si no: List[Dict] vacío (no soportamos devolver todos sin municipio)
        """
        if self.municipio:
            # Buscar municipio exacto primero
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
                        'fecha_texto': f['fecha'],
                        'descripcion': f['descripcion'],
                        'tipo': 'local',
                        'ambito': 'local',
                        'municipio': self.municipio,
                        'provincia': f.get('provincia', ''),
                        'codigo_ine': f.get('codigo_ine', ''),
                        'year': self.year
                    })
                print(f"   ✅ {len(result)} festivos locales desde cache para {self.municipio}")
                return result
            else:
                print(f"   ⚠️  Municipio '{self.municipio}' no encontrado en cache")
                return []
        else:
            # Sin municipio específico, no devolver todos (sería demasiado)
            return []

    def scrape(self):
        """
        Extrae festivos locales de Castilla y León.

        Estrategia de 4 niveles:
        1. Cache de festivos pre-generado (instantáneo, fiable en cloud)
        2. URL en cache (castilla_leon_urls_cache.json) → descarga CSV
        3. URL conocida en ccaa_registry.yaml → descarga CSV
        4. Auto-discovery URL predecible → descarga CSV

        Returns:
            List[Dict] de festivos del municipio
        """
        # Nivel 1: Cache de festivos pre-generado
        cache = self._load_festivos_cache()
        if cache:
            print(f"📦 Usando cache de festivos locales de Castilla y León {self.year} ({len(cache)} municipios)")
            return self._resolve_from_cache(cache)

        # Niveles 2-4: Flujo estándar BaseScraper (get_source_url → fetch → parse)
        print(f"⚠️  No hay cache de festivos para Castilla y León {self.year}, descargando CSV...")
        return super().scrape()

    def get_source_url(self) -> str:
        """
        Devuelve la URL del CSV de OpenData JCyL.

        Estrategia de 3 niveles:
        1. Cache de URLs (descubiertas previamente)
        2. URL en ccaa_registry.yaml
        3. Auto-discovery vía URL predecible
        """
        year_str = str(self.year)

        # Nivel 1: Cache
        if year_str in self.cached_urls:
            url = self.cached_urls[year_str]
            print(f"📦 URL en cache para {self.year}: {url}")
            return url

        # Nivel 2: Registry
        url = registry.get_url('castilla_leon', self.year, 'locales')
        if url:
            print(f"✅ URL oficial (registry) para {self.year}: {url}")
            return url

        # Nivel 3: Auto-discovery
        print(f"🔍 Auto-discovery para Castilla y León {self.year}...")
        try:
            from scrapers.discovery.ccaa.castilla_leon_discovery import auto_discover_castilla_leon
            url = auto_discover_castilla_leon(self.year)

            if url:
                print(f"✅ URL encontrada via discovery: {url}")
                self._save_to_cache(year_str, url)
                return url
        except Exception as e:
            print(f"⚠️  Error en auto-discovery: {e}")

        raise ValueError(
            f"No se encontró URL para Castilla y León {self.year}.\n"
            f"Añade la URL a {self.CACHE_FILE}"
        )

    def fetch_content(self, url: str) -> str:
        """
        Descarga el CSV desde OpenData JCyL.

        El CSV usa encoding ISO-8859-1 (latin-1), con separador ; y
        municipios en MAYÚSCULAS.
        """
        try:
            print(f"📥 Descargando CSV: {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # JCyL sirve CSV en ISO-8859-1
            response.encoding = 'latin-1'

            print(f"✅ CSV descargado ({len(response.text)} caracteres)")
            return response.text

        except Exception as e:
            print(f"❌ Error descargando {url}: {e}")
            return ""

    def parse_festivos(self, content: str) -> List[Dict]:
        """
        Parsea festivos desde el CSV de OpenData JCyL.

        Formato CSV (separador ;):
            Provincia;Municipio;Fecha fiesta;Nombre fiesta;INE

        Conversión de fechas: DD/MM/YYYY → YYYY-MM-DD
        Municipios en MAYÚSCULAS: matching case-insensitive
        NombreFestivo vacío → "Fiesta local"

        Returns:
            List[Dict] con festivos (filtrados por municipio si se especificó)
        """
        print("🔍 Parseando festivos locales de Castilla y León...")

        if self.municipio:
            print(f"   🎯 Filtrando por municipio: {self.municipio}")

        festivos = []

        try:
            reader = csv.reader(io.StringIO(content), delimiter=';')
            header = next(reader)

            # Validar header
            expected_cols = ['Provincia', 'Municipio', 'Fecha fiesta', 'Nombre fiesta', 'INE']
            if header[:5] != expected_cols:
                print(f"   ⚠️  Header inesperado: {header}")
                print(f"   ⚠️  Esperado: {expected_cols}")
                # Intentar continuar de todas formas

            total = 0
            for row in reader:
                if len(row) < 4:
                    continue

                provincia_raw = row[0].strip()
                municipio_csv = row[1].strip()
                fecha_raw = row[2].strip()
                nombre_festivo = row[3].strip() if len(row) > 3 else ''
                codigo_ine = row[4].strip() if len(row) > 4 else ''

                if not municipio_csv or not fecha_raw:
                    continue

                total += 1

                # Normalizar provincia
                provincia = PROVINCIA_MAP.get(provincia_raw.upper(), _title_case_municipio(provincia_raw))

                # Filtrar por municipio si se especificó (comparación case-insensitive)
                if self.municipio:
                    # Primero comparar case-insensitive
                    if self.municipio.upper() != municipio_csv.upper():
                        # Si no coincide exacto, intentar Title Case
                        muni_title = _title_case_municipio(municipio_csv)
                        if self.municipio.upper() != muni_title.upper():
                            # Último recurso: fuzzy matching
                            from utils.normalizer import MunicipioNormalizer
                            if not MunicipioNormalizer.are_equivalent(
                                self.municipio, municipio_csv, threshold=85
                            ) and not MunicipioNormalizer.are_equivalent(
                                self.municipio, muni_title, threshold=85
                            ):
                                continue

                # Convertir fecha: DD/MM/YYYY → YYYY-MM-DD
                try:
                    parts = fecha_raw.split('/')
                    if len(parts) == 3:
                        dia, mes, anio = parts
                        fecha_iso = f"{anio}-{mes.zfill(2)}-{dia.zfill(2)}"

                        # Validar que el año coincide
                        if int(anio) != self.year:
                            continue
                    else:
                        print(f"   ⚠️  Formato de fecha inesperado: {fecha_raw}")
                        continue
                except (ValueError, IndexError):
                    print(f"   ⚠️  Error parseando fecha: {fecha_raw}")
                    continue

                # Descripción: usar nombre del festivo o default
                descripcion = nombre_festivo if nombre_festivo else 'Fiesta local'

                # Nombre del municipio: Title Case para consistencia
                municipio_normalizado = _title_case_municipio(municipio_csv)

                festivos.append({
                    'fecha': fecha_iso,
                    'fecha_texto': fecha_iso,
                    'descripcion': descripcion,
                    'tipo': 'local',
                    'ambito': 'local',
                    'municipio': municipio_normalizado,
                    'provincia': provincia,
                    'codigo_ine': codigo_ine,
                    'year': self.year
                })

        except Exception as e:
            print(f"   ❌ Error parseando CSV: {e}")
            return []

        if self.municipio:
            print(f"   ✅ {len(festivos)} festivos locales para {self.municipio}")
        else:
            print(f"   ✅ {len(festivos)} festivos locales de {total} entradas totales")

        return festivos


if __name__ == "__main__":
    import sys

    municipio = sys.argv[1] if len(sys.argv) > 1 else None
    year = int(sys.argv[2]) if len(sys.argv) > 2 else 2026

    scraper = CastillaLeonLocalesScraper(year=year, municipio=municipio)
    festivos = scraper.scrape()

    if festivos:
        print(f"\n📅 Festivos encontrados: {len(festivos)}")
        for f in festivos:
            print(f"   {f['fecha']} - {f['descripcion']} ({f.get('municipio', 'N/A')})")
    else:
        print("\n❌ No se encontraron festivos")
