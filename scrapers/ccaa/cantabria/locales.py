"""
Cantabria Locales Scraper - Festivos locales de los 102 municipios
Extrae festivos desde el BOC (Boletín Oficial de Cantabria)
"""

from typing import List, Dict
import json
import os
import requests
from scrapers.core.base_scraper import BaseScraper


class CantabriaLocalesScraper(BaseScraper):
    """
    Scraper para festivos locales de Cantabria desde el BOC

    Fuente: BOC PDF con listado de festivos locales por municipio
    Publicación: Generalmente en diciembre del año anterior
    Municipios: 102
    """

    CACHE_FILE = "config/cantabria_urls_cache.json"

    def __init__(self, year: int, municipio: str = None):
        super().__init__(year=year, ccaa='cantabria', tipo='locales')
        self.municipio = municipio
        self.cached_urls = {}
        self._load_cache()

    def _load_cache(self):
        """Carga URLs del cache"""
        if os.path.exists(self.CACHE_FILE):
            try:
                with open(self.CACHE_FILE, 'r', encoding='utf-8') as f:
                    self.cached_urls = json.load(f)
                print(f"📦 Cache cargado: {len(self.cached_urls)} URLs")
            except:
                self.cached_urls = {}
        else:
            self.cached_urls = {}

    def _save_to_cache(self, year: int, url: str):
        """Guarda URL en el cache"""
        try:
            # Cargar cache completo
            if os.path.exists(self.CACHE_FILE):
                with open(self.CACHE_FILE, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
            else:
                cache = {}

            # Actualizar
            cache[str(year)] = url

            # Guardar
            with open(self.CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)

            print(f"💾 URL guardada en cache: {year} → {url}")

        except Exception as e:
            print(f"⚠️  No se pudo guardar en cache: {e}")

    def get_source_url(self) -> str:
        """Devuelve URL del BOC (con sistema de cache)"""
        year_str = str(self.year)

        # Verificar cache
        if year_str in self.cached_urls:
            url = self.cached_urls[year_str]
            print(f"📦 URL en cache para {self.year}: {url}")
            return url

        # Si no existe en cache, dar instrucciones
        raise ValueError(
            f"No se encontró URL para Cantabria {self.year}.\n"
            f"Añade la URL a {self.CACHE_FILE}"
        )

    def parse_festivos(self, content: str) -> List[Dict]:
        """Parsea festivos desde PDF de Cantabria (ya procesado como JSON)"""

        if not content:
            return []

        print("🔍 Parseando festivos locales de Cantabria...")

        # El content ya viene como JSON del _fetch_pdf
        try:
            datos = json.loads(content)
        except:
            print("   ❌ Error parseando JSON")
            return []

        if self.municipio:
            print(f"   🎯 Filtrando por municipio: {self.municipio}")

        festivos = []

        for item in datos:
            # Estructura del PDF parser:
            # {
            #   "fecha": "2026-05-15",
            #   "descripcion": "San Isidro Labrador",
            #   "fecha_texto": "15 de mayo",
            #   "municipio": "ALFOZ DE LLOREDO"
            # }

            municipio_item = item.get('municipio', '')
            fecha = item.get('fecha', '')
            descripcion = item.get('descripcion', 'Festivo local')

            # Filtrar por municipio si se especificó
            if self.municipio and municipio_item:
                from utils.normalizer import MunicipioNormalizer
                if not MunicipioNormalizer.are_equivalent(self.municipio, municipio_item, threshold=85):
                    continue

            festivos.append({
                'fecha': fecha,
                'fecha_texto': item.get('fecha_texto', fecha),
                'descripcion': descripcion,
                'tipo': 'local',
                'ambito': 'local',
                'municipio': municipio_item,
                'year': self.year
            })

        print(f"   ✅ Festivos locales extraídos: {len(festivos)}")

        return festivos

    def fetch_content(self, url: str) -> str:
        """Descarga el PDF desde el BOC y lo parsea"""

        # En Cantabria, la URL del BOC puede no terminar en .pdf pero devuelve PDF
        # Vamos a detectar si es PDF por el contenido
        try:
            print(f"📥 Descargando: {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # Detectar si es PDF por magic bytes o content-type
            is_pdf = (
                response.content[:4] == b'%PDF' or
                'application/pdf' in response.headers.get('Content-Type', '')
            )

            if is_pdf:
                print(f"✅ PDF descargado ({len(response.content)} bytes)")
                # Guardar contenido binario y procesar
                import tempfile
                import os

                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                    tmp_file.write(response.content)
                    tmp_path = tmp_file.name

                try:
                    from .pdf_parser import BOCPDFParser
                    parser = BOCPDFParser(tmp_path, self.year)

                    if self.municipio:
                        festivos = parser.get_festivos_municipio(self.municipio)
                        print(f"   ✅ Festivos locales extraídos del PDF: {len(festivos)}")

                        # Añadir municipio a cada festivo
                        for f in festivos:
                            f['municipio'] = self.municipio.upper()

                        return json.dumps(festivos)
                    else:
                        festivos_todos = parser.parse()
                        festivos_lista = []
                        for mun, fests in festivos_todos.items():
                            for f in fests:
                                f['municipio'] = mun
                                festivos_lista.append(f)

                        print(f"   ✅ Festivos locales extraídos del PDF: {len(festivos_lista)}")
                        return json.dumps(festivos_lista)

                finally:
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
            else:
                # No es PDF, devolver como texto
                print(f"✅ Archivo descargado ({len(response.text)} caracteres)")
                return response.text

        except Exception as e:
            print(f"❌ Error descargando {url}: {e}")
            import traceback
            traceback.print_exc()
            return ""



def main():
    """Test del scraper"""
    import sys

    if len(sys.argv) > 1:
        try:
            year = int(sys.argv[1])
        except ValueError:
            print("❌ Año inválido. Uso: python -m scrapers.ccaa.cantabria.locales [año] [municipio]")
            return
    else:
        year = 2026

    municipio = sys.argv[2] if len(sys.argv) > 2 else None

    print("=" * 80)
    print(f"🧪 TEST: Cantabria Locales Scraper - Festivos {year}")
    if municipio:
        print(f"   Municipio: {municipio}")
    print("=" * 80)

    scraper = CantabriaLocalesScraper(year=year, municipio=municipio)
    festivos = scraper.scrape()

    if festivos:
        scraper.print_summary()

        if municipio:
            filename = f"data/cantabria_{municipio.lower().replace(' ', '_')}_{year}"
        else:
            filename = f"data/cantabria_locales_{year}"

        scraper.save_to_json(f"{filename}.json")
        scraper.save_to_excel(f"{filename}.xlsx")

        print(f"\n✅ Test completado para {year}")
    else:
        print(f"\n❌ No se pudieron extraer festivos para {year}")


if __name__ == "__main__":
    main()
