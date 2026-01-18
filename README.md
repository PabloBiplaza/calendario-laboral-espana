# 📅 Calendario Laboral España

**Generador automático de calendarios laborales personalizados por municipio en España.**

Extrae festivos nacionales, autonómicos y locales desde fuentes oficiales (BOE, boletines autonómicos) y genera calendarios visuales listos para imprimir o descargar.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://calendario-laboral-espana-yornkkgnnzizqn4omxfhr5.streamlit.app)

---

## 🎯 Características

✅ **10 Comunidades Autónomas** completas
✅ **3,316+ municipios** soportados con festivos exactos
✅ **14 festivos precisos** por municipio (8 nacionales + 4-6 autonómicos + 2 locales)
✅ **Auto-discovery** automático de URLs de boletines oficiales (90% CCAA)
✅ **Parsing inteligente** de HTML, PDF, XML, YAML y JSON
✅ **Generación de PDF** para imprimir con branding personalizable
✅ **Deploy en Streamlit Cloud** - acceso público y gratuito  

---

## 📊 Cobertura Actual

| CCAA | Municipios | Provincias/Comarcas | Fuente Oficial | Auto-discovery | Formato |
|------|------------|---------------------|----------------|----------------|---------|
| **Canarias** | 88 | 2 islas principales | BOC | ✅ | YAML |
| **Madrid** | 181 | 1 provincia | BOCM | ✅ | PDF |
| **Andalucía** | 746 | 8 provincias | BOJA | ✅ | HTML |
| **Valencia** | 540+ | 3 provincias | DOGV | ✅ | PDF |
| **Baleares** | 67 | 4 islas | CAIB | ❌ (URLs predecibles) | HTML |
| **Cataluña** | 950+ | 42 comarcas | DOGC | ❌ | XML (Akoma Ntoso) |
| **Galicia** | 313 | 4 provincias | DOG | ✅ (RDF) | HTML |
| **País Vasco** | 251 | 3 territorios | OpenData Euskadi | ✅ (URLs predecibles) | JSON |
| **Asturias** | 78 | 1 provincia | BOPA | ✅ | PDF |
| **Cantabria** | 102 | 1 provincia | BOC | ✅ | PDF |
| **TOTAL** | **3,316+** | **65+** | - | **90%** | - |

**Progreso:** 10/17 CCAA (59% de España)

---

## 🚀 Uso Rápido

### Opción 1: App Web (Recomendado)

Accede directamente a la aplicación desplegada:

👉 **[calendario-laboral-espana.streamlit.app](https://calendario-laboral-espana-yornkkgn4omxfhr5.streamlit.app)**

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
│   ├── base_scraper.py      # Clase base abstracta
│   └── boe_scraper.py        # Festivos nacionales + autonómicos
├── ccaa/
│   ├── canarias/
│   │   └── locales.py        # BOC - YAML parsing
│   ├── madrid/
│   │   └── locales.py        # BOCM - PDF parsing
│   ├── andalucia/
│   │   └── locales.py        # BOJA - HTML secuencial
│   ├── valencia/
│   │   └── locales.py        # DOGV - PDF multiidioma
│   ├── baleares/
│   │   └── locales.py        # CAIB - HTML tablas por islas
│   ├── cataluna/
│   │   └── locales.py        # DOGC - XML Akoma Ntoso (curl)
│   ├── galicia/
│   │   └── locales.py        # DOG - HTML parsing robusto
│   ├── pais_vasco/
│   │   └── locales.py        # OpenData Euskadi - JSON API
│   ├── asturias/
│   │   └── locales.py        # BOPA - PDF parsing
│   ├── cantabria/
│   │   └── locales.py        # BOC - PDF parsing
│   └── pais_vasco/
│       └── locales.py        # OpenData - JSON estructurado
└── discovery/
    └── ccaa/
        ├── canarias_discovery.py    # Auto-discovery BOC
        ├── madrid_discovery.py      # Auto-discovery BOCM
        ├── andalucia_discovery.py   # Auto-discovery BOJA
        ├── valencia_discovery.py    # Auto-discovery DOGV
        ├── galicia_discovery.py     # Auto-discovery DOG (RDF catalog)
        └── pais_vasco_discovery.py  # Auto-discovery OpenData
```

### Auto-discovery Inteligente

Los scrapers incluyen **auto-discovery** que:

1. 🔍 Busca automáticamente en páginas oficiales
2. 📋 Extrae signaturas y enlaces
3. ✅ Valida contenido (provincias, municipios, año)
4. 💾 Cachea URLs descubiertas
5. 🔄 Actualiza automáticamente cada año

**Casos especiales:**
- **Galicia:** Usa catálogo RDF de datos abiertos de Xunta
- **País Vasco:** URLs predecibles en OpenData Euskadi desde 2017

### Parsing Robusto

- **HTML:** BeautifulSoup con normalización de caracteres (ñ, ü, tildes, artículos catalanes)
- **PDF:** pypdf con extracción de texto y validación de estructura
- **XML:** ElementTree con HTML escapado (Akoma Ntoso estándar)
- **YAML:** Safe loading con manejo de encoding UTF-8
- **JSON:** Datos estructurados de OpenData (País Vasco)
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

### Próximas CCAA (En orden de prioridad)

- [✅] **Asturias** (78 municipios) - BOPA (Completado)
- [ ] **Cantabria** (102 municipios) - BOC
- [ ] **Castilla y León** (2,248 municipios) - BOCYL
- [ ] **Aragón** (731 municipios) - BOA
- [ ] **Murcia** (45 municipios) - BORM
- [ ] **Castilla-La Mancha** (~900 municipios) - DOCM
- [ ] **Extremadura** (388 municipios) - DOE
- [ ] **La Rioja** (174 municipios) - BOR
- [ ] **Navarra** (272 municipios) - BON

### Features Planificadas

- [ ] Export a Google Calendar (ICS)
- [ ] Integración con Bitrix24 API
- [ ] Festivos personalizados de empresa
- [ ] Comparador entre municipios
- [ ] API REST pública
- [ ] Histórico de festivos (2020-2030)
- [ ] Auto-discovery para Baleares y Cataluña

---

## 🤝 Contribuir

Las contribuciones son bienvenidas. Para añadir una nueva CCAA:

1. Crea el scraper en `scrapers/ccaa/nombre_ccaa/locales.py`
2. Implementa auto-discovery en `scrapers/discovery/ccaa/` (opcional)
3. Añade municipios en `config/nombre_ccaa_municipios.json`
4. Actualiza `CCAA_DISPONIBLES` en `app.py`
5. Añade tests y documentación

**Ver:** [CONTRIBUTING.md](CONTRIBUTING.md) para guía detallada

---

## 📄 Fuentes Oficiales

- **Nacional:** [BOE](https://www.boe.es/) - Boletín Oficial del Estado
- **Canarias:** [BOC](https://sede.gobcan.es/boc/) - Boletín Oficial de Canarias
- **Madrid:** [BOCM](https://www.bocm.es/) - Boletín Oficial de la Comunidad de Madrid
- **Andalucía:** [BOJA](https://www.juntadeandalucia.es/boja/) - Boletín Oficial de la Junta de Andalucía
- **Valencia:** [DOGV](https://dogv.gva.es/) - Diari Oficial de la Generalitat Valenciana
- **Baleares:** [CAIB](https://www.caib.es/sites/calendarilaboral/) - Govern de les Illes Balears
- **Cataluña:** [DOGC](https://dogc.gencat.cat/) - Diari Oficial de la Generalitat de Catalunya
- **Galicia:** [DOG](https://www.xunta.gal/dog) - Diario Oficial de Galicia
- **País Vasco:** [OpenData Euskadi](https://opendata.euskadi.eus/) - Datos Abiertos del Gobierno Vasco
- **Asturias:** [BOPA](https://miprincipado.asturias.es/bopa) - Boletín Oficial del Principado de Asturias

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

![Municipios](https://img.shields.io/badge/Municipios-3214+-blue)
![CCAA](https://img.shields.io/badge/CCAA-9%2F17-green)
![Coverage](https://img.shields.io/badge/Cobertura-53%25-yellow)
![Python](https://img.shields.io/badge/Python-3.9+-blue)
