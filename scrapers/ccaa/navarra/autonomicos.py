"""
Scraper de festivos autonómicos para Navarra.

Navarra tiene festivos autonómicos propios, algunos de los cuales son
fechas móviles calculadas a partir de la Pascua.
"""

from typing import List, Dict
from datetime import datetime

from scrapers.core.base_scraper import BaseScraper
from scrapers.utils.date_calculator import calcular_pascua


class NavarraAutonomicosScraper(BaseScraper):
    """
    Scraper para festivos autonómicos de Navarra.

    Festivos autonómicos de Navarra (pueden variar por año):
    - San José (19 de marzo)
    - Jueves Santo (fecha móvil: Pascua - 3 días)
    - Viernes Santo (fecha móvil: Pascua - 2 días)
    - Lunes de Pascua (fecha móvil: Pascua + 1 día)
    - San Francisco Javier (3 de diciembre) - Patrón de Navarra
    """

    def __init__(self, year: int = 2026, municipio: str = None):
        super().__init__(year, ccaa='navarra', tipo='autonomicos')
        self.municipio = municipio

    def get_source_url(self) -> str:
        """
        Obtiene la URL del BON con festivos autonómicos.

        Returns:
            URL del BON (puede estar vacía si no hay URL específica)
        """
        from config.config_manager import registry
        url = registry.get_url('navarra', self.year, 'autonomicos')
        return url or ""

    def parse_festivos(self, content: str) -> List[Dict]:
        """
        Para Navarra, los festivos autonómicos son fijos/calculables,
        no necesitamos parsear un documento.

        Returns:
            Lista vacía (no usamos parsing)
        """
        return []

    def scrape(self) -> List[Dict]:
        """
        Retorna los festivos autonómicos de Navarra para el año dado.

        Los festivos son mayormente fijos, excepto los relacionados con Pascua
        que se calculan dinámicamente.

        Returns:
            Lista de festivos autonómicos
        """
        print(f"Obteniendo festivos autonómicos de Navarra {self.year}")

        festivos = []

        # Calcular Pascua para el año
        pascua = calcular_pascua(self.year)

        # 1. San José - 19 de marzo (festivo fijo)
        festivos.append({
            'fecha': f'{self.year}-03-19',
            'descripcion': 'San José',
            'tipo': 'autonomico',
            'ambito': 'autonomico',
            'year': self.year
        })

        # 2. Jueves Santo - 3 días antes de Pascua
        jueves_santo = pascua.replace(day=pascua.day - 3)
        festivos.append({
            'fecha': jueves_santo.strftime('%Y-%m-%d'),
            'descripcion': 'Jueves Santo',
            'tipo': 'autonomico',
            'ambito': 'autonomico',
            'year': self.year,
            'calculada': True,
            'metodo_calculo': 'liturgico_pascua: -3 días'
        })

        # 3. Viernes Santo - 2 días antes de Pascua (también es festivo nacional, pero lo incluimos)
        viernes_santo = pascua.replace(day=pascua.day - 2)
        festivos.append({
            'fecha': viernes_santo.strftime('%Y-%m-%d'),
            'descripcion': 'Viernes Santo',
            'tipo': 'autonomico',
            'ambito': 'autonomico',
            'year': self.year,
            'calculada': True,
            'metodo_calculo': 'liturgico_pascua: -2 días'
        })

        # 4. Lunes de Pascua - 1 día después de Pascua
        lunes_pascua = pascua.replace(day=pascua.day + 1)
        festivos.append({
            'fecha': lunes_pascua.strftime('%Y-%m-%d'),
            'descripcion': 'Lunes de Pascua',
            'tipo': 'autonomico',
            'ambito': 'autonomico',
            'year': self.year,
            'calculada': True,
            'metodo_calculo': 'liturgico_pascua: +1 día'
        })

        # 5. San Francisco Javier - 3 de diciembre (Patrón de Navarra)
        festivos.append({
            'fecha': f'{self.year}-12-03',
            'descripcion': 'San Francisco Javier',
            'tipo': 'autonomico',
            'ambito': 'autonomico',
            'year': self.year
        })

        print(f"✅ {len(festivos)} festivos autonómicos obtenidos")

        return festivos


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Uso: python autonomicos.py <año>")
        print("Ejemplo: python autonomicos.py 2026")
        sys.exit(1)

    year = int(sys.argv[1])
    scraper = NavarraAutonomicosScraper(year=year)

    try:
        festivos = scraper.scrape()
        print(f"\nFestivos autonómicos de Navarra en {year}:")
        for f in festivos:
            calculada_info = f" [calculada: {f.get('metodo_calculo', '')}]" if f.get('calculada') else ""
            print(f"  - {f['fecha']}: {f['descripcion']}" + calculada_info)
    except Exception as e:
        print(f"\n⚠️  Error: {e}")
        import traceback
        traceback.print_exc()
