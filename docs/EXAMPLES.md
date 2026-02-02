# 📚 Ejemplos de Uso

## Casos de Uso Comunes

### 1. Obtener calendario completo de un municipio

```bash
# Canarias - Arrecife 2025
python3 scrape_municipio.py "Arrecife" canarias 2025

# Madrid - Alcala de Henares 2026
python3 scrape_municipio.py "Alcala de Henares" madrid 2026

# Aragon - Zaragoza 2026
python3 scrape_municipio.py "Zaragoza" aragon 2026

# Castilla y Leon - Valladolid 2026
python3 scrape_municipio.py "Valladolid" castilla_leon 2026

# Castilla-La Mancha - Toledo 2026
python3 scrape_municipio.py "Toledo" castilla_mancha 2026

# Extremadura - Badajoz 2026
python3 scrape_municipio.py "Badajoz" extremadura 2026

# Navarra - Pamplona 2026
python3 scrape_municipio.py "Pamplona" navarra 2026

# Pais Vasco - Vitoria-Gasteiz 2026
python3 scrape_municipio.py "Vitoria-Gasteiz" pais_vasco 2026

# Cataluña - Barcelona 2026
python3 scrape_municipio.py "Barcelona" cataluna 2026

# Andalucia - Sevilla 2026
python3 scrape_municipio.py "Sevilla" andalucia 2026
```

**Salida:**
- `data/canarias_arrecife_completo_2025.json`
- `data/canarias_arrecife_completo_2025.xlsx`

---

### 2. Solo festivos nacionales

```bash
python3 -m scrapers.core.boe_scraper 2025
```

**Salida:**
```json
{
  "year": 2025,
  "tipo": "nacionales",
  "total_festivos": 11,
  "festivos": [
    {
      "fecha": "2025-01-01",
      "descripcion": "Año Nuevo",
      "tipo": "nacional",
      ...
    }
  ]
}
```

---

### 3. Solo festivos autonomicos

```bash
# Canarias 2025
python3 -m scrapers.ccaa.canarias.autonomicos 2025

# Madrid 2026
python3 -m scrapers.ccaa.madrid.autonomicos 2026

# Navarra 2026
python3 -m scrapers.ccaa.navarra.autonomicos 2026
```

---

### 4. Solo festivos locales de un municipio

```bash
# Canarias - Santa Cruz de Tenerife
python3 -m scrapers.ccaa.canarias.locales "Santa Cruz de Tenerife" 2025

# Madrid - Madrid capital
python3 -m scrapers.ccaa.madrid.locales "Madrid" 2026
```

---

### 5. Multiples municipios (script bash)

```bash
#!/bin/bash
# Script para procesar varios municipios de diferentes CCAA

declare -A MUNICIPIOS=(
    ["Madrid,madrid"]="2026"
    ["Arrecife,canarias"]="2026"
    ["Zaragoza,aragon"]="2026"
    ["Sevilla,andalucia"]="2026"
    ["Barcelona,cataluna"]="2026"
    ["Valladolid,castilla_leon"]="2026"
)

for key in "${!MUNICIPIOS[@]}"; do
    IFS=',' read -r municipio ccaa <<< "$key"
    year="${MUNICIPIOS[$key]}"
    echo "Procesando: $municipio ($ccaa) $year"
    python3 scrape_municipio.py "$municipio" "$ccaa" "$year"
done
```

---

### 6. Comparar festivos entre municipios

```python
# compare_municipios.py
import json

def cargar_festivos(municipio, ccaa, year):
    filename = f"data/{ccaa}_{municipio.lower().replace(' ', '_')}_completo_{year}.json"
    with open(filename, 'r') as f:
        return json.load(f)

# Cargar datos
arrecife = cargar_festivos("Arrecife", "canarias", 2025)
tenerife = cargar_festivos("Santa Cruz de Tenerife", "canarias", 2025)

# Comparar
fechas_arrecife = {f['fecha'] for f in arrecife['festivos']}
fechas_tenerife = {f['fecha'] for f in tenerife['festivos']}

comunes = fechas_arrecife & fechas_tenerife
solo_arrecife = fechas_arrecife - fechas_tenerife
solo_tenerife = fechas_tenerife - fechas_arrecife

print(f"Festivos comunes: {len(comunes)}")
print(f"Solo Arrecife: {solo_arrecife}")
print(f"Solo Tenerife: {solo_tenerife}")
```

---

### 7. Exportar a calendario iCal

```python
# export_ical.py
import json
from icalendar import Calendar, Event
from datetime import datetime

def json_to_ical(json_file, ical_file):
    # Cargar JSON
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    # Crear calendario
    cal = Calendar()
    cal.add('prodid', '-//Calendario Laboral España//ES')
    cal.add('version', '2.0')
    
    # Añadir eventos
    for festivo in data['festivos']:
        event = Event()
        event.add('summary', festivo['descripcion'])
        event.add('dtstart', datetime.fromisoformat(festivo['fecha']))
        event.add('dtend', datetime.fromisoformat(festivo['fecha']))
        cal.add_component(event)
    
    # Guardar
    with open(ical_file, 'wb') as f:
        f.write(cal.to_ical())

# Usar
json_to_ical(
    'data/canarias_arrecife_completo_2025.json',
    'data/arrecife_2025.ics'
)
```

---

### 8. API Flask simple

```python
# api.py
from flask import Flask, jsonify
import subprocess
import json

app = Flask(__name__)

@app.route('/festivos/<ccaa>/<municipio>/<int:year>')
def get_festivos(ccaa, municipio, year):
    # Ejecutar scraper
    subprocess.run([
        'python', 'scrape_municipio.py',
        municipio, ccaa, str(year)
    ])
    
    # Cargar resultado
    filename = f"data/{ccaa}_{municipio.lower().replace(' ', '_')}_completo_{year}.json"
    with open(filename, 'r') as f:
        data = json.load(f)
    
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)
```

**Uso:**
```bash
python api.py

# En otro terminal:
curl http://localhost:5000/festivos/canarias/Arrecife/2025
```

---

### 9. Análisis de datos con pandas

```python
# analyze.py
import pandas as pd
import json

# Cargar datos
with open('data/canarias_arrecife_completo_2025.json', 'r') as f:
    data = json.load(f)

# Crear DataFrame
df = pd.DataFrame(data['festivos'])
df['fecha'] = pd.to_datetime(df['fecha'])
df['mes'] = df['fecha'].dt.month
df['dia_semana'] = df['fecha'].dt.day_name()

# Análisis
print("Festivos por mes:")
print(df['mes'].value_counts().sort_index())

print("\nFestivos por día de semana:")
print(df['dia_semana'].value_counts())

print("\nFestivos por tipo:")
print(df['tipo'].value_counts())

# Visualización
import matplotlib.pyplot as plt

df['mes'].value_counts().sort_index().plot(kind='bar')
plt.title('Festivos por mes - Arrecife 2025')
plt.xlabel('Mes')
plt.ylabel('Número de festivos')
plt.savefig('festivos_por_mes.png')
```

---

### 10. Generar informe HTML

```python
# generate_report.py
import json
from jinja2 import Template

# Template HTML
template_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Calendario Laboral {{ municipio }} {{ year }}</title>
    <style>
        body { font-family: Arial; margin: 40px; }
        h1 { color: #333; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #4CAF50; color: white; }
        .nacional { background-color: #e3f2fd; }
        .autonomico { background-color: #fff3e0; }
        .local { background-color: #f3e5f5; }
    </style>
</head>
<body>
    <h1>Calendario Laboral {{ municipio }}, {{ ccaa|upper }} {{ year }}</h1>
    <p>Total festivos: <strong>{{ total_festivos }}</strong></p>
    
    <table>
        <tr>
            <th>Fecha</th>
            <th>Descripción</th>
            <th>Tipo</th>
        </tr>
        {% for festivo in festivos %}
        <tr class="{{ festivo.tipo }}">
            <td>{{ festivo.fecha }}</td>
            <td>{{ festivo.descripcion }}</td>
            <td>{{ festivo.tipo|upper }}</td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""

# Cargar datos
with open('data/canarias_arrecife_completo_2025.json', 'r') as f:
    data = json.load(f)

# Generar HTML
template = Template(template_html)
html = template.render(**data)

# Guardar
with open('data/arrecife_2025.html', 'w') as f:
    f.write(html)

print("Informe generado: data/arrecife_2025.html")
```

---

### 11. Integración con Google Calendar

```python
# google_calendar_integration.py
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import json
from datetime import datetime

def add_to_google_calendar(json_file, calendar_id='primary'):
    # Cargar credenciales (requiere setup previo)
    creds = Credentials.from_authorized_user_file('token.json')
    service = build('calendar', 'v3', credentials=creds)
    
    # Cargar festivos
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    # Añadir eventos
    for festivo in data['festivos']:
        event = {
            'summary': festivo['descripcion'],
            'start': {'date': festivo['fecha']},
            'end': {'date': festivo['fecha']},
            'description': f"Festivo {festivo['tipo']} - {data['municipio']}"
        }
        
        service.events().insert(calendarId=calendar_id, body=event).execute()
        print(f"Añadido: {festivo['fecha']} - {festivo['descripcion']}")

# Usar
add_to_google_calendar('data/canarias_arrecife_completo_2025.json')
```

---

### 12. Notificaciones por email

```python
# email_festivos.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
from datetime import datetime, timedelta

def enviar_recordatorios(json_file, email_destino, dias_anticipacion=7):
    # Cargar festivos
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    # Filtrar próximos festivos
    hoy = datetime.now().date()
    proximos = [
        f for f in data['festivos']
        if 0 <= (datetime.fromisoformat(f['fecha']).date() - hoy).days <= dias_anticipacion
    ]
    
    if not proximos:
        print("No hay festivos próximos")
        return
    
    # Crear email
    msg = MIMEMultipart()
    msg['Subject'] = f"Próximos festivos en {data['municipio']}"
    msg['From'] = 'tu_email@gmail.com'
    msg['To'] = email_destino
    
    body = "Próximos festivos:\n\n"
    for f in proximos:
        body += f"• {f['fecha']} - {f['descripcion']}\n"
    
    msg.attach(MIMEText(body, 'plain'))
    
    # Enviar
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login('tu_email@gmail.com', 'tu_password')
        server.send_message(msg)
    
    print(f"Email enviado a {email_destino}")

# Usar
enviar_recordatorios(
    'data/canarias_arrecife_completo_2025.json',
    'destinatario@example.com',
    dias_anticipacion=7
)
```

---

### 13. Dashboard con Streamlit

El proyecto incluye un dashboard completo en `app.py`:

```bash
streamlit run app.py
```

Soporta las 17 CCAA con selector dinamico de municipios.
La lista de CCAA se carga automaticamente desde `ccaa_registry.yaml`.

---

### 14. Webhook para notificaciones

```python
# webhook_festivos.py
from flask import Flask, request
import json

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    
    # Procesar municipio
    municipio = data.get('municipio')
    ccaa = data.get('ccaa')
    year = data.get('year')
    
    # Ejecutar scraper
    subprocess.run([
        'python', 'scrape_municipio.py',
        municipio, ccaa, str(year)
    ])
    
    # Cargar resultado
    filename = f"data/{ccaa}_{municipio.lower().replace(' ', '_')}_completo_{year}.json"
    with open(filename, 'r') as f:
        festivos = json.load(f)
    
    # Enviar a Slack/Discord/etc
    # ...
    
    return {'status': 'success', 'festivos': festivos['total_festivos']}

if __name__ == '__main__':
    app.run(port=5001)
```

---

### 15. Automatización con cron

```bash
# Script: update_festivos.sh
#!/bin/bash

YEAR=$(date +%Y)
NEXT_YEAR=$((YEAR + 1))

# Actualizar festivos para año siguiente
python3 scrape_municipio.py "Arrecife" canarias $NEXT_YEAR
python3 scrape_municipio.py "Madrid" madrid $NEXT_YEAR

# Enviar notificación
python email_festivos.py
```

**Crontab:**
```bash
# Ejecutar cada 1 de enero a las 9:00 AM
0 9 1 1 * /path/to/update_festivos.sh
```

---

## Tips y Trucos

### Depuración

```bash
# Ver solo municipios disponibles
python -m scrapers.ccaa.madrid.locales "Madrid" 2026 | grep "municipios encontrados"

# Ver cache actual
cat config/canarias_urls_cache.json | jq .

# Limpiar cache
echo '{"autonomicos": {}, "locales": {}}' > config/canarias_urls_cache.json
```

### Performance

```python
# Procesamiento paralelo con concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import subprocess

municipios = ["Arrecife", "Santa Cruz", "Las Palmas"]

def procesar(municipio):
    subprocess.run(['python', 'scrape_municipio.py', municipio, 'canarias', '2025'])

with ThreadPoolExecutor(max_workers=3) as executor:
    executor.map(procesar, municipios)
```

### Validación

```python
# Validar que tenga exactamente 14 festivos
import json

with open('data/canarias_arrecife_completo_2025.json', 'r') as f:
    data = json.load(f)

assert data['total_festivos'] == 14, f"Expected 14, got {data['total_festivos']}"
assert len(data['festivos']) == 14, "Mismatch in count"

print("✅ Validación pasada")
```
