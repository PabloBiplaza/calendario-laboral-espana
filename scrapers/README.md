# Arquitectura de Scrapers - Calendario Laboral España

Este directorio contiene los scrapers para extraer festivos laborales de todas las Comunidades Autónomas de España.

## 📁 Estructura del Proyecto

```
scrapers/
├── ccaa/                      # Scrapers por Comunidad Autónoma
│   ├── andalucia/
│   ├── asturias/
│   ├── baleares/
│   ├── canarias/
│   ├── cantabria/
│   ├── cataluna/
│   ├── galicia/
│   ├── madrid/
│   ├── pais_vasco/
│   └── valencia/
├── core/                      # Clases base y lógica común
│   ├── base_scraper.py       # Scraper abstracto base
│   ├── boe_scraper.py        # Scraper del BOE (festivos nacionales)
│   └── parallel.py           # Ejecución paralela
├── parsers/                   # Parsers reutilizables (NUEVO ✨)
│   ├── base_pdf_parser.py    # Parser base para PDFs
│   └── __init__.py
├── discovery/                 # Auto-discovery de URLs
│   ├── boe_discovery.py      # Discovery genérico
│   └── ccaa/                 # Discovery específico por CCAA
└── utils/                     # Utilidades
    └── pascua.py             # Cálculo de Semana Santa
```

## 🏗️ Arquitectura por Capas

### Capa 1: Configuración Centralizada

**Archivo**: `config/ccaa_registry.yaml`

Contiene toda la metadata de las 10 CCAA implementadas:
- URLs de boletines oficiales
- Métodos de auto-discovery
- Paths a archivos de municipios
- Información de provincias y formato

**API**: `config/config_manager.py`

```python
from config.config_manager import registry

# Obtener URL de una CCAA
url = registry.get_url('canarias', 2026, 'locales')

# Obtener info completa
info = registry.get_ccaa_info('madrid')

# Listar CCAA con auto-discovery
ccaa_discovery = registry.list_ccaa_with_discovery()
```

### Capa 2: Scrapers Base

**BaseScraper** (`core/base_scraper.py`)
- Clase abstracta para todos los scrapers
- Manejo de errores común
- Logging estandarizado
- Métodos helper compartidos

**BOEScraper** (`core/boe_scraper.py`)
- Scraper especializado para festivos nacionales del BOE
- Usado por todas las CCAA

### Capa 3: Parsers Reutilizables (✨ Refactor)

**BasePDFParser** (`parsers/base_pdf_parser.py`)

Parser base abstracto para PDFs de boletines oficiales. Elimina duplicación entre CCAA.

**Características**:
- ✅ Caching automático de resultados
- ✅ Búsqueda flexible de municipios (exacta, case-insensitive, parcial)
- ✅ Métodos helper compartidos
- ✅ Template Method Pattern

**Ejemplo de uso**:

```python
from scrapers.parsers.base_pdf_parser import BasePDFParser

class MiPDFParser(BasePDFParser):
    """Parser personalizado para mi CCAA"""

    def _parse_text(self, text: str) -> Dict[str, List[Dict]]:
        # Implementar lógica específica del formato de tu CCAA
        festivos_por_municipio = {}
        # ... tu lógica aquí ...
        return festivos_por_municipio

    def _normalizar_municipio(self, nombre: str) -> Optional[str]:
        # Implementar reglas de normalización específicas
        if len(nombre) < 3:
            return None
        return nombre.upper()
```

**CCAA que ya usan BasePDFParser**:
- ✅ Asturias (BOPAPDFParser) - 218 líneas
- ✅ Cantabria (BOCPDFParser) - 193 líneas

### Capa 4: Scrapers por CCAA

Cada CCAA tiene su propio directorio con:

**`locales.py`** - Scraper de festivos locales
```python
class CCAaLocalesScraper(BaseScraper):
    def scrape(self) -> Dict[str, List[Dict]]:
        # Obtener PDF/HTML del boletín oficial
        # Parsear festivos locales
        # Devolver dict {municipio: [festivos]}
        pass
```

**`autonomicos.py`** (opcional) - Scraper de festivos autonómicos
- Solo si la CCAA publica festivos autonómicos separados del BOE
- Ejemplos: Canarias, Madrid

**`pdf_parser.py`** (opcional) - Parser específico de PDF
- Solo si usa PDFs con formato complejo
- Debe heredar de `BasePDFParser`

## 🆕 Cómo Añadir una Nueva CCAA

### Paso 1: Actualizar `config/ccaa_registry.yaml`

```yaml
ccaa:
  mi_ccaa:
    name: "Mi Comunidad"
    municipios_count: 100
    provincias:
      - "Provincia 1"
      - "Provincia 2"
    boletin: "BO-CCAA"
    boletin_url: "https://boletin.ejemplo.es/"
    formato: "pdf"  # o "html", "xml", "json"
    auto_discovery: true
    discovery_method: "mi_metodo"
    urls:
      locales:
        2026: "https://ejemplo.es/festivos-2026.pdf"
    municipios_file: "config/mi_ccaa_municipios.json"
```

### Paso 2: Crear archivo de municipios

`config/mi_ccaa_municipios.json`:
```json
{
  "MUNICIPIO 1": "id_o_metadata",
  "MUNICIPIO 2": "id_o_metadata"
}
```

### Paso 3: Crear scraper de locales

`scrapers/ccaa/mi_ccaa/locales.py`:

```python
from scrapers.core.base_scraper import BaseScraper
from typing import List, Dict

class MiCCAaLocalesScraper(BaseScraper):
    """Scraper de festivos locales para Mi CCAA"""

    def __init__(self, year: int = 2026):
        super().__init__(year, ccaa='mi_ccaa')

    def scrape(self) -> Dict[str, List[Dict]]:
        """
        Extrae festivos locales del boletín oficial.

        Returns:
            Dict con {MUNICIPIO: [festivos]}
        """
        # 1. Obtener URL del registro
        from config.config_manager import registry
        url = registry.get_url('mi_ccaa', self.year, 'locales')

        # 2. Si es PDF, usar parser
        if url.endswith('.pdf'):
            from .pdf_parser import MiCCAaPDFParser
            parser = MiCCAaPDFParser(url, self.year)
            return parser.parse()

        # 3. Si es HTML, parsear directamente
        response = self.session.get(url)
        # ... parsear HTML ...

        return festivos_por_municipio
```

### Paso 4 (Opcional): Crear parser de PDF

Si tu CCAA usa PDFs, crea `scrapers/ccaa/mi_ccaa/pdf_parser.py`:

```python
from scrapers.parsers.base_pdf_parser import BasePDFParser
from typing import Dict, List, Optional

class MiCCAaPDFParser(BasePDFParser):
    """Parser para PDFs del boletín de Mi CCAA"""

    def _parse_text(self, text: str) -> Dict[str, List[Dict]]:
        """Implementar parsing específico del formato"""
        lines = text.split('\n')
        festivos_por_municipio = {}

        for line in lines:
            # Tu lógica de parsing aquí
            # Usar helpers de la clase base:
            # - self._crear_festivo(dia, mes, descripcion)
            # - self._es_fecha_valida(dia, mes_nombre)
            # - self._debe_ignorar_linea(line, palabras_clave)
            pass

        return festivos_por_municipio

    def _normalizar_municipio(self, nombre: str) -> Optional[str]:
        """Normalizar nombre de municipio"""
        if len(nombre) < 3:
            return None

        # Ignorar líneas con palabras clave
        if self._debe_ignorar_linea(nombre, ['boletín', 'oficial']):
            return None

        return nombre.upper()
```

### Paso 5: Crear `__init__.py`

`scrapers/ccaa/mi_ccaa/__init__.py`:
```python
from .locales import MiCCAaLocalesScraper

__all__ = ['MiCCAaLocalesScraper']
```

### Paso 6: Tests

Crear tests en `tests/unit/test_mi_ccaa.py` y `tests/integration/`:

```python
def test_mi_ccaa_extrae_festivos(mi_ccaa_pdf_2026):
    """Test que Mi CCAA extrae festivos correctamente"""
    from scrapers.ccaa.mi_ccaa.pdf_parser import MiCCAaPDFParser

    parser = MiCCAaPDFParser(mi_ccaa_pdf_2026, 2026)
    festivos = parser.get_festivos_municipio("MUNICIPIO TEST")

    assert len(festivos) == 2
```

## 🧪 Testing

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
│   └── test_pdf_parsers.py
└── integration/           # Tests de integración
    └── test_scrapers_smoke.py
```

### Ejecutar Tests

```bash
# Todos los tests
pytest tests/ -v

# Solo tests unitarios
pytest tests/unit/ -v

# Con cobertura
pytest tests/ --cov=scrapers --cov=config --cov-report=term-missing
```

## 📊 Estado Actual

### CCAA Implementadas (10)

| CCAA | Municipios | Formato | Auto-Discovery | Parser PDF |
|------|-----------|---------|----------------|------------|
| Canarias | 88 | YAML | ✅ | ❌ |
| Madrid | 181 | PDF | ✅ | ❌ (tabla HTML) |
| Andalucía | 746 | HTML | ✅ | ❌ |
| Valencia | 542 | PDF | ✅ | ❌ |
| Baleares | 67 | HTML | ❌ | ❌ |
| Cataluña | 950 | XML | ❌ | ❌ |
| Galicia | 313 | HTML | ✅ | ❌ |
| País Vasco | 251 | JSON | ✅ | ❌ |
| Asturias | 78 | PDF | ✅ | ✅ BasePDFParser |
| Cantabria | 102 | PDF | ✅ | ✅ BasePDFParser |

**Total**: 3,318 municipios teóricos

### Cobertura de Tests

- ✅ 45 tests passing
- ✅ 0 regresiones
- ✅ Cobertura: config (100%), parsers (100%)

## 🔧 Utilidades

### Validación de Configuración

```bash
# Validar que el YAML está correcto
python config/migrate_to_yaml.py --validate
```

### Ejecución Paralela

```python
from scrapers.core.parallel import ejecutar_scrapers_paralelo

# Ejecutar múltiples scrapers en paralelo
resultados = ejecutar_scrapers_paralelo(['canarias', 'madrid', 'andalucia'])
```

## 📚 Referencias

- **BOE**: https://www.boe.es/
- **Calendario laboral oficial**: https://www.mites.gob.es/
- **Documentación interna**: `/docs/`

## 🤝 Contribuir

1. Añadir tests para nuevos scrapers
2. Documentar formatos específicos de cada CCAA
3. Reutilizar `BasePDFParser` cuando sea posible
4. Actualizar `ccaa_registry.yaml` con nueva metadata

---

**Última actualización**: 2026-01-18
**Versión**: 1.0.0-refactor
