# 📝 Changelog

Todos los cambios notables del proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/).

## [No publicado]

### Por Hacer
- Auto-discovery para Madrid (BOCM anti-scraping)
- Soporte para 17 comunidades autónomas restantes
- Tests unitarios con pytest
- Generalización de lógica de sustituciones
- API REST
- Frontend web

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

### v1.1.0 (Próxima versión)
- [ ] Auto-discovery para Madrid
- [ ] Añadir Valencia
- [ ] Tests unitarios con pytest
- [ ] CI/CD con GitHub Actions

### v1.2.0
- [ ] Añadir Cataluña
- [ ] Añadir Andalucía
- [ ] Generalizar lógica de sustituciones

### v2.0.0
- [ ] API REST completa
- [ ] Frontend web
- [ ] Autenticación de usuarios
- [ ] Base de datos persistente

### Futuro
- [ ] 17 comunidades autónomas completas
- [ ] Histórico desde 2010
- [ ] Exportación a iCal
- [ ] Integración con Google Calendar
- [ ] App móvil
