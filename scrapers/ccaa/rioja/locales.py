"""
Scraper de festivos locales para La Rioja.

Extrae festivos del BOR (Boletín Oficial de La Rioja).
"""

from typing import List, Dict
import json
from pathlib import Path
import tempfile
import requests

from scrapers.core.base_scraper import BaseScraper
from config.config_manager import registry
from scrapers.ccaa.rioja.pdf_parser import BORPDFParser


class RiojaLocalesScraper(BaseScraper):
    """
    Scraper para festivos locales de La Rioja.

    La Rioja tiene 174 municipios, cada uno con 2 festivos locales.
    Los festivos se publican en el BOR (Boletín Oficial de La Rioja).
    """

    def __init__(self, year: int = 2026, municipio: str = None):
        super().__init__(year, ccaa='rioja', tipo='locales')
        self.municipio = municipio
        self.municipios = self._load_municipios()

    def _load_municipios(self) -> Dict[str, str]:
        """
        Carga la lista de municipios de La Rioja.

        Returns:
            Dict con {NOMBRE_NORMALIZADO: nombre_display}
        """
        municipios_file = registry.get_municipios_file('rioja')

        if not municipios_file:
            print("No se encontró archivo de municipios para La Rioja")
            return {}

        municipios_path = Path(municipios_file)

        if not municipios_path.exists():
            print(f"Archivo de municipios no existe: {municipios_path}")
            return {}

        with open(municipios_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_source_url(self) -> str:
        """Obtiene la URL del BOR para el año actual"""
        url = registry.get_url('rioja', self.year, 'locales')
        return url or ""

    def parse_festivos(self, pdf_path: str) -> Dict[str, List[Dict]]:
        """
        Parsea el contenido del BOR PDF.

        Args:
            pdf_path: Ruta al archivo PDF

        Returns:
            Dict con {municipio: [festivos]}
        """
        parser = BORPDFParser(pdf_path, self.year)
        return parser.parse()

    def scrape(self):
        """
        Extrae festivos locales de La Rioja del BOR.

        Returns:
            Si self.municipio está definido: List[Dict] de festivos del municipio
            Si no: Dict[str, List[Dict]] con {municipio: [festivos]}
        """
        # Obtener URL del BOR
        url = registry.get_url('rioja', self.year, 'locales')

        if not url:
            print(f"No hay URL configurada para La Rioja {self.year}")
            return [] if self.municipio else {}

        print(f"Scraping festivos locales de La Rioja {self.year}")
        print(f"URL: {url}")

        # Descargar el PDF
        try:
            # Primero obtener la página HTML para extraer el enlace al PDF
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            html_content = response.text

            # Extraer la URL del PDF del HTML
            import re
            pdf_match = re.search(r'https://ias1\.larioja\.org/boletin/[^"\']+\.pdf[^"\']*', html_content, re.IGNORECASE)

            if not pdf_match:
                # Buscar el patrón alternativo (Servlet)
                pdf_match = re.search(r'(https://ias1\.larioja\.org/boletin/Bor_Boletin_visor_Servlet\?[^"\']+)', html_content)

            if not pdf_match:
                print("No se encontró enlace al PDF en la página")
                return [] if self.municipio else {}

            pdf_url = pdf_match.group(0) if isinstance(pdf_match.group(0), str) else pdf_match.group(1)
            print(f"URL del PDF: {pdf_url}")

            # Descargar el PDF
            pdf_response = requests.get(pdf_url, timeout=30)
            pdf_response.raise_for_status()

            # Guardar temporalmente
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(pdf_response.content)
                tmp_path = tmp_file.name

            # Parsear el PDF
            festivos_todos = self.parse_festivos(tmp_path)

            # Limpiar archivo temporal
            Path(tmp_path).unlink()

            # Si se especificó un municipio, filtrar y retornar solo sus festivos
            if self.municipio:
                print(f"🎯 Filtrando por municipio: {self.municipio}")
                festivos_municipio = self.get_festivos_municipio_from_dict(festivos_todos, self.municipio)

                # Añadir tipo 'local' a cada festivo
                for festivo in festivos_municipio:
                    festivo['tipo'] = 'local'
                    festivo['ambito'] = 'local'
                    festivo['year'] = self.year

                print(f"✅ Festivos locales extraídos: {len(festivos_municipio)}")
                return festivos_municipio
            else:
                print(f"Extraídos festivos de {len(festivos_todos)} municipios")
                return festivos_todos

        except requests.RequestException as e:
            print(f"Error descargando el BOR: {e}")
            return [] if self.municipio else {}
        except Exception as e:
            print(f"Error parseando el BOR: {e}")
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
        print("Ejemplo: python locales.py 2026 LOGROÑO")
        sys.exit(1)

    year = int(sys.argv[1])
    municipio = sys.argv[2] if len(sys.argv) > 2 else None

    scraper = RiojaLocalesScraper(year=year)

    try:
        if municipio:
            festivos = scraper.get_festivos_municipio(municipio)
            print(f"\nFestivos de {municipio} en {year}:")
            for f in festivos:
                print(f"  - {f['fecha']}: {f['descripcion']}")
        else:
            festivos_todos = scraper.scrape()
            print(f"\nTotal municipios: {len(festivos_todos)}")
            print("\nPrimeros 10 municipios:")
            for idx, (mun, fests) in enumerate(list(festivos_todos.items())[:10]):
                print(f"  {mun}: {len(fests)} festivos")
    except NotImplementedError as e:
        print(f"\n⚠️  {e}")
        print("\nPara completar la implementación:")
        print("1. Descarga el PDF del BOR nº 159/2025")
        print("2. Analiza su estructura (tabla, columnas, formato)")
        print("3. Decide si crear un PDFParser o parsear directamente")
        print("4. Actualiza el método scrape() con la lógica de parseo")
