# 📅 Calendario Laboral España

Sistema automatizado para extraer festivos laborales oficiales en España desde fuentes gubernamentales (BOE, BOCM, BOC Canarias).

## 🎯 Características

### ✅ Implementado

- **BOE (Festivos Nacionales)**: Auto-discovery para cualquier año desde 2012
- **Canarias**: Sistema completo con auto-discovery BOC
  - Festivos autonómicos con filtrado por isla
  - Festivos locales (88 municipios)
  - Gestión automática de sustituciones
  - Años disponibles: 2025, 2026
- **Madrid**: Parser completo BOCM
  - Festivos autonómicos
  - Festivos locales (181 municipios)
  - Años disponibles: 2026
- **Scraper Unificado**: Un comando para BOE + CCAA + locales
- **Eliminación de duplicados**: Prioridad local > autonómico > nacional
- **Múltiples formatos**: JSON y Excel

### ⏳ Pendiente

- Auto-discovery para Madrid (BOCM tiene anti-scraping)
- 17 comunidades autónomas restantes
- Generalización de lógica de sustituciones

## 🚀 Instalación

```bash
# Clonar repositorio
git clone https://github.com/tu-usuario/calendario-laboral-espana.git
cd calendario-laboral-espana

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

## 📖 Uso

### Comando Unificado (Recomendado)

Extrae festivos nacionales + autonómicos + locales en un solo comando:

```bash
# Canarias - Arrecife 2025
python scrape_municipio.py "Arrecife" canarias 2025

# Madrid - Alcalá de Henares 2026
python scrape_municipio.py "Alcalá de Henares" madrid 2026
```

**Salida:**
- `data/canarias_arrecife_completo_2025.json`
- `data/canarias_arrecife_completo_2025.xlsx`

### Scrapers Individuales

```bash
# Solo festivos nacionales
python -m scrapers.core.boe_scraper 2025

# Solo autonómicos de Canarias
python -m scrapers.ccaa.canarias.autonomicos 2025

# Solo locales de Canarias para un municipio
python -m scrapers.ccaa.canarias.locales "Santa Cruz de Tenerife" 2025

# Solo autonómicos de Madrid
python -m scrapers.ccaa.madrid.autonomicos 2026

# Solo locales de Madrid para un municipio
python -m scrapers.ccaa.madrid.locales "Madrid" 2026
```

## 🏗️ Arquitectura

```
calendario-laboral-espana/
│
├── scrapers/
│   ├── core/
│   │   ├── base_scraper.py          # Clase base común
│   │   └── boe_scraper.py           # Festivos nacionales
│   │
│   ├── ccaa/
│   │   ├── canarias/
│   │   │   ├── autonomicos.py       # Festivos autonómicos Canarias
│   │   │   └── locales.py           # Festivos locales Canarias
│   │   └── madrid/
│   │       ├── autonomicos.py       # Festivos autonómicos Madrid
│   │       └── locales.py           # Festivos locales Madrid
│   │
│   └── discovery/
│       └── ccaa/
│           ├── canarias_discovery.py # Auto-discovery BOC
│           └── madrid_discovery.py   # Auto-discovery BOCM (WIP)
│
├── config/
│   ├── boe_urls_cache.json          # Cache URLs BOE
│   ├── canarias_urls_cache.json     # Cache URLs BOC
│   └── madrid_urls_cache.json       # Cache URLs BOCM
│
├── data/                             # Salidas JSON/Excel
├── scrape_municipio.py              # Scraper unificado
└── requirements.txt
```

## 🔍 Auto-Discovery

### Canarias (BOC)

El sistema busca automáticamente las publicaciones oficiales:

- **Autonómicos**: Busca en BOC 50-250 del año anterior
- **Locales**: Busca en BOC 130-280 del año anterior
- **Cache**: URLs descubiertas se guardan automáticamente
- **Conversión**: PDF → HTML automática

```bash
# Primera ejecución: auto-discovery (1-2 minutos)
python scrape_municipio.py "Arrecife" canarias 2027

# Siguientes ejecuciones: usa cache (instantáneo)
python scrape_municipio.py "Arrecife" canarias 2027
```

### BOE (Nacionales)

Auto-discovery vía API del BOE:

```python
# Busca automáticamente la resolución oficial
python -m scrapers.core.boe_scraper 2027
```

## 📊 Formato de Salida

### JSON

```json
{
  "municipio": "Arrecife",
  "ccaa": "Canarias",
  "year": 2025,
  "total_festivos": 14,
  "festivos": [
    {
      "fecha": "2025-01-01",
      "descripcion": "Año Nuevo",
      "tipo": "nacional",
      "ambito": "nacional",
      "sustituible": false
    },
    ...
  ]
}
```

### Excel

Tabla con columnas:
- Fecha
- Descripción
- Tipo (nacional/autonómico/local)
- Ámbito
- Sustituible

## 🎨 Características Especiales

### Canarias: Filtrado por Isla

Cada municipio de Canarias tiene:
- 1 festivo regional (Día de Canarias - 30 mayo)
- 1 festivo insular (específico de cada isla)

```bash
# Tenerife: Virgen de la Candelaria (2 febrero)
python scrape_municipio.py "Santa Cruz de Tenerife" canarias 2025

# Gran Canaria: Virgen del Pino (8 septiembre)
python scrape_municipio.py "Las Palmas de Gran Canaria" canarias 2025

# Lanzarote: Virgen de los Volcanes (15 septiembre)
python scrape_municipio.py "Arrecife" canarias 2025
```

### Gestión de Sustituciones

El sistema maneja automáticamente festivos sustituidos:

```python
# Ejemplo: Canarias 2025
# 12 octubre (domingo) → sustituido por 30 mayo
# El sistema elimina el 12 octubre automáticamente
```

### Eliminación de Duplicados

Cuando un festivo aparece en varias fuentes, se mantiene el de mayor prioridad:

**Prioridad**: Local > Autonómico > Nacional

Ejemplo:
- 1 enero aparece en BOE (nacional) y BOCM (autonómico)
- Se mantiene como "autonómico" (prioridad mayor)

## 🛠️ Desarrollo

### Añadir Nueva CCAA

Ver [CONTRIBUTING.md](docs/CONTRIBUTING.md) para guía detallada.

### Estructura de Clases

```python
from scrapers.core.base_scraper import BaseScraper

class NuevaCCAAScraper(BaseScraper):
    def get_source_url(self) -> str:
        # Lógica para obtener URL
        pass
    
    def parse_festivos(self, content: str) -> List[Dict]:
        # Lógica para parsear festivos
        pass
```

### Testing

```bash
# Test individual
python -m scrapers.ccaa.canarias.locales "Arrecife" 2025

# Test completo
python scrape_municipio.py "Arrecife" canarias 2025
```

## 📝 Cache

El sistema usa cache de 3 niveles:

1. **KNOWN_URLS**: URLs hardcoded para años conocidos
2. **Cache**: URLs descubiertas previamente
3. **Auto-discovery**: Búsqueda automática (lento)

Archivos de cache:
- `config/boe_urls_cache.json`
- `config/canarias_urls_cache.json`
- `config/madrid_urls_cache.json`

## 🤝 Contribuir

Ver [CONTRIBUTING.md](docs/CONTRIBUTING.md)

## 📄 Licencia

MIT License - ver [LICENSE](LICENSE)

## ✨ Créditos

Desarrollado por Pablo Biplaza

Fuentes oficiales:
- BOE: https://www.boe.es
- BOC Canarias: https://www.gobiernodecanarias.org/boc
- BOCM Madrid: https://www.bocm.es
