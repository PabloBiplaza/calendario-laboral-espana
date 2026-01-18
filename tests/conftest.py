"""
Configuración de pytest y fixtures compartidos
"""

import sys
from pathlib import Path

# Añadir el directorio raíz al PYTHONPATH para que funcionen los imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pytest

# Path al directorio de fixtures
FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir():
    """Devuelve el path al directorio de fixtures"""
    return FIXTURES_DIR


@pytest.fixture
def canarias_html_2026(fixtures_dir):
    """Fixture con HTML de Canarias 2026"""
    path = fixtures_dir / "canarias" / "locales_2026.html"
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


@pytest.fixture
def madrid_pdf_2026(fixtures_dir):
    """Fixture con path al PDF de Madrid 2026"""
    return str(fixtures_dir / "madrid" / "locales_2026.pdf")


@pytest.fixture
def cantabria_pdf_2026(fixtures_dir):
    """Fixture con path al PDF de Cantabria 2026"""
    return str(fixtures_dir / "cantabria" / "locales_2026.pdf")


@pytest.fixture
def asturias_pdf_2026(fixtures_dir):
    """Fixture con path al PDF de Asturias 2026"""
    return str(fixtures_dir / "asturias" / "locales_2026.pdf")
