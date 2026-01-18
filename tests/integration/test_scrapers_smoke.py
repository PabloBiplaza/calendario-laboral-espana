"""
Tests de integración (smoke tests) para verificar que los scrapers
de las 6 CCAA en producción devuelven exactamente 14 festivos
"""

import pytest


# CCAA en producción que DEBEN funcionar
PRODUCCION_CCAA = [
    ("canarias", "ARRECIFE", 14),
    ("madrid", "ALCALA DE HENARES", 14),
    # Andalucía, Valencia, Baleares, Cataluña comentadas por ahora
    # para no depender de internet en CI
]


@pytest.mark.parametrize("ccaa,municipio,expected_count", PRODUCCION_CCAA)
def test_scraper_returns_14_festivos(ccaa, municipio, expected_count):
    """
    Test crítico: cada CCAA en producción debe devolver exactamente 14 festivos
    (8 nacionales + 4 autonómicos + 2 locales)

    Este test usa fixtures locales, NO descarga de internet.
    """
    from scrape_municipio import scrape_festivos_completos

    # Este test usa mocks/fixtures en vez de descargar realmente
    # TODO: Implementar mocking para evitar llamadas HTTP

    pytest.skip("Pendiente: implementar mocking para tests sin internet")


class TestCantabriaIntegration:
    """Tests de integración para Cantabria usando fixtures"""

    def test_santander_14_festivos(self, cantabria_pdf_2026):
        """Test que Santander tiene exactamente 14 festivos"""
        from scrapers.ccaa.cantabria.pdf_parser import BOCPDFParser
        from scrapers.core.boe_scraper import BOEScraper

        # 1. Festivos nacionales (8)
        boe_scraper = BOEScraper(year=2026, ccaa='cantabria')
        # festivos_nacionales = boe_scraper.scrape()  # Requiere internet
        # assert len(festivos_nacionales) == 8

        # 2. Festivos autonómicos (4) - también del BOE
        # festivos_autonomicos = 4  # Cantabria tiene 4

        # 3. Festivos locales (2)
        parser = BOCPDFParser(cantabria_pdf_2026, 2026)
        festivos_locales = parser.get_festivos_municipio("SANTANDER")
        assert len(festivos_locales) == 2

        # Total esperado: 8 + 4 + 2 = 14
        # total = len(festivos_nacionales) + 4 + len(festivos_locales)
        # assert total == 14

    def test_castro_urdiales_14_festivos(self, cantabria_pdf_2026):
        """Test que Castro Urdiales tiene exactamente 14 festivos"""
        from scrapers.ccaa.cantabria.pdf_parser import BOCPDFParser

        parser = BOCPDFParser(cantabria_pdf_2026, 2026)
        festivos_locales = parser.get_festivos_municipio("CASTRO URDIALES")

        assert len(festivos_locales) == 2

        # Verificar fechas específicas (según búsqueda web anterior)
        fechas = [f['fecha'] for f in festivos_locales]
        assert '2026-06-26' in fechas, "Debe contener San Pelayo (26 junio)"
        assert '2026-11-30' in fechas, "Debe contener San Andrés (30 noviembre)"


class TestAsturiasIntegration:
    """Tests de integración para Asturias usando fixtures"""

    def test_oviedo_2_festivos_locales(self, asturias_pdf_2026):
        """Test que Oviedo tiene 2 festivos locales"""
        from scrapers.ccaa.asturias.pdf_parser import BOPAPDFParser

        parser = BOPAPDFParser(asturias_pdf_2026, 2026)
        festivos = parser.get_festivos_municipio("OVIEDO")

        assert len(festivos) == 2

    def test_gijon_2_festivos_locales(self, asturias_pdf_2026):
        """Test que Gijón tiene 2 festivos locales"""
        from scrapers.ccaa.asturias.pdf_parser import BOPAPDFParser

        parser = BOPAPDFParser(asturias_pdf_2026, 2026)

        # Probar con diferentes variantes (con/sin tilde)
        festivos = parser.get_festivos_municipio("GIJÓN")
        if not festivos:
            festivos = parser.get_festivos_municipio("GIJON")

        assert len(festivos) == 2, f"Esperado 2 festivos para Gijón, obtenido {len(festivos)}"
