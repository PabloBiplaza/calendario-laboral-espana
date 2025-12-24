"""
Canarias Autonómicos Scraper
Extrae festivos autonómicos e insulares desde el Decreto del BOC
"""

from typing import List, Dict
import re
from bs4 import BeautifulSoup
from scrapers.core.base_scraper import BaseScraper


class CanariasAutonomicosScraper(BaseScraper):
    """
    Scraper para festivos autonómicos e insulares de Canarias
    Extrae desde el Decreto publicado en el BOC
    """
    
    def __init__(self, year: int):
        super().__init__(year=year, ccaa='canarias', tipo='autonomicos')
        
        # Mapping de municipios a islas (heredado de config si es necesario)
        self.municipios_islas = self._load_municipios_islas()
    
    def _load_municipios_islas(self) -> Dict[str, List[str]]:
        """Carga mapping de municipios a islas desde configuración o hardcoded"""
        return {
            'Tenerife': [
                'ADEJE', 'ARAFO', 'ARICO', 'ARONA', 'BUENAVISTA DEL NORTE',
                'CANDELARIA', 'FASNIA', 'GARACHICO', 'GRANADILLA DE ABONA',
                'GUÍA DE ISORA', 'GÜÍMAR', 'ICOD DE LOS VINOS', 'LA GUANCHA',
                'LA MATANZA DE ACENTEJO', 'LA OROTAVA', 'LA VICTORIA DE ACENTEJO',
                'LOS REALEJOS', 'LOS SILOS', 'PUERTO DE LA CRUZ', 'EL ROSARIO',
                'SAN CRISTÓBAL DE LA LAGUNA', 'SAN JUAN DE LA RAMBLA',
                'SAN MIGUEL DE ABONA', 'SANTA CRUZ DE TENERIFE', 'SANTA ÚRSULA',
                'SANTIAGO DEL TEIDE', 'EL SAUZAL', 'TACORONTE', 'EL TANQUE',
                'TEGUESTE', 'VILAFLOR DE CHASNA'
            ],
            'La Palma': [
                'BARLOVENTO', 'BREÑA ALTA', 'BREÑA BAJA', 'FUENCALIENTE DE LA PALMA',
                'GARAFÍA', 'LOS LLANOS DE ARIDANE', 'EL PASO', 'PUNTAGORDA',
                'PUNTALLANA', 'SAN ANDRÉS Y SAUCES', 'SANTA CRUZ DE LA PALMA',
                'TAZACORTE', 'TIJARAFE', 'VILLA DE MAZO'
            ],
            'La Gomera': [
                'AGULO', 'ALAJERÓ', 'HERMIGUA', 'SAN SEBASTIÁN DE LA GOMERA',
                'VALLE GRAN REY', 'VALLEHERMOSO'
            ],
            'El Hierro': [
                'LA FRONTERA', 'EL PINAR DE EL HIERRO', 'VALVERDE'
            ],
            'Gran Canaria': [
                'AGAETE', 'AGÜIMES', 'ARTENARA', 'ARUCAS', 'FIRGAS', 'GÁLDAR',
                'INGENIO', 'LA ALDEA DE SAN NICOLÁS', 'LAS PALMAS DE GRAN CANARIA',
                'MOGÁN', 'MOYA', 'SAN BARTOLOMÉ DE TIRAJANA', 'SANTA BRÍGIDA',
                'SANTA LUCÍA', 'SANTA MARÍA DE GUÍA', 'TELDE', 'TEJEDA', 'TEROR',
                'VALLESECO', 'VALSEQUILLO', 'VEGA DE SAN MATEO'
            ],
            'Lanzarote': [
                'ARRECIFE', 'HARÍA', 'SAN BARTOLOMÉ DE LANZAROTE', 'TEGUISE',
                'TÍAS', 'TINAJO', 'YAIZA'
            ],
            'La Graciosa': [],
            'Fuerteventura': [
                'ANTIGUA', 'BETANCURIA', 'LA OLIVA', 'PÁJARA', 
                'PUERTO DEL ROSARIO', 'TUINEJE'
            ]
        }
    
    def get_source_url(self) -> str:
        """Obtiene URL del Decreto desde configuración"""
        publicaciones = self.config.get('publicaciones', {})
        year_config = publicaciones.get(str(self.year), {})
        autonomicos_config = year_config.get('autonomicos', {})
        
        url = autonomicos_config.get('url', '')
        
        if not url:
            print(f"⚠️  URL no configurada para {self.ccaa} {self.year}")
        
        return url
    
    def get_isla_municipio(self, municipio: str) -> str:
        """Devuelve la isla a la que pertenece un municipio"""
        for isla, municipios in self.municipios_islas.items():
            if municipio in municipios:
                return isla
        return None
    
    def parse_festivos(self, content: str) -> List[Dict]:
        """
        Parsea el Decreto del BOC y extrae festivos autonómicos e insulares
        """
        soup = BeautifulSoup(content, 'lxml')
        festivos = []
        
        # Extraer texto
        texto = soup.get_text()
        
        # Buscar el ANEXO
        anexo_pos = texto.find("ANEXO")
        if anexo_pos == -1:
            print("❌ No se encontró ANEXO en el Decreto")
            return []
        
        # Extraer contenido del anexo
        contenido_anexo = texto[anexo_pos:]
        lineas = contenido_anexo.split('\n')
        
        festivos_canarias = []
        festivos_insulares = {}
        isla_actual = None
        modo = 'canarias'
        
        for linea in lineas:
            linea = linea.strip()
            
            if not linea:
                continue
            
            # Detectar cambio a festivos insulares
            if 'En las islas de' in linea or 'las fiestas laborales serán' in linea:
                modo = 'insulares'
                continue
            
            # Detectar isla específica
            isla_match = re.match(r'^[-–]\s*En\s+(.+?):\s*(.+)', linea, re.IGNORECASE)
            if isla_match:
                isla_actual = isla_match.group(1).strip()
                resto_linea = isla_match.group(2)
                
                # Normalizar nombre de isla
                isla_actual = self._normalizar_isla(isla_actual)
                
                # Intentar extraer el festivo de la misma línea
                fecha_info = self.parse_fecha_espanol(resto_linea)
                if fecha_info:
                    match_desc = re.search(r'festividad\s+de\s+(.+?)\.?$', resto_linea, re.IGNORECASE)
                    if match_desc:
                        descripcion = match_desc.group(1).strip()
                        festivos_insulares[isla_actual] = {
                            'fecha': fecha_info['fecha'],
                            'fecha_texto': fecha_info['fecha_texto'],
                            'descripcion': f"Festividad de {descripcion}"
                        }
                
                continue
            
            # Detectar festivos (formato: "- día de mes, Nombre.")
            if linea.startswith('-') or linea.startswith('•'):
                fecha_info = self.parse_fecha_espanol(linea)
                
                if fecha_info:
                    partes = linea.split(',', 1)
                    if len(partes) > 1:
                        descripcion = partes[1].strip().rstrip('.')
                        
                        if modo == 'canarias':
                            festivos_canarias.append({
                                'fecha': fecha_info['fecha'],
                                'fecha_texto': fecha_info['fecha_texto'],
                                'descripcion': descripcion
                            })
        
        # Construir lista estructurada
        # 1. Festivos de toda Canarias
        for fest in festivos_canarias:
            festivo = {
                'fecha': fest['fecha'],
                'fecha_texto': fest['fecha_texto'],
                'descripcion': fest['descripcion'],
                'tipo': 'autonomico',
                'ambito': 'autonomico',
                'ccaa': 'Canarias',
                'islas': 'Todas',
                'municipios_aplicables': 'Todos',
                'year': self.year
            }
            festivos.append(festivo)
        
        # 2. Festivos insulares
        for isla, datos in festivos_insulares.items():
            islas_aplicables = isla.split('/') if '/' in isla else [isla]
            
            festivo = {
                'fecha': datos['fecha'],
                'fecha_texto': datos['fecha_texto'],
                'descripcion': datos['descripcion'],
                'tipo': 'autonomico',
                'ambito': 'insular',
                'ccaa': 'Canarias',
                'islas': isla,
                'municipios_aplicables': islas_aplicables,
                'year': self.year
            }
            festivos.append(festivo)
        
        return festivos
    
    def _normalizar_isla(self, isla: str) -> str:
        """Normaliza nombres de islas"""
        if 'Hierro' in isla:
            return 'El Hierro'
        elif 'Palma' in isla and 'Gran' not in isla:
            return 'La Palma'
        elif 'Gomera' in isla:
            return 'La Gomera'
        elif 'Tenerife' in isla:
            return 'Tenerife'
        elif 'Gran Canaria' in isla:
            return 'Gran Canaria'
        elif 'Lanzarote' in isla or 'Graciosa' in isla:
            return 'Lanzarote/La Graciosa'
        elif 'Fuerteventura' in isla:
            return 'Fuerteventura'
        return isla


if __name__ == "__main__":
    # Test del scraper
    scraper = CanariasAutonomicosScraper(year=2026)
    festivos = scraper.scrape()
    
    if festivos:
        scraper.print_summary()
        scraper.save_to_json('data/canarias_autonomicos_2026.json')
        scraper.save_to_excel('data/canarias_autonomicos_2026.xlsx')