# 📅 Calendario Laboral España

**Generador automático de calendarios laborales personalizados por municipio en España.**

Extrae festivos nacionales, autonómicos y locales desde fuentes oficiales (BOE, boletines autonómicos) y genera calendarios visuales listos para imprimir o descargar.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://calendario-laboral-espana-yornkkgnnzizqn4omxfhr5.streamlit.app)

---

## 🎯 Características

✅ **17/17 Comunidades Autónomas** — cobertura completa de España
✅ **8,351+ municipios** soportados con festivos exactos
✅ **14 festivos precisos** por municipio (8 nacionales + 4-6 autonómicos + 2 locales)
✅ **Auto-discovery** automático de URLs de boletines oficiales (88% CCAA)
✅ **Cache-first** — datos pre-generados para funcionamiento sin dependencias externas
✅ **Parsing inteligente** de HTML, PDF, XML, CSV, YAML y JSON
✅ **Generación de PDF** para imprimir con branding personalizable
✅ **Deploy en Streamlit Cloud** — acceso público y gratuito

---

## 📊 Cobertura

| CCAA | Municipios | Provincias | Fuente Oficial | Auto-discovery | Formato |
|------|------------|------------|----------------|----------------|---------|
| **Andalucía** | 746 | 8 | BOJA | ✅ | PDF |
| **Aragón** | 565 | 3 | OpenData Aragón | ✅ (CKAN) | CSV |
| **Asturias** | 78 | 1 | BOPA | ✅ | PDF |
| **Baleares** | 67 | 4 islas | BOIB | ❌ | HTML |
| **Canarias** | 88 | 2 islas | BOC | ✅ | YAML |
| **Cantabria** | 102 | 1 | BOC | ✅ | PDF |
| **Castilla y León** | 2,248 | 9 | OpenData JCyL | ✅ | CSV |
| **Castilla-La Mancha** | 919 | 5 | DOCM | ✅ | PDF |
| **Cataluña** | 950 | 4 (42 comarcas) | DOGC | ❌ | XML |
| **Extremadura** | 388 | 2 | DOE | ✅ | PDF |
| **Galicia** | 313 | 4 | DOG | ✅ (RDF) | HTML |
| **La Rioja** | 164 | 1 | BOR | ✅ | PDF |
| **Madrid** | 181 | 1 | BOCM | ✅ | PDF |
| **Murcia** | 45 | 1 | BORM | ✅ | PDF |
| **Navarra** | 694 | 1 | BON | ✅ | HTML |
| **País Vasco** | 251 | 3 territorios | OpenData Euskadi | ✅ | JSON |
| **Valencia** | 542 | 3 | DOGV | ✅ | PDF |
| **TOTAL** | **8,351+** | **53+** | - | **88%** (15/17) | - |

**17/17 CCAA — 100% de España**

---

## 🚀 Uso Rápido

### Opción 1: App Web (Recomendado)

Accede directamente a la aplicación desplegada:

👉 **[calendario-laboral-espana.streamlit.app](https://calendario-laboral-espana-yornkkgnnzizqn4omxfhr5.streamlit.app)**

1. Selecciona tu comunidad autónoma
2. Selecciona tu municipio
3. Elige el año
4. Genera el calendario visual
5. Descarga el PDF para imprimir

### Opción 2: Línea de Comandos
```bash
# Clonar repositorio
git clone https://github.com/tu-usuario/calendario-laboral-espana.git
cd calendario-laboral-espana

# Instalar dependencias
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt

# Generar calendario para un municipio
python scrape_municipio.py "BARCELONA" cataluna 2026
python scrape_municipio.py "Valladolid" castilla_leon 2026
python scrape_municipio.py "Mérida" extremadura 2026

# Iniciar la app local
streamlit run app.py
```

---

## 🛠️ Arquitectura Técnica

### Scrapers Modulares

El proyecto utiliza scrapers especializados para cada fuente oficial:
```
scrapers/
├── core/
│   ├── base_scraper.py          # Clase base abstracta
│   └── boe_scraper.py           # Festivos nacionales + autonómicos (BOE)
├── ccaa/
│   ├── andalucia/locales.py     # BOJA — PDF parsing
│   ├── aragon/locales.py        # OpenData Aragón — CSV (CKAN)
│   ├── asturias/locales.py      # BOPA — PDF parsing
│   ├── baleares/locales.py      # BOIB — HTML tablas por islas
│   ├── canarias/locales.py      # BOC — YAML parsing
│   ├── cantabria/locales.py     # BOC — PDF parsing
│   ├── castilla_leon/locales.py # OpenData JCyL — CSV (latin-1)
│   ├── castilla_mancha/locales.py # DOCM — PDF text extraction
│   ├── cataluna/locales.py      # DOGC — XML Akoma Ntoso (curl)
│   ├── extremadura/locales.py   # DOE — PDF text extraction
│   ├── galicia/locales.py       # DOG — HTML parsing robusto
│   ├── madrid/locales.py        # BOCM — PDF parsing
│   ├── murcia/locales.py        # BORM — PDF parsing
│   ├── navarra/locales.py       # BON — HTML table parsing
│   ├── pais_vasco/locales.py    # OpenData Euskadi — JSON API
│   ├── rioja/locales.py         # BOR — PDF parsing
│   └── valencia/locales.py      # DOGV — PDF multiidioma
└── discovery/
    └── ccaa/
        ├── andalucia_discovery.py       # BOJA sequential search
        ├── aragon_discovery.py          # CKAN API search
        ├── asturias_discovery.py        # BOPA direct
        ├── canarias_discovery.py        # BOC RDF catalog
        ├── cantabria_discovery.py       # BOC search
        ├── castilla_leon_discovery.py   # Predictable URL + HEAD
        ├── castilla_mancha_discovery.py # DOCM + datos abiertos
        ├── extremadura_discovery.py     # DOE + juntaex.es
        ├── galicia_discovery.py         # DOG RDF catalog
        ├── madrid_discovery.py          # BOCM search
        ├── murcia_discovery.py          # BORM search
        ├── navarra_discovery.py         # BON search
        ├── pais_vasco_discovery.py      # OpenData Euskadi
        ├── rioja_discovery.py           # BOR search
        └── valencia_discovery.py        # DOGV search
```

### Estrategia de Datos (4 niveles)

Cada scraper sigue una estrategia de 4 niveles para máxima fiabilidad:

1. **Cache de festivos** — JSON pre-generado con todos los festivos (instantáneo, funciona en Streamlit Cloud)
2. **Cache de URLs** — URL descubierta previamente guardada en JSON local
3. **Registry** — URL oficial configurada en `ccaa_registry.yaml`
4. **Auto-discovery** — Búsqueda automática en portales oficiales y datos abiertos

### Auto-discovery Inteligente

Los scrapers incluyen **auto-discovery** que:

1. Busca automáticamente en portales oficiales (CKAN, RDF, datos abiertos)
2. Extrae signaturas y enlaces de boletines
3. Valida contenido (provincias, municipios, año)
4. Cachea URLs descubiertas para futuras consultas
5. Se actualiza automáticamente cada año

**Métodos de discovery:**
- **CKAN API:** Aragón (opendata.aragon.es)
- **RDF catalog:** Galicia (xunta.gal), Canarias (BOC)
- **URLs predecibles:** Castilla y León (transparencia.jcyl.es), País Vasco, Baleares
- **Búsqueda directa:** Madrid, Andalucía, Valencia, Asturias, Cantabria, La Rioja, Murcia, Navarra
- **Datos abiertos + boletín:** Castilla-La Mancha, Extremadura

### Parsing Robusto

- **HTML:** BeautifulSoup con normalización de caracteres (ñ, ü, tildes, artículos catalanes)
- **PDF:** pdfplumber/pypdf con extracción de texto y validación de estructura
- **XML:** ElementTree con HTML escapado (Akoma Ntoso estándar)
- **CSV:** Semicolon-delimited con manejo de encoding (UTF-8, latin-1)
- **YAML:** Safe loading con manejo de encoding UTF-8
- **JSON:** Datos estructurados de OpenData (País Vasco, Aragón)
- **Formatos complejos:** Regex adaptativo para "14y17deagosto", "27 y 28 de agosto"
- **Múltiples fechas:** "27 de julio, 7 de diciembre" → 2 festivos separados
- **Tablas HTML:** Extracción estructurada por islas/provincias/comarcas/territorios
- **SSL problemático:** Fallback a curl para servidores con certificados antiguos

---

## 📝 Ejemplos de Salida

### Calendario Visual
```
Calendario generado: 14 festivos

┌─────────────────────────────────────────┐
│  CALENDARIO LABORAL 2026 - BILBAO       │
│  País Vasco - Bizkaia                   │
└─────────────────────────────────────────┘

📅 FESTIVOS:
   2026-01-01 - [NACIONAL   ] Año Nuevo
   2026-01-06 - [NACIONAL   ] Epifanía del Señor
   2026-03-19 - [AUTONOMICO ] San José
   2026-04-02 - [AUTONOMICO ] Jueves Santo
   2026-04-03 - [NACIONAL   ] Viernes Santo
   2026-04-06 - [AUTONOMICO ] Lunes de Pascua
   2026-05-01 - [NACIONAL   ] Fiesta del Trabajo
   2026-07-25 - [AUTONOMICO ] Santiago Apóstol
   2026-07-31 - [LOCAL      ] San Ignacio de Loyola
   2026-08-15 - [NACIONAL   ] Asunción de la Virgen
   2026-08-21 - [LOCAL      ] Viernes de la Semana Grande
   2026-10-12 - [NACIONAL   ] Fiesta Nacional de España
   2026-12-08 - [NACIONAL   ] Inmaculada Concepción
   2026-12-25 - [NACIONAL   ] Natividad del Señor
```

### JSON Output
```json
{
  "municipio": "Bilbao",
  "ccaa": "pais_vasco",
  "territorio": "Bizkaia",
  "year": 2026,
  "festivos": [
    {
      "fecha": "2026-01-01",
      "descripcion": "Año Nuevo",
      "tipo": "nacional"
    },
    {
      "fecha": "2026-07-31",
      "descripcion": "San Ignacio de Loyola",
      "tipo": "local",
      "territorio": "Bizkaia"
    },
    {
      "fecha": "2026-08-21",
      "descripcion": "Viernes de la Semana Grande",
      "tipo": "local",
      "municipio": "Bilbao"
    }
  ]
}
```

---

## 🗺️ Roadmap

### CCAA Completadas

- [x] **Canarias** (88 municipios) — BOC / YAML
- [x] **Madrid** (181 municipios) — BOCM / PDF
- [x] **Andalucía** (746 municipios) — BOJA / PDF
- [x] **Valencia** (542 municipios) — DOGV / PDF
- [x] **Baleares** (67 municipios) — BOIB / HTML
- [x] **Cataluña** (950 municipios) — DOGC / XML
- [x] **Galicia** (313 municipios) — DOG / HTML
- [x] **País Vasco** (251 municipios) — OpenData / JSON
- [x] **Asturias** (78 municipios) — BOPA / PDF
- [x] **Cantabria** (102 municipios) — BOC / PDF
- [x] **La Rioja** (164 municipios) — BOR / PDF
- [x] **Murcia** (45 municipios) — BORM / PDF
- [x] **Navarra** (694 municipios) — BON / HTML
- [x] **Aragón** (565 municipios) — OpenData / CSV
- [x] **Castilla y León** (2,248 municipios) — OpenData JCyL / CSV
- [x] **Castilla-La Mancha** (919 municipios) — DOCM / PDF
- [x] **Extremadura** (388 municipios) — DOE / PDF

### Features Planificadas

- [ ] Refactoring: factory pattern para scrapers
- [ ] Export a Google Calendar (ICS)
- [ ] API REST pública
- [ ] Comparador entre municipios
- [ ] Histórico de festivos (2020-2030)
- [ ] Festivos personalizados de empresa

---

## 🤝 Contribuir

Las contribuciones son bienvenidas. Para añadir soporte a un nuevo año:

1. Busca la URL del boletín oficial correspondiente
2. Añade la URL a `config/ccaa_registry.yaml`
3. Genera el cache de festivos pre-generado en `config/`
4. Actualiza tests y documentación
5. Envía un PR

**Ver:** [CONTRIBUTING.md](CONTRIBUTING.md) para guía detallada

---

## 📄 Fuentes Oficiales

| CCAA | Boletín | URL |
|------|---------|-----|
| Nacional | BOE | [boe.es](https://www.boe.es/) |
| Andalucía | BOJA | [juntadeandalucia.es/boja](https://www.juntadeandalucia.es/boja/) |
| Aragón | OpenData | [opendata.aragon.es](https://opendata.aragon.es/) |
| Asturias | BOPA | [sede.asturias.es/bopa](https://sede.asturias.es/bopa) |
| Baleares | BOIB | [caib.es](https://www.caib.es/eboibfront/) |
| Canarias | BOC | [gobiernodecanarias.org/boc](https://www.gobiernodecanarias.org/boc/) |
| Cantabria | BOC | [boc.cantabria.es](https://boc.cantabria.es/) |
| Castilla y León | OpenData JCyL | [transparencia.jcyl.es](https://transparencia.jcyl.es/) |
| Castilla-La Mancha | DOCM | [docm.jccm.es](https://docm.jccm.es/) |
| Cataluña | DOGC | [dogc.gencat.cat](https://dogc.gencat.cat/) |
| Extremadura | DOE | [doe.juntaex.es](https://doe.juntaex.es/) |
| Galicia | DOG | [xunta.gal/dog](https://www.xunta.gal/dog) |
| La Rioja | BOR | [web.larioja.org/bor-portada](https://web.larioja.org/bor-portada) |
| Madrid | BOCM | [bocm.es](https://www.bocm.es/) |
| Murcia | BORM | [borm.es](https://www.borm.es/) |
| Navarra | BON | [bon.navarra.es](https://bon.navarra.es/) |
| País Vasco | OpenData Euskadi | [opendata.euskadi.eus](https://opendata.euskadi.eus/) |
| Valencia | DOGV | [dogv.gva.es](https://dogv.gva.es/) |

---

## 📋 Requisitos

- Python 3.9+
- Dependencias: `streamlit`, `requests`, `beautifulsoup4`, `pypdf`, `pyyaml`, `pdfplumber`
- Sistema: `curl` (para Cataluña, generalmente preinstalado en Linux/Mac)
```bash
pip install -r requirements.txt
```

---

## 📜 Licencia

MIT License - Ver [LICENSE](LICENSE) para más detalles

---

## 👨‍💻 Autor

Desarrollado con ❤️ para facilitar la gestión de calendarios laborales en España.

**¿Preguntas o sugerencias?** Abre un [issue](https://github.com/tu-usuario/calendario-laboral-espana/issues)

---

## ⭐ Stats

![Municipios](https://img.shields.io/badge/Municipios-8351+-blue)
![CCAA](https://img.shields.io/badge/CCAA-17%2F17-brightgreen)
![Coverage](https://img.shields.io/badge/Cobertura-100%25-brightgreen)
![Python](https://img.shields.io/badge/Python-3.9+-blue)
