"""
Generador de Calendarios Laborales
Aplicación Streamlit para generar calendarios personalizados
"""

import streamlit as st
import subprocess
import json
import os
from pathlib import Path

# Añadir al path para imports
import sys
sys.path.insert(0, str(Path(__file__).parent))

from utils.calendar_generator import CalendarGenerator


# Configuración de la página
st.set_page_config(
    page_title="Generador de Calendarios Laborales",
    page_icon="📅",
    layout="wide"
)


def cargar_municipios(ccaa: str):
    """
    Carga municipios dinámicamente desde archivo de configuración
    
    Args:
        ccaa: Nombre de la CCAA (canarias, madrid, valencia, etc)
    
    Returns:
        Lista ordenada de municipios
    """
    import json
    import os
    
    # Buscar archivo de configuración (dos posibles nombres)
    archivos_posibles = [
        f'config/{ccaa}_municipios.json',
        f'config/{ccaa}_municipios_islas.json'  # Para Canarias
    ]
    
    for archivo in archivos_posibles:
        if os.path.exists(archivo):
            with open(archivo, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Si es estructura de islas (Canarias)
            if isinstance(data, dict) and all(isinstance(v, list) for v in data.values()):
                municipios = set()
                for lista_municipios in data.values():
                    municipios.update(lista_municipios)
                return sorted(list(municipios))
            
            # Si es lista directa
            elif isinstance(data, list):
                return sorted(data)
            
            # Si es dict con clave "municipios"
            elif isinstance(data, dict) and 'municipios' in data:
                return sorted(data['municipios'])
    
    # Fallback si no existe archivo
    fallbacks = {
        'canarias': ['Arrecife', 'Santa Cruz de Tenerife', 'Las Palmas de Gran Canaria'],
        'madrid': ['Madrid', 'Alcalá de Henares', 'Alcobendas']
    }
    
    return fallbacks.get(ccaa, [f'Municipio de {ccaa.title()}'])


# Cargar municipios para CCAA disponibles
CCAA_DISPONIBLES = ['canarias', 'madrid']  # ← Fácil añadir más

MUNICIPIOS = {
    ccaa: cargar_municipios(ccaa)
    for ccaa in CCAA_DISPONIBLES
}


def ejecutar_scraper(municipio: str, ccaa: str, year: int) -> dict:
    """
    Ejecuta el scraper y devuelve los festivos
    """
    try:
        # Ejecutar scraper
        result = subprocess.run(
            ['python', 'scrape_municipio.py', municipio, ccaa, str(year)],
            capture_output=True,
            text=True,
            timeout=180  # 3 minutos máximo
        )
        
        # Leer JSON generado
        municipio_slug = municipio.lower().replace(' ', '_')
        json_path = f'data/{ccaa}_{municipio_slug}_completo_{year}.json'
        
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            st.error(f"No se encontró el archivo: {json_path}")
            return None
            
    except subprocess.TimeoutExpired:
        st.error("⏱️ Tiempo de espera agotado. Intenta de nuevo.")
        return None
    except Exception as e:
        st.error(f"❌ Error ejecutando scraper: {e}")
        return None


def main():
    # Header
    st.title("📅 Generador de Calendarios Laborales")
    st.markdown("Genera calendarios personalizados con festivos oficiales de España")
    
    st.markdown("---")
    
    # Sidebar - Configuración
    with st.sidebar:
        st.header("⚙️ Configuración")
        
        # Selección de CCAA
        ccaa = st.selectbox(
            "Comunidad Autónoma",
            options=['canarias', 'madrid'],
            format_func=lambda x: x.title()
        )
        
        # Selección de municipio
        municipio = st.selectbox(
            "Municipio",
            options=MUNICIPIOS[ccaa]
        )
        
        # Selección de año
        year = st.number_input(
            "Año",
            min_value=2025,
            max_value=2030,
            value=2025,
            step=1
        )
        
        st.markdown("---")
        
        # Personalización (opcional)
        st.subheader("🎨 Personalización")
        
        empresa = st.text_input(
            "Nombre empresa (opcional)",
            placeholder="Ej: Biplaza Asesoría"
        )
        
        st.markdown("---")
        
        # Botón generar
        generar = st.button("🎨 Generar Calendario", type="primary", use_container_width=True)
    
    # Área principal
    if generar:
        with st.spinner(f"⏳ Generando calendario para {municipio}, {ccaa.title()} {year}..."):
            
            # Ejecutar scraper
            data = ejecutar_scraper(municipio, ccaa, year)
            
            if data:
                st.success(f"✅ Calendario generado: {data['total_festivos']} festivos")
                
                # Generar HTML del calendario
                generator = CalendarGenerator(
                    year=year,
                    festivos=data['festivos'],
                    municipio=municipio,
                    ccaa=ccaa,
                    empresa=empresa
                )
                
                html = generator.generate_html()
                
                # Tabs para visualizar
                tab1, tab2 = st.tabs(["📅 Preview", "📊 Datos"])
                
                with tab1:
                    # Mostrar preview del calendario
                    st.components.v1.html(html, height=1400, scrolling=True)
                    
                    # Botones de descarga
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.download_button(
                            label="📥 Descargar HTML",
                            data=html,
                            file_name=f"calendario_{ccaa}_{municipio.lower().replace(' ', '_')}_{year}.html",
                            mime="text/html",
                            use_container_width=True
                        )
                    
                    with col2:
                        st.markdown(
                            "🖨️ **Imprimir:** Abre el HTML descargado y usa Ctrl+P (⌘+P en Mac)",
                            help="El navegador te permitirá guardar como PDF"
                        )
                
                with tab2:
                    # Mostrar tabla de festivos
                    st.subheader("📋 Listado de festivos")
                    
                    import pandas as pd
                    df = pd.DataFrame(data['festivos'])
                    df = df[['fecha', 'descripcion', 'tipo']]
                    df.columns = ['Fecha', 'Descripción', 'Tipo']
                    
                    st.dataframe(df, use_container_width=True, height=400)
                    
                    # Resumen por tipo
                    st.subheader("📊 Resumen por tipo")
                    resumen = df['Tipo'].value_counts()
                    st.bar_chart(resumen)
            else:
                st.error("❌ No se pudo generar el calendario. Revisa los logs.")
    
    else:
        # Instrucciones iniciales
        st.info("👈 Configura los parámetros en la barra lateral y haz clic en 'Generar Calendario'")
        
        # Características
        st.markdown("### ✨ Características")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **📅 Fuentes oficiales**
            - BOE (nacionales)
            - BOCM / BOC (autonómicos)
            - Festivos locales
            """)
        
        with col2:
            st.markdown("""
            **🎨 Personalizable**
            - Nombre de empresa
            - Diseño profesional
            - Listo para imprimir
            """)
        
        with col3:
            st.markdown("""
            **📥 Múltiples formatos**
            - HTML interactivo
            - Impresión a PDF
            - Datos en tabla
            """)
        
        # Ejemplo
        st.markdown("---")
        st.markdown("### 📸 Ejemplo")
        st.markdown("El calendario generado incluye:")
        st.markdown("- Vista de 12 meses en cuadrícula")
        st.markdown("- Festivos destacados en amarillo")
        st.markdown("- Tooltip al pasar el ratón sobre festivos")
        st.markdown("- Diseño responsive (móvil, tablet, desktop)")
        st.markdown("- Listo para imprimir")


if __name__ == "__main__":
    main()
