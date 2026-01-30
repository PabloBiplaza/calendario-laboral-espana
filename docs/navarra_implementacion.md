# Implementación de Navarra (CCAA #13)

## Resumen

Se ha completado la implementación de **Navarra** como la CCAA #13 del proyecto, con soporte completo para cálculo de fechas relativas.

### Estadísticas

- **694 municipios/localidades** con festivos locales
- **1 festivo local por municipio** (diferente al patrón típico de 2)
- **94.4% fechas fijas** (655 municipios): "22 de enero", "30 de noviembre"
- **5.6% fechas relativas** (39 municipios): "Segundo viernes de septiembre", "Viernes de carnaval"

## Archivos Creados

### 1. Módulo de Cálculo de Fechas (`scrapers/utils/date_calculator.py`)

Módulo reutilizable para calcular fechas relativas. Soporta:

**a) Ordinales simples (71.8% de casos relativos)**
- "Primer sábado de septiembre"
- "Segundo viernes de noviembre"
- "Último lunes de mayo"
- "Tercer domingo de julio"

**b) Ordinales compuestos (con modificadores)**
- "Lunes siguiente al primer domingo de mayo"
- "Viernes anterior al tercer domingo de septiembre"

**c) Fechas litúrgicas (23.1% de casos relativos)**
- **Carnaval**: "Viernes/Martes/Lunes de carnaval"
  - Calculado como 47-49 días antes de Pascua
- **Pentecostés**: "Lunes de Pentecostés", "Segundo día de Pentecostés"
  - Calculado como 50-51 días después de Pascua
- **Ascensión**: "Festividad de la Ascensión"
  - Calculado como 39 días después de Pascua
- **Pascua**: Usando algoritmo de Gauss (`dateutil.easter`)

**d) Santoral relativo (2.6% de casos relativos)**
- "Viernes de la semana siguiente a San Lucas" (BAZTAN)
- Soporta referencias a santos con fechas fijas

**Funciones principales:**
```python
calcular_fecha_relativa(year: int, texto: str) -> Optional[Tuple[datetime, str]]
calcular_pascua(year: int) -> datetime
calcular_carnaval(year: int, dia_semana: str) -> Optional[datetime]
calcular_pentecostes(year: int, dia: str) -> Optional[datetime]
calcular_ascension(year: int) -> datetime
obtener_nth_dia_semana_del_mes(year: int, month: int, dia_semana: int, n: int) -> Optional[datetime]
```

### 2. Scraper HTML de Navarra (`scrapers/ccaa/navarra/locales.py`)

Scraper especializado para el BON (formato HTML, no PDF).

**Características:**
- Parsea tabla HTML con 694 filas
- Detecta automáticamente si la fecha es fija o relativa
- Llama al `date_calculator` para fechas relativas
- Retorna metadata adicional:
  - `calculada`: True/False
  - `metodo_calculo`: Descripción del método usado
  - `fecha_original`: Texto original del BON

**Uso:**
```bash
# Un municipio específico
python3 scrapers/ccaa/navarra/locales.py 2026 PAMPLONA

# Todos los municipios
python3 scrapers/ccaa/navarra/locales.py 2026
```

### 3. Auto-discovery (`scrapers/discovery/ccaa/navarra_discovery.py`)

Script para descubrir URLs del BON automáticamente con **búsqueda paralela**.

**Características:**
- Búsqueda en 4 rangos paralelos (4 workers simultáneos)
- Optimizado para encontrar URLs en BON 230-250 (nov-dic)
- Valida automáticamente el contenido (palabras clave + tabla con 694 filas)
- Tiempo típico: ~3-4 minutos para encontrar la URL

**Uso:**
```bash
python3 scrapers/discovery/ccaa/navarra_discovery.py 2027
```

**Rendimiento probado:**
- 2026: ✅ Encontrado en 215 segundos (3.6 minutos)
- Prueba ~480 URLs en paralelo: 20 BON × 24 anuncios × 4 rangos

### 4. Extractor de municipios (`scrapers/discovery/ccaa/navarra_extract_municipios.py`)

Extrae los 694 municipios desde el BON y genera `config/navarra_municipios.json`.

### 5. Archivo de municipios (`config/navarra_municipios.json`)

JSON con 694 municipios en formato:
```json
{
  "PAMPLONA": "PAMPLONA",
  "TUDELA": "TUDELA",
  ...
}
```

### 6. Documentación (`docs/navarra_fechas_relativas.md`)

Análisis completo de:
- Los 39 casos de fechas relativas
- Patrones identificados
- Algoritmos de cálculo
- Ejemplos

## Configuración

### Actualizado `config/ccaa_registry.yaml`:

```yaml
navarra:
  name: "Comunidad Foral de Navarra"
  municipios_count: 694
  provincias:
    - "Navarra"
  boletin: "BON"
  boletin_url: "https://bon.navarra.es/"
  formato: "html"
  formato_especifico: "html_table"
  auto_discovery: true
  discovery_method: "bon_search"
  particularidades:
    - "1 festivo local por municipio (no 2 como otras CCAA)"
    - "94.4% fechas fijas, 5.6% fechas relativas/calculadas"
    - "Fechas relativas: ordinales, litúrgicas, santoral"
  urls:
    locales:
      2026: "https://bon.navarra.es/es/anuncio/-/texto/2025/241/12"
  municipios_file: "config/navarra_municipios.json"
```

### Metadatos actualizados:

```yaml
metadata:
  total_ccaa: 13
  total_municipios: 4231
  municipios_en_json: 989
  auto_discovery_percentage: 85
  ultima_actualizacion: "2026-01-30"
  version: "1.0.3"
```

## Tests

Todos los tests actualizados y pasando (27/27):

```bash
pytest tests/unit/test_config_manager.py -v
```

**Nuevos tests añadidos:**
- `test_get_ccaa_info_navarra`: Verifica info de Navarra
- `test_get_url_navarra_2026`: Verifica URL del BON
- `test_get_ccaa_by_provincia_navarra`: Búsqueda por provincia

**Tests actualizados:**
- `test_list_ccaa`: 12 → 13 CCAA
- `test_list_ccaa_with_discovery`: 10 → 11 CCAA con auto-discovery
- `test_get_total_municipios`: 3,537 → 4,231 municipios
- `test_get_metadata`: Metadatos globales actualizados

## Ejemplos de Uso

### Fecha fija (PAMPLONA):
```bash
$ python3 scrapers/ccaa/navarra/locales.py 2026 PAMPLONA
Festivos de PAMPLONA en 2026:
  - 2026-11-30: Fiesta local (original: '30 de noviembre')
```

### Fecha litúrgica (ARANTZA):
```bash
$ python3 scrapers/ccaa/navarra/locales.py 2026 ARANTZA
Festivos de ARANTZA en 2026:
  - 2026-02-14: Fiesta local (original: 'Viernes de carnaval')
    [calculada: liturgico_carnaval: viernes]
```

### Fecha santoral relativa (BAZTAN):
```bash
$ python3 scrapers/ccaa/navarra/locales.py 2026 BAZTAN
Festivos de BAZTAN en 2026:
  - 2026-10-23: Fiesta local (original: 'Viernes de la semana siguiente a San Lucas')
    [calculada: santoral_relativo: viernes siguiente a san lucas]
```

### Todos los municipios:
```bash
$ python3 scrapers/ccaa/navarra/locales.py 2026
✅ Extraídos festivos de 694 municipios
   • Fechas fijas: 655
   • Fechas calculadas: 39
```

## Reutilización del Módulo date_calculator

El módulo `scrapers/utils/date_calculator.py` está diseñado para ser reutilizable:

1. **Otras CCAA con fechas relativas**: Extremadura, Aragón, etc.
2. **Años futuros**: Funciona para cualquier año
3. **Extensible**: Fácil añadir nuevos patrones o santos

**Ejemplo de uso en otro scraper:**
```python
from scrapers.utils.date_calculator import calcular_fecha_relativa

resultado = calcular_fecha_relativa(2027, "Segundo viernes de septiembre")
if resultado:
    fecha, metodo = resultado
    print(f"Fecha: {fecha.strftime('%Y-%m-%d')}, Método: {metodo}")
```

## Particularidades de Navarra

1. **Estructura de festivos diferente**: 8 nacionales + 4 autonómicos + 1 local = 14 totales
   - La mayoría de CCAA: 8 + 4 + 2 = 14
   - Navarra: 8 + 4 + 1 = 13 (+ San Francisco Javier autonómico)

2. **Formato HTML**: Primera CCAA con tabla HTML directa (no PDF)

3. **Fechas relativas**: 5.6% de municipios usan fechas calculadas

4. **694 municipios**: Más que la mayoría de CCAA (solo Andalucía y Castilla y León tienen más)

## Próximos Pasos

El módulo `date_calculator.py` está listo para ser usado en:

- **Extremadura** (si tiene fechas relativas)
- **Aragón** (si tiene fechas relativas)
- **Castilla-La Mancha** (si tiene fechas relativas)
- **Castilla y León** (si tiene fechas relativas)

La implementación de Navarra sirve como referencia para otras CCAA con formato HTML y fechas relativas.

## Progreso del Proyecto

**CCAA Completadas: 13 de 17 (76.5%)**

✅ Implementadas:
1. Canarias (88 municipios)
2. Madrid (181 municipios)
3. Andalucía (746 municipios)
4. Valencia (542 municipios)
5. Baleares (67 municipios)
6. Cataluña (950 municipios)
7. Galicia (313 municipios)
8. País Vasco (251 municipios)
9. Asturias (78 municipios)
10. Cantabria (102 municipios)
11. La Rioja (164 municipios)
12. Murcia (45 municipios)
13. **Navarra (694 municipios)** ← NUEVA

⏳ Pendientes:
14. Extremadura (388 municipios)
15. Aragón (731 municipios)
16. Castilla-La Mancha (~900 municipios)
17. Castilla y León (2,248 municipios)

**Total municipios cubiertos: 4,231 de ~8,132 (52%)**
