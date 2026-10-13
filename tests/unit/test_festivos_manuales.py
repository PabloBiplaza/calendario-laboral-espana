"""Tests de festivos añadidos manualmente (lógica + rutas web)"""

import json
import sys
import uuid
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from web.festivos_manuales import (  # noqa: E402
    FestivoInvalido, crear_festivo_manual, eliminar_festivo_manual,
    combinar_festivos, contar_festivos,
)

OFICIALES = [
    {'fecha': '2027-01-01', 'fecha_texto': '1 de enero', 'descripcion': 'Año Nuevo', 'tipo': 'nacional'},
    {'fecha': '2027-03-19', 'fecha_texto': '19 de marzo', 'descripcion': 'San José', 'tipo': 'autonomico'},
]


def _crear(**kwargs):
    datos = dict(fecha='2027-05-15', descripcion='San Isidro', tipo='local',
                 etiqueta='', year=2027, existentes=[])
    datos.update(kwargs)
    return crear_festivo_manual(**datos)


# --- Validación ---

def test_crear_festivo_valido():
    f = _crear()
    assert f['fecha'] == '2027-05-15'
    assert f['fecha_texto'] == '15 de mayo'
    assert f['tipo'] == 'local'
    assert f['origen'] == 'manual'
    assert 'etiqueta' not in f
    assert f['id']


def test_permite_fin_de_semana():
    # 15/05/2027 es sábado: debe aceptarse
    assert _crear(fecha='2027-05-15')['fecha'] == '2027-05-15'


def test_empresa_con_etiqueta():
    f = _crear(tipo='empresa', descripcion='  Aniversario   empresa ', etiqueta='Convenio')
    assert f['descripcion'] == 'Aniversario empresa'
    assert f['etiqueta'] == 'Convenio'
    assert f['ambito'] == 'empresa'


@pytest.mark.parametrize('kwargs, mensaje', [
    ({'fecha': '2027-02-30'}, 'fecha no es válida'),
    ({'fecha': 'mañana'}, 'fecha no es válida'),
    ({'fecha': '2026-05-15'}, 'año 2027'),
    ({'descripcion': '   '}, 'descripción'),
    ({'descripcion': 'x' * 81}, '80 caracteres'),
    ({'tipo': 'inventado'}, 'tipo'),
    ({'etiqueta': 'x' * 41}, '40 caracteres'),
])
def test_rechaza_datos_invalidos(kwargs, mensaje):
    with pytest.raises(FestivoInvalido, match=mensaje):
        _crear(**kwargs)


def test_rechaza_dos_manuales_mismo_dia():
    existente = _crear()
    with pytest.raises(FestivoInvalido, match='Ya has añadido'):
        _crear(existentes=[existente])


# --- Combinación con los oficiales ---

def test_combinar_ordena_y_sustituye():
    manual = _crear(fecha='2027-03-19', descripcion='Fiesta propia', tipo='empresa')
    combinados = combinar_festivos(OFICIALES, [manual, _crear()])

    assert [f['fecha'] for f in combinados] == ['2027-01-01', '2027-03-19', '2027-05-15']
    sustituido = combinados[1]
    assert sustituido['descripcion'] == 'Fiesta propia'
    assert sustituido['sustituye'] == 'San José'
    # Los oficiales originales no se modifican
    assert OFICIALES[1]['descripcion'] == 'San José'


def test_eliminar_restaura_oficial():
    manual = _crear(fecha='2027-03-19', descripcion='Fiesta propia')
    restantes, encontrado = eliminar_festivo_manual([manual], manual['id'])
    assert encontrado and restantes == []
    assert combinar_festivos(OFICIALES, restantes)[1]['descripcion'] == 'San José'


def test_contar_separa_empresa():
    combinados = combinar_festivos(OFICIALES, [_crear(tipo='empresa', fecha='2027-08-16')])
    assert contar_festivos(combinados) == {'laborales': 2, 'empresa': 1}


# --- Rutas web ---

@pytest.fixture
def sesion(tmp_path, monkeypatch):
    pytest.importorskip('flask')
    import web.app as web_app

    monkeypatch.setattr(web_app, 'SESSION_DIR', tmp_path)
    session_id = str(uuid.uuid4())
    datos = {
        'session_id': session_id, 'municipio': 'Madrid', 'ccaa': 'madrid',
        'ccaa_nombre': 'Madrid', 'year': 2027, 'status': 'done',
        'data': {'municipio': 'Madrid', 'year': 2027, 'total_festivos': 2,
                 'festivos': [dict(f) for f in OFICIALES]},
    }
    (tmp_path / f'{session_id}.json').write_text(json.dumps(datos), encoding='utf-8')
    web_app.app.config['TESTING'] = True
    return web_app.app.test_client(), session_id, tmp_path


def _leer(tmp_path, session_id):
    return json.loads((tmp_path / f'{session_id}.json').read_text(encoding='utf-8'))


def test_ruta_anadir_y_eliminar(sesion):
    client, sid, tmp_path = sesion

    r = client.post(f'/calendario/{sid}/festivos', data={
        'fecha': '2027-05-15', 'descripcion': 'San Isidro', 'tipo': 'local'})
    assert r.status_code == 302
    manuales = _leer(tmp_path, sid)['festivos_manuales']
    assert len(manuales) == 1

    pagina = client.get(f'/calendario/{sid}').get_data(as_text=True)
    assert 'San Isidro' in pagina
    assert 'Añadido manualmente' in pagina
    # Ya hay un local: no debe salir el aviso de locales pendientes
    assert 'No hemos encontrado los festivos locales' not in pagina

    r = client.post(f"/calendario/{sid}/festivos/{manuales[0]['id']}/eliminar")
    assert r.status_code == 302
    assert _leer(tmp_path, sid)['festivos_manuales'] == []


def test_ruta_rechaza_invalido_con_mensaje(sesion):
    client, sid, tmp_path = sesion
    r = client.post(f'/calendario/{sid}/festivos', data={
        'fecha': '2026-05-15', 'descripcion': 'X', 'tipo': 'local'}, follow_redirects=True)
    assert 'La fecha debe ser del año 2027.' in r.get_data(as_text=True)
    assert 'festivos_manuales' not in _leer(tmp_path, sid)


def test_aviso_si_faltan_locales(sesion):
    client, sid, _ = sesion
    pagina = client.get(f'/calendario/{sid}').get_data(as_text=True)
    assert 'No hemos encontrado los festivos locales' in pagina


def test_texto_escapado_en_vista_y_pdf(sesion):
    client, sid, _ = sesion
    client.post(f'/calendario/{sid}/festivos', data={
        'fecha': '2027-08-16', 'descripcion': '<script>alert(1)</script>', 'tipo': 'empresa'})

    pagina = client.get(f'/calendario/{sid}').get_data(as_text=True)
    assert '<script>alert(1)</script>' not in pagina

    pdf = client.post(f'/download/{sid}', data={
        'empresa': 'ACME', 'direccion': 'C/ X', 'horario_invierno': '9-14'}).get_data(as_text=True)
    assert '<script>alert(1)</script>' not in pdf
    assert 'DÍAS NO LABORABLES DE EMPRESA' in pdf
    assert 'Total festivos: 2 | Días de empresa: 1' in pdf


def test_csv_incluye_manuales(sesion):
    client, sid, _ = sesion
    client.post(f'/calendario/{sid}/festivos', data={
        'fecha': '2027-08-16', 'descripcion': 'Cierre', 'tipo': 'empresa', 'etiqueta': 'Verano'})
    csv = client.get(f'/download-csv/{sid}').get_data(as_text=True)
    assert 'etiqueta' in csv.splitlines()[0]
    assert '2027-08-16' in csv and 'Verano' in csv and 'manual' in csv


def test_xlsx_incluye_oficiales_y_manuales(sesion):
    import io
    from openpyxl import load_workbook

    client, sid, _ = sesion
    client.post(f'/calendario/{sid}/festivos', data={
        'fecha': '2027-08-16', 'descripcion': 'Cierre', 'tipo': 'empresa', 'etiqueta': 'Verano'})
    r = client.get(f'/download-xlsx/{sid}')

    assert r.status_code == 200
    assert 'festivos_madrid_2027.xlsx' in r.headers['Content-Disposition']
    filas = list(load_workbook(io.BytesIO(r.data))['Festivos 2027'].values)
    cabecera = filas[0]
    assert cabecera[:4] == ('fecha', 'fecha_texto', 'descripcion', 'tipo')
    datos = {f[0]: dict(zip(cabecera, f)) for f in filas[1:]}
    assert set(datos) == {'2027-01-01', '2027-03-19', '2027-08-16'}
    assert datos['2027-01-01']['origen'] == 'oficial'
    assert datos['2027-08-16']['etiqueta'] == 'Verano'
    assert datos['2027-08-16']['origen'] == 'manual'


def test_xlsx_sesion_inexistente(sesion):
    client, _, _ = sesion
    assert client.get(f'/download-xlsx/{uuid.uuid4()}').status_code == 404


def test_sesion_invalida_404(sesion):
    client, _, _ = sesion
    assert client.post('/calendario/no-es-uuid/festivos', data={}).status_code == 404
    assert client.post(f'/calendario/{uuid.uuid4()}/festivos', data={}).status_code == 404
