# 📝 Changelog

Todos los cambios notables del proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/).

## [No publicado]

### Por Hacer
- Generalización de lógica de sustituciones
- Optimización de normalización (O(1) con fuzzy matching)
- API REST
- Frontend web

---

## [2.0.0] - 2026-02-02

### 🏭 ScraperFactory + Eliminación de Duplicación

**Añadido:**
- `ScraperFactory` (`scrapers/core/scraper_factory.py`) — imports dinámicos vía `importlib`
  - `create_locales_scraper()` para las 17 CCAA
  - `create_autonomicos_scraper()` para madrid, canarias, navarra
  - Derivación automática de nombre de clase desde código CCAA
  - Override explícito para nombres irregulares (`castilla_mancha`)
- 27 tests unitarios para el factory (`tests/unit/test_scraper_factory.py`)

**Cambiado:**
- `scrape_municipio.py`: 17 elif locales + 3 elif autonómicos → 2 llamadas al factory
- `scrape_municipio.py`: lista hardcodeada de CCAA → `CCAaRegistry().list_ccaa()`
- `app.py`: `CCAA_DISPONIBLES` hardcodeada → `CCAaRegistry().list_ccaa()`
- Estandarizados 9 `__init__.py` de CCAA (exports uniformes)

**Eliminado:**
- `scrapers/orchestrator.py` — código muerto (solo soportaba Canarias)
- `scrapers/unificador.py` — código muerto (solo importaba orchestrator)

**Resultados:**
- ✅ +273 líneas, −571 líneas = reducción neta de 298 líneas
- ✅ 79 tests passing, 3 skipped
- ✅ 0 regresiones

---

## [1.2.0] - 2026-02-02

### 🐛 Fix: Mapeo BOE para Castilla-La Mancha

**Corregido:**
- `boe_scraper.py`: `CCAA_MAP` mapeaba `'Castilla-La Mancha'` a `'castilla_la_mancha'` (con `_la_`) pero el proyecto usa `'castilla_mancha'` → la tabla BOE no filtraba festivos autonómicos correctamente
- Resultado: CLM pasó de 13 festivos a 14 festivos (correcto)

---

## [1.1.0] - 2026-02-01

### 🎉 17/17 Comunidades Autónomas Completas

7 nuevas CCAA implementadas en una sesión:

#### CCAA #11: La Rioja (`c8e36fe` → `2d17595`)
- Parser PDF del BOR
- 164 municipios
- Auto-discovery implementado

#### CCAA #12: Región de Murcia (`98003db`)
- Parser PDF del BORM
- 45 municipios

#### CCAA #13: Navarra (`42bcee6` → `411287d`)
- Parser HTML del BON con sistema de fechas relativas
- 694 municipios (solo 1 festivo local por municipio)
- Scraper de autonómicos dedicado
- Auto-discovery de 4 niveles con cache-first
- 5.6% de fechas son relativas (ordinales, litúrgicas, santoral)

#### CCAA #14: Aragón (`693b32e` → `0bfeba7`)
- OpenData CSV desde portal de datos abiertos de Aragón
- 565 municipios
- Estrategia cache-first

#### CCAA #15: Castilla y León (`3665a0b`)
- OpenData CSV desde portal de transparencia JCyL
- 2248 municipios (la CCAA con más municipios)
- URLs predecibles por año

#### CCAA #16: Castilla-La Mancha (`b25c58a`)
- Parser PDF del DOCM
- 919 municipios
- Estrategia cache-first

#### CCAA #17: Extremadura (`85c6e9a`)
- Parser PDF del DOE
- 388 municipios
- Estrategia cache-first

**Resultados:**
- ✅ 17/17 CCAA implementadas (100% cobertura)
- ✅ 8.351 municipios teóricos cubiertos
- ✅ 52 tests passing, 3 skipped

---

## [1.0.0-refactor] - 2026-01-18

### 🎉 Refactor Mayor Completado (4 Días)

Refactor arquitectónico enfocado en mantenibilidad, testabilidad y escalabilidad, **sin romper funcionalidad** en producción.

#### ✨ DÍA 1: Tests + Fixtures + CI (Commit: `0f82b87`)

**Añadido:**
- Tests unitarios para parsers de PDF (8 tests): `tests/unit/test_pdf_parsers.py`
- Tests de integración para Asturias y Cantabria (4 tests): `tests/integration/test_scrapers_smoke.py`
- Fixtures locales para testing sin internet (4 PDFs/HTMLs)
- CI/CD con GitHub Actions: `.github/workflows/test.yml`
- Configuración pytest: `tests/conftest.py`
- Dependencias de testing: pytest, pytest-cov

**Resultados:**
- ✅ 29 tests passing, 3 skipped
- ✅ 0 regresiones en código existente
- ✅ CI verde en GitHub Actions

#### 🔧 DÍA 2: Unificar Configuración (Commit: `b107ff7`)

**Añadido:**
- Registro centralizado YAML (197 líneas): `config/ccaa_registry.yaml`
  - Metadata unificada de 10 CCAA
  - URLs de boletines (locales + autonómicos)
  - Info de auto-discovery, formatos, provincias
- API Python para configuración: `config/config_manager.py`
  - Patrón Singleton
  - 15 métodos públicos + 21 tests unitarios
- Script de validación: `config/migrate_to_yaml.py`
  - Validador YAML vs JSONs existentes
  - 5 validaciones automáticas

**Cambiado:**
- Corregidos paths: `baleares_municipios.json`, `cataluna_municipios.json`
- Total municipios: 3316 → 3318

**Resultados:**
- ✅ 21 tests nuevos passing
- ✅ Total acumulado: 50 tests passing

#### 🏗️ DÍA 3: Refactorizar PDF Parsing (Commit: `8e8e9ab`)

**Añadido:**
- `BasePDFParser` (235 líneas): `scrapers/parsers/base_pdf_parser.py`
  - Clase base abstracta con Template Method Pattern
  - Caching automático de resultados
  - Búsqueda flexible (exacta → case-insensitive → parcial)
  - Métodos helper: `_crear_festivo()`, `_es_fecha_valida()`, etc.
- Tests unitarios (16 tests): `tests/unit/test_base_pdf_parser.py`
  - Tests de helpers, caching, búsqueda

**Cambiado:**
- Asturias refactorizado: 267 líneas → 218 líneas (-18%)
- Cantabria refactorizado: 239 líneas → 193 líneas (-19%)
- Eliminadas -95 líneas de duplicación

**Resultados:**
- ✅ 16 tests nuevos passing
- ✅ Total acumulado: 45 tests passing, 3 skipped
- ✅ 0 regresiones

#### 📚 DÍA 4: Consolidación y Documentación (Este commit)

**Añadido:**
- README técnico: `scrapers/README.md`
  - Arquitectura completa documentada
  - Guía "Cómo añadir una nueva CCAA"
  - Ejemplos de código
  - Tabla de estado de 10 CCAA
- Script de validación end-to-end: `scripts/validate_all_ccaa.py`
  - 14 validaciones automáticas
  - Verifica imports, config, parsers
- CHANGELOG actualizado (este archivo)

**Resultados:**
- ✅ 14 validaciones end-to-end passing
- ✅ Documentación completa
- ✅ Refactor cerrado y consolidado

### 📊 Resumen del Refactor (Métricas)

| Métrica | Antes | Después | Mejora |
|---------|-------|---------|--------|
| Tests totales | 0 | 45 | +45 |
| Validaciones E2E | 0 | 14 | +14 |
| Cobertura config | 0% | 100% | +100% |
| Cobertura parsers | 0% | 100% | +100% |
| Código duplicado | ~500 líneas | ~405 líneas | -95 |
| CCAA documentadas | 0 | 10 | +10 |
| CI/CD | ❌ | ✅ GitHub Actions | ✅ |

### 🎯 Beneficios

- **Mantenibilidad** ⬆️: Config centralizada, código compartido, documentación
- **Testabilidad** ⬆️: 45 tests automáticos, CI/CD, fixtures locales
- **Extensibilidad** ⬆️: Añadir CCAA nueva ~2-3h (antes ~1 día)
- **Confiabilidad** ⬆️: 0 regresiones, validación automatizada

### 🚀 Próximos Pasos Recomendados

1. **Volver a Features**: Implementar La Rioja, Aragón, Extremadura... (CCAA #11-17)
2. **O continuar refactor**: DÍA 5-7 (error handling, optimización, cleanup)

---

## [1.0.0] - 2025-12-26

### Añadido

#### Sistema Base
- ✅ Arquitectura de scrapers con herencia común (`BaseScraper`)
- ✅ Sistema de cache de 3 niveles (KNOWN_URLS → Cache → Auto-discovery)
- ✅ Scraper unificado (`scrape_municipio.py`) para BOE + CCAA + locales
- ✅ Exportación a JSON y Excel
- ✅ Eliminación inteligente de duplicados con prioridad

#### BOE (Festivos Nacionales)
- ✅ Auto-discovery vía API del BOE para cualquier año desde 2012
- ✅ Parser robusto con patrones conocidos
- ✅ Cache automático de URLs descubiertas
- ✅ Soporte para años futuros

#### Canarias
- ✅ **Auto-discovery completo para BOC Canarias**
  - Búsqueda automática en boletines del año anterior
  - Conversión automática PDF → HTML
  - Cache automático de URLs descubiertas
- ✅ **Sistema de filtrado por isla**
  - Mapeo de 88 municipios a 7 islas
  - Extracción correcta: 1 regional + 1 insular por municipio
- ✅ **Parser HTML con normalización Unicode**
  - Gestión de caracteres especiales (Ã±, Ã©, etc)
  - Extracción de festivos insulares
- ✅ **Gestión de sustituciones**
  - Festivos que caen en domingo se sustituyen (ej: 12 oct → 30 mayo en 2025)
- ✅ **Años disponibles: 2025, 2026**

#### Madrid
- ✅ **Parser completo BOCM (PDF)**
  - Festivos autonómicos (Decreto)
  - Festivos locales (Resolución)
- ✅ **Normalización mejorada de nombres de municipios**
  - Gestión de espacios y tildes
  - Soporte para 181 municipios
- ✅ **Cache manual para 2026**
- ⏳ Auto-discovery pendiente (BOCM tiene anti-scraping)

#### Documentación
- ✅ README.md completo con instalación y uso
- ✅ Documentación técnica (ARCHITECTURE.md)
- ✅ Guía de contribución (CONTRIBUTING.md)
- ✅ Ejemplos de uso (EXAMPLES.md)
- ✅ Changelog (CHANGELOG.md)

### Corregido

#### Canarias
- 🐛 Filtrado por isla: ahora extrae exactamente 2 festivos autonómicos por municipio
- 🐛 Normalización Unicode: caracteres especiales se procesan correctamente
- 🐛 Auto-discovery: conversión correcta de URLs PDF → HTML
- 🐛 Cache: inicialización correcta antes de primer acceso

#### Madrid
- 🐛 Normalización de nombres: "Alcalá de Henares" vs "Alcaládehenares"
- 🐛 Comparación de municipios: eliminación de espacios y tildes
- 🐛 Parser PDF: extracción mejorada de festivos locales

#### General
- 🐛 Eliminación de duplicados: prioridad local > autonómico > nacional
- 🐛 Gestión de errores: mensajes más informativos
- 🐛 Cache: método `_save_to_cache()` corregido para aceptar 3 parámetros

### Técnico

#### Arquitectura
```
scrapers/
├── core/
│   ├── base_scraper.py          # Clases base
│   └── boe_scraper.py           # BOE
├── ccaa/
│   ├── canarias/
│   │   ├── autonomicos.py       # Con auto-discovery
│   │   └── locales.py           # Con auto-discovery
│   └── madrid/
│       ├── autonomicos.py
│       └── locales.py
└── discovery/
    └── ccaa/
        ├── canarias_discovery.py  # Funcionando
        └── madrid_discovery.py    # WIP
```

#### Cache
```
config/
├── boe_urls_cache.json          # 4 años
├── canarias_urls_cache.json     # 2025-2026
└── madrid_urls_cache.json       # 2026
```

#### Datos de Prueba
- ✅ Canarias - Arrecife 2025: 14 festivos
- ✅ Canarias - Santa Cruz de Tenerife 2025: 14 festivos
- ✅ Canarias - Las Palmas de Gran Canaria 2025: 14 festivos
- ✅ Canarias - Arrecife 2026: 14 festivos
- ✅ Madrid - Alcalá de Henares 2026: 14 festivos
- ✅ Madrid - Madrid 2026: 14 festivos

### Notas de Versión

#### v1.0.0 - "Primera versión funcional"

Esta es la primera versión estable del proyecto con soporte completo para:
- **BOE**: Festivos nacionales (cualquier año)
- **Canarias**: Sistema completo con auto-discovery
- **Madrid**: Sistema completo (auto-discovery pendiente)

**Limitaciones conocidas:**
- Auto-discovery de Madrid pendiente (BOCM anti-scraping)
- Solo 2 de 17 comunidades autónomas implementadas
- Lógica de sustituciones hardcoded por año

**Siguiente versión (v1.1.0):**
- Añadir Valencia
- Mejorar auto-discovery Madrid
- Generalizar sustituciones

---

## Formato del Changelog

### Tipos de Cambios
- **Añadido** - para funcionalidades nuevas
- **Cambiado** - para cambios en funcionalidades existentes
- **Obsoleto** - para funcionalidades que pronto se eliminarán
- **Eliminado** - para funcionalidades eliminadas
- **Corregido** - para corrección de errores
- **Seguridad** - en caso de vulnerabilidades

### Commits Relevantes

#### 2025-12-26 - Sistema Completo
```bash
feat: sistema completo calendarios laborales BOE+Madrid+Canarias

- Auto-discovery BOC Canarias funcionando
- Filtrado por isla implementado
- Normalización Madrid corregida
- Scraper unificado operativo
- Documentación completa
```

#### 2025-12-26 - Auto-discovery Canarias
```bash
feat: auto-discovery completo para BOC Canarias

- Módulo scrapers/discovery/ccaa/canarias_discovery.py
- Búsqueda automática en BOC por rango
- Conversión PDF → HTML
- Integrado en scrapers
```

#### 2025-12-25 - Cache System
```bash
feat: sistema de cache para Madrid y Canarias

- Cache de 3 niveles implementado
- Auto-save de URLs descubiertas
- Mejora de performance
```

#### 2025-12-25 - Madrid Implementation
```bash
feat: implementar scrapers completos de Madrid

- Scraper autonómicos BOCM
- Scraper locales BOCM (179 municipios)
- Parser PDF con PyPDF2
```

#### 2025-12-24 - Canarias Implementation
```bash
feat: implementar scrapers de Canarias

- Filtrado por isla
- 88 municipios soportados
- Parser HTML BOC
```

---

## Roadmap

### v2.1.0 (Próxima versión)
- [ ] Generalizar lógica de sustituciones
- [ ] Optimización fuzzy matching (O(1) con índices)
- [ ] Extraer CacheFirstMixin para reducir duplicación

### v3.0.0
- [ ] API REST completa
- [ ] Frontend web
- [ ] Base de datos persistente

### Futuro
- [x] ~~17 comunidades autónomas completas~~ (completado v1.1.0)
- [x] ~~Tests unitarios con pytest~~ (completado v1.0.0-refactor)
- [x] ~~CI/CD con GitHub Actions~~ (completado v1.0.0-refactor)
- [ ] Histórico desde 2010
- [ ] Exportación a iCal
- [ ] Integración con Google Calendar
