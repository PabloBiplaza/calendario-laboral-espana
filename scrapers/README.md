# Arquitectura de Scrapers - Calendario Laboral España

Este directorio contiene los scrapers para extraer festivos laborales de todas las Comunidades Autonomas de España.

## Estructura del Proyecto

```
scrapers/
├── ccaa/                      # Scrapers por Comunidad Autonoma (17)
│   ├── andalucia/
│   ├── aragon/
│   ├── asturias/
│   ├── baleares/
│   ├── canarias/
│   ├── cantabria/
│   ├── castilla_leon/
│   ├── castilla_mancha/
│   ├── cataluna/
│   ├── extremadura/
│   ├── galicia/
│   ├── madrid/
│   ├── murcia/
│   ├── navarra/
│   ├── pais_vasco/
│   ├── rioja/
│   └── valencia/
├── core/                      # Clases base y logica comun
│   ├── base_scraper.py       # Scraper abstracto base
│   ├── boe_scraper.py        # Scraper del BOE (festivos nacionales)
│   ├── scraper_factory.py    # Factory con imports dinamicos
│   └── parallel.py           # Ejecucion paralela
├── parsers/                   # Parsers reutilizables
│   ├── base_pdf_parser.py    # Parser base para PDFs
│   └── __init__.py
├── discovery/                 # Auto-discovery de URLs
│   ├── boe_discovery.py      # Discovery generico
│   └── ccaa/                 # Discovery especifico por CCAA
└── utils/                     # Utilidades
    └── pascua.py             # Calculo de Semana Santa
```

## Arquitectura por Capas

### Capa 1: Configuracion Centralizada

**Archivo**: `config/ccaa_registry.yaml`

Contiene toda la metadata de las 17 CCAA implementadas:
- URLs de boletines oficiales
- Metodos de auto-discovery
- Paths a archivos de municipios
- Informacion de provincias y formato

**API**: `config/config_manager.py`

```python
from config.config_manager import CCAaRegistry

registry = CCAaRegistry()

# Listar CCAA soportadas
registry.list_ccaa()  # ['canarias', 'madrid', ..., 'extremadura']

# Obtener URL de una CCAA
url = registry.get_url('canarias', 2026, 'locales')

# Obtener info completa
info = registry.get_ccaa_info('madrid')
```

### Capa 2: ScraperFactory

**Archivo**: `core/scraper_factory.py`

Punto central de instanciacion. Reemplaza cadenas if/elif usando `importlib`:

```python
from scrapers.core.scraper_factory import ScraperFactory

factory = ScraperFactory()

# Locales: cualquiera de las 17 CCAA
scraper = factory.create_locales_scraper('aragon', year=2026, municipio='Zaragoza')

# Autonomicos: solo 3 CCAA tienen scraper dedicado
scraper = factory.create_autonomicos_scraper('canarias', year=2026, municipio='Arrecife')
# Devuelve None para CCAA sin scraper dedicado (usan tabla BOE)
```

**Derivacion de nombres de clase:**
- Regla: `ccaa_code.split('_')` -> title -> join -> `+ 'LocalesScraper'`
- Override: `castilla_mancha` -> `CastillaLaManchaLocalesScraper`

### Capa 3: Scrapers Base

**BaseScraper** (`core/base_scraper.py`)
- Clase abstracta para todos los scrapers
- Manejo de errores comun
- Logging estandarizado

**BOEScraper** (`core/boe_scraper.py`)
- Festivos nacionales + tabla de festivos por CCAA
- `parse_tabla_ccaa(ccaa)` devuelve festivos autonomicos de la tabla del BOE

### Capa 4: Parsers Reutilizables

**BasePDFParser** (`parsers/base_pdf_parser.py`)

Parser base abstracto para PDFs de boletines oficiales:
- Caching automatico de resultados
- Busqueda flexible de municipios (exacta, case-insensitive, parcial)
- Template Method Pattern

CCAA que usan BasePDFParser: Asturias, Cantabria

### Capa 5: Scrapers por CCAA

Cada CCAA tiene su propio directorio con:

- **`locales.py`** — Scraper de festivos locales (obligatorio)
- **`autonomicos.py`** — Scraper de festivos autonomicos (solo canarias, madrid, navarra)
- **`pdf_parser.py`** — Parser especifico de PDF (opcional)
- **`__init__.py`** — Exporta la clase del scraper

## Como Añadir una Nueva CCAA

1. Actualizar `config/ccaa_registry.yaml` con metadata y URLs
2. Crear `scrapers/ccaa/mi_ccaa/locales.py` con clase `MiCcaaLocalesScraper`
3. Crear `scrapers/ccaa/mi_ccaa/__init__.py` exportando la clase
4. El ScraperFactory lo detecta automaticamente (no hay que tocar `scrape_municipio.py`)
5. Verificar: `python3 scrape_municipio.py "Municipio" mi_ccaa 2026`

Ver `docs/CONTRIBUTING.md` para la guia completa.

## Testing

### Estructura de Tests

```
tests/
├── fixtures/              # PDFs/HTMLs de ejemplo
│   ├── asturias/
│   ├── cantabria/
│   └── ...
├── unit/                  # Tests unitarios
│   ├── test_base_pdf_parser.py
│   ├── test_config_manager.py
│   ├── test_pdf_parsers.py
│   └── test_scraper_factory.py
└── integration/           # Tests de integracion
    └── test_scrapers_smoke.py
```

### Ejecutar Tests

```bash
# Todos los tests
python3 -m pytest tests/ -v

# Solo tests unitarios
python3 -m pytest tests/unit/ -v

# Con cobertura
python3 -m pytest tests/ --cov=scrapers --cov=config --cov-report=term-missing
```

## Estado Actual

### CCAA Implementadas (17/17)

| CCAA | Municipios | Formato | Auto-Discovery | Parser PDF |
|------|-----------|---------|----------------|------------|
| Andalucia | 746 | HTML/PDF | Si | No |
| Aragon | 565 | CSV | Si (CKAN) | No |
| Asturias | 78 | PDF | Si | Si (BasePDFParser) |
| Baleares | 67 | HTML | No | No |
| Canarias | 88 | HTML | Si (BOC) | No |
| Cantabria | 102 | PDF | Si | Si (BasePDFParser) |
| Castilla y Leon | 2248 | CSV | Si (predecible) | No |
| Castilla-La Mancha | 919 | PDF | Si | No (cache-first) |
| Cataluña | 950 | XML | No | No |
| Extremadura | 388 | PDF | Si | No (cache-first) |
| Galicia | 313 | HTML | Si (RDF) | No |
| Madrid | 181 | PDF | Si (BOCM) | No |
| Murcia | 45 | PDF | Si | No |
| Navarra | 694 | HTML | Si (BON) | No |
| Pais Vasco | 251 | JSON | Si (OpenData) | No |
| La Rioja | 164 | PDF | Si (BOR) | No |
| Valencia | 542 | PDF | Si (DOGV) | No |

**Total**: 8.351 municipios teoricos

### Cobertura de Tests

- 90 tests passing, 3 skipped
- Cobertura: config (100%), parsers (100%), factory (100%), web (100%)
- CI/CD: GitHub Actions

## Utilidades

### Validacion de Configuracion

```bash
# Validar que el YAML esta correcto
python3 config/migrate_to_yaml.py --validate
```

## Referencias

- **BOE**: https://www.boe.es/
- **Calendario laboral oficial**: https://www.mites.gob.es/
- **Documentacion interna**: `/docs/`

## Contribuir

1. Añadir tests para nuevos scrapers
2. Documentar formatos especificos de cada CCAA
3. Reutilizar `BasePDFParser` cuando sea posible
4. Actualizar `ccaa_registry.yaml` con nueva metadata
5. Ver `docs/CONTRIBUTING.md` para guia detallada

---

**Ultima actualizacion**: 2026-02-03
**Version**: 2.1.0
