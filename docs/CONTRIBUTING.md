# 🤝 Guía de Contribución

## Cómo Añadir una Nueva CCAA

Esta guía explica paso a paso cómo añadir soporte para una nueva comunidad autónoma.

### Ejemplo: Añadir Valencia

---

## PASO 1: Investigar Fuentes Oficiales

### 1.1 Encontrar el Boletín Oficial

Buscar el boletín oficial de la CCAA:
- **Valencia**: DOGV (Diari Oficial de la Generalitat Valenciana)
- **Cataluña**: DOGC (Diari Oficial de la Generalitat de Catalunya)
- **Andalucía**: BOJA (Boletín Oficial de la Junta de Andalucía)

### 1.2 Encontrar Publicaciones Recientes

Web search: `site:dogv.gva.es fiestas laborales 2025`

Identificar:
- **Tipo de documento**: Decreto, Orden, Resolución
- **Fecha de publicación**: ¿Cuándo se publica? (septiembre, octubre, diciembre)
- **URL pattern**: ¿Cómo están estructuradas las URLs?

**Ejemplo Valencia:**
```
Autonómicos: Decreto del Consell (septiembre)
URL: https://www.dogv.gva.es/datos/2024/09/25/pdf/2024_8765.pdf

Locales: Resolución (diciembre)
URL: https://www.dogv.gva.es/datos/2024/12/15/pdf/2024_10234.pdf
```

---

## PASO 2: Crear Estructura de Directorios

```bash
mkdir -p scrapers/ccaa/valencia
touch scrapers/ccaa/valencia/__init__.py
touch scrapers/ccaa/valencia/autonomicos.py
touch scrapers/ccaa/valencia/locales.py
```

---

## PASO 3: Implementar Scraper de Autonómicos

### 3.1 Template Básico

**scrapers/ccaa/valencia/autonomicos.py:**

```python
"""
Scraper de festivos autonómicos de Valencia desde el DOGV
"""

from typing import Dict, List, Optional
from scrapers.core.base_scraper import CCAAAutonomicosScraper
import re
from datetime import datetime


class ValenciaAutonomicosScraper(CCAAAutonomicosScraper):
    """
    Extrae festivos autonómicos de la Comunidad Valenciana
    desde el DOGV (Diari Oficial de la Generalitat Valenciana)
    """
    
    # URLs conocidas (añadir según se vayan publicando)
    KNOWN_URLS = {
        2025: "https://www.dogv.gva.es/datos/2024/09/25/pdf/2024_8765.pdf",
        # Añadir más años según se publiquen
    }
    
    # Archivo de cache
    CACHE_FILE = 'config/valencia_urls_cache.json'
    
    def __init__(self, year: int):
        super().__init__(year=year, ccaa='valencia', tipo='autonomicos')
        self._load_cache()
    
    def get_source_url(self) -> str:
        """
        Obtiene la URL de la fuente oficial
        
        Niveles:
        1. KNOWN_URLS (hardcoded)
        2. Cache (descubierto previamente)
        3. Auto-discovery (si existe)
        """
        
        # Nivel 1: KNOWN_URLS
        if self.year in self.KNOWN_URLS:
            print(f"✅ URL oficial (KNOWN_URLS) para {self.year}: {self.KNOWN_URLS[self.year]}")
            return self.KNOWN_URLS[self.year]
        
        # Nivel 2: Cache
        if self.year in self.cache.get('autonomicos', {}):
            url = self.cache['autonomicos'][self.year]
            print(f"📦 URL en cache para {self.year}: {url}")
            return url
        
        # Nivel 3: Auto-discovery (implementar si es posible)
        # TODO: Implementar auto_discover_valencia()
        
        raise ValueError(
            f"❌ No se pudo encontrar URL para festivos autonómicos Valencia {self.year}\n"
            f"   Añade manualmente la URL en KNOWN_URLS o cache."
        )
    
    def parse_festivos(self, content: str) -> List[Dict]:
        """
        Parsea festivos desde el contenido del DOGV
        
        IMPORTANTE: Adaptar según el formato real del DOGV
        """
        print(f"🔍 Parseando festivos autonómicos de Valencia...")
        
        festivos = []
        
        # TODO: Implementar parsing específico del DOGV
        # Ejemplo genérico:
        
        # Buscar fechas en formato "dd de mes de yyyy"
        patron_fecha = r'(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})'
        matches = re.finditer(patron_fecha, content, re.IGNORECASE)
        
        meses = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
            'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
            'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
        }
        
        for match in matches:
            dia = int(match.group(1))
            mes_texto = match.group(2).lower()
            year = int(match.group(3))
            
            if year == self.year and mes_texto in meses:
                mes = meses[mes_texto]
                fecha_iso = f"{year:04d}-{mes:02d}-{dia:02d}"
                
                # Extraer descripción (adaptar según formato real)
                # ...
                
                festivos.append({
                    'fecha': fecha_iso,
                    'descripcion': 'Festivo autonómico',  # TODO: Extraer descripción real
                    'tipo': 'autonomico',
                    'ambito': 'autonomico',
                    'sustituible': False,
                    'year': self.year
                })
        
        print(f"   ✅ Extraídos {len(festivos)} festivos autonómicos")
        return festivos
    
    def _load_cache(self):
        """Carga URLs del cache"""
        import os
        import json
        
        self.cache = {'autonomicos': {}, 'locales': {}}
        
        if os.path.exists(self.CACHE_FILE):
            try:
                with open(self.CACHE_FILE, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
                print(f"📦 Cache cargado: {len(self.cache.get('autonomicos', {}))} URLs autonómicas")
            except Exception as e:
                print(f"⚠️  Error cargando cache: {e}")


# Test individual
if __name__ == "__main__":
    import sys
    
    year = int(sys.argv[1]) if len(sys.argv) > 1 else 2025
    
    print("=" * 80)
    print(f"🧪 TEST: Valencia Autonómicos Scraper - Festivos {year}")
    print("=" * 80)
    
    scraper = ValenciaAutonomicosScraper(year=year)
    festivos = scraper.scrape()
    
    # Mostrar resumen
    scraper.print_summary(festivos)
    
    # Guardar
    scraper.save_to_json(festivos, f'data/valencia_autonomicos_{year}.json')
    scraper.save_to_excel(festivos, f'data/valencia_autonomicos_{year}.xlsx')
```

### 3.2 Adaptar el Parser

**CRÍTICO:** El método `parse_festivos()` debe adaptarse al formato específico del boletín oficial.

**Pasos:**
1. Descargar un PDF/HTML de ejemplo
2. Analizar la estructura
3. Crear expresiones regulares específicas
4. Probar con varios años

**Ejemplo de formatos comunes:**

```python
# Formato 1: Lista numerada
"""
1. 1 de enero - Año Nuevo
2. 6 de enero - Epifanía del Señor
...
"""
patron = r'(\d+)\.\s+(\d{1,2})\s+de\s+(\w+)\s+-\s+([^\n]+)'

# Formato 2: Tabla
"""
| Fecha       | Festividad          |
|-------------|---------------------|
| 1 de enero  | Año Nuevo          |
"""
# Usar Beautiful Soup para parsear tablas HTML

# Formato 3: Párrafos
"""
Artículo 1. Se establecen como festivos:
El día 1 de enero (Año Nuevo), el 6 de enero (Epifanía)...
"""
patron = r'(\d{1,2})\s+de\s+(\w+)\s+\(([^)]+)\)'
```

---

## PASO 4: Implementar Scraper de Locales

Similar al de autonómicos, pero filtrando por municipio:

**scrapers/ccaa/valencia/locales.py:**

```python
class ValenciaLocalesScraper(CCAALocalesScraper):
    def __init__(self, municipio: str, year: int):
        super().__init__(year=year, ccaa='valencia', municipio=municipio, tipo='locales')
        self._load_cache()
    
    def parse_festivos(self, content: str) -> List[Dict]:
        """
        Parsea festivos locales
        
        Formato típico:
        — Valencia: 9 de octubre y 19 de marzo
        — Alicante: 24 de junio y 29 de junio
        """
        
        festivos = []
        
        # Buscar líneas con municipio
        patron = r'—\s*([^:]+):\s*([^.\n]+)'
        matches = re.finditer(patron, content)
        
        for match in matches:
            nombre_municipio = match.group(1).strip()
            fechas_texto = match.group(2).strip()
            
            # Filtrar por municipio
            if self.municipio.lower() not in nombre_municipio.lower():
                continue
            
            # Extraer fechas del texto
            # ...
            
        return festivos
```

---

## PASO 5: Crear Cache

**config/valencia_urls_cache.json:**

```json
{
  "autonomicos": {
    "2025": "https://www.dogv.gva.es/datos/2024/09/25/pdf/2024_8765.pdf"
  },
  "locales": {
    "2025": "https://www.dogv.gva.es/datos/2024/12/15/pdf/2024_10234.pdf"
  }
}
```

---

## PASO 6: Integrar en Scraper Unificado

**scrape_municipio.py:**

```python
# Añadir en la función scrape_festivos_completos()

elif ccaa.lower() == 'valencia':
    # Autonómicos
    from scrapers.ccaa.valencia.autonomicos import ValenciaAutonomicosScraper
    scraper_auto = ValenciaAutonomicosScraper(year=year)
    festivos_autonomicos = scraper_auto.scrape()
    
    # Locales
    from scrapers.ccaa.valencia.locales import ValenciaLocalesScraper
    scraper_local = ValenciaLocalesScraper(municipio=municipio, year=year)
    festivos_locales = scraper_local.scrape()
```

---

## PASO 7: Testing

### 7.1 Test Individual Autonómicos

```bash
python -m scrapers.ccaa.valencia.autonomicos 2025
```

**Verificar:**
- ✅ Descarga correctamente
- ✅ Parsea festivos
- ✅ Número correcto de festivos (típicamente 10-12)

### 7.2 Test Individual Locales

```bash
python -m scrapers.ccaa.valencia.locales "Valencia" 2025
```

**Verificar:**
- ✅ Encuentra el municipio
- ✅ Extrae 2 festivos locales

### 7.3 Test Unificado

```bash
python scrape_municipio.py "Valencia" valencia 2025
```

**Verificar:**
- ✅ Total: 14 festivos (11-12 únicos tras eliminar duplicados)
- ✅ Sin duplicados
- ✅ JSON y Excel generados

---

## PASO 8: Documentación

Actualizar README.md:

```markdown
## ✅ Implementado

- **Valencia**: Sistema completo
  - Festivos autonómicos
  - Festivos locales (540 municipios)
  - Años disponibles: 2025
```

---

## PASO 9: Auto-Discovery (Opcional)

Si el boletín oficial tiene búsqueda web, implementar:

**scrapers/discovery/ccaa/valencia_discovery.py:**

```python
def auto_discover_valencia(year: int) -> Dict[str, str]:
    """
    Busca automáticamente publicaciones en el DOGV
    """
    
    # Estrategia 1: Web search
    query = f"site:dogv.gva.es fiestas laborales {year}"
    
    # Estrategia 2: Scraping de índices
    # ...
    
    # Estrategia 3: API si existe
    # ...
```

---

## PASO 10: Pull Request

### 10.1 Commit

```bash
git add .
git commit -m "feat: añadir soporte para Valencia

- Scraper de festivos autonómicos
- Scraper de festivos locales (540 municipios)
- Cache para 2025
- Tests pasando
- Documentación actualizada"
```

### 10.2 PR Description

```markdown
## Añadir soporte para Valencia

### ✅ Implementado
- Festivos autonómicos desde DOGV
- Festivos locales (540 municipios)
- Parser adaptado al formato del DOGV
- Cache inicial: 2025

### 🧪 Tests
- [x] Autonómicos: 10 festivos extraídos
- [x] Locales Valencia: 2 festivos extraídos
- [x] Unificado: 14 festivos totales
- [x] Sin duplicados

### 📝 Formato del DOGV
- Autonómicos: Decreto del Consell (septiembre)
- Locales: Resolución (diciembre)
- Parser: Expresiones regulares adaptadas

### ⏳ Pendiente
- Auto-discovery (DOGV tiene protección anti-scraping)
```

---

## Checklist de Nueva CCAA

- [ ] Investigar fuente oficial
- [ ] Identificar patrón de URLs
- [ ] Crear estructura de directorios
- [ ] Implementar scraper autonómicos
- [ ] Implementar scraper locales
- [ ] Adaptar parsers al formato específico
- [ ] Crear archivo de cache
- [ ] Integrar en scraper unificado
- [ ] Tests individuales pasando
- [ ] Test unificado pasando
- [ ] Documentación actualizada
- [ ] (Opcional) Implementar auto-discovery
- [ ] Commit y PR

---

## Recursos Útiles

### Boletines Oficiales de CCAA

| CCAA | Boletín | URL |
|------|---------|-----|
| Andalucía | BOJA | https://www.juntadeandalucia.es/boja |
| Aragón | BOA | https://www.boa.aragon.es |
| Asturias | BOPA | https://sede.asturias.es/bopa |
| Baleares | BOIB | https://www.caib.es/boib |
| Canarias | BOC | https://www.gobiernodecanarias.org/boc |
| Cantabria | BOC | https://boc.cantabria.es |
| Castilla y León | BOCYL | https://bocyl.jcyl.es |
| Castilla-La Mancha | DOCM | https://docm.jccm.es |
| Cataluña | DOGC | https://dogc.gencat.cat |
| Extremadura | DOE | https://doe.juntaex.es |
| Galicia | DOG | https://www.xunta.gal/diario-oficial-galicia |
| Madrid | BOCM | https://www.bocm.es |
| Murcia | BORM | https://www.borm.es |
| Navarra | BON | https://bon.navarra.es |
| País Vasco | BOPV | https://www.euskadi.eus/bopv2 |
| La Rioja | BOR | https://web.larioja.org/bor |
| Valencia | DOGV | https://www.dogv.gva.es |

### Herramientas de Desarrollo

```bash
# Ver contenido de PDF
pdftotext documento.pdf - | less

# Extraer texto limpio
python -c "import pdfplumber; print(pdfplumber.open('doc.pdf').pages[0].extract_text())"

# Test regex
python -c "import re; print(re.findall(r'tu_patron', 'texto_prueba'))"

# Ver encoding
file -I documento.txt
```

### Patrones Comunes

```python
# Fechas español
r'(\d{1,2})\s+de\s+(enero|febrero|...|diciembre)'

# Municipios
r'—\s*([^:]+):\s*([^.\n]+)'

# Descripciones
r'([A-ZÁÉÍÓÚÑ][a-záéíóúñ\s]+)'

# Normalizar texto
import unicodedata
texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')
```

---

## Preguntas Frecuentes

### ¿Qué hacer si el PDF no se puede parsear?

1. Probar con `pdfplumber` en lugar de `PyPDF2`
2. Usar OCR si es imagen: `pytesseract`
3. Convertir PDF → HTML: herramientas online

### ¿Cómo manejar formatos inconsistentes?

Implementar múltiples patrones y probar en orden:

```python
for patron in [patron1, patron2, patron3]:
    matches = re.finditer(patron, content)
    if matches:
        return parse_matches(matches)
```

### ¿Qué hacer si hay actualizaciones del boletín?

El mismo boletín puede tener correcciones:

```python
# Buscar "modificación", "corrección"
# Aplicar cambios sobre datos anteriores
```

---

¡Gracias por contribuir! 🎉
