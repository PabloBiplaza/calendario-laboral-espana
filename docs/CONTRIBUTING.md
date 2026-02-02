# Guia de Contribucion

## Como Añadir una Nueva CCAA

Esta guia explica paso a paso como añadir soporte para una nueva comunidad autonoma.

> **Nota:** Las 17 CCAA ya estan implementadas. Esta guia sirve como referencia para mantenimiento y para añadir nuevos años.

---

## PASO 1: Investigar Fuentes Oficiales

### 1.1 Encontrar el Boletin Oficial

Buscar el boletin oficial de la CCAA. Consultar la tabla en la seccion "Recursos Utiles" al final.

### 1.2 Encontrar Publicaciones Recientes

Web search: `site:boletin.ejemplo.es fiestas laborales 2027`

Identificar:
- **Tipo de documento**: Decreto, Orden, Resolucion
- **Fecha de publicacion**: Cuando se publica (septiembre, octubre, diciembre)
- **Formato**: PDF, HTML, XML, CSV, JSON
- **URL pattern**: Como estan estructuradas las URLs

---

## PASO 2: Actualizar `config/ccaa_registry.yaml`

Añadir la nueva URL en la seccion de la CCAA existente:

```yaml
ccaa:
  mi_ccaa:
    # ... metadata existente ...
    urls:
      locales:
        2027: "https://boletin.ejemplo.es/festivos-2027.pdf"  # <-- Nuevo
        2026: "https://boletin.ejemplo.es/festivos-2026.pdf"
```

Si es una CCAA nueva (caso hipotetico), añadir toda la metadata:

```yaml
ccaa:
  mi_ccaa:
    name: "Mi Comunidad"
    municipios_count: 100
    provincias:
      - "Provincia 1"
    boletin: "BO-CCAA"
    boletin_url: "https://boletin.ejemplo.es/"
    formato: "pdf"
    auto_discovery: true
    discovery_method: "mi_metodo"
    urls:
      locales:
        2027: "https://ejemplo.es/festivos-2027.pdf"
    municipios_file: "config/mi_ccaa_municipios.json"
```

---

## PASO 3: Crear Estructura de Directorios

```bash
mkdir -p scrapers/ccaa/mi_ccaa
touch scrapers/ccaa/mi_ccaa/__init__.py
touch scrapers/ccaa/mi_ccaa/locales.py
```

---

## PASO 4: Implementar Scraper de Locales

**scrapers/ccaa/mi_ccaa/locales.py:**

```python
"""Scraper de festivos locales de Mi CCAA"""

from scrapers.core.base_scraper import BaseScraper
from config.config_manager import CCAaRegistry
from typing import List, Dict


class MiCcaaLocalesScraper(BaseScraper):
    """Extrae festivos locales de Mi CCAA desde su boletin oficial"""

    def __init__(self, year: int = 2026, municipio: str = None):
        super().__init__(year=year, ccaa='mi_ccaa')
        self.municipio = municipio
        self._registry = CCAaRegistry()

    def scrape(self) -> List[Dict]:
        # 1. Obtener URL del registry
        url = self._registry.get_url('mi_ccaa', self.year, 'locales')

        # 2. Descargar y parsear
        # ... tu logica aqui ...

        # 3. Filtrar por municipio
        if self.municipio:
            festivos = [f for f in festivos if self._match_municipio(f)]

        return festivos
```

> **Importante:** La clase debe aceptar `year` y `municipio` como parametros en `__init__`, ya que el `ScraperFactory` los pasa al instanciar.

---

## PASO 5: Crear `__init__.py`

**scrapers/ccaa/mi_ccaa/__init__.py:**

```python
"""Scrapers para Mi CCAA"""

from .locales import MiCcaaLocalesScraper

__all__ = ['MiCcaaLocalesScraper']
```

> **Convencion de nombres:** El nombre de la clase se deriva automaticamente por el `ScraperFactory`:
> - `mi_ccaa` -> `MiCcaaLocalesScraper`
> - `pais_vasco` -> `PaisVascoLocalesScraper`
> - Excepcion: `castilla_mancha` -> `CastillaLaManchaLocalesScraper` (override en factory)

---

## PASO 6: Verificar integracion automatica

**No hace falta tocar `scrape_municipio.py` ni `app.py`.**

El `ScraperFactory` importa dinamicamente el scraper usando `importlib`:

```python
# El factory hace esto internamente:
module = importlib.import_module('scrapers.ccaa.mi_ccaa.locales')
scraper_class = getattr(module, 'MiCcaaLocalesScraper')
scraper = scraper_class(year=2026, municipio='Mi Municipio')
```

Verificar:

```bash
# Debe funcionar sin modificar nada mas
python3 scrape_municipio.py "Mi Municipio" mi_ccaa 2026
```

---

## PASO 7: Crear archivo de municipios (si es necesario)

**config/mi_ccaa_municipios.json:**

```json
{
  "MUNICIPIO 1": "metadata",
  "MUNICIPIO 2": "metadata"
}
```

---

## PASO 8: Testing

### 8.1 Test unificado

```bash
python3 scrape_municipio.py "Municipio" mi_ccaa 2026
```

**Verificar:**
- Total: 14 festivos (11-12 nacionales/autonomicos + 2 locales)
- Sin duplicados
- Tipo correcto (nacional/autonomico/local)

### 8.2 Tests unitarios

Crear `tests/unit/test_mi_ccaa.py`:

```python
def test_mi_ccaa_extrae_festivos():
    from scrapers.ccaa.mi_ccaa.locales import MiCcaaLocalesScraper
    scraper = MiCcaaLocalesScraper(year=2026, municipio='Municipio Test')
    festivos = scraper.scrape()
    assert len(festivos) == 2
```

### 8.3 Test de factory

```python
def test_factory_instancia_mi_ccaa():
    from scrapers.core.scraper_factory import ScraperFactory
    factory = ScraperFactory()
    scraper = factory.create_locales_scraper('mi_ccaa', 2026, 'Municipio')
    assert scraper is not None
```

### 8.4 Ejecutar suite completa

```bash
python3 -m pytest tests/ -v
```

---

## PASO 9: Autonomicos (Opcional)

La mayoria de CCAA obtienen los festivos autonomicos de la tabla del BOE (via `BOEScraper.parse_tabla_ccaa()`). Solo si la CCAA publica festivos autonomicos separados (como Canarias, Madrid o Navarra), crear:

**scrapers/ccaa/mi_ccaa/autonomicos.py:**

```python
class MiCcaaAutonomicosScraper(BaseScraper):
    # ...
```

Y añadir al `_AUTONOMICOS_CCAA` en `scrapers/core/scraper_factory.py`:

```python
_AUTONOMICOS_CCAA = {
    'madrid': 'MadridAutonomicosScraper',
    'canarias': 'CanariasAutonomicosScraper',
    'navarra': 'NavarraAutonomicosScraper',
    'mi_ccaa': 'MiCcaaAutonomicosScraper',  # <-- Nuevo
}
```

---

## PASO 10: Documentacion y Commit

1. Actualizar `config/ccaa_registry.yaml` (ya hecho en PASO 2)
2. Actualizar `CHANGELOG.md`
3. Commit:

```bash
git add scrapers/ccaa/mi_ccaa/ config/ tests/
git commit -m "feat: añadir soporte para Mi CCAA (#XX)

- Scraper de festivos locales
- N municipios soportados
- Tests unitarios
- Documentacion actualizada"
```

---

## Checklist de Nueva CCAA

- [ ] Investigar fuente oficial y formato
- [ ] Actualizar `ccaa_registry.yaml` con URLs y metadata
- [ ] Crear `scrapers/ccaa/mi_ccaa/locales.py`
- [ ] Crear `scrapers/ccaa/mi_ccaa/__init__.py`
- [ ] Verificar que ScraperFactory lo instancia correctamente
- [ ] Test: `python3 scrape_municipio.py "Municipio" mi_ccaa 2026` -> 14 festivos
- [ ] Tests unitarios pasando
- [ ] Suite completa: `pytest tests/ -v`
- [ ] (Opcional) Scraper de autonomicos si es necesario
- [ ] Documentacion actualizada

---

## Añadir un Nuevo Año a una CCAA Existente

Para añadir datos de un nuevo año (ej. 2027):

1. Buscar la URL del boletin oficial con los festivos de 2027
2. Añadir en `ccaa_registry.yaml`:
   ```yaml
   urls:
     locales:
       2027: "https://nueva-url..."  # <-- Nuevo
       2026: "https://url-existente..."
   ```
3. Para CCAA con cache-first (Aragon, CyL, CLM, Extremadura): generar el JSON de festivos
4. Verificar: `python3 scrape_municipio.py "Municipio" ccaa 2027`

---

## Recursos Utiles

### Boletines Oficiales de CCAA

| CCAA | Boletin | URL |
|------|---------|-----|
| Andalucia | BOJA | https://www.juntadeandalucia.es/boja |
| Aragon | BOA | https://www.boa.aragon.es |
| Asturias | BOPA | https://sede.asturias.es/bopa |
| Baleares | BOIB | https://www.caib.es/boib |
| Canarias | BOC | https://www.gobiernodecanarias.org/boc |
| Cantabria | BOC | https://boc.cantabria.es |
| Castilla y Leon | BOCYL | https://bocyl.jcyl.es |
| Castilla-La Mancha | DOCM | https://docm.jccm.es |
| Cataluña | DOGC | https://dogc.gencat.cat |
| Extremadura | DOE | https://doe.juntaex.es |
| Galicia | DOG | https://www.xunta.gal/diario-oficial-galicia |
| Madrid | BOCM | https://www.bocm.es |
| Murcia | BORM | https://www.borm.es |
| Navarra | BON | https://bon.navarra.es |
| Pais Vasco | BOPV | https://www.euskadi.eus/bopv2 |
| La Rioja | BOR | https://web.larioja.org/bor |
| Valencia | DOGV | https://www.dogv.gva.es |

### Herramientas de Desarrollo

```bash
# Ver contenido de PDF
pdftotext documento.pdf - | less

# Extraer texto limpio
python3 -c "import pdfplumber; print(pdfplumber.open('doc.pdf').pages[0].extract_text())"

# Test regex
python3 -c "import re; print(re.findall(r'tu_patron', 'texto_prueba'))"

# Ejecutar tests
python3 -m pytest tests/ -v

# Validar YAML
python3 config/migrate_to_yaml.py --validate
```

### Patrones de Formato por CCAA

| Formato | CCAA | Libreria |
|---------|------|----------|
| PDF | Madrid, Asturias, Cantabria, CLM, Extremadura, Murcia, Rioja, Valencia | PyPDF2, pdfplumber |
| HTML | Andalucia, Baleares, Galicia, Navarra, Canarias | BeautifulSoup |
| CSV | Aragon, Castilla y Leon | pandas |
| XML | Cataluña (Akoma Ntoso) | BeautifulSoup |
| JSON | Pais Vasco (OpenData API) | json nativo |
