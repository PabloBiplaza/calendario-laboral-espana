# 📅 Calendario Laboral España

**Sistema automatizado de extracción y gestión de festivos laborales de España desde fuentes oficiales (BOE, boletines autonómicos).**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

---

## 🎯 Problema que resuelve

Las empresas, asesorías y desarrolladores necesitan conocer los festivos laborales aplicables a cada municipio de España para:
- **Gestión de nóminas** → Cálculo correcto de días laborables
- **Planificación empresarial** → Calendarios de trabajo por centro
- **Aplicaciones de RRHH** → Integración automatizada de festivos
- **Asesorías laborales** → Generación de calendarios para múltiples clientes

**El problema:** Los festivos están dispersos en múltiples publicaciones oficiales (BOE, BOC, BOJA, etc.) y cambian cada año.

**La solución:** Este proyecto extrae, estructura y unifica automáticamente todos los festivos desde las fuentes oficiales.

---

## ✨ Características

### 🔍 Extracción Automatizada
- ✅ **BOE** → Festivos nacionales (9 festivos comunes a toda España)
- ✅ **Boletines Autonómicos** → Festivos de Comunidades Autónomas e insulares
- ✅ **Órdenes Municipales** → Festivos locales (2 por cada municipio)
- ✅ **Parsing inteligente** → HTML, tablas y texto estructurado
- ✅ **Sin hardcoding** → Todo extraído de publicaciones oficiales

### 🏗️ Arquitectura Escalable
- **BaseScraper abstracto** → Framework reutilizable para cualquier CCAA
- **Configuración YAML** → URLs y metadatos centralizados
- **Orquestador** → Ejecuta múltiples scrapers y combina resultados
- **Validación de datos** → Fechas, estructura y coherencia
- **Sistema de cache** → Evita re-scraping innecesario

### 📊 Actualmente Implementado
- 🇪🇸 **España (Nacional)** → 9 festivos
- 🏝️ **Canarias** → 88 municipios, 8 festivos autonómicos/insulares, 176 festivos locales

### 🚀 Listo para Escalar
La arquitectura permite añadir las **16 CCAA restantes** fácilmente:
- Andalucía (786 municipios)
- Madrid (179 municipios)
- Cataluña (947 municipios)
- ... y el resto

---

## 🚀 Instalación
```bash
# Clonar repositorio
git clone https://github.com/TU_USUARIO/calendario-laboral-espana.git
cd calendario-laboral-espana

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

---

## 📖 Uso

### 1. Consultar festivos de un municipio
```bash
python -m scrapers.unificador "San Cristóbal de La Laguna"
```

**Output:**
```
📅 CALENDARIO LABORAL 2026
================================================================================
📍 Municipio: SAN CRISTÓBAL DE LA LAGUNA
📍 Provincia: Santa Cruz de Tenerife
📍 Comunidad Autónoma: Canarias
--------------------------------------------------------------------------------
📊 RESUMEN:
   • Festivos nacionales: 9
   • Festivos autonómicos/insulares: 2
   • Festivos locales: 2
   • TOTAL: 13 días festivos
--------------------------------------------------------------------------------
📆 LISTADO DE FESTIVOS:

   🇪🇸 2026-01-01 (Jueves   ) - Año Nuevo
      └─ Tipo: Nacional
   🇪🇸 2026-01-06 (Martes   ) - Epifanía del Señor
      └─ Tipo: Nacional
   🏝️ 2026-02-02 (Lunes    ) - Festividad de la Virgen de la Candelaria
      └─ Tipo: Autonómico/Insular
   🏠 2026-02-17 (Martes   ) - Martes de Carnaval
      └─ Tipo: Local
   ...
```

### 2. Modo interactivo
```bash
python -m scrapers.unificador
```

Menú con opciones para:
- Consultar municipios
- Listar todos los municipios
- Exportar a Excel (individual o masivo)
- Refrescar datos

### 3. Ejecutar scrapers manualmente
```bash
# Scraper BOE (nacionales)
python -m scrapers.core.boe_scraper

# Scraper Canarias autonómicos
python -m scrapers.ccaa.canarias.autonomicos

# Scraper Canarias locales
python -m scrapers.ccaa.canarias.locales

# Orquestador (ejecuta todos)
python -m scrapers.orchestrator
```

### 4. Exportar a Excel
```python
from scrapers.unificador import CalendarioLaboral

calendario = CalendarioLaboral(year=2026, ccaa='canarias')
calendario.cargar_datos()

# Exportar un municipio
calendario.exportar_excel('SAN CRISTÓBAL DE LA LAGUNA')

# Exportar todos los municipios
calendario.exportar_todos_municipios()
```

---

## 🏗️ Arquitectura
```
scrapers/
├── core/
│   ├── base_scraper.py          # Clase abstracta base
│   └── boe_scraper.py           # Festivos nacionales
├── ccaa/
│   └── canarias/
│       ├── autonomicos.py       # Festivos autonómicos/insulares
│       └── locales.py           # Festivos locales por municipio
├── orchestrator.py              # Orquestador de scrapers
└── unificador.py                # CLI para usuarios

config/
└── ccaa.yaml                    # URLs y configuración por CCAA

data/
├── nacionales_2026.json         # Festivos nacionales
├── canarias_autonomicos_2026.json
├── canarias_locales_2026.json
└── combined/
    └── canarias_2026_completo.json  # Todos combinados
```

---

## 🔧 Para Desarrolladores

### Añadir una nueva CCAA

1. **Actualizar configuración** (`config/ccaa.yaml`):
```yaml
andalucia:
  nombre_completo: "Andalucía"
  boletin_oficial:
    nombre: "BOJA"
    url_base: "https://www.juntadeandalucia.es/boja"
  publicaciones:
    "2026":
      autonomicos:
        url: "..."
      locales:
        url: "..."
```

2. **Crear scrapers** (heredan de `BaseScraper`):
```python
# scrapers/ccaa/andalucia/autonomicos.py
from scrapers.core.base_scraper import BaseScraper

class AndaluciaAutonomicosScraper(BaseScraper):
    def get_source_url(self) -> str:
        # Obtener URL desde config
        pass
    
    def parse_festivos(self, content: str) -> List[Dict]:
        # Parsear boletín oficial
        pass
```

3. **Integrar en orquestador** → Listo ✅

---

## 📊 Datos Generados

### Estructura de un festivo
```json
{
  "fecha": "2026-05-30",
  "fecha_texto": "30 de mayo",
  "descripcion": "Día de Canarias",
  "tipo": "autonomico",
  "ambito": "autonomico",
  "ccaa": "Canarias",
  "islas": "Todas",
  "year": 2026
}
```

### Metadata incluida

- **Fuente oficial** → URL del BOE/BOC/etc
- **Fecha de scraping** → Trazabilidad
- **Tipo y ámbito** → Nacional/autonómico/local
- **Sustituible** → Indica si la CCAA puede sustituirlo

---

## 🗺️ Roadmap

### v1.0 (Actual)
- ✅ Framework base escalable
- ✅ Scraping de BOE (nacionales)
- ✅ Scraping de Canarias completo (autonómicos + locales)
- ✅ CLI y exportación Excel
- ✅ Sistema de cache

### v1.1 (Próximo)
- [ ] Andalucía (786 municipios)
- [ ] Madrid (179 municipios)
- [ ] Cataluña (947 municipios)

### v2.0 (Futuro)
- [ ] Base de datos PostgreSQL/Supabase
- [ ] API REST con FastAPI
- [ ] Web app para consultas públicas
- [ ] GitHub Actions (scraping automático anual)
- [ ] Webhooks para notificar cambios

### v3.0 (Visión)
- [ ] 17 CCAA completas (8,131 municipios)
- [ ] Datos históricos (años anteriores)
- [ ] Integraciones: Excel Add-in, Google Sheets, PowerBI
- [ ] Modelo de negocio (tier gratuito + premium)

---

## 🤝 Contribuir

¡Las contribuciones son bienvenidas!

**Especialmente necesitamos:**
- Scrapers para las 16 CCAA restantes
- Mejoras en parsing de boletines oficiales
- Tests unitarios y de integración
- Documentación

**Cómo contribuir:**
1. Fork del repositorio
2. Crea una rama (`git checkout -b feature/nueva-ccaa`)
3. Commit tus cambios (`git commit -m 'feat: añadir Andalucía'`)
4. Push a la rama (`git push origin feature/nueva-ccaa`)
5. Abre un Pull Request

---

## 📄 Licencia

MIT License - ver archivo [LICENSE](LICENSE)

---

## 🙏 Agradecimientos

- **BOE** → Boletín Oficial del Estado
- **Gobierno de Canarias** → Boletín Oficial de Canarias
- Comunidad Python de España

---

## ⚖️ Disclaimer

Este proyecto extrae información de fuentes públicas oficiales. Los datos se proporcionan "tal cual" sin garantías. Para uso oficial, consulta siempre las publicaciones originales en los boletines oficiales correspondientes.

---

**⭐ Si este proyecto te resulta útil, dale una estrella en GitHub**