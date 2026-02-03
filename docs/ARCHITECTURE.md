# Documentacion Tecnica

## Arquitectura del Sistema

### Jerarquia de Clases

```
BaseScraper (base_scraper.py)
|
+-- BOEScraper (boe_scraper.py)
|   +-- Festivos nacionales + tabla CCAA
|
+-- CCAAAutonomicosScraper (base_scraper.py)
|   +-- CanariasAutonomicosScraper
|   +-- MadridAutonomicosScraper
|   +-- NavarraAutonomicosScraper
|
+-- CCAALocalesScraper (base_scraper.py)
|   +-- 17 scrapers (uno por CCAA)
|
+-- BasePDFParser (parsers/base_pdf_parser.py)
    +-- BOPAPDFParser (Asturias)
    +-- BOCPDFParser (Cantabria)

ScraperFactory (core/scraper_factory.py)
|-- Imports dinamicos via importlib
|-- Unica fuente de verdad: ccaa_registry.yaml
```

### ScraperFactory

Punto central de instanciacion que reemplaza las cadenas if/elif:

```python
from scrapers.core.scraper_factory import ScraperFactory

factory = ScraperFactory()

# Locales: cualquiera de las 17 CCAA
scraper = factory.create_locales_scraper('aragon', year=2026, municipio='Zaragoza')
festivos = scraper.scrape()

# Autonomicos: solo madrid, canarias, navarra (el resto usa tabla BOE)
scraper_auto = factory.create_autonomicos_scraper('canarias', year=2026, municipio='Arrecife')
```

**Derivacion de nombres de clase:**
- Regla general: `ccaa_code.split('_')` -> title cada parte -> join -> `+ 'LocalesScraper'`
- Override para irregulares: `castilla_mancha` -> `CastillaLaManchaLocalesScraper`

### BaseScraper

Clase base abstracta que define la interfaz comun:

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
        """Flujo principal: obtener URL -> descargar -> parsear"""
        url = self.get_source_url()
        content = self.download_content(url)
        festivos = self.parse_festivos(content)
        return festivos
```

### Flujo de Ejecucion

```
+---------------------------------------------+
|  scrape_municipio.py                        |
|  (Scraper Unificado)                        |
+----------------+----------------------------+
                 |
                 +-> ScraperFactory
                 |   +-- create_locales_scraper()
                 |   +-- create_autonomicos_scraper()
                 |
                 +-> BOEScraper
                 |   +-> parse_tabla_ccaa(ccaa)
                 |       +-> Festivos nacionales + autonomicos por CCAA
                 |
                 +-> AutonomicosScraper (solo 3 CCAA)
                 |   +-> Canarias / Madrid / Navarra
                 |
                 +-> LocalesScraper (17 CCAA)
                 |   +-> Instanciado dinamicamente por factory
                 |
                 +-> Eliminar duplicados
                 |   +-> Prioridad: local > autonomico > nacional
                 |
                 +-> Resultado: ~14 festivos por municipio
```

## Configuracion Centralizada

### ccaa_registry.yaml

Unica fuente de verdad para toda la metadata de las 17 CCAA:

```yaml
ccaa:
  aragon:
    name: "Aragon"
    municipios_count: 565
    provincias: ["Huesca", "Teruel", "Zaragoza"]
    boletin: "BOA"
    formato: "csv"
    auto_discovery: true
    urls:
      locales:
        2026: "https://opendata.aragon.es/..."
    municipios_file: "config/aragon_municipios.json"
```

### API Python (`config/config_manager.py`)

```python
from config.config_manager import CCAaRegistry

registry = CCAaRegistry()

# Listar CCAA soportadas
ccaa_list = registry.list_ccaa()  # ['canarias', 'madrid', ..., 'extremadura']

# Obtener info de una CCAA
info = registry.get_ccaa_info('madrid')

# Obtener URL
url = registry.get_url('canarias', 2026, 'locales')
```

## Sistema de Cache (4 Niveles)

### Estrategia de resolucion de datos

```python
# Nivel 0: Festivos pre-generados en JSON (cache-first)
# Usado por: Aragon, Castilla y Leon, Castilla-La Mancha, Extremadura
if os.path.exists(f'data/festivos_{ccaa}_{year}.json'):
    return cargar_json()

# Nivel 1: KNOWN_URLS (hardcoded en ccaa_registry.yaml)
url = registry.get_url(ccaa, year, 'locales')

# Nivel 2: Cache de URLs (descubierto previamente)
if year in self.cache:
    return self.cache[year]

# Nivel 3: Auto-discovery (busqueda automatica)
url = auto_discover(year)
self._save_to_cache(url)
```

### CCAA con estrategia cache-first

Varias CCAA usan un fichero JSON pre-generado como fuente primaria de festivos locales:

| CCAA | Fichero | Formato origen |
|------|---------|----------------|
| Aragon | `data/festivos_aragon_2026.json` | CSV OpenData |
| Castilla y Leon | `data/festivos_castilla_leon_2026.json` | CSV JCyL |
| Castilla-La Mancha | `data/festivos_castilla_mancha_2026.json` | PDF DOCM |
| Extremadura | `data/festivos_extremadura_2026.json` | PDF DOE |

### Estructura del Cache de URLs

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

## Auto-Discovery

### Canarias (BOC)

**Estrategia:** Web scraping de indices del BOC

```python
def auto_discover_canarias(year: int) -> Dict[str, str]:
    """
    Busca publicaciones oficiales en el BOC

    Autonomicos:
    - Rango: BOC 50-250 del anyo anterior
    - Keywords: ['decreto', 'fiestas', 'laborales', str(year)]

    Locales:
    - Rango: BOC 130-280 del anyo anterior
    - Keywords: ['orden', 'fiestas', 'locales', str(year)]
    """
```

### BOE (Nacionales)

**Estrategia:** API del BOE

```python
def auto_discover_boe(year: int) -> str:
    """
    Usa la API de busqueda del BOE

    Busqueda:
    - Texto: "fiestas laborales {year}"
    - Fecha: septiembre-noviembre del anyo anterior
    - Seccion: Administracion del Estado
    """
```

### Madrid (BOCM)

**Estado:** Cache manual (BOCM tiene anti-scraping)

## Parsers Especificos

### Canarias: Filtrado por Isla

**Problema:** Canarias tiene 8 festivos autonomicos (1 regional + 7 insulares) pero cada municipio solo tiene 2.

**Solucion:** Mapeo municipio -> isla (`config/canarias_municipios_islas.json`)

### Pais Vasco: API OpenData JSON

**Fuente:** `opendata.euskadi.eus` — API JSON estructurada con todos los municipios y festivos.

### Cataluña: XML Akoma Ntoso

**Fuente:** DOGC — formato XML juridico (Akoma Ntoso) parseado con BeautifulSoup.

### Navarra: HTML + Fechas Relativas

**Particularidad:** 5.6% de fechas son relativas (ordinales, liturgicas, santoral).
Solo 1 festivo local por municipio (no 2).

### Aragon / Castilla y Leon: CSV OpenData

**Fuente:** Portales de datos abiertos con CSV estructurado.

### Madrid: Normalizacion de Nombres

**Problema:** El BOCM normaliza nombres eliminando espacios y tildes.

```
Usuario escribe: "Alcala de Henares"
PDF contiene:    "Alcaladehenares"
```

**Solucion:** Normalizacion en ambos lados con `unicodedata.normalize('NFKD', ...)`.

## Eliminacion de Duplicados

### Estrategia

Cuando un festivo aparece en multiples fuentes, mantener el de mayor prioridad:

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

## Formato de Datos

### Estructura de Festivo

```python
{
    'fecha': '2025-05-30',           # ISO 8601
    'fecha_texto': '30 de mayo',     # Texto original
    'descripcion': 'Dia de Canarias',
    'tipo': 'autonomico',            # nacional | autonomico | local
    'ambito': 'autonomico',          # nacional | autonomico | insular | municipal
    'municipio': None,               # Solo para locales
    'sustituible': False,
    'year': 2025
}
```

## Testing

### Ejecutar Tests

```bash
# Todos los tests
python3 -m pytest tests/ -v

# Solo tests unitarios
python3 -m pytest tests/unit/ -v

# Con cobertura
python3 -m pytest tests/ --cov=scrapers --cov=config --cov-report=term-missing
```

### Tests Actuales

- 90 tests passing, 3 skipped
- Cobertura: config (100%), parsers (100%), factory (100%), web (100%)
- CI/CD: GitHub Actions

### Casos de Prueba Criticos

```bash
# Test unificado por CCAA
python3 scrape_municipio.py "Madrid" madrid 2026          # 14 festivos
python3 scrape_municipio.py "Arrecife" canarias 2026      # 14 festivos
python3 scrape_municipio.py "Zaragoza" aragon 2026        # 14 festivos
python3 scrape_municipio.py "Albacete" castilla_mancha 2026  # 14 festivos
python3 scrape_municipio.py "Badajoz" extremadura 2026    # 14 festivos
```

## Performance

### Tiempos de Ejecucion

| Operacion | Primera vez | Cache |
|-----------|-------------|-------|
| BOE nacionales | 2-3 seg | 2-3 seg |
| CCAA con cache-first | N/A | < 1 seg |
| Canarias auto | 5-10 seg | 1-2 seg |
| Canarias locales | 60-120 seg | 1-2 seg |
| Madrid | N/A | 1-2 seg |
| **Unificado tipico** | **5-10 seg** | **3-5 seg** |

## Frontend Web (Flask)

La web profesional (`web/`) usa Flask desplegado en Railway:

```
web/
├── app.py                     # Flask app (17 CCAA vía CCAaRegistry)
├── utils/
│   └── calendar_generator.py  # Generador HTML para PDF
├── templates/
│   ├── landing.html           # Selector CCAA + municipio
│   └── calendario.html        # Vista festivos + descarga PDF/CSV/Excel
├── static/images/
└── temp_sessions/             # Sesiones temporales (JSON)
```

**URL:** [calendariolaboral.biplaza.es](https://calendariolaboral.biplaza.es)
**Deploy:** Railway con `gunicorn web.app:app`
**Build:** nixpacks.toml (cairo, pango, fontconfig para WeasyPrint)

## Proximos Pasos

1. **Generalizar sustituciones**: Leer de publicaciones oficiales (actualmente hardcoded)
2. **Optimizacion fuzzy matching**: O(1) con indices
3. **API REST**: Endpoint `/festivos/{ccaa}/{municipio}/{year}`
