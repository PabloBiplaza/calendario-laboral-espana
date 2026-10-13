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
        Parsea festivos desde el contenido del BOE.
        Estrategia genérica: buscar fechas + descripciones cercanas
        """
        festivos = []
        
        print("🔍 Parseando festivos...")
        
        # ESTRATEGIA 1: Buscar tabla HTML estructurada
        festivos_tabla = self._parse_tabla_html(content)
        if festivos_tabla and len(festivos_tabla) >= 8:
            print(f"   ✅ Método: Tabla HTML estructurada")
            return festivos_tabla
        
        # ESTRATEGIA 2: Buscar patrones de texto con fechas
        festivos_texto = self._parse_texto_patrones(content)
        if festivos_texto and len(festivos_texto) >= 8:
            print(f"   ✅ Método: Patrones de texto")
            return festivos_texto
        
        # ESTRATEGIA 3: Fallback - patrones conocidos (actual)
        festivos_conocidos = self._parse_patrones_conocidos(content)
        if festivos_conocidos:
            print(f"   ⚠️  Método: Patrones conocidos (fallback)")
            return festivos_conocidos
        
        return []
    
    def _parse_tabla_html(self, content: str) -> List[Dict]:
        """Parsea tabla HTML del BOE"""
        try:
            from bs4 import BeautifulSoup
            
            soup = BeautifulSoup(content, 'lxml')
            festivos = []
            
            # Buscar todas las tablas
            tablas = soup.find_all('table')
            
            for tabla in tablas:
                filas = tabla.find_all('tr')
                
                for fila in filas:
                    celdas = fila.find_all(['td', 'th'])
                    if len(celdas) < 2:
                        continue
                    
                    texto_fila = ' '.join([c.get_text(strip=True) for c in celdas])
                    
                    # Buscar fechas en formato "1 de enero", "6 de enero", etc.
                    fecha_match = self._extraer_fecha_de_texto(texto_fila)
                    
                    if fecha_match:
                        fecha_iso, fecha_texto = fecha_match
                        
                        # Extraer descripción (eliminar la fecha del texto)
                        descripcion = texto_fila.replace(fecha_texto, '').strip()
                        descripcion = re.sub(r'^\d+\s*', '', descripcion)  # Quitar número inicial
                        descripcion = descripcion.strip('.,;:-')
                        
                        if descripcion and len(descripcion) > 3:
                            festivos.append({
                                'fecha': fecha_iso,
                                'fecha_texto': fecha_texto,
                                'descripcion': descripcion.title(),
                                'tipo': 'nacional',
                                'ambito': 'nacional',
                                'sustituible': False,
                                'year': self.year
                            })
            
            # Deduplicar por fecha
            fechas_vistas = set()
            festivos_unicos = []
            for f in festivos:
                if f['fecha'] not in fechas_vistas:
                    fechas_vistas.add(f['fecha'])
                    festivos_unicos.append(f)
            
            return festivos_unicos
            
        except Exception as e:
            print(f"   ⚠️  Error en parse_tabla_html: {e}")
            return []
    
    def _parse_texto_patrones(self, content: str) -> List[Dict]:
        """Parsea texto buscando patrones de fecha + descripción"""
        try:
            festivos = []
            
            # Dividir en líneas
            lineas = content.split('\n')
            
            for linea in lineas:
                # Buscar líneas que contengan fechas
                fecha_match = self._extraer_fecha_de_texto(linea)
                
                if fecha_match:
                    fecha_iso, fecha_texto = fecha_match
                    
                    # La descripción es lo que viene después de la fecha
                    # Eliminar la fecha del texto
                    resto = linea.replace(fecha_texto, '')
                    
                    # Limpiar
                    resto = re.sub(r'^\d+\s*[.)\-:]\s*', '', resto)  # Quitar numeración
                    resto = resto.strip('.,;:-()[]')
                    
                    if resto and len(resto) > 3:
                        # Tomar hasta el primer punto o 100 caracteres
                        descripcion = resto.split('.')[0][:100].strip()
                        
                        if descripcion:
                            festivos.append({
                                'fecha': fecha_iso,
                                'fecha_texto': fecha_texto,
                                'descripcion': descripcion.title(),
                                'tipo': 'nacional',
                                'ambito': 'nacional',
                                'sustituible': False,
                                'year': self.year
                            })
            
            # Deduplicar
            fechas_vistas = set()
            festivos_unicos = []
            for f in festivos:
                if f['fecha'] not in fechas_vistas:
                    fechas_vistas.add(f['fecha'])
                    festivos_unicos.append(f)
            
            return festivos_unicos
            
        except Exception as e:
            print(f"   ⚠️  Error en parse_texto_patrones: {e}")
            return []
    
    def _extraer_fecha_de_texto(self, texto: str) -> Optional[tuple]:
        """
        Extrae fecha de un texto en formato español.
        Retorna (fecha_iso, fecha_texto) o None
        """
        texto_lower = texto.lower()
        
        # Patrón: "1 de enero", "6 de enero", etc.
        patron = r'(\d{1,2})\s+de\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)'
        match = re.search(patron, texto_lower)
        
        if match:
            dia = int(match.group(1))
            mes_texto = match.group(2)
            fecha_texto = f"{dia} de {mes_texto}"
            
            # Convertir a fecha ISO
            meses = {
                'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
                'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
                'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
            }
            
            mes = meses.get(mes_texto)
            if mes:
                fecha_iso = f"{self.year}-{mes:02d}-{dia:02d}"
                return (fecha_iso, fecha_texto)
        
        return None
    
    def _parse_patrones_conocidos(self, content: str) -> List[Dict]:
        """
        Fallback: Patrones conocidos específicos
        Solo se usa si los otros métodos fallan
        """
        from scrapers.utils.pascua import calcular_jueves_santo, calcular_viernes_santo
        
        festivos = []
        
        # Lista de festivos nacionales conocidos (siempre son estos)
        festivos_conocidos = [
            (1, 'enero', 'Año Nuevo', False),
            (6, 'enero', 'Epifanía del Señor', True),
            (1, 'mayo', 'Fiesta del Trabajo', False),
            (15, 'agosto', 'Asunción de la Virgen', True),
            (12, 'octubre', 'Fiesta Nacional de España', False),
            (1, 'noviembre', 'Todos los Santos', True),
            (6, 'diciembre', 'Día de la Constitución Española', False),
            (8, 'diciembre', 'Inmaculada Concepción', True),
            (25, 'diciembre', 'Natividad del Señor', False),
        ]
        
        # Añadir festivos fijos
        for dia, mes_texto, descripcion, sustituible in festivos_conocidos:
            meses = {
                'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
                'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
                'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
            }
            mes = meses[mes_texto]
            fecha_iso = f"{self.year}-{mes:02d}-{dia:02d}"
            fecha_texto = f"{dia} de {mes_texto}"
            
            festivos.append({
                'fecha': fecha_iso,
                'fecha_texto': fecha_texto,
                'descripcion': descripcion,
                'tipo': 'nacional',
                'ambito': 'nacional',
                'sustituible': sustituible,
                'year': self.year
            })
        
        # Añadir Semana Santa (calculada matemáticamente)
        try:
            jueves_santo = calcular_jueves_santo(self.year)
            viernes_santo = calcular_viernes_santo(self.year)
            
            meses_es = {
                1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
                5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
                9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
            }
            
            festivos.append({
                'fecha': jueves_santo.isoformat(),
                'fecha_texto': f"{jueves_santo.day} de {meses_es[jueves_santo.month]}",
                'descripcion': 'Jueves Santo',
                'tipo': 'nacional',
                'ambito': 'nacional',
                'sustituible': True,
                'year': self.year
            })
            
            festivos.append({
                'fecha': viernes_santo.isoformat(),
                'fecha_texto': f"{viernes_santo.day} de {meses_es[viernes_santo.month]}",
                'descripcion': 'Viernes Santo',
                'tipo': 'nacional',
                'ambito': 'nacional',
                'sustituible': False,
                'year': self.year
            })
        except Exception as e:
            print(f"⚠️  Error calculando Semana Santa: {e}")
        
        return festivos
    
    def _get_con_reintentos(self, url: str, intentos: int = 3, timeout: int = 45):
        """
        GET con reintentos ante timeouts y errores de conexión o 5xx: algunos
        boletines (p. ej. el BOC de Canarias) fallan de forma intermitente y,
        sin reintentar, el calendario sale incompleto sin avisar.
        """
        import time

        for intento in range(1, intentos + 1):
            try:
                response = requests.get(url, timeout=timeout)
                if response.status_code < 500:
                    response.raise_for_status()
                    return response
                error = requests.HTTPError(f"{response.status_code} en {url}")
            except (requests.Timeout, requests.ConnectionError) as e:
                error = e
            if intento < intentos:
                print(f"   ⚠️  Intento {intento}/{intentos} fallido ({error}); reintentando...")
                time.sleep(2 * intento)
        raise error

    def fetch_content(self, url: str) -> str:
        """Descarga el contenido desde una URL (soporta PDFs)"""
        try:
            print(f"📥 Descargando: {url}")
            response = self._get_con_reintentos(url)
            
            # Verificar si es un PDF
            content_type = response.headers.get('Content-Type', '').lower()
            is_pdf = 'application/pdf' in content_type or url.lower().endswith('.pdf')
            
            if is_pdf:
                # Extraer texto del PDF usando pdfplumber
                import pdfplumber
                import io
                
                pdf_file = io.BytesIO(response.content)
                text_content = []
                
                with pdfplumber.open(pdf_file) as pdf:
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            text_content.append(text)
                
                content = '\n'.join(text_content)
                print(f"✅ PDF extraído ({len(content)} caracteres)")
            else:
                # Contenido HTML/texto normal. Si la cabecera no trae charset,
                # requests asume ISO-8859-1 aunque la página declare UTF-8 en su
                # <meta> (pasa con el BOC de Canarias) y salen textos como "SeÃ±ora".
                if 'charset' not in content_type:
                    meta = re.search(rb'<meta[^>]+charset=["\']?([\w-]+)', response.content[:4096], re.I)
                    if meta:
                        response.encoding = meta.group(1).decode('ascii')
                content = response.text
                print(f"✅ Descarga completada ({len(content)} caracteres)")
            
            return content
            
        except Exception as e:
            print(f"❌ Error descargando {url}: {e}")
            return ""
    
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