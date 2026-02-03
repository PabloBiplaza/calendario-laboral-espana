"""Scraper para festivos locales del Principado de Asturias"""

from scrapers.core.base_scraper import BaseScraper
from typing import List, Dict, Optional
import requests
import json
import csv
import io

MESES_INV = {
    1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
    5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
    9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
}


def _iso_to_fecha_texto(fecha_iso: str) -> str:
    """Convierte '2026-06-04' → '4 de junio'."""
    try:
        partes = fecha_iso.split('-')
        mes = int(partes[1])
        dia = int(partes[2])
        return f"{dia} de {MESES_INV.get(mes, str(mes))}"
    except (IndexError, ValueError):
        return fecha_iso


class AsturiasLocalesScraper(BaseScraper):
    """Scraper para festivos locales de Asturias desde OpenData Asturias"""

    CACHE_FILE = "config/asturias_urls_cache.json"

    def __init__(self, year: int, municipio: Optional[str] = None):
        super().__init__(year=year, ccaa='asturias', tipo='locales')
        self._load_cache()

        # Si se especifica municipio, hacer fuzzy matching
        if municipio:
            import json
            from utils.normalizer import find_municipio

            # Cargar todos los municipios de Asturias
            with open('config/asturias_municipios.json', 'r', encoding='utf-8') as f:
                municipios_data = json.load(f)

            # Obtener lista de municipios
            if isinstance(municipios_data, list):
                todos_municipios = municipios_data
            elif isinstance(municipios_data, dict):
                todos_municipios = municipios_data.get('municipios', [])
            else:
                todos_municipios = []

            # Buscar mejor match
            mejor_match = find_municipio(municipio, todos_municipios, threshold=85)

            if mejor_match:
                self.municipio = mejor_match
                if mejor_match.lower() != municipio.lower():
                    print(f"   🔍 Fuzzy match: '{municipio}' → '{mejor_match}'")
            else:
                self.municipio = municipio
        else:
            self.municipio = None

    def _load_cache(self):
        """Carga URLs del cache"""
        import os
        import json

        self.cached_urls = {}

        if os.path.exists(self.CACHE_FILE):
            try:
                with open(self.CACHE_FILE, 'r', encoding='utf-8') as f:
                    self.cached_urls = json.load(f)
                print(f"📦 Cache cargado: {len(self.cached_urls)} URLs")
            except:
                self.cached_urls = {}
        else:
            self.cached_urls = {}

    def _save_to_cache(self, year_str: str, url: str):
        """Guarda URL en el cache"""
        import os
        import json

        # Cargar cache actual
        cache = {}
        if os.path.exists(self.CACHE_FILE):
            with open(self.CACHE_FILE, 'r', encoding='utf-8') as f:
                cache = json.load(f)

        # Añadir nueva URL
        cache[year_str] = url

        # Guardar
        with open(self.CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)

        print(f"💾 URL guardada en cache: {self.CACHE_FILE}")

    def get_source_url(self) -> str:
        """Devuelve la URL del CSV/JSON de OpenData Asturias"""
        year_str = str(self.year)

        # 1. Cache
        if year_str in self.cached_urls:
            url = self.cached_urls[year_str]
            print(f"📦 URL en cache para {self.year}: {url}")
            return url

        # 2. Auto-discovery
        print(f"🔍 Auto-discovery para {self.year} (no está en cache)...")

        from scrapers.discovery.ccaa.asturias_discovery import auto_discover_asturias
        url = auto_discover_asturias(self.year)

        if url:
            print(f"✅ URL encontrada via discovery: {url}")

            # Guardar en cache
            self._save_to_cache(year_str, url)

            return url

        raise ValueError(
            f"No se encontró URL para Asturias {self.year}.\n"
            f"Añade la URL a {self.CACHE_FILE}"
        )

    def parse_festivos(self, content: str) -> List[Dict]:
        """Parsea festivos desde CSV, JSON o PDF de Asturias"""

        if not content:
            return []

        print("🔍 Parseando festivos locales de Asturias...")

        # Detectar formato (CSV o JSON)
        formato = self._detectar_formato(content)

        if formato == 'json':
            return self._parse_json(content)
        elif formato == 'csv':
            return self._parse_csv(content)
        else:
            print("   ❌ Formato no reconocido")
            return []

    def _detectar_formato(self, content: str) -> str:
        """Detecta si el contenido es JSON o CSV"""
        content_stripped = content.strip()

        if content_stripped.startswith('[') or content_stripped.startswith('{'):
            return 'json'
        else:
            return 'csv'

    def _parse_json(self, content: str) -> List[Dict]:
        """Parsea festivos desde JSON (incluye datos del PDF ya parseados)"""
        try:
            datos = json.loads(content)
        except:
            print("   ❌ Error parseando JSON")
            return []

        if self.municipio:
            print(f"   🎯 Filtrando por municipio: {self.municipio}")

        festivos = []

        for item in datos:
            # Estructura esperada del JSON de Asturias
            # {
            #   "Año": "2026" (opcional),
            #   "Municipio": "Oviedo",
            #   "Fecha": "2026-09-21",
            #   "Descripción": "San Mateo"
            # }
            # O del PDF parser:
            # {
            #   "fecha": "2026-09-21",
            #   "descripcion": "San Mateo",
            #   "fecha_texto": "21 de septiembre",
            #   "municipio": "OVIEDO"
            # }

            municipio_item = item.get('Municipio', item.get('municipio', ''))
            fecha = item.get('Fecha', item.get('fecha', ''))
            descripcion = item.get('Descripción', item.get('Descripcion', item.get('descripcion', 'Festivo local')))
            year_item = item.get('Año', item.get('año', item.get('year', '')))

            # Si viene del PDF, no tiene año separado
            if not year_item and fecha:
                try:
                    year_item = int(fecha.split('-')[0])
                except:
                    year_item = self.year

            # Filtrar por año
            if year_item and str(year_item) != str(self.year):
                continue

            # Filtrar por municipio si se especificó
            if self.municipio and municipio_item:
                from utils.normalizer import MunicipioNormalizer
                if not MunicipioNormalizer.are_equivalent(self.municipio, municipio_item, threshold=85):
                    continue

            festivos.append({
                'fecha': fecha,
                'fecha_texto': item.get('fecha_texto', _iso_to_fecha_texto(fecha)),
                'descripcion': descripcion,
                'tipo': 'local',
                'ambito': 'local',
                'municipio': municipio_item,
                'year': self.year
            })

        print(f"   ✅ Festivos locales extraídos: {len(festivos)}")

        return festivos

    def _parse_csv(self, content: str) -> List[Dict]:
        """Parsea festivos desde CSV"""
        if self.municipio:
            print(f"   🎯 Filtrando por municipio: {self.municipio}")

        festivos = []

        try:
            # Leer CSV
            csv_file = io.StringIO(content)
            reader = csv.DictReader(csv_file)

            for row in reader:
                # Estructura esperada del CSV de Asturias
                # Año,Municipio,Fecha,Descripción

                municipio_item = row.get('Municipio', row.get('municipio', ''))
                fecha = row.get('Fecha', row.get('fecha', ''))
                descripcion = row.get('Descripción', row.get('Descripcion', row.get('descripcion', 'Festivo local')))
                year_item = row.get('Año', row.get('año', row.get('year', '')))

                # Filtrar por año
                if str(year_item) != str(self.year):
                    continue

                # Filtrar por municipio si se especificó
                if self.municipio:
                    from utils.normalizer import MunicipioNormalizer
                    if not MunicipioNormalizer.are_equivalent(self.municipio, municipio_item, threshold=85):
                        continue

                festivos.append({
                    'fecha': fecha,
                    'fecha_texto': _iso_to_fecha_texto(fecha),
                    'descripcion': descripcion,
                    'tipo': 'local',
                    'ambito': 'local',
                    'municipio': municipio_item,
                    'year': self.year
                })

            print(f"   ✅ Festivos locales extraídos: {len(festivos)}")

        except Exception as e:
            print(f"   ❌ Error parseando CSV: {e}")

        return festivos

    def fetch_content(self, url: str) -> str:
        """Descarga el CSV/JSON/PDF desde las fuentes de Asturias"""

        # Si es un PDF, usar parser especial
        if url.endswith('.pdf'):
            return self._fetch_pdf(url)

        try:
            print(f"📥 Descargando: {url}")

            # Desactivar verificación SSL si es necesario (servidor de Asturias tiene problemas)
            response = requests.get(url, timeout=30, verify=False)
            response.raise_for_status()

            print(f"✅ Archivo descargado ({len(response.text)} caracteres)")

            return response.text

        except Exception as e:
            print(f"❌ Error descargando {url}: {e}")
            return ""

    def _fetch_pdf(self, url: str) -> str:
        """Descarga y parsea PDF del BOPA"""
        import tempfile
        import os

        try:
            print(f"📥 Descargando PDF: {url}")

            response = requests.get(url, timeout=30)
            response.raise_for_status()

            print(f"✅ PDF descargado ({len(response.content)} bytes)")

            # Guardar temporalmente el PDF
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(response.content)
                tmp_path = tmp_file.name

            try:
                # Usar el parser de PDF
                from .pdf_parser import BOPAPDFParser

                parser = BOPAPDFParser(tmp_path, self.year)

                if self.municipio:
                    festivos = parser.get_festivos_municipio(self.municipio)
                    print(f"   ✅ Festivos locales extraídos del PDF: {len(festivos)}")

                    # Devolver en formato que parse_festivos espera
                    # Como el PDF ya parsea, devolver JSON string
                    return json.dumps(festivos)
                else:
                    # Sin municipio, devolver todos
                    festivos_todos = parser.parse()
                    festivos_lista = []
                    for mun, fests in festivos_todos.items():
                        for f in fests:
                            f['municipio'] = mun
                            festivos_lista.append(f)

                    print(f"   ✅ Festivos locales extraídos del PDF: {len(festivos_lista)}")
                    return json.dumps(festivos_lista)

            finally:
                # Limpiar archivo temporal
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        except Exception as e:
            print(f"❌ Error procesando PDF {url}: {e}")
            import traceback
            traceback.print_exc()
            return ""
