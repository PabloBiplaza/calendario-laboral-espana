"""
Scraper para el Boletín Oficial del Estado (BOE)
Extrae festivos nacionales de España desde XML
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import json
import re
import xml.etree.ElementTree as ET

class BOEScraper:
    """
    Extrae festivos nacionales del BOE usando XML
    """
    
    def __init__(self, year=2026):
        self.year = year
        self.base_url = "https://www.boe.es"
        self.festivos = []
        
    def get_boe_url_for_year(self):
        """Construye la URL XML del BOE para el año especificado"""
        if self.year == 2026:
            return "https://www.boe.es/diario_boe/xml.php?id=BOE-A-2025-21667"
        elif self.year == 2025:
            return "https://www.boe.es/diario_boe/xml.php?id=BOE-A-2024-20829"
        else:
            raise NotImplementedError(f"URL para año {self.year} no implementada aún")
    
    def fetch_boe_content(self, url):
        """Descarga el contenido XML del BOE"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'
            return response.text
        except requests.RequestException as e:
            print(f"❌ Error al descargar BOE: {e}")
            return None
    
    def parse_fecha_texto(self, texto):
        """
        Extrae fecha de texto como '1 de enero (jueves)' o similar
        """
        meses = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
            'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
            'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
        }
        
        # Buscar patrón "día de mes"
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
    
    def parse_festivos_from_xml(self, xml_content):
        """
        Parsea el XML del BOE y extrae los festivos
        """
        festivos = []
        
        try:
            # Parsear XML
            root = ET.fromstring(xml_content)
            
            # Buscar el texto del documento
            # La estructura del XML del BOE suele tener el texto en <texto>
            texto_completo = ""
            
            # Intentar diferentes estructuras comunes del BOE
            for texto_elem in root.iter('texto'):
                texto_completo += texto_elem.text or ""
            
            # Si no encontramos nada, extraer todo el texto
            if not texto_completo:
                texto_completo = ET.tostring(root, encoding='unicode', method='text')
            
            print(f"📄 Texto extraído del XML ({len(texto_completo)} caracteres)")
            
            # Buscar menciones de festivos en el texto
            lineas = texto_completo.split('\n')
            
            for linea in lineas:
                linea = linea.strip()
                
                # Buscar líneas que contengan fechas y posibles festivos
                if re.search(r'\d+\s+de\s+\w+', linea, re.IGNORECASE):
                    # Extraer fecha
                    fecha_info = self.parse_fecha_texto(linea)
                    
                    if fecha_info:
                        # Intentar extraer el nombre del festivo
                        # Buscar después de la fecha
                        partes = re.split(r'\d+\s+de\s+\w+', linea, flags=re.IGNORECASE)
                        if len(partes) > 1:
                            descripcion = partes[1].strip()
                            # Limpiar
                            descripcion = re.sub(r'^\W+', '', descripcion)
                            descripcion = re.sub(r'\.$', '', descripcion)
                            
                            if descripcion and len(descripcion) > 3:
                                festivo = {
                                    'fecha': fecha_info['fecha'],
                                    'fecha_texto': fecha_info['fecha_texto'],
                                    'descripcion': descripcion[:100],  # Limitar longitud
                                    'tipo': 'nacional',
                                    'ambito': 'nacional',
                                    'sustituible': self._es_sustituible(descripcion),
                                    'ccaa': 'Todas',
                                    'provincia': 'Todas',
                                    'municipio': 'Todos',
                                    'year': self.year
                                }
                                
                                # Evitar duplicados
                                if not any(f['fecha'] == festivo['fecha'] for f in festivos):
                                    festivos.append(festivo)
            
            # Si no encontramos suficientes festivos, usar lista hardcoded como fallback
            if len(festivos) < 9:
                print("⚠️  Pocos festivos extraídos del XML, usando lista conocida...")
                festivos = self._get_festivos_conocidos()
            
        except ET.ParseError as e:
            print(f"❌ Error parseando XML: {e}")
            print("📋 Usando lista de festivos conocidos...")
            festivos = self._get_festivos_conocidos()
        
        return festivos
    
    def _es_sustituible(self, descripcion):
        """
        Determina si un festivo es sustituible por las CCAA
        """
        # Jueves Santo es sustituible, el resto generalmente no
        sustituibles = ['jueves santo', 'san josé', 'santiago apóstol']
        desc_lower = descripcion.lower()
        return any(s in desc_lower for s in sustituibles)
    
    def _get_festivos_conocidos(self):
        """
        Retorna lista de festivos nacionales conocidos para el año
        """
        festivos_base = [
            {'dia': 1, 'mes': 1, 'nombre': 'Año Nuevo', 'sustituible': False},
            {'dia': 6, 'mes': 1, 'nombre': 'Epifanía del Señor', 'sustituible': False},
            {'dia': 1, 'mes': 5, 'nombre': 'Fiesta del Trabajo', 'sustituible': False},
            {'dia': 15, 'mes': 8, 'nombre': 'Asunción de la Virgen', 'sustituible': False},
            {'dia': 12, 'mes': 10, 'nombre': 'Fiesta Nacional de España', 'sustituible': False},
            {'dia': 1, 'mes': 11, 'nombre': 'Todos los Santos', 'sustituible': False},
            {'dia': 6, 'mes': 12, 'nombre': 'Día de la Constitución Española', 'sustituible': False},
            {'dia': 8, 'mes': 12, 'nombre': 'Inmaculada Concepción', 'sustituible': False},
            {'dia': 25, 'mes': 12, 'nombre': 'Natividad del Señor', 'sustituible': False},
        ]
        
        # Añadir Semana Santa según el año
        if self.year == 2026:
            festivos_base.extend([
                {'dia': 2, 'mes': 4, 'nombre': 'Jueves Santo', 'sustituible': True},
                {'dia': 3, 'mes': 4, 'nombre': 'Viernes Santo', 'sustituible': False},
            ])
        elif self.year == 2025:
            festivos_base.extend([
                {'dia': 17, 'mes': 4, 'nombre': 'Jueves Santo', 'sustituible': True},
                {'dia': 18, 'mes': 4, 'nombre': 'Viernes Santo', 'sustituible': False},
            ])
        
        festivos = []
        for fest in festivos_base:
            try:
                fecha = datetime(self.year, fest['mes'], fest['dia'])
                festivo = {
                    'fecha': fecha.strftime('%Y-%m-%d'),
                    'fecha_texto': f"{fest['dia']} de {self._nombre_mes(fest['mes'])}",
                    'descripcion': fest['nombre'],
                    'tipo': 'nacional',
                    'ambito': 'nacional',
                    'sustituible': fest['sustituible'],
                    'ccaa': 'Todas',
                    'provincia': 'Todas',
                    'municipio': 'Todos',
                    'year': self.year
                }
                festivos.append(festivo)
            except ValueError:
                continue
        
        return festivos
    
    def _nombre_mes(self, numero_mes):
        """Convierte número de mes a nombre"""
        meses = ['', 'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
                'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
        return meses[numero_mes]
    
    def scrape(self):
        """Ejecuta el scraping completo"""
        print(f"🔍 Iniciando scraping BOE para {self.year}...")
        
        url = self.get_boe_url_for_year()
        print(f"📄 URL (XML): {url}")
        
        xml_content = self.fetch_boe_content(url)
        
        if xml_content:
            self.festivos = self.parse_festivos_from_xml(xml_content)
            print(f"✅ Scraping completado:")
            print(f"   - {len(self.festivos)} festivos nacionales extraídos")
        else:
            print("❌ Error en el scraping, usando festivos conocidos")
            self.festivos = self._get_festivos_conocidos()
        
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
        """Imprime un resumen de los datos extraídos"""
        df = self.to_dataframe()
        if not df.empty:
            print("\n📊 RESUMEN:")
            print(f"   Total festivos nacionales: {len(df)}")
            
            sustituibles = df[df['sustituible'] == True]
            no_sustituibles = df[df['sustituible'] == False]
            
            print(f"   - No sustituibles: {len(no_sustituibles)}")
            print(f"   - Sustituibles por CCAA: {len(sustituibles)}")
            
            print(f"\n📅 Festivos nacionales {self.year}:")
            for _, row in df.iterrows():
                sust = " (sustituible)" if row['sustituible'] else ""
                print(f"   {row['fecha']} - {row['descripcion']}{sust}")


if __name__ == "__main__":
    # Test del scraper
    scraper = BOEScraper(year=2026)
    festivos = scraper.scrape()
    
    if festivos:
        scraper.print_summary()
        
        # Guardar resultados
        scraper.save_to_json('data/nacionales_2026.json')
        scraper.save_to_excel('data/nacionales_2026.xlsx')