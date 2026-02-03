"""Tests basicos para la aplicacion web Flask"""

import sys
from pathlib import Path

# Asegurar imports desde raiz del proyecto
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def test_web_app_imports():
    """Verifica que web/app.py se puede importar sin errores"""
    from web.app import app
    assert app is not None


def test_ccaa_17_from_registry():
    """Verifica que las CCAA vienen del registry (17, no 8)"""
    from web.app import CCAA_SOPORTADAS
    assert len(CCAA_SOPORTADAS) >= 17, (
        f"Expected >= 17 CCAA, got {len(CCAA_SOPORTADAS)}"
    )


def test_ccaa_nombres_completos():
    """Verifica que hay nombre para cada CCAA"""
    from web.app import CCAA_SOPORTADAS, CCAA_NOMBRES
    for ccaa in CCAA_SOPORTADAS:
        assert ccaa in CCAA_NOMBRES, f"Falta nombre para CCAA: {ccaa}"
        assert len(CCAA_NOMBRES[ccaa]) > 0


def test_health_check():
    """Verifica que el health check funciona"""
    from web.app import app
    client = app.test_client()
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'ok'
    assert data['ccaa_count'] >= 17


def test_landing_loads():
    """Verifica que la landing page carga"""
    from web.app import app
    client = app.test_client()
    response = client.get('/')
    assert response.status_code == 200
    # Debe contener el titulo
    assert b'Calendario Laboral' in response.data or b'calendario' in response.data.lower()


def test_api_municipios_madrid():
    """Verifica que /api/municipios/madrid devuelve datos"""
    from web.app import app
    client = app.test_client()
    response = client.get('/api/municipios/madrid')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) > 100  # Madrid tiene 179+ municipios


def test_api_municipios_canarias():
    """Verifica que /api/municipios/canarias devuelve datos (formato islas)"""
    from web.app import app
    client = app.test_client()
    response = client.get('/api/municipios/canarias')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) > 50  # Canarias tiene 88 municipios


def test_api_municipios_aragon():
    """Verifica que /api/municipios/aragon funciona (CCAA nueva, no en calendario-web)"""
    from web.app import app
    client = app.test_client()
    response = client.get('/api/municipios/aragon')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) > 100  # Aragon tiene 565+ municipios


def test_api_municipios_asturias():
    """Verifica formato {NORMALIZADO: display} (Asturias)"""
    from web.app import app
    client = app.test_client()
    response = client.get('/api/municipios/asturias')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) > 50  # Asturias tiene 78 municipios


def test_api_municipios_invalid():
    """Verifica que CCAA inexistente devuelve 404"""
    from web.app import app
    client = app.test_client()
    response = client.get('/api/municipios/inventada')
    assert response.status_code == 404


def test_generar_requires_post():
    """Verifica que /generar solo acepta POST"""
    from web.app import app
    client = app.test_client()
    response = client.get('/generar')
    assert response.status_code == 405  # Method Not Allowed
