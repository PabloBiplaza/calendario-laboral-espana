"""
Scraper de festivos locales para La Rioja.

Extrae festivos del BOR (Boletín Oficial de La Rioja).
"""

from typing import List, Dict
import json
from pathlib import Path

from scrapers.core.base_scraper import BaseScraper
from config.config_manager import registry


class RiojaLocalesScraper(BaseScraper):
    """
    Scraper para festivos locales de La Rioja.

    La Rioja tiene 174 municipios, cada uno con 2 festivos locales.
    Los festivos se publican en el BOR (Boletín Oficial de La Rioja).
    """

    def __init__(self, year: int = 2026):
        super().__init__(year, ccaa='rioja', tipo='locales')
        self.municipios = self._load_municipios()

    def _load_municipios(self) -> Dict[str, str]:
        """
        Carga la lista de municipios de La Rioja.

        Returns:
            Dict con {NOMBRE_NORMALIZADO: nombre_display}
        """
        municipios_file = registry.get_municipios_file('rioja')

        if not municipios_file:
            self.logger.warning("No se encontró archivo de municipios para La Rioja")
            return {}

        municipios_path = Path(municipios_file)

        if not municipios_path.exists():
            self.logger.warning(f"Archivo de municipios no existe: {municipios_path}")
            return {}

        with open(municipios_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_source_url(self) -> str:
        """Obtiene la URL del BOR para el año actual"""
        url = registry.get_url('rioja', self.year, 'locales')
        return url or ""

    def parse_festivos(self, content: str) -> Dict[str, List[Dict]]:
        """
        Parsea el contenido del BOR (PDF o HTML).

        Args:
            content: Contenido del BOR

        Returns:
            Dict con {municipio: [festivos]}

        Note:
            Por implementar cuando se analice el formato del BOR
        """
        raise NotImplementedError(
            "El parseo del BOR de La Rioja está pendiente. "
            "Necesita análisis del formato del boletín."
        )

    def scrape(self) -> Dict[str, List[Dict]]:
        """
        Extrae festivos locales de La Rioja del BOR.

        Returns:
            Dict con {municipio: [festivos]}

        Raises:
            NotImplementedError: Este scraper está en desarrollo.
                Necesita la URL correcta del BOR y análisis del formato.
        """
        # Obtener URL del BOR
        url = registry.get_url('rioja', self.year, 'locales')

        if not url:
            self.logger.error(f"No hay URL configurada para La Rioja {self.year}")
            return {}

        self.logger.info(f"Scraping festivos locales de La Rioja {self.year}")
        self.logger.info(f"URL: {url}")

        # TODO: Implementar parseo del BOR
        # El BOR publica en PDF, necesitamos:
        # 1. Descargar el PDF
        # 2. Analizar el formato (tabla con municipios y festivos)
        # 3. Parsear usando pdfplumber o similar
        # 4. Normalizar nombres de municipios

        raise NotImplementedError(
            "El scraper de La Rioja está en desarrollo. "
            "Necesita análisis del formato del BOR nº 159/2025. "
            "Por favor, descarga manualmente el PDF y analiza su estructura."
        )

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
