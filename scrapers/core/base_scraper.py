"""
Base Scraper - Clase abstracta para todos los scrapers de festivos
Proporciona funcionalidad común y define la interfaz que deben implementar
todos los scrapers específicos de cada CCAA.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime
import requests
import pandas as pd
import json
import re
import yaml
from pathlib import Path


class BaseScraper(ABC):
    """
    Clase base abstracta para todos los scrapers de festivos.
    
    Proporciona:
    - Descarga de contenido HTTP
    - Parsing de fechas
    - Validación de datos
    - Guardado en JSON/Excel
    - Logging
    
    Los scrapers hijos deben implementar:
    - get_source_url()
    - parse_festivos()
    """
    
    def __init__(self, year: int, ccaa: str, tipo: str):
        """
        Inicializa el scraper base.
        
        Args:
            year: Año del calendario (ej: 2026)
            ccaa: Código de CCAA (ej: 'canarias', 'andalucia')
            tipo: Tipo de festivos ('autonomicos', 'locales', 'nacionales')
        """
        self.year = year
        self.ccaa = ccaa
        self.tipo = tipo
        self.festivos = []
        self.config = self._load_config()
        
        # Metadatos del scraping
        self.metadata = {
            'fecha_scraping': datetime.now().isoformat(),
            'year': year,
            'ccaa': ccaa,
            'tipo': tipo,
            'fuente': None,
            'num_festivos': 0
        }
    
    def _load_config(self) -> Dict:
        """Carga configuración desde config/ccaa.yaml"""
        config_path = Path(__file__).parent.parent.parent / 'config' / 'ccaa.yaml'
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                all_config = yaml.safe_load(f)
                return all_config.get(self.ccaa, {})
        except FileNotFoundError:
            print(f"⚠️  Archivo de configuración no encontrado: {config_path}")
            return {}
    
    @abstractmethod
    def get_source_url(self) -> str:
        """
        Devuelve la URL de la fuente oficial de datos.
        Debe ser implementado por cada scraper específico.
        
        Returns:
            URL completa del boletín oficial
        """
        pass
    
    @abstractmethod
    def parse_festivos(self, content: str) -> List[Dict]:
        """
        Parsea el contenido descargado y extrae los festivos.
        Debe ser implementado por cada scraper específico.
        
        Args:
            content: Contenido HTML/XML descargado
            
        Returns:
            Lista de diccionarios con festivos estructurados
        """
        pass
    
    def fetch_content(self, url: str, encoding: str = 'utf-8') -> Optional[str]:
        """
        Descarga contenido desde una URL.
        
        Args:
            url: URL a descargar
            encoding: Codificación del contenido (default: utf-8)
            
        Returns:
            Contenido como string o None si falla
        """
        try:
            print(f"📥 Descargando: {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            response.encoding = encoding
            print(f"✅ Descarga completada ({len(response.text)} caracteres)")
            return response.text
        except requests.RequestException as e:
            print(f"❌ Error al descargar: {e}")
            return None
    
    def parse_fecha_espanol(self, texto: str) -> Optional[Dict[str, str]]:
        """
        Parsea fechas en español (ej: "1 de enero", "25 diciembre").
        
        Args:
            texto: Texto con la fecha
            
        Returns:
            Dict con 'fecha' (ISO) y 'fecha_texto' o None si no se puede parsear
        """
        meses = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
            'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
            'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
        }
        
        # Patrón flexible: "DD de mes" o "DD mes"
        match = re.search(r'(\d+)\s+(?:de\s+)?(\w+)', texto, re.IGNORECASE)
        
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
                except ValueError as e:
                    print(f"⚠️  Fecha inválida: {dia}/{mes}/{self.year} - {e}")
        
        return None
    
    def validate_festivo(self, festivo: Dict) -> bool:
        """
        Valida que un festivo tenga la estructura correcta.
        
        Args:
            festivo: Diccionario con datos del festivo
            
        Returns:
            True si es válido, False si no
        """
        campos_requeridos = ['fecha', 'descripcion', 'tipo', 'ambito']
        
        for campo in campos_requeridos:
            if campo not in festivo:
                print(f"⚠️  Festivo inválido - falta campo '{campo}': {festivo}")
                return False
        
        # Validar formato de fecha
        try:
            datetime.strptime(festivo['fecha'], '%Y-%m-%d')
        except ValueError:
            print(f"⚠️  Formato de fecha inválido: {festivo['fecha']}")
            return False
        
        return True
    
    def scrape(self) -> List[Dict]:
        """
        Ejecuta el proceso completo de scraping.
        
        Returns:
            Lista de festivos extraídos
        """
        print(f"\n{'='*80}")
        print(f"🔍 Iniciando scraping: {self.ccaa.upper()} - {self.tipo.upper()} - {self.year}")
        print(f"{'='*80}")
        
        # 1. Obtener URL
        url = self.get_source_url()
        if not url:
            print("❌ No se pudo obtener URL de la fuente")
            return []
        
        self.metadata['fuente'] = url
        
        # 2. Descargar contenido
        content = self.fetch_content(url)
        if not content:
            print("❌ No se pudo descargar el contenido")
            return []
        
        # 3. Parsear festivos (implementado por clase hija)
        print(f"🔍 Parseando festivos...")
        self.festivos = self.parse_festivos(content)
        
        # 4. Validar festivos
        festivos_validos = []
        for festivo in self.festivos:
            if self.validate_festivo(festivo):
                festivos_validos.append(festivo)
        
        self.festivos = festivos_validos
        self.metadata['num_festivos'] = len(self.festivos)
        
        # 5. Resumen
        print(f"\n✅ Scraping completado:")
        print(f"   • Festivos extraídos: {len(self.festivos)}")
        print(f"   • Fuente: {url}")
        print(f"{'='*80}\n")
        
        return self.festivos
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convierte festivos a DataFrame de pandas"""
        df = pd.DataFrame(self.festivos)
        if not df.empty:
            df = df.sort_values(['fecha'])
        return df
    
    def save_to_json(self, filepath: str):
        """
        Guarda festivos en formato JSON.
        
        Args:
            filepath: Ruta del archivo a guardar
        """
        output = {
            'metadata': self.metadata,
            'festivos': self.festivos
        }
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"💾 JSON guardado: {filepath}")
    
    def save_to_excel(self, filepath: str):
        """
        Guarda festivos en formato Excel.
        
        Args:
            filepath: Ruta del archivo a guardar
        """
        df = self.to_dataframe()
        
        if df.empty:
            print("⚠️  No hay festivos para guardar en Excel")
            return
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Hoja de festivos
            df.to_excel(writer, sheet_name='Festivos', index=False)
            
            # Hoja de metadatos
            metadata_df = pd.DataFrame([self.metadata])
            metadata_df.to_excel(writer, sheet_name='Metadata', index=False)
        
        print(f"💾 Excel guardado: {filepath}")
    
    def print_summary(self):
        """Imprime un resumen de los festivos extraídos"""
        if not self.festivos:
            print("⚠️  No hay festivos para mostrar")
            return
        
        df = self.to_dataframe()
        
        print(f"\n{'='*80}")
        print(f"📊 RESUMEN - {self.ccaa.upper()} {self.year}")
        print(f"{'='*80}")
        print(f"Tipo: {self.tipo}")
        print(f"Total festivos: {len(df)}")
        
        # Agrupar por tipo
        if 'tipo' in df.columns:
            print(f"\nPor tipo:")
            for tipo, grupo in df.groupby('tipo'):
                print(f"   • {tipo}: {len(grupo)}")
        
        # Agrupar por ámbito
        if 'ambito' in df.columns:
            print(f"\nPor ámbito:")
            for ambito, grupo in df.groupby('ambito'):
                print(f"   • {ambito}: {len(grupo)}")
        
        print(f"\n📅 Festivos:")
        for _, row in df.iterrows():
            print(f"   • {row['fecha']} - {row['descripcion']}")
        
        print(f"{'='*80}\n")