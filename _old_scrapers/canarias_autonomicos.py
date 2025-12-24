"""
Scraper para festivos autonómicos de Canarias
Extrae festivos de toda la CCAA y festivos insulares desde el BOC
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import json
import re

class CanariasAutonomicosScraper:
    """
    Extrae festivos autonómicos e insulares de Canarias desde el BOC (Decreto)
    """
    
    def __init__(self, year=2026):
        self.year = year
        self.base_url = "https://www.gobiernodecanarias.org/boc"
        self.festivos = []
        
        # Mapping de municipios a islas
        self.municipios_islas = {
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
            'La Graciosa': [],  # Sin municipios propios, comparte con Lanzarote
            'Fuerteventura': [
                'ANTIGUA', 'BETANCURIA', 'LA OLIVA', 'PÁJARA', 
                'PUERTO DEL ROSARIO', 'TUINEJE'
            ]
        }
    
    def get_boc_decreto_url(self):
        """Obtiene la URL del Decreto del BOC con festivos autonómicos"""
        if self.year == 2026:
            return "https://www.gobiernodecanarias.org/boc/2025/088/1659.html"
        elif self.year == 2025:
            return "https://www.gobiernodecanarias.org/boc/2024/187/3013.html"
        else:
            raise NotImplementedError(f"URL del Decreto para año {self.year} no implementada")
    
    def fetch_boc_content(self, url):
        """Descarga el contenido del BOC"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'
            return response.text
        except requests.RequestException as e:
            print(f"❌ Error al descargar BOC: {e}")
            return None
    
    def parse_fecha(self, texto):
        """Extrae fecha de texto como '1 de enero' o '30 de mayo'"""
        meses = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
            'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
            'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
        }
        
        match = re.search(r'(\d+)\s+de\s+(\w+)', texto, re.IGNORECASE)
        if match:
            dia = int(match.group(1))
            mes_texto = match.group(2).lower()
            mes = meses.get(mes_texto)
            
            if mes:
                try:
                    fecha = datetime(self.year, mes, dia)
                    return {
                        'fecha': fecha.strftime('%Y-%m-%d'),
                        'fecha_texto': f"{dia} de {mes_texto}"
                    }
                except ValueError:
                    pass
        
        return None
    
    def get_isla_municipio(self, municipio):
        """Devuelve la isla a la que pertenece un municipio"""
        for isla, municipios in self.municipios_islas.items():
            if municipio in municipios:
                return isla
        return None
    
    def parse_festivos(self, html_content):
        """Parsea el HTML del BOC y extrae festivos autonómicos e insulares"""
        soup = BeautifulSoup(html_content, 'lxml')
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
        
        # Dividir en líneas
        lineas = contenido_anexo.split('\n')
        
        festivos_canarias = []
        festivos_insulares = {}
        isla_actual = None
        
        modo = 'canarias'  # Empezamos con festivos de toda Canarias
        
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
                if 'Hierro' in isla_actual:
                    isla_actual = 'El Hierro'
                elif 'Palma' in isla_actual:
                    isla_actual = 'La Palma'
                elif 'Gomera' in isla_actual:
                    isla_actual = 'La Gomera'
                elif 'Tenerife' in isla_actual:
                    isla_actual = 'Tenerife'
                elif 'Gran Canaria' in isla_actual:
                    isla_actual = 'Gran Canaria'
                elif 'Lanzarote' in isla_actual or 'Graciosa' in isla_actual:
                    # Festivo compartido entre Lanzarote y La Graciosa
                    isla_actual = 'Lanzarote/La Graciosa'
                elif 'Fuerteventura' in isla_actual:
                    isla_actual = 'Fuerteventura'
                
                # Intentar extraer el festivo de la misma línea
                fecha_info = self.parse_fecha(resto_linea)
                if fecha_info:
                    # Extraer descripción
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
                fecha_info = self.parse_fecha(linea)
                
                if fecha_info:
                    # Extraer descripción (después de la fecha y coma)
                    partes = linea.split(',', 1)
                    if len(partes) > 1:
                        descripcion = partes[1].strip().rstrip('.')
                        
                        if modo == 'canarias':
                            festivos_canarias.append({
                                'fecha': fecha_info['fecha'],
                                'fecha_texto': fecha_info['fecha_texto'],
                                'descripcion': descripcion
                            })
        
        # Construir lista de festivos estructurados
        # 1. Festivos de toda Canarias (autonómicos)
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
            # Separar si es compartido
            islas_aplicables = []
            if '/' in isla:
                islas_aplicables = isla.split('/')
            else:
                islas_aplicables = [isla]
            
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
    
    def scrape(self):
        """Ejecuta el scraping del Decreto del BOC"""
        print(f"🔍 Scrapeando festivos autonómicos de Canarias desde BOC para {self.year}...")
        
        url = self.get_boc_decreto_url()
        print(f"📄 URL: {url}")
        
        html = self.fetch_boc_content(url)
        
        if html:
            self.festivos = self.parse_festivos(html)
            
            autonomicos = [f for f in self.festivos if f['ambito'] == 'autonomico' and f['islas'] == 'Todas']
            insulares = [f for f in self.festivos if f['ambito'] == 'insular']
            
            print(f"✅ Scraping completado:")
            print(f"   - {len(autonomicos)} festivos autonómicos (toda Canarias)")
            print(f"   - {len(insulares)} festivos insulares")
            print(f"   - {len(self.festivos)} festivos totales")
        else:
            print("❌ Error en el scraping")
        
        return self.festivos
    
    def to_dataframe(self):
        """Convierte los festivos a DataFrame de pandas"""
        df = pd.DataFrame(self.festivos)
        if not df.empty:
            df = df.sort_values(['fecha'])
        return df
    
    def save_to_json(self, filepath):
        """Guarda los festivos en formato JSON"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.festivos, f, ensure_ascii=False, indent=2)
        print(f"💾 Guardado en: {filepath}")
    
    def save_to_excel(self, filepath):
        """Guarda los festivos en formato Excel"""
        df = self.to_dataframe()
        df.to_excel(filepath, index=False)
        print(f"💾 Guardado en: {filepath}")
    
    def print_summary(self):
        """Imprime un resumen de los datos"""
        df = self.to_dataframe()
        if not df.empty:
            print("\n📊 RESUMEN:")
            print(f"   Total festivos: {len(df)}")
            
            autonomicos = df[df['ambito'] == 'autonomico']
            auto_canarias = autonomicos[autonomicos['islas'] == 'Todas']
            insulares = df[df['ambito'] == 'insular']
            
            print(f"   - Autonómicos (toda Canarias): {len(auto_canarias)}")
            print(f"   - Insulares: {len(insulares)}")
            
            print(f"\n📅 Festivos autonómicos {self.year}:")
            for _, row in auto_canarias.iterrows():
                print(f"   {row['fecha']} - {row['descripcion']}")
            
            print(f"\n🏝️  Festivos insulares {self.year}:")
            for _, row in insulares.iterrows():
                print(f"   {row['fecha']} - {row['descripcion']}")
                print(f"      └─ Islas: {row['islas']}")


if __name__ == "__main__":
    # Test del scraper
    scraper = CanariasAutonomicosScraper(year=2026)
    festivos = scraper.scrape()
    
    if festivos:
        scraper.print_summary()
        
        # Guardar resultados
        scraper.save_to_json('data/canarias_autonomicos_2026.json')
        scraper.save_to_excel('data/canarias_autonomicos_2026.xlsx')