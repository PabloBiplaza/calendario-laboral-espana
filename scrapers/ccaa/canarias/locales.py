"""
Canarias Locales Scraper
Extrae festivos locales por municipio desde la Orden del BOC
"""

from typing import List, Dict
import re
from bs4 import BeautifulSoup
from scrapers.core.base_scraper import BaseScraper


class CanariasLocalesScraper(BaseScraper):
    """
    Scraper para festivos locales de Canarias
    Extrae desde la Orden publicada en el BOC (2 festivos por municipio)
    """
    
    def __init__(self, year: int):
        super().__init__(year=year, ccaa='canarias', tipo='locales')
    
    def get_source_url(self) -> str:
        """Obtiene URL de la Orden desde configuración"""
        publicaciones = self.config.get('publicaciones', {})
        year_config = publicaciones.get(str(self.year), {})
        locales_config = year_config.get('locales', {})
        
        url = locales_config.get('url', '')
        
        if not url:
            print(f"⚠️  URL no configurada para {self.ccaa} {self.year}")
        
        return url
    
    def parse_festivos(self, content: str) -> List[Dict]:
        """
        Parsea la Orden del BOC y extrae festivos locales por municipio.
        Cada municipio tiene exactamente 2 festivos locales.
        """
        soup = BeautifulSoup(content, 'lxml')
        festivos = []
        
        # Extraer texto
        texto = soup.get_text()
        lineas = texto.split('\n')
        
        municipio_actual = None
        festivos_municipio = []
        
        for linea in lineas:
            linea = linea.strip()
            
            if not linea:
                continue
            
            # Detectar municipio (mayúsculas + punto)
            if re.match(r'^[A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s]+\.$', linea):
                # Guardar festivos del municipio anterior
                if municipio_actual and festivos_municipio:
                    for fest in festivos_municipio:
                        festivos.append(fest)
                
                # Nuevo municipio
                municipio_actual = linea.rstrip('.').strip()
                festivos_municipio = []
                continue
            
            # Detectar festivo (formato: "DD mes: Descripción" o "DD de mes: Descripción")
            if municipio_actual:
                match_festivo = re.match(r'(\d+\s+(?:de\s+)?\w+):\s*(.+)', linea)
                
                if match_festivo:
                    fecha_texto = match_festivo.group(1)
                    descripcion = match_festivo.group(2).strip()
                    
                    fecha_info = self.parse_fecha_espanol(fecha_texto)
                    
                    if fecha_info:
                        # Verificar que no exista ya este festivo para este municipio
                        fecha_existe = any(
                            f['fecha'] == fecha_info['fecha'] and f['municipio'] == municipio_actual
                            for f in festivos_municipio
                        )
                        
                        if not fecha_existe:
                            provincia = self._detectar_provincia(municipio_actual)
                            
                            festivo = {
                                'municipio': municipio_actual,
                                'fecha': fecha_info['fecha'],
                                'fecha_texto': fecha_info['fecha_texto'],
                                'descripcion': descripcion,
                                'tipo': 'local',
                                'ambito': 'municipal',
                                'ccaa': 'Canarias',
                                'provincia': provincia,
                                'year': self.year
                            }
                            festivos_municipio.append(festivo)
        
        # Guardar festivos del último municipio
        if municipio_actual and festivos_municipio:
            for fest in festivos_municipio:
                festivos.append(fest)
        
        return festivos
    
    def _detectar_provincia(self, municipio: str) -> str:
        """
        Detecta la provincia basándose en el municipio.
        Usa configuración YAML si está disponible.
        """
        # Municipios de Las Palmas
        municipios_las_palmas = [
            'AGAETE', 'AGÜIMES', 'ANTIGUA', 'ARRECIFE', 'ARTENARA', 'ARUCAS',
            'BETANCURIA', 'FIRGAS', 'GÁLDAR', 'HARÍA', 'INGENIO',
            'LA ALDEA DE SAN NICOLÁS', 'LA OLIVA', 'LAS PALMAS DE GRAN CANARIA',
            'MOGÁN', 'MOYA', 'PÁJARA', 'PUERTO DEL ROSARIO',
            'SAN BARTOLOMÉ DE LANZAROTE', 'SAN BARTOLOMÉ DE TIRAJANA',
            'SANTA BRÍGIDA', 'SANTA LUCÍA', 'SANTA MARÍA DE GUÍA', 'TEGUISE',
            'TEJEDA', 'TELDE', 'TEROR', 'TÍAS', 'TINAJO', 'TUINEJE',
            'VALLESECO', 'VALSEQUILLO', 'VEGA DE SAN MATEO', 'YAIZA'
        ]
        
        if municipio in municipios_las_palmas:
            return 'Las Palmas'
        else:
            return 'Santa Cruz de Tenerife'


if __name__ == "__main__":
    # Test del scraper
    scraper = CanariasLocalesScraper(year=2026)
    festivos = scraper.scrape()
    
    if festivos:
        scraper.print_summary()
        scraper.save_to_json('data/canarias_locales_2026.json')
        scraper.save_to_excel('data/canarias_locales_2026.xlsx')