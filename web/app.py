"""
Frontend web Flask para el Calendario Laboral de España.

Usa el motor de scraping del proyecto principal (ScraperFactory + CCAaRegistry)
para generar calendarios laborales personalizados con las 17 CCAA.
"""

import os
import sys
import uuid
import json
import tempfile
from pathlib import Path
from datetime import datetime

# Añadir raíz del monorepo al path para acceder a scrapers/, config/, etc.
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from flask import (
    Flask, render_template, request, jsonify,
    redirect, url_for, send_file
)

from web.utils.calendar_generator import CalendarGenerator
from web.analytics import log_generation, log_download, get_stats
from scrape_municipio import scrape_festivos_completos
from config.config_manager import CCAaRegistry

# ---------------------------------------------------------------------------
# App Flask
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = os.environ.get(
    'SECRET_KEY', 'dev-secret-key-super-importante-cambiar-en-produccion'
)
app.config['UMAMI_WEBSITE_ID'] = os.environ.get('UMAMI_WEBSITE_ID', '')

# ---------------------------------------------------------------------------
# CCAA dinámicas desde el registry (17 CCAA)
# ---------------------------------------------------------------------------
_registry = CCAaRegistry()
CCAA_SOPORTADAS = _registry.list_ccaa()

CCAA_NOMBRES = {}
for _code in CCAA_SOPORTADAS:
    _info = _registry.get_ccaa_info(_code)
    CCAA_NOMBRES[_code] = _info.get('name', _code.title()) if _info else _code.title()

# ---------------------------------------------------------------------------
# Sesiones temporales
# ---------------------------------------------------------------------------
SESSION_DIR = Path(__file__).parent / 'temp_sessions'
SESSION_DIR.mkdir(exist_ok=True)


# ===================================================================
# RUTAS
# ===================================================================

@app.route('/')
def landing():
    """Landing page principal"""
    ccaas = [
        {'value': ccaa, 'nombre': CCAA_NOMBRES.get(ccaa, ccaa.title())}
        for ccaa in CCAA_SOPORTADAS
    ]
    ccaas.sort(key=lambda x: x['nombre'])
    return render_template('landing.html', ccaas=ccaas)


@app.route('/generar', methods=['POST'])
def generar():
    """Procesa el formulario y genera el calendario"""
    try:
        municipio = request.form.get('municipio', '').strip()
        ccaa = request.form.get('ccaa', '').strip()
        year = int(request.form.get('year', 2026))

        if not municipio or not ccaa:
            return "Error: Faltan datos del formulario", 400

        if ccaa not in CCAA_SOPORTADAS:
            return f"Error: CCAA '{ccaa}' no soportada", 400

        session_id = str(uuid.uuid4())

        print(f"  Generando calendario: {municipio}, {ccaa}, {year}")
        data = scrape_festivos_completos(municipio, ccaa, year)

        if not data:
            return "Error: No se pudieron obtener los festivos", 500

        session_file = SESSION_DIR / f"{session_id}.json"
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump({
                'session_id': session_id,
                'municipio': municipio,
                'ccaa': ccaa,
                'ccaa_nombre': CCAA_NOMBRES.get(ccaa, ccaa.title()),
                'year': year,
                'data': data,
                'created_at': datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)

        print(f"  Calendario generado: {session_id}")

        try:
            log_generation(ccaa, municipio, year, session_id, request)
        except Exception:
            pass

        return redirect(url_for('calendario', session_id=session_id))

    except Exception as e:
        print(f"  Error generando calendario: {e}")
        import traceback
        traceback.print_exc()
        return f"Error: {str(e)}", 500


@app.route('/calendario/<session_id>')
def calendario(session_id):
    """Muestra el calendario generado"""
    session_file = SESSION_DIR / f"{session_id}.json"

    if not session_file.exists():
        return "Error: Sesion no encontrada o expirada", 404

    with open(session_file, 'r', encoding='utf-8') as f:
        session_data = json.load(f)

    return render_template('calendario.html', **session_data)


@app.route('/download-csv/<session_id>')
def download_csv(session_id):
    """Descarga festivos en formato CSV"""
    import pandas as pd

    session_file = SESSION_DIR / f"{session_id}.json"
    if not session_file.exists():
        return "Error: Sesion no encontrada", 404

    with open(session_file, 'r', encoding='utf-8') as f:
        session_data = json.load(f)

    try:
        festivos = session_data['data']['festivos']
        df = pd.DataFrame(festivos)

        columnas = ['fecha', 'fecha_texto', 'descripcion', 'tipo']
        if 'ambito' in df.columns:
            columnas.append('ambito')
        df = df[columnas]

        with tempfile.NamedTemporaryFile(
            delete=False, suffix='.csv', mode='w', encoding='utf-8'
        ) as tmp:
            csv_path = tmp.name
            df.to_csv(csv_path, index=False, encoding='utf-8')

        municipio_safe = session_data['municipio'].lower().replace(' ', '_')
        filename = f"festivos_{municipio_safe}_{session_data['year']}.csv"

        try:
            log_download(session_id, 'csv')
        except Exception:
            pass

        return send_file(
            csv_path,
            as_attachment=True,
            download_name=filename,
            mimetype='text/csv'
        )

    except Exception as e:
        print(f"  Error generando CSV: {e}")
        import traceback
        traceback.print_exc()
        return f"Error generando CSV: {str(e)}", 500


@app.route('/download/<session_id>', methods=['POST'])
def download(session_id):
    """Genera y descarga HTML con auto-print para PDF"""

    session_file = SESSION_DIR / f"{session_id}.json"
    if not session_file.exists():
        return "Error: Sesion no encontrada", 404

    with open(session_file, 'r', encoding='utf-8') as f:
        session_data = json.load(f)

    # === RECOGER DATOS DEL FORMULARIO ===
    empresa = request.form.get('empresa', '').strip()
    direccion = request.form.get('direccion', '').strip()
    horario_invierno = request.form.get('horario_invierno', '').strip()

    horario = {
        'invierno': horario_invierno,
        'tiene_verano': bool(request.form.get('tiene_verano'))
    }

    if horario['tiene_verano']:
        horario['verano'] = request.form.get('horario_verano', '').strip()
        verano_inicio = request.form.get('verano_inicio', '').strip()
        verano_fin = request.form.get('verano_fin', '').strip()
        if verano_inicio:
            horario['verano_inicio'] = datetime.strptime(verano_inicio, '%Y-%m-%d')
        if verano_fin:
            horario['verano_fin'] = datetime.strptime(verano_fin, '%Y-%m-%d')

    datos_opcionales = {'direccion': direccion}

    convenio = request.form.get('convenio', '').strip()
    if convenio:
        datos_opcionales['convenio'] = convenio

    num_patronal = request.form.get('num_patronal', '').strip()
    if num_patronal:
        datos_opcionales['num_patronal'] = num_patronal

    mutua = request.form.get('mutua', '').strip()
    if mutua:
        datos_opcionales['mutua'] = mutua

    try:
        generator = CalendarGenerator(
            year=session_data['year'],
            festivos=session_data['data']['festivos'],
            municipio=session_data['municipio'],
            ccaa=session_data['ccaa_nombre'],
            empresa=empresa,
            horario=horario,
            datos_opcionales=datos_opcionales
        )

        html_content = generator.generate_html()

        # Auto-print al abrir
        html_content = html_content.replace('</body>', '''
            <script>
            window.onload = function() {
                setTimeout(function() {
                    window.print();
                }, 500);
            };
            </script>
            </body>
        ''')

        with tempfile.NamedTemporaryFile(
            delete=False, suffix='.html', mode='w', encoding='utf-8'
        ) as tmp:
            tmp.write(html_content)
            html_path = tmp.name

        municipio_safe = session_data['municipio'].lower().replace(' ', '_')
        filename = f"calendario_{municipio_safe}_{session_data['year']}.html"

        try:
            log_download(session_id, 'pdf', has_empresa=bool(empresa))
        except Exception:
            pass

        return send_file(
            html_path,
            as_attachment=True,
            download_name=filename,
            mimetype='text/html'
        )

    except Exception as e:
        print(f"  Error generando calendario: {e}")
        import traceback
        traceback.print_exc()
        return f"Error: {str(e)}", 500


@app.route('/health')
def health():
    """Health check para Railway"""
    return jsonify({
        'status': 'ok',
        'ccaa_count': len(CCAA_SOPORTADAS),
    })


@app.route('/api/municipios/<ccaa>')
def api_municipios(ccaa):
    """API que devuelve municipios de una CCAA"""

    # Mapeo de nombres especiales de archivos
    FILENAME_MAP = {
        'canarias': 'canarias_municipios_islas.json',
    }

    filename = FILENAME_MAP.get(ccaa, f'{ccaa}_municipios.json')
    config_file = PROJECT_ROOT / 'config' / filename

    if not config_file.exists():
        return jsonify({'error': f'CCAA {ccaa} no encontrada'}), 404

    with open(config_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    municipios = []

    if isinstance(data, list):
        # Lista directa (ej. baleares)
        municipios = sorted(data)

    elif isinstance(data, dict):
        # Dict con valores string: {NORMALIZADO: display} (asturias, cantabria, rioja)
        if all(isinstance(v, str) for v in data.values()):
            municipios = sorted(data.values())

        # Dict con listas: {region: [municipios]} (canarias, madrid, cataluna, etc.)
        elif any(isinstance(v, list) for v in data.values()):
            for valores in data.values():
                if isinstance(valores, list):
                    municipios.extend(valores)
            municipios = sorted(set(municipios))

        # Dict con clave "municipios"
        elif 'municipios' in data:
            municipios = sorted(data['municipios'])

    return jsonify(municipios)


@app.route('/admin/stats')
def admin_stats():
    """Dashboard de estadísticas (protegido por ADMIN_SECRET)."""
    secret = request.args.get('key', '')
    expected = os.environ.get('ADMIN_SECRET', '')

    if not expected or secret != expected:
        return "Unauthorized", 401

    return jsonify(get_stats())


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)
