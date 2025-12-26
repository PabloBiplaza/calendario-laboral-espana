# 🏗️ Documentación Técnica

## Arquitectura del Sistema

### Jerarquía de Clases

```
BaseScraper (base_scraper.py)
│
├── BOEScraper (boe_scraper.py)
│   └── Festivos nacionales
│
├── CCAAAutonomicosScraper (base_scraper.py)
│   ├── CanariasAutonomicosScraper
│   └── MadridAutonomicosScraper
│
└── CCAALocalesScraper (base_scraper.py)
    ├── CanariasLocalesScraper
    └── MadridLocalesScraper
```

### BaseScraper

Clase base abstracta que define la interfaz común:

```python
class BaseScraper(ABC):
    @abstractmethod
    def get_source_url(self) -> str:
        """Obtiene la URL de la fuente oficial"""
        pass
    
    @abstractmethod
    def parse_festivos(self, content: str) -> List[Dict]:
        """Parsea el contenido y extrae festivos"""
        pass
    
    def scrape(self) -> List[Dict]:
        """Flujo principal: obtener URL → descargar → parsear"""
        url = self.get_source_url()
        content = self.download_content(url)
        festivos = self.parse_festivos(content)
        return festivos
```

### Flujo de Ejecución

```
┌─────────────────────────────────────────────┐
│  scrape_municipio.py                        │
│  (Scraper Unificado)                        │
└──────────────┬──────────────────────────────┘
               │
               ├─► BOEScraper
               │   └─► 11 festivos nacionales
               │
               ├─► CanariasAutonomicosScraper
               │   ├─► get_source_url()
               │   │   ├─► 1. KNOWN_URLS
               │   │   ├─► 2. Cache
               │   │   └─► 3. Auto-discovery
               │   └─► parse_festivos()
               │       └─► Filtrar por isla
               │
               ├─► CanariasLocalesScraper
               │   └─► Filtrar por municipio
               │
               ├─► Eliminar duplicados
               │   └─► Prioridad: local > auto > nacional
               │
               └─► Aplicar sustituciones
                   └─► Guardar JSON + Excel
```

## Sistema de Cache

### Arquitectura de 3 Niveles

```python
def get_source_url(self) -> str:
    # NIVEL 1: KNOWN_URLS (hardcoded)
    if self.year in self.KNOWN_URLS:
        return self.KNOWN_URLS[self.year]
    
    # NIVEL 2: Cache (descubierto previamente)
    if self.year in self.cache:
        return self.cache[self.year]
    
    # NIVEL 3: Auto-discovery (búsqueda)
    url = auto_discover(self.year)
    self._save_to_cache(url)
    return url
```

### Estructura del Cache

**config/canarias_urls_cache.json:**
```json
{
  "autonomicos": {
    "2025": "https://www.gobiernodecanarias.org/boc/2024/187/3013.html",
    "2026": "https://www.gobiernodecanarias.org/boc/2025/088/1659.html"
  },
  "locales": {
    "2025": "https://www.gobiernodecanarias.org/boc/2024/238/3948.html",
    "2026": "https://www.gobiernodecanarias.org/boc/2025/165/3029.html"
  }
}
```

### Actualización del Cache

El cache se actualiza automáticamente cuando:
1. Auto-discovery encuentra una nueva URL
2. Se llama a `_save_to_cache(tipo, year, url)`

## Auto-Discovery

### Canarias (BOC)

**Estrategia:** Web scraping de índices del BOC

```python
def auto_discover_canarias(year: int) -> Dict[str, str]:
    """
    Busca publicaciones oficiales en el BOC
    
    Autonómicos:
    - Rango: BOC 50-250 del año anterior
    - Keywords: ['decreto', 'fiestas', 'laborales', str(year)]
    
    Locales:
    - Rango: BOC 130-280 del año anterior
    - Keywords: ['orden', 'fiestas', 'locales', str(year)]
    """
    
    # Buscar en índices BOC
    for numero_boc in range(50, 250):
        url_indice = f"https://www.gobiernodecanarias.org/boc/{year-1}/{numero_boc:03d}/"
        
        # Verificar si contiene keywords
        if all(kw in contenido for kw in keywords):
            # Extraer URL y convertir PDF → HTML
            return convertir_pdf_a_html_url(url_pdf)
```

**Conversión PDF → HTML:**

El BOC devuelve URLs a PDFs desde sede electrónica, pero los parsers necesitan HTML:

```python
# IN:  https://sede.gobiernodecanarias.org/boc/boc-a-2024-187-3013.pdf
# OUT: https://www.gobiernodecanarias.org/boc/2024/187/3013.html

def convertir_pdf_a_html_url(url_pdf: str) -> str:
    match = re.search(r'boc-a-(\d{4})-(\d+)-(\d+)\.pdf', url_pdf)
    year, numero, anuncio = match.groups()
    return f"https://www.gobiernodecanarias.org/boc/{year}/{numero}/{anuncio}.html"
```

### BOE (Nacionales)

**Estrategia:** API del BOE

```python
def auto_discover_boe(year: int) -> str:
    """
    Usa la API de búsqueda del BOE
    
    Búsqueda:
    - Texto: "fiestas laborales {year}"
    - Fecha: septiembre-noviembre del año anterior
    - Sección: Administración del Estado
    """
    
    url_api = "https://www.boe.es/diario_boe/xml.php"
    params = {
        'q': f'fiestas laborales {year}',
        'fecha_desde': f'{year-1}0901',
        'fecha_hasta': f'{year-1}1130'
    }
```

### Madrid (BOCM)

**Estado:** Pendiente - el BOCM tiene anti-scraping

**Estrategias probadas:**
1. ❌ Scraping directo de índices
2. ❌ Formulario de búsqueda avanzada
3. ❌ Prueba de URLs directas

**Solución temporal:** Cache manual

## Parsers Específicos

### Canarias: Filtrado por Isla

**Problema:** Canarias tiene 8 festivos autonómicos (1 regional + 7 insulares) pero cada municipio solo tiene 2.

**Solución:** Mapeo municipio → isla

```python
# config/canarias_municipios_islas.json
{
  "TENERIFE": ["Santa Cruz de Tenerife", "La Laguna", ...],
  "GRAN CANARIA": ["Las Palmas de Gran Canaria", "Telde", ...],
  "LANZAROTE": ["Arrecife", "Teguise", ...],
  ...
}

# scrapers/ccaa/canarias/autonomicos.py
def parse_festivos(self, content: str) -> List[Dict]:
    # Extraer todos los festivos
    festivos = extraer_festivos_html(content)  # 8 festivos
    
    # Filtrar por isla
    if self.municipio:
        isla = self.get_isla_municipio(self.municipio)
        festivos = [f for f in festivos 
                   if f['ambito'] == 'autonomico'  # Día Canarias
                   or isla in f['municipios_aplicables']]  # Insular
    
    return festivos  # 2 festivos
```

### Madrid: Normalización de Nombres

**Problema:** El BOCM normaliza nombres eliminando espacios y tildes.

```
Usuario escribe: "Alcalá de Henares"
PDF contiene:    "Alcaládehenares"
```

**Solución:** Normalización en ambos lados

```python
def _normalizar_municipio(self, nombre: str) -> str:
    # Eliminar tildes
    nombre = unicodedata.normalize('NFKD', nombre)
    nombre = nombre.encode('ASCII', 'ignore').decode('ASCII')
    # Eliminar espacios para comparación
    return nombre.replace(' ', '')

# Comparación
if municipio_busqueda.lower() == municipio_encontrado.lower():
    # Match!
```

## Eliminación de Duplicados

### Estrategia

Cuando un festivo aparece en múltiples fuentes, mantener el de mayor prioridad:

```python
prioridad = {'local': 3, 'autonomico': 2, 'nacional': 1}

festivos_unicos = {}
for festivo in festivos_todos:
    fecha = festivo['fecha']
    tipo = festivo['tipo']
    
    if fecha not in festivos_unicos:
        festivos_unicos[fecha] = festivo
    else:
        tipo_existente = festivos_unicos[fecha]['tipo']
        if prioridad[tipo] > prioridad[tipo_existente]:
            festivos_unicos[fecha] = festivo
```

### Ejemplo Real

```
BOE:  1 enero - "Año Nuevo" (nacional)
BOCM: 1 enero - "Año Nuevo" (autonómico)
→ Resultado: 1 enero - "Año Nuevo" (autonómico)

Razón: La fuente autonómica tiene prioridad sobre nacional
```

## Sustituciones

### Canarias 2025

**Regla:** Si un festivo cae en domingo, se sustituye:

```python
# 12 octubre 2025 (domingo) → sustituido por 30 mayo
festivos_sustituidos = {'2025-10-12'}

# Eliminar festivos sustituidos
festivos = [f for f in festivos if f['fecha'] not in festivos_sustituidos]
```

**Problema actual:** Lógica hardcoded por año

**Mejora futura:** Detectar automáticamente sustituciones leyendo publicaciones oficiales

## Formato de Datos

### Estructura de Festivo

```python
{
    'fecha': '2025-05-30',           # ISO 8601
    'fecha_texto': '30 de mayo',     # Texto original
    'descripcion': 'Día de Canarias',
    'tipo': 'autonomico',            # nacional | autonomico | local
    'ambito': 'autonomico',          # nacional | autonomico | insular | municipal
    'municipio': None,               # Solo para locales
    'municipios_aplicables': ['TENERIFE'],  # Solo para insulares
    'sustituible': False,
    'year': 2025
}
```

### Validación

Todos los festivos pasan validación:

```python
def validar_festivo(festivo: Dict) -> bool:
    assert 'fecha' in festivo
    assert 'descripcion' in festivo
    assert festivo['tipo'] in ['nacional', 'autonomico', 'local']
    assert len(festivo['fecha']) == 10  # YYYY-MM-DD
    return True
```

## Manejo de Errores

### Jerarquía de Fallbacks

```python
try:
    # Nivel 1: KNOWN_URLS
    url = self.KNOWN_URLS[year]
except KeyError:
    try:
        # Nivel 2: Cache
        url = self.cache[year]
    except KeyError:
        try:
            # Nivel 3: Auto-discovery
            url = auto_discover(year)
        except Exception:
            # Nivel 4: Error informativo
            raise ValueError(f"No se pudo encontrar URL para {year}")
```

### Logging

Todos los scrapers tienen logging detallado:

```
🔍 Iniciando scraping: CANARIAS - AUTONOMICOS - 2025
✅ URL oficial (KNOWN_URLS) para 2025
📥 Descargando: https://...
✅ Descarga completada (20516 caracteres)
🔍 Parseando festivos...
   ✅ Encontrado Día de Canarias
   🔍 Matches insulares encontrados: 7
   🏝️  Filtrando festivos para isla: Lanzarote
   ✅ Festivos tras filtrar por isla: 2
✅ Scraping completado: 2 festivos extraídos
```

## Performance

### Tiempos de Ejecución

| Operación | Primera vez | Cache |
|-----------|-------------|-------|
| BOE nacionales | 2-3 seg | 2-3 seg |
| Canarias auto | 5-10 seg | 1-2 seg |
| Canarias locales | 60-120 seg | 1-2 seg |
| Madrid | N/A | 1-2 seg |
| **Unificado completo** | **70-135 seg** | **5-8 seg** |

### Optimizaciones

1. **Cache agresivo**: URLs descubiertas se reutilizan
2. **Rate limiting**: 0.1 seg entre requests en auto-discovery
3. **Requests con timeout**: Evitar bloqueos
4. **Parsing eficiente**: Regex optimizados

## Testing

### Tests Manuales

```bash
# Test BOE
python -m scrapers.core.boe_scraper 2025

# Test Canarias autonómicos
python -m scrapers.ccaa.canarias.autonomicos 2025

# Test Canarias locales
python -m scrapers.ccaa.canarias.locales "Arrecife" 2025

# Test Madrid
python -m scrapers.ccaa.madrid.locales "Madrid" 2026

# Test unificado
python scrape_municipio.py "Arrecife" canarias 2025
```

### Casos de Prueba Críticos

1. **Canarias con isla correcta**
   ```bash
   python scrape_municipio.py "Arrecife" canarias 2025
   # Debe incluir: Día Canarias + Virgen de los Volcanes (Lanzarote)
   ```

2. **Madrid con normalización**
   ```bash
   python scrape_municipio.py "Alcalá de Henares" madrid 2026
   # Debe encontrar el municipio a pesar de espacios/tildes
   ```

3. **Eliminación de duplicados**
   ```bash
   python scrape_municipio.py "Madrid" madrid 2026
   # No debe haber duplicados en las 14 fechas
   ```

4. **Auto-discovery**
   ```bash
   # Vaciar cache primero
   echo '{"autonomicos": {}, "locales": {}}' > config/canarias_urls_cache.json
   
   # Ejecutar
   python scrape_municipio.py "Arrecife" canarias 2025
   # Debe encontrar URLs automáticamente
   ```

## Próximos Pasos

1. **Auto-discovery Madrid**: Solucionar anti-scraping del BOCM
2. **Resto de CCAA**: Implementar 17 comunidades restantes
3. **Tests unitarios**: pytest con fixtures
4. **Generalizar sustituciones**: Leer de publicaciones oficiales
5. **API REST**: Endpoint `/festivos/{ccaa}/{municipio}/{year}`
6. **Frontend**: Interfaz web para consultas
