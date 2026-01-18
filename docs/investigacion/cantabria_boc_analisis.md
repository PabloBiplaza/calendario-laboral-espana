# Investigación: BOC de Cantabria - Festivos Locales

**Fecha de investigación**: 17/01/2026
**Investigado por**: Claude Code

---

## 1. URL Oficial del BOC

**URL principal**: https://boc.cantabria.es/boces/

El Boletín Oficial de Cantabria (BOC) es completamente electrónico desde el 1 de enero de 2010. Es un servicio público de acceso universal gratuito que garantiza el derecho de acceso a los documentos publicados.

---

## 2. Cómo Publican los Festivos Locales

### Documentos Encontrados (URLs Reales)

| Año | URL del Documento | Archivo PDF | Tamaño | Fecha Publicación |
|-----|------------------|-------------|--------|-------------------|
| 2026 | [idAnuBlob=428192](https://boc.cantabria.es/boces/verAnuncioAction.do?idAnuBlob=428192) | 2025-10276.pdf | 445KB | 02/12/2025 |
| 2025 | [idAnuBlob=423185](https://boc.cantabria.es/boces/verAnuncioAction.do?idAnuBlob=423185) | 2025-6591.pdf | 334KB | Mayo/Junio 2025 |
| 2024 | [idAnuBlob=407917](https://boc.cantabria.es/boces/verAnuncioAction.do?idAnuBlob=407917) | 2024-6339.pdf | 225KB | Agosto 2024 |
| 2023 | [idAnuBlob=392673](https://boc.cantabria.es/boces/verAnuncioAction.do?idAnuBlob=392673) | 2023-7293.pdf | 258KB | 17/08/2023 |

### Características de la Publicación

- **Organismo emisor**: Dirección General de Trabajo, Economía Social y Empleo Autónomo
- **Tipo de documento**: Resolución oficial
- **Título típico**: "Resolución [...] por la que se publica el calendario de fiestas laborales de la Comunidad Autónoma de Cantabria para el año [XXXX]"
- **Contenido**: Calendario de fiestas nacionales, autonómicas y locales
- **Periodicidad**: Anual (normalmente publicado en diciembre del año anterior, pero puede haber actualizaciones)

---

## 3. Formato de Publicación

**Formato principal**: PDF

- Documentos PDF firmados digitalmente
- Descarga directa mediante URL: `https://boc.cantabria.es/boces/verAnuncioAction.do?idAnuBlob={ID}`
- Headers HTTP:
  ```
  Content-Type: application/pdf
  Content-disposition: inline; filename=XXXX-XXXX.pdf
  ```

**NO hay**:
- Formato HTML estructurado
- Formato XML/JSON oficial
- API REST pública

---

## 4. Sistema de Búsqueda y Auto-Discovery

### A. Buscador Oficial

**URL del buscador**: https://boc.cantabria.es/boces/inicioBusquedaAnuncios.do

**Parámetros de búsqueda**:
- Texto libre (búsqueda en entradilla o cuerpo del anuncio)
- Fecha de publicación (rango desde-hasta)
- Tipo de BOC (Ordinario/Extraordinario)
- Filtros: todas las palabras, algunas palabras, texto exacto

**Términos de búsqueda efectivos**:
- "festivos locales"
- "fiestas locales"
- "calendario laboral"
- "Dirección General de Trabajo"

### B. RSS Feeds

Cantabria proporciona 17 feeds RSS diferentes por categorías del BOC.

**Feed principal para festivos**:
- URL: http://www.cantabria.es/o/BOC/feed/6802081
- Categoría: "1. Disposiciones Generales"
- Formato: XML/RSS 2.0
- Contenido: últimos 100 anuncios

**Otros feeds disponibles**:
- Página con todos los feeds: https://www.cantabria.es/enlaces_rss
- 17 categorías diferentes (personal, contratación, subvenciones, urbanismo, etc.)

### C. Método de Auto-Discovery Recomendado

**Opción 1: Scraping del Buscador**
```python
# Pseudocódigo
1. POST a https://boc.cantabria.es/boces/inicioBusquedaAnuncios.do
2. Parámetros:
   - texto: "festivos locales"
   - fecha_desde: "01/11/{año-1}"
   - fecha_hasta: "31/12/{año-1}"
3. Parsear resultados HTML
4. Filtrar por "Dirección General de Trabajo"
5. Extraer idAnuBlob del resultado más reciente
6. Descargar PDF
```

**Opción 2: Monitoreo RSS Feed**
```python
# Pseudocódigo
1. Fetch http://www.cantabria.es/o/BOC/feed/6802081
2. Parsear XML
3. Buscar <title> que contenga "festivos" o "calendario laboral"
4. Filtrar por <categorias> que contenga "Dirección General de Trabajo"
5. Extraer <link> para obtener idAnuBlob
6. Descargar PDF
```

**Opción 3: Búsqueda Web Programática**
```python
# Usar motor de búsqueda con site:
site:boc.cantabria.es "festivos locales" {año} "Dirección General de Trabajo"
```

---

## 5. Estructura de la Información

### Organización del Documento

**Estructura**: Documento único PDF que contiene TODOS los municipios de Cantabria

**Formato de la tabla** (según búsquedas web):
```
| Municipio (Ayuntamiento) | Festividad | Día | Mes |
|--------------------------|------------|-----|-----|
| Alfoz de Lloredo         | San Isidro Labrador | 15 | Mayo |
| Alfoz de Lloredo         | Santa Ana | 27 | Julio |
| Ampuero                  | Natividad de Ntra Sra Virgen Niña | 8 | Septiembre |
| Ampuero                  | San Mateo | 21 | Septiembre |
```

**Características**:
- Cada municipio tiene exactamente 2 festivos locales
- Orden alfabético por municipio
- Formato de fecha: Día (número) + Mes (texto)
- Nombre completo de la festividad incluido

**Secciones del documento**:
1. Resolución oficial (cabecera)
2. Festivos nacionales (lista)
3. Festivos autonómicos de Cantabria (lista)
4. Tabla de festivos locales por municipio (tabla completa)

---

## 6. Ejemplos de URLs de Documentos Reales

### 2026 (Publicado 02/12/2025)
```
https://boc.cantabria.es/boces/verAnuncioAction.do?idAnuBlob=428192
```
**Contenido**: Calendario completo 2026 con todos los municipios

### 2025 (Actualizado en mayo/junio 2025)
```
https://boc.cantabria.es/boces/verAnuncioAction.do?idAnuBlob=423185
```
**Contenido**: Calendario completo 2025 con todos los municipios

### 2024
```
https://boc.cantabria.es/boces/verAnuncioAction.do?idAnuBlob=407917
```
**Contenido**: Calendario completo 2024 con todos los municipios

### 2023 (Publicado 17/08/2023)
```
https://boc.cantabria.es/boces/verAnuncioAction.do?idAnuBlob=392673
```
**Contenido**: Calendario completo 2023 con todos los municipios

---

## 7. Viabilidad de Auto-Discovery

### Calificación: **MEDIA-ALTA** ⭐⭐⭐⭐

### Ventajas ✅

1. **Formato consistente**: PDF con tabla de municipios, estructura predecible
2. **Documento único**: Un solo PDF por año con TODOS los municipios (no hay que buscar 102 documentos)
3. **RSS feeds disponibles**: Sistema de notificaciones automáticas
4. **Buscador funcional**: Permite búsquedas programáticas por texto y fecha
5. **Organismo emisor consistente**: Siempre la Dirección General de Trabajo
6. **PDFs firmados digitalmente**: Garantía de autenticidad

### Desventajas ❌

1. **No hay patrón en idAnuBlob**: IDs no son secuenciales ni predecibles
   - 2023: 392673
   - 2024: 407917
   - 2025: 423185
   - 2026: 428192

2. **Fechas de publicación variables**: No hay un día fijo
   - 2023: Agosto
   - 2024: Agosto (estimado)
   - 2025: Mayo/Junio (actualización posterior)
   - 2026: Diciembre 2025

3. **No hay API REST oficial**: Requiere scraping HTML/RSS

4. **Posibles actualizaciones**: El documento puede ser republicado/actualizado

5. **Parsing de PDF necesario**: Requiere OCR o extracción de texto estructurado

---

## 8. Comparación con Otras CCAA

### Similar a:
- **Madrid**: También publica documento único con todos los municipios
- **Andalucía**: RSS feeds disponibles, PDFs por municipio
- **Galicia**: Datos estructurados en RDF

### Mejor que:
- **Canarias**: Cantabria tiene documento consolidado, Canarias tiene PDFs dispersos
- **Asturias**: Más organizado que Asturias (anuncios individuales)

### Peor que:
- **País Vasco**: No tiene datos estructurados como OpenData Euskadi
- **Galicia**: No tiene RDF/SPARQL endpoint

---

## 9. Estrategia Recomendada de Implementación

### Fase 1: Discovery
```python
def discover_cantabria_festivos(year):
    # Opción A: RSS Feed
    feed_url = "http://www.cantabria.es/o/BOC/feed/6802081"
    items = parse_rss(feed_url)

    for item in items:
        if "festivos locales" in item.title.lower() or \
           "calendario laboral" in item.title.lower():
            if str(year) in item.title:
                return extract_id_from_url(item.link)

    # Opción B: Web Search
    results = search_web(f"site:boc.cantabria.es festivos locales {year}")
    return extract_id_from_first_result(results)
```

### Fase 2: Descarga
```python
def download_pdf(id_anu_blob):
    url = f"https://boc.cantabria.es/boces/verAnuncioAction.do?idAnuBlob={id_anu_blob}"
    pdf_content = download(url)
    return pdf_content
```

### Fase 3: Parsing
```python
def parse_cantabria_pdf(pdf_path):
    # Usar pdfplumber, PyPDF2, o tabula-py
    text = extract_text(pdf_path)

    # Buscar sección "FESTIVOS LOCALES" o tabla de municipios
    municipios = []

    # Regex para extraer: Municipio | Festividad | Día | Mes
    pattern = r"([A-ZÁÉÍÓÚ][a-záéíóúñ\s]+)\s+\|\s+([A-Za-záéíóúñ\s\.]+)\s+\|\s+(\d{1,2})\s+\|\s+([A-Za-z]+)"

    matches = re.findall(pattern, text)

    for municipio, festividad, dia, mes in matches:
        municipios.append({
            "municipio": municipio.strip(),
            "festividad": festividad.strip(),
            "fecha": f"{dia} de {mes}"
        })

    return group_by_municipio(municipios)
```

### Fase 4: Almacenamiento
```python
# Guardar en formato JSON estructurado
{
    "comunidad_autonoma": "Cantabria",
    "year": 2026,
    "fuente": "BOC - Dirección General de Trabajo",
    "url_documento": "https://boc.cantabria.es/boces/verAnuncioAction.do?idAnuBlob=428192",
    "fecha_publicacion": "2025-12-02",
    "municipios": [
        {
            "nombre": "Alfoz de Lloredo",
            "festivos": [
                {"fecha": "2026-05-15", "nombre": "San Isidro Labrador"},
                {"fecha": "2026-07-27", "nombre": "Santa Ana"}
            ]
        },
        ...
    ]
}
```

---

## 10. Conclusiones y Próximos Pasos

### Conclusiones

1. **Es viable implementar auto-discovery para Cantabria** similar a Madrid, Valencia, o Andalucía
2. **El formato es consistente y predecible** (documento único anual)
3. **Hay múltiples métodos de discovery** (RSS, buscador, web search)
4. **Requiere parsing de PDF** pero el formato es estructurado (tabla)

### Próximos Pasos

1. ✅ **Investigación completada**
2. ⏭️ Implementar scraper en `/scrapers/discovery/boc_cantabria_discovery.py`
3. ⏭️ Implementar parser de PDF en `/scrapers/parsers/cantabria_pdf_parser.py`
4. ⏭️ Crear configuración en `/config/cantabria_municipios.json`
5. ⏭️ Integrar en la aplicación Streamlit
6. ⏭️ Añadir tests

### Estimación de Esfuerzo

- **Discovery script**: 2-3 horas
- **PDF parser**: 3-4 horas (depende de la complejidad del PDF)
- **Integración**: 1-2 horas
- **Tests**: 1-2 horas

**Total estimado**: 7-11 horas

---

## Referencias

- [BOC Cantabria - Sitio Oficial](https://boc.cantabria.es/boces/)
- [BOC - Buscador de Anuncios](https://boc.cantabria.es/boces/inicioBusquedaAnuncios.do)
- [Cantabria - Enlaces RSS](https://www.cantabria.es/enlaces_rss)
- [BOC - Wikipedia](https://es.wikipedia.org/wiki/Bolet%C3%ADn_Oficial_de_Cantabria)
