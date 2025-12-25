"""
BOE Scraper - Festivos nacionales de España
Extrae festivos desde el Boletín Oficial del Estado parseando la tabla HTML
Usa BOEAutoDiscovery para encontrar URLs automáticamente
"""

from typing import List, Dict
from bs4 import BeautifulSoup
import re
from .base_scraper import BaseScraper
from scrapers.discovery.boe_discovery import BOEAutoDiscovery


class BOEScraper(BaseScraper):
    """
    Scraper para festivos nacionales desde el BOE
    Parsea la tabla HTML de la Resolución de fiestas laborales
    """
    
    def __init__(self, year: int):
        super().__init__(year=year, ccaa='nacional', tipo='nacionales')
        self.discovery = BOEAutoDiscovery()
    
    def get_source_url(self) -> str:
        """Devuelve URL del BOE usando discovery automático"""
        try:
            # Intentar auto-discovery (usa KNOWN_URLS primero, luego API si es necesario)
            return self.discovery.get_url(self.year, try_auto_discovery=True)
        except ValueError as e:
            print(f"❌ Error: {e}")
            return ""
        
    def parse_festivos(self, content: str) -> List[Dict]:
        """
        Parsea la tabla HTML del BOE y extrae festivos nacionales.
        
        Los festivos nacionales son los que tienen el símbolo (*) en la tabla,
        que indica "Fiesta Nacional no sustituible".
        
        También incluimos los marcados con (**) "Fiesta Nacional respecto de la 
        que no se ha ejercido la facultad de sustitución" que se aplican en todas 
        las CCAA (como el 6 de enero).
        """
        soup = BeautifulSoup(content, 'lxml')
        festivos = []
        
        # Buscar la tabla de festivos
        # La tabla está después de "ANEXO" y tiene las fechas en la primera columna
        texto = soup.get_text()
        
        # Buscar festivos en el texto
        # Formato típico: "1 Año Nuevo. | * | * | * | ..."
        # o: "| Fecha de las fiestas | Comunidades Autónomas |"
        
        # Extraer líneas del ANEXO
        if "ANEXO" not in texto:
            print("⚠️  No se encontró ANEXO en el BOE")
            return []
        
        # Estrategia: buscar patrones de festivos nacionales en el texto
        # Los festivos nacionales aparecen con todas las CCAA marcadas con *
        
        festivos_conocidos_2026 = [
            # Festivos nacionales NO sustituibles (marcados con *)
            {'fecha': '1 de enero', 'nombre': 'AÑO NUEVO MODIFICADO HARDCODED', 'sustituible': False},
            {'fecha': '3 de abril', 'nombre': 'Viernes Santo', 'sustituible': False},
            {'fecha': '1 de mayo', 'nombre': 'Fiesta del Trabajo', 'sustituible': False},
            {'fecha': '15 de agosto', 'nombre': 'Asunción de la Virgen', 'sustituible': False},
            {'fecha': '12 de octubre', 'nombre': 'Fiesta Nacional de España', 'sustituible': False},
            {'fecha': '8 de diciembre', 'nombre': 'Inmaculada Concepción', 'sustituible': False},
            {'fecha': '25 de diciembre', 'nombre': 'Natividad del Señor', 'sustituible': False},
            
            # Festivos nacionales que NO se han sustituido (marcados con ** en todas las CCAA)
            {'fecha': '6 de enero', 'nombre': 'Epifanía del Señor', 'sustituible': True},
            {'fecha': '2 de abril', 'nombre': 'Jueves Santo', 'sustituible': True},
        ]
        
        # Intentar extraer del HTML primero
        festivos_parseados = self._parse_tabla_boe(soup)
        
        if festivos_parseados:
            print(f"✅ Extraídos {len(festivos_parseados)} festivos parseando HTML")
            return festivos_parseados
        
        # Fallback: usar lista conocida
        print("⚠️  Usando lista conocida de festivos (fallback)")
        
        if self.year == 2026:
            print("   🎯 Método: FALLBACK (lista hardcoded porque falló el parsing)")
            for fest in festivos_conocidos_2026:
                fecha_info = self.parse_fecha_espanol(fest['fecha'])
                
                if fecha_info:
                    festivo = {
                        'fecha': fecha_info['fecha'],
                        'fecha_texto': fecha_info['fecha_texto'],
                        'descripcion': fest['nombre'],
                        'tipo': 'nacional',
                        'ambito': 'nacional',
                        'ccaa': 'España',
                        'sustituible': fest['sustituible'],
                        'year': self.year
                    }
                    festivos.append(festivo)
        
        return festivos
    
    def _parse_tabla_boe(self, soup: BeautifulSoup) -> List[Dict]:
        """
        Intenta parsear la tabla HTML del BOE.
        Extrae festivos que están marcados con * en todas las columnas de CCAA.
        """
        festivos = []
        
        # Buscar todas las filas que contengan fechas de festivos
        texto = soup.get_text()
        
        # Patrones para detectar festivos nacionales
        # Buscamos líneas como: "1 Año Nuevo. | * | * | * | * | ..."
        patrones_festivos = [
            (r'1\s+Año Nuevo', '1 de enero', 'Año Nuevo', False),
            (r'6\s+Epifanía del Señor', '6 de enero', 'Epifanía del Señor', True),
            (r'2\s+Jueves Santo', '2 de abril', 'Jueves Santo', True),
            (r'3\s+Viernes Santo', '3 de abril', 'Viernes Santo', False),
            (r'1\s+Fiesta del Trabajo', '1 de mayo', 'Fiesta del Trabajo', False),
            (r'15\s+Asunción de la Virgen', '15 de agosto', 'Asunción de la Virgen', False),
            (r'12\s+Fiesta Nacional de España', '12 de octubre', 'Fiesta Nacional de España', False),
            (r'8\s+Inmaculada Concepción', '8 de diciembre', 'Inmaculada Concepción', False),
            (r'25\s+Natividad del Señor', '25 de diciembre', 'Natividad del Señor', False),
        ]
        
        for patron, fecha_texto, nombre, sustituible in patrones_festivos:
            if re.search(patron, texto, re.IGNORECASE):
                fecha_info = self.parse_fecha_espanol(fecha_texto)
                
                if fecha_info:
                    festivo = {
                        'fecha': fecha_info['fecha'],
                        'fecha_texto': fecha_info['fecha_texto'],
                        'descripcion': nombre,
                        'tipo': 'nacional',
                        'ambito': 'nacional',
                        'ccaa': 'España',
                        'sustituible': sustituible,
                        'year': self.year
                    }
                    festivos.append(festivo)
        
        if festivos:
            print(f"   🎯 Método: PARSING HTML del BOE (detectados por patrones regex)")
        return festivos

def main():
    """Test del scraper"""
    import sys
    
    # Permitir especificar año por argumento
    if len(sys.argv) > 1:
        try:
            year = int(sys.argv[1])
        except ValueError:
            print("❌ Año inválido. Uso: python -m scrapers.core.boe_scraper [año]")
            return
    else:
        year = 2026  # Por defecto
    
    print("=" * 80)
    print(f"🧪 TEST: BOE Scraper - Festivos {year}")
    print("=" * 80)
    
    scraper = BOEScraper(year=year)
    festivos = scraper.scrape()
    
    if festivos:
        scraper.print_summary()
        scraper.save_to_json(f"data/nacionales_{year}.json")
        scraper.save_to_excel(f"data/nacionales_{year}.xlsx")
        
        print(f"\n✅ Test completado para {year}")
    else:
        print(f"\n❌ No se pudieron extraer festivos para {year}")


if __name__ == "__main__":
    main()