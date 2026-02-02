"""
Tests para ScraperFactory — instanciación dinámica de scrapers.
"""

import pytest
from scrapers.core.scraper_factory import ScraperFactory
from config.config_manager import CCAaRegistry


class TestScraperFactory:
    """Tests del factory de scrapers."""

    def setup_method(self):
        self.factory = ScraperFactory()

    # --- list_supported_ccaa ---

    def test_list_supported_ccaa_returns_17(self):
        ccaa = self.factory.list_supported_ccaa()
        assert len(ccaa) == 17

    def test_list_supported_ccaa_matches_registry(self):
        assert self.factory.list_supported_ccaa() == CCAaRegistry().list_ccaa()

    # --- Derivación de nombres de clase ---

    def test_derive_regular_class_names(self):
        """Nombres regulares siguen la convención split+title+join."""
        assert self.factory._derive_locales_class_name('aragon') == 'AragonLocalesScraper'
        assert self.factory._derive_locales_class_name('madrid') == 'MadridLocalesScraper'
        assert self.factory._derive_locales_class_name('pais_vasco') == 'PaisVascoLocalesScraper'
        assert self.factory._derive_locales_class_name('castilla_leon') == 'CastillaLeonLocalesScraper'
        assert self.factory._derive_locales_class_name('canarias') == 'CanariasLocalesScraper'

    def test_derive_irregular_class_name_castilla_mancha(self):
        """castilla_mancha es caso irregular: incluye 'La' en el nombre."""
        assert self.factory._derive_locales_class_name('castilla_mancha') == 'CastillaLaManchaLocalesScraper'

    # --- create_locales_scraper (17 CCAA) ---

    @pytest.mark.parametrize("ccaa", CCAaRegistry().list_ccaa())
    def test_create_locales_scraper_all_17(self, ccaa):
        """Todas las CCAA del registry se pueden instanciar."""
        scraper = self.factory.create_locales_scraper(ccaa, year=2026, municipio='Test')
        assert scraper is not None
        assert hasattr(scraper, 'scrape')

    def test_create_locales_scraper_invalid_raises(self):
        with pytest.raises(ValueError, match="no está en el registry"):
            self.factory.create_locales_scraper('inventada', year=2026)

    # --- create_autonomicos_scraper ---

    def test_create_autonomicos_madrid(self):
        scraper = self.factory.create_autonomicos_scraper('madrid', year=2026)
        assert scraper is not None
        assert hasattr(scraper, 'scrape')

    def test_create_autonomicos_canarias(self):
        scraper = self.factory.create_autonomicos_scraper('canarias', year=2026, municipio='Las Palmas')
        assert scraper is not None

    def test_create_autonomicos_navarra(self):
        scraper = self.factory.create_autonomicos_scraper('navarra', year=2026, municipio='Pamplona')
        assert scraper is not None

    def test_create_autonomicos_unsupported_returns_none(self):
        """CCAA sin scraper de autonómicos devuelve None."""
        assert self.factory.create_autonomicos_scraper('aragon', year=2026) is None
        assert self.factory.create_autonomicos_scraper('extremadura', year=2026) is None
        assert self.factory.create_autonomicos_scraper('andalucia', year=2026) is None

    # --- has_autonomicos_scraper ---

    def test_has_autonomicos_scraper(self):
        assert self.factory.has_autonomicos_scraper('madrid') is True
        assert self.factory.has_autonomicos_scraper('canarias') is True
        assert self.factory.has_autonomicos_scraper('navarra') is True
        assert self.factory.has_autonomicos_scraper('aragon') is False
        assert self.factory.has_autonomicos_scraper('extremadura') is False
