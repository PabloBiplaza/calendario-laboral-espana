# Análisis de Fechas Relativas en Navarra

## Resumen

De los **694 municipios** de Navarra, encontramos:
- **655 (94.4%)** usan fechas fijas (ej: "22 de enero")
- **39 (5.6%)** usan fechas relativas/calculadas

## Categorías de Fechas Relativas

### 1. Ordinales + Día de la semana (28 casos - 71.8%)

Patrón: "Primer/Segundo/Tercer/Cuarto/Último + día_semana + de + mes"

**Ejemplos:**
- "Lunes siguiente al primer domingo de mayo" (13 municipios)
- "Tercer sábado de septiembre" (3 municipios)
- "Segundo viernes de septiembre"
- "Cuarto viernes de julio"
- "Último viernes de septiembre"
- "Primer sábado de septiembre"
- "Segundo lunes de agosto"
- "Viernes anterior al tercer domingo de septiembre"

**Lista completa:**
1. AMATRIAIN → Lunes siguiente al primer domingo de mayo
2. AMUNARRIZQUETA → Lunes siguiente al primer domingo de mayo
3. ANSOÁIN → Viernes anterior al tercer domingo de septiembre
4. ARAMENDÍA (Allín) → Tercer sábado de septiembre
5. ARBEIZA (Allín) → Tercer sábado de agosto
6. ARTARIAIN → Lunes siguiente al primer domingo de mayo
7. ARTAVIA → Primer sábado de septiembre
8. ARTAZA → Segundo lunes de agosto
9. ASARTA → Tercer sábado de septiembre
10. BAQUEDANO → Segundo viernes de septiembre
11. BARÍNDANO → Cuarto viernes de julio
12. BENEGORRI → Lunes siguiente al primer domingo de mayo
13. BÉZQUIZ (Leoz) → Lunes siguiente al primer domingo de mayo
14. ECALA (Améscoa Baja) → Último viernes de septiembre
15. ETSAIN (Anue) → Primer sábado de agosto
16. EULZ → Primer sábado de septiembre
17. GANUZA (Metauten) → Tercer sábado de septiembre
18. HUARTE → Tercer lunes de septiembre
19. IRACHETA (Leoz) → Lunes siguiente al primer domingo de mayo
20. LARRAYOZ → Primer lunes de septiembre
21. LEOZ → Lunes siguiente al primer domingo de mayo
22. MAQUIRRIAIN (Leoz) → Lunes siguiente al primer domingo de mayo
23. MUNETA (Allín) → Segundo sábado de septiembre
24. OLLETA → Lunes siguiente al primer domingo de mayo
25. SAN MARTÍN DE AMESCOA → Segundo viernes de noviembre
26. SANSOÁIN → Lunes siguiente al primer domingo de mayo
27. SANSOMAIN → Lunes siguiente al primer domingo de mayo
28. UBAGO (Mendaza) → Primer sábado de octubre
29. UZQUITA → Lunes siguiente al primer domingo de mayo

### 2. Fechas Litúrgicas (4 casos - 10.3%)

Patrón: Festividades religiosas móviles

**Ejemplos:**
- "Viernes de carnaval" → ARANTZA
- "Martes de carnaval" → ETXALAR, GOIZUETA
- "Lunes de carnaval" → ITUREN
- "Lunes de Pentecostés" → BURGUI, MENDAVIA, URDAZUBI/URDAX
- "Segundo día de Pentecostés" → SANSOL
- "Festividad de la Ascensión" → ERANSUS (Egüés)

**Lista completa:**
1. ARANTZA → Viernes de carnaval
2. BURGUI → Lunes de Pentecostés
3. ERANSUS (Egüés) → Festividad de la Ascensión
4. ETXALAR → Martes de carnaval
5. GOIZUETA → Martes de carnaval
6. ITUREN → Lunes de carnaval
7. MENDAVIA → Lunes de Pentecostés
8. SANSOL → Segundo día de Pentecostés
9. URDAZUBI / URDAX → Lunes de Pentecostés

### 3. Relativo a Santoral (1 caso - 2.6%)

Patrón: Relativo a día de santo

**Ejemplo:**
- "Viernes de la semana siguiente a San Lucas" → BAZTAN

### 4. Otros (6 casos - 15.4%)

Estos son casos categorizados como "otro" que en realidad son variantes de ordinales:
- "Lunes siguiente al primer domingo de mayo" (ya contabilizados arriba)

## Estrategia de Implementación

### Fase 1: Soporte para Ordinales (71.8% de casos relativos)

Implementar función para calcular:
- Primer/Segundo/Tercer/Cuarto/Último + día_semana + de + mes
- Variante: "día_semana anterior/siguiente al Nth día_semana de mes"

**Algoritmo:**
1. Encontrar todos los días de la semana objetivo en el mes
2. Seleccionar el Nth (1º, 2º, 3º, 4º, último)
3. Si tiene modificador "anterior/siguiente", ajustar

### Fase 2: Soporte para Fechas Litúrgicas (10.3% de casos relativos)

Implementar función para calcular fechas móviles:
- **Carnaval**: 47 días antes de Pascua
  - Lunes de carnaval: -47 días
  - Martes de carnaval: -46 días
  - Viernes de carnaval: -49 días
- **Pascua**: Algoritmo de Gauss (base para cálculos)
- **Pentecostés**: 50 días después de Pascua
  - Lunes de Pentecostés: +50 días
  - Segundo día de Pentecostés: +51 días
- **Ascensión**: 39 días después de Pascua

### Fase 3: Soporte para Santoral (2.6% de casos relativos)

Implementar para San Lucas (18 de octubre):
- "Viernes de la semana siguiente a San Lucas" → Primer viernes después del 18 de octubre

## Prioridad de Implementación

1. **Alta prioridad** (71.8% cobertura): Ordinales + día de semana
2. **Media prioridad** (10.3% cobertura): Fechas litúrgicas (Carnaval, Pentecostés, Ascensión)
3. **Baja prioridad** (2.6% cobertura): Santoral relativo

## Dependencias

- `dateutil.easter` para calcular Pascua
- `calendar` (stdlib) para operaciones con días de la semana
- Crear módulo `scrapers/utils/date_calculator.py` con todas las funciones

## Patrones Regex Necesarios

```python
# Ordinales simples
r'(Primer|Segundo|Tercer|Cuarto|Último)\s+(lunes|martes|miércoles|jueves|viernes|sábado|domingo)\s+de\s+(\w+)'

# Ordinales con modificador anterior/siguiente
r'(lunes|martes|...|domingo)\s+(anterior|siguiente)\s+al\s+(primer|segundo|...)\s+(domingo|...)\s+de\s+(\w+)'

# Litúrgicos
r'(Lunes|Martes|Miércoles|Jueves|Viernes|Sábado|Domingo)\s+de\s+carnaval'
r'(Lunes|Segundo día)\s+de\s+Pentecostés'
r'Festividad de la Ascensión'

# Santoral relativo
r'(\w+)\s+de\s+la\s+semana\s+siguiente\s+a\s+San\s+(\w+)'
```

## Archivo de Salida Propuesto

Para facilitar el debugging, el parser de Navarra debe generar:

```json
{
  "ABANILLA": [
    {
      "fecha": "2026-01-22",
      "descripcion": "Fiesta local",
      "fecha_original": "22 de enero",
      "calculada": false
    }
  ],
  "ARANTZA": [
    {
      "fecha": "2026-02-13",
      "descripcion": "Fiesta local",
      "fecha_original": "Viernes de carnaval",
      "calculada": true,
      "metodo": "liturgico_carnaval"
    }
  ]
}
```
