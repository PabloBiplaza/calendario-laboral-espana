"""
Scraper de festivos locales para Aragón.

Extrae festivos del catálogo OpenData Aragón en formato CSV.
Los datos provienen de la Dirección General de Trabajo del Gobierno de Aragón,
publicados anualmente en https://opendata.aragon.es/

Formato CSV (separador ;):
    Provincia;CodigoINE;Municipio;Fecha;NombreFestivo

Estrategia de obtención de datos (3 niveles):
1. URL en cache (aragon_urls_cache.json)
2. URL conocida en ccaa_registry.yaml
3. Auto-discovery vía CKAN API de OpenData Aragón
"""

from scrapers.core.base_scraper import BaseScraper
from config.config_manager import CCAaRegistry
from typing import List, Dict, Optional
import requests
import json
import csv
import io
import os


registry = CCAaRegistry()


class AragonLocalesScraper(BaseScraper):
    """
    Scraper para festivos locales de Aragón desde OpenData Aragón.

    Aragón publica festivos locales como CSV en su portal de datos abiertos.
    Cada municipio tiene típicamente 2 festivos locales.

    Provincias: Huesca, Teruel, Zaragoza
    Municipios: ~565 con festivos declarados
    Total esperado: 8 nacionales + 4 autonómicos + 2 locales = 14 festivos
    """

    CACHE_FILE = "config/aragon_urls_cache.json"

    def __init__(self, year: int = 2026, municipio: Optional[str] = None):
        super().__init__(year=year, ccaa='aragon', tipo='locales')
        self._load_cache()

        # Fuzzy matching del municipio
        if municipio:
            from utils.normalizer import find_municipio

            # Cargar todos los municipios de Aragón
            try:
                with open('config/aragon_municipios.json', 'r', encoding='utf-8') as f:
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

    def get_source_url(self) -> str:
        """
        Devuelve la URL del CSV de OpenData Aragón.

        Estrategia de 3 niveles:
        1. Cache de URLs (descubiertas previamente)
        2. URL en ccaa_registry.yaml
        3. Auto-discovery vía CKAN API
        """
        year_str = str(self.year)

        # Nivel 1: Cache
        if year_str in self.cached_urls:
            url = self.cached_urls[year_str]
            print(f"📦 URL en cache para {self.year}: {url}")
            return url

        # Nivel 2: Registry
        url = registry.get_url('aragon', self.year, 'locales')
        if url:
            print(f"✅ URL oficial (registry) para {self.year}: {url}")
            return url

        # Nivel 3: Auto-discovery
        print(f"🔍 Auto-discovery para Aragón {self.year}...")
        try:
            from scrapers.discovery.ccaa.aragon_discovery import auto_discover_aragon
            url = auto_discover_aragon(self.year)

            if url:
                print(f"✅ URL encontrada via discovery: {url}")
                self._save_to_cache(year_str, url)
                return url
        except Exception as e:
            print(f"⚠️  Error en auto-discovery: {e}")

        raise ValueError(
            f"No se encontró URL para Aragón {self.year}.\n"
            f"Añade la URL a {self.CACHE_FILE}"
        )

    def fetch_content(self, url: str) -> str:
        """
        Descarga el CSV desde OpenData Aragón.

        El CSV usa encoding ISO-8859-1 (latin-1), común en datos españoles.
        """
        try:
            print(f"📥 Descargando CSV: {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # OpenData Aragón sirve CSV en ISO-8859-1
            response.encoding = 'latin-1'

            print(f"✅ CSV descargado ({len(response.text)} caracteres)")
            return response.text

        except Exception as e:
            print(f"❌ Error descargando {url}: {e}")
            return ""

    def parse_festivos(self, content: str) -> List[Dict]:
        """
        Parsea festivos desde el CSV de OpenData Aragón.

        Formato CSV (separador ;):
            Provincia;CodigoINE;Municipio;Fecha;NombreFestivo

        Conversión de fechas: DD-MM-YYYY → YYYY-MM-DD
        NombreFestivo vacío → "Fiesta local"

        Returns:
            List[Dict] con festivos (filtrados por municipio si se especificó)
        """
        print("🔍 Parseando festivos locales de Aragón...")

        if self.municipio:
            print(f"   🎯 Filtrando por municipio: {self.municipio}")

        festivos = []

        try:
            reader = csv.reader(io.StringIO(content), delimiter=';')
            header = next(reader)

            # Validar header
            expected_cols = ['Provincia', 'CodigoINE', 'Municipio', 'Fecha', 'NombreFestivo']
            if header[:5] != expected_cols:
                print(f"   ⚠️  Header inesperado: {header}")
                print(f"   ⚠️  Esperado: {expected_cols}")
                # Intentar continuar de todas formas

            total = 0
            for row in reader:
                if len(row) < 4:
                    continue

                provincia = row[0].strip()
                codigo_ine = row[1].strip() if len(row) > 1 else ''
                municipio_csv = row[2].strip()
                fecha_raw = row[3].strip()
                nombre_festivo = row[4].strip() if len(row) > 4 else ''

                if not municipio_csv or not fecha_raw:
                    continue

                total += 1

                # Filtrar por municipio si se especificó
                if self.municipio:
                    from utils.normalizer import MunicipioNormalizer
                    if not MunicipioNormalizer.are_equivalent(
                        self.municipio, municipio_csv, threshold=85
                    ):
                        continue

                # Convertir fecha: DD-MM-YYYY → YYYY-MM-DD
                try:
                    parts = fecha_raw.split('-')
                    if len(parts) == 3:
                        dia, mes, anio = parts
                        fecha_iso = f"{anio}-{mes}-{dia}"

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

                festivos.append({
                    'fecha': fecha_iso,
                    'fecha_texto': fecha_iso,
                    'descripcion': descripcion,
                    'tipo': 'local',
                    'ambito': 'local',
                    'municipio': municipio_csv,
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

    scraper = AragonLocalesScraper(year=year, municipio=municipio)
    festivos = scraper.scrape()

    if festivos:
        print(f"\n📅 Festivos encontrados: {len(festivos)}")
        for f in festivos:
            print(f"   {f['fecha']} - {f['descripcion']} ({f.get('municipio', 'N/A')})")
    else:
        print("\n❌ No se encontraron festivos")
