"""
Script unificador de festivos
Combina festivos nacionales, autonómicos y locales para un municipio específico
"""

import json
import pandas as pd
from datetime import datetime
import sys

class CalendarioLaboral:
    """
    Clase para consultar el calendario laboral completo de un municipio
    """
    
    def __init__(self, year=2026):
        self.year = year
        self.festivos_nacionales = []
        self.festivos_canarias = []
        self.cargar_datos()
    
    def cargar_datos(self):
        """Carga los datos de festivos desde los archivos JSON"""
        try:
            # Cargar festivos nacionales
            with open(f'data/nacionales_{self.year}.json', 'r', encoding='utf-8') as f:
                self.festivos_nacionales = json.load(f)
            print(f"✅ Cargados {len(self.festivos_nacionales)} festivos nacionales")
        except FileNotFoundError:
            print(f"⚠️  No se encontró archivo de festivos nacionales para {self.year}")
        
        try:
            # Cargar festivos locales de Canarias
            with open(f'data/canarias_{self.year}.json', 'r', encoding='utf-8') as f:
                self.festivos_canarias = json.load(f)
            print(f"✅ Cargados {len(self.festivos_canarias)} festivos locales de Canarias")
        except FileNotFoundError:
            print(f"⚠️  No se encontró archivo de festivos de Canarias para {self.year}")
    
    def listar_municipios(self):
        """Lista todos los municipios disponibles en Canarias"""
        municipios = sorted(set([f['municipio'] for f in self.festivos_canarias]))
        return municipios
    
    def buscar_municipio(self, termino_busqueda):
        """
        Busca municipios que coincidan con el término de búsqueda
        """
        termino = termino_busqueda.upper()
        municipios = self.listar_municipios()
        coincidencias = [m for m in municipios if termino in m]
        return coincidencias
    
    def obtener_festivos_municipio(self, municipio):
        """
        Obtiene todos los festivos aplicables a un municipio específico
        """
        municipio = municipio.upper()
        
        # Verificar que el municipio existe
        if municipio not in self.listar_municipios():
            print(f"❌ Municipio '{municipio}' no encontrado")
            coincidencias = self.buscar_municipio(municipio)
            if coincidencias:
                print(f"   ¿Quisiste decir? {', '.join(coincidencias[:5])}")
            return None
        
        # Combinar festivos
        festivos_totales = []
        
        # 1. Festivos nacionales
        festivos_totales.extend(self.festivos_nacionales)
        
        # 2. Festivos locales del municipio
        festivos_locales = [f for f in self.festivos_canarias if f['municipio'] == municipio]
        festivos_totales.extend(festivos_locales)
        
        # Ordenar por fecha
        festivos_totales.sort(key=lambda x: x['fecha'])
        
        return festivos_totales
    
    def generar_informe(self, municipio):
        """
        Genera un informe completo del calendario laboral de un municipio
        """
        festivos = self.obtener_festivos_municipio(municipio)
        
        if not festivos:
            return None
        
        # Obtener datos del municipio
        festivo_local = next((f for f in self.festivos_canarias if f['municipio'] == municipio), None)
        provincia = festivo_local['provincia'] if festivo_local else 'Desconocida'
        
        # Separar por tipo
        nacionales = [f for f in festivos if f['tipo'] == 'nacional']
        locales = [f for f in festivos if f['tipo'] == 'local']
        
        informe = {
            'municipio': municipio,
            'provincia': provincia,
            'ccaa': 'Canarias',
            'year': self.year,
            'total_festivos': len(festivos),
            'festivos_nacionales': len(nacionales),
            'festivos_locales': len(locales),
            'festivos': festivos
        }
        
        return informe
    
    def imprimir_informe(self, municipio):
        """
        Imprime un informe formateado del calendario laboral
        """
        informe = self.generar_informe(municipio)
        
        if not informe:
            return
        
        print("\n" + "="*80)
        print(f"📅 CALENDARIO LABORAL {self.year}")
        print("="*80)
        print(f"📍 Municipio: {informe['municipio']}")
        print(f"📍 Provincia: {informe['provincia']}")
        print(f"📍 Comunidad Autónoma: {informe['ccaa']}")
        print("-"*80)
        print(f"📊 RESUMEN:")
        print(f"   • Festivos nacionales: {informe['festivos_nacionales']}")
        print(f"   • Festivos locales: {informe['festivos_locales']}")
        print(f"   • TOTAL: {informe['total_festivos']} días festivos")
        print("-"*80)
        print(f"📆 LISTADO DE FESTIVOS:")
        print()
        
        for festivo in informe['festivos']:
            # Formatear fecha
            fecha_obj = datetime.strptime(festivo['fecha'], '%Y-%m-%d')
            dia_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'][fecha_obj.weekday()]
            
            tipo_emoji = "🇪🇸" if festivo['tipo'] == 'nacional' else "🏠"
            tipo_texto = "Nacional" if festivo['tipo'] == 'nacional' else "Local"
            
            print(f"   {tipo_emoji} {festivo['fecha']} ({dia_semana:9s}) - {festivo['descripcion']}")
            print(f"      └─ Tipo: {tipo_texto}")
        
        print("="*80)
        print()
    
    def exportar_excel(self, municipio, filepath):
        """
        Exporta el calendario de un municipio a Excel
        """
        informe = self.generar_informe(municipio)
        
        if not informe:
            return False
        
        # Crear DataFrame
        df = pd.DataFrame(informe['festivos'])
        
        # Añadir día de la semana
        df['dia_semana'] = pd.to_datetime(df['fecha']).dt.day_name()
        
        # Reordenar columnas
        columnas = ['fecha', 'dia_semana', 'descripcion', 'tipo', 'ambito']
        df = df[[col for col in columnas if col in df.columns]]
        
        # Guardar
        df.to_excel(filepath, index=False, sheet_name=municipio[:30])
        print(f"💾 Calendario guardado en: {filepath}")
        
        return True
    
    def exportar_todos_municipios(self, filepath):
        """
        Exporta un Excel con todos los municipios de Canarias
        """
        writer = pd.ExcelWriter(filepath, engine='openpyxl')
        
        municipios = self.listar_municipios()
        print(f"📊 Generando calendario para {len(municipios)} municipios...")
        
        for municipio in municipios:
            festivos = self.obtener_festivos_municipio(municipio)
            if festivos:
                df = pd.DataFrame(festivos)
                df['dia_semana'] = pd.to_datetime(df['fecha']).dt.day_name()
                
                # Nombre de hoja limitado a 31 caracteres
                nombre_hoja = municipio[:31]
                df.to_excel(writer, sheet_name=nombre_hoja, index=False)
        
        writer.close()
        print(f"💾 Calendario de todos los municipios guardado en: {filepath}")


def main():
    """Función principal para uso por línea de comandos"""
    calendario = CalendarioLaboral(year=2026)
    
    if len(sys.argv) > 1:
        # Municipio especificado por línea de comandos
        municipio = ' '.join(sys.argv[1:])
        calendario.imprimir_informe(municipio)
    else:
        # Modo interactivo
        print("\n🏝️  CALENDARIO LABORAL CANARIAS 2026")
        print("-" * 50)
        
        while True:
            print("\nOpciones:")
            print("  1. Consultar municipio específico")
            print("  2. Listar todos los municipios")
            print("  3. Exportar municipio a Excel")
            print("  4. Exportar todos los municipios a Excel")
            print("  5. Salir")
            
            opcion = input("\nElige una opción (1-5): ").strip()
            
            if opcion == '1':
                municipio = input("Nombre del municipio: ").strip()
                calendario.imprimir_informe(municipio)
            
            elif opcion == '2':
                print("\n📋 MUNICIPIOS DISPONIBLES:")
                municipios = calendario.listar_municipios()
                for i, muni in enumerate(municipios, 1):
                    print(f"   {i:2d}. {muni}")
            
            elif opcion == '3':
                municipio = input("Nombre del municipio: ").strip()
                municipio_clean = municipio.upper().replace(' ', '_')
                filepath = f'data/calendario_{municipio_clean}_2026.xlsx'
                if calendario.exportar_excel(municipio, filepath):
                    print("✅ Exportación completada")
            
            elif opcion == '4':
                filepath = 'data/calendario_canarias_todos_2026.xlsx'
                calendario.exportar_todos_municipios(filepath)
                print("✅ Exportación completada")
            
            elif opcion == '5':
                print("👋 ¡Hasta pronto!")
                break
            
            else:
                print("❌ Opción no válida")


if __name__ == "__main__":
    main()