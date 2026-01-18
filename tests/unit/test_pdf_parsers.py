"""
Tests unitarios para parsers de PDF
"""

import pytest


class TestCantabriaPDFParser:
    """Tests para el parser de PDF de Cantabria"""

    def test_parser_extrae_festivos_santander(self, cantabria_pdf_2026):
        """Test que el parser extrae los 2 festivos locales de Santander"""
        from scrapers.ccaa.cantabria.pdf_parser import BOCPDFParser

        parser = BOCPDFParser(cantabria_pdf_2026, 2026)
        festivos = parser.get_festivos_municipio("SANTANDER")

        assert len(festivos) == 2, f"Esperado 2 festivos, obtenido {len(festivos)}"

        # Verificar fechas específicas
        fechas = [f['fecha'] for f in festivos]
        assert '2026-05-25' in fechas, "Debe contener Virgen del Mar (25 mayo)"
        assert '2026-07-25' in fechas, "Debe contener Apóstol Santiago (25 julio)"

    def test_parser_extrae_todos_los_municipios(self, cantabria_pdf_2026):
        """Test que el parser extrae festivos de mayoría de municipios (Cantabria: 102)"""
        from scrapers.ccaa.cantabria.pdf_parser import BOCPDFParser

        parser = BOCPDFParser(cantabria_pdf_2026, 2026)
        festivos_todos = parser.parse()

        # Cantabria tiene 102 municipios, esperamos al menos 85% (87+)
        assert len(festivos_todos) >= 87, f"Esperado >=87 municipios (85% de 102), obtenido {len(festivos_todos)}"

        # La mayoría deben tener 2 festivos
        municipios_con_2_festivos = sum(1 for f in festivos_todos.values() if len(f) == 2)
        assert municipios_con_2_festivos >= 80, f"La mayoría deben tener 2 festivos, solo {municipios_con_2_festivos} tienen 2"


class TestAsturiasPDFParser:
    """Tests para el parser de PDF de Asturias"""

    def test_parser_extrae_festivos_oviedo(self, asturias_pdf_2026):
        """Test que el parser extrae los 2 festivos locales de Oviedo"""
        from scrapers.ccaa.asturias.pdf_parser import BOPAPDFParser

        parser = BOPAPDFParser(asturias_pdf_2026, 2026)
        festivos = parser.get_festivos_municipio("OVIEDO")

        assert len(festivos) == 2, f"Esperado 2 festivos, obtenido {len(festivos)}"

        # Verificar que son fechas válidas
        for festivo in festivos:
            assert 'fecha' in festivo
            assert 'descripcion' in festivo
            assert festivo['fecha'].startswith('2026-')

    def test_parser_extrae_todos_los_municipios(self, asturias_pdf_2026):
        """Test que el parser extrae festivos de mayoría de municipios (Asturias: 78)"""
        from scrapers.ccaa.asturias.pdf_parser import BOPAPDFParser

        parser = BOPAPDFParser(asturias_pdf_2026, 2026)
        festivos_todos = parser.parse()

        # Asturias tiene 78 municipios, esperamos al menos 85% (66+)
        assert len(festivos_todos) >= 66, f"Esperado >=66 municipios (85% de 78), obtenido {len(festivos_todos)}"


class TestMadridPDFParser:
    """Tests para el parser de PDF de Madrid"""

    def test_madrid_pdf_exists(self, madrid_pdf_2026):
        """Test que el fixture de Madrid existe"""
        import os
        assert os.path.exists(madrid_pdf_2026), "El PDF de Madrid debe existir"

        # Madrid no tiene parser de PDF separado, usa tabla HTML
        # Este test solo verifica que el fixture está disponible
        pytest.skip("Madrid usa tabla HTML, no parser de PDF directo")
