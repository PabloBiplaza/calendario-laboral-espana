"""
Factory para instanciar scrapers de CCAA dinámicamente.

Elimina las cadenas if/elif de 17 ramas en scrape_municipio.py
usando importlib para cargar scrapers en tiempo de ejecución.

Uso:
    from scrapers.core.scraper_factory import ScraperFactory

    factory = ScraperFactory()
    scraper = factory.create_locales_scraper('aragon', 2026, 'Zaragoza')
    festivos = scraper.scrape()
"""

import importlib
from typing import Optional, List

from config.config_manager import CCAaRegistry


# Override explícito SOLO para nombres de clase irregulares.
# Convención regular: ccaa_code.split('_') → title each → join → + 'LocalesScraper'
#   pais_vasco → PaisVascoLocalesScraper ✅
#   castilla_leon → CastillaLeonLocalesScraper ✅
#   castilla_mancha → CastillaManchaLocalesScraper ❌ (debería ser CastillaLaManchaLocalesScraper)
_LOCALES_CLASS_OVERRIDES = {
    'castilla_mancha': 'CastillaLaManchaLocalesScraper',
}

# Solo 3 CCAA tienen scraper de autonómicos dedicado.
# El resto obtiene los autonómicos de la tabla del BOE (parse_tabla_ccaa).
_AUTONOMICOS_CCAA = {
    'madrid': 'MadridAutonomicosScraper',
    'canarias': 'CanariasAutonomicosScraper',
    'navarra': 'NavarraAutonomicosScraper',
}


class ScraperFactory:
    """
    Factory que importa e instancia scrapers de CCAA dinámicamente.

    Usa ccaa_registry.yaml (vía CCAaRegistry) como única fuente de verdad
    para saber qué CCAA están soportadas.
    """

    def __init__(self):
        self._registry = CCAaRegistry()

    def list_supported_ccaa(self) -> List[str]:
        """Devuelve todos los códigos de CCAA del registry."""
        return self._registry.list_ccaa()

    def _derive_locales_class_name(self, ccaa_code: str) -> str:
        """
        Deriva el nombre de clase LocalesScraper a partir del código CCAA.

        Regla general: split('_') → title() cada parte → join → + 'LocalesScraper'
          'pais_vasco'    → 'PaisVascoLocalesScraper'
          'castilla_leon' → 'CastillaLeonLocalesScraper'
          'aragon'        → 'AragonLocalesScraper'

        Override para nombres irregulares:
          'castilla_mancha' → 'CastillaLaManchaLocalesScraper'
        """
        if ccaa_code in _LOCALES_CLASS_OVERRIDES:
            return _LOCALES_CLASS_OVERRIDES[ccaa_code]

        parts = ccaa_code.split('_')
        camel = ''.join(part.title() for part in parts)
        return f'{camel}LocalesScraper'

    def create_locales_scraper(
        self,
        ccaa_code: str,
        year: int,
        municipio: Optional[str] = None
    ):
        """
        Importa dinámicamente e instancia un LocalesScraper.

        Args:
            ccaa_code: ej. 'aragon', 'castilla_mancha', 'madrid'
            year: año del calendario
            municipio: nombre del municipio (opcional)

        Returns:
            Instancia del LocalesScraper correspondiente

        Raises:
            ValueError: si ccaa_code no está en el registry
            ImportError: si no se puede cargar el módulo/clase
        """
        if ccaa_code not in self.list_supported_ccaa():
            raise ValueError(f"CCAA '{ccaa_code}' no está en el registry")

        module_path = f'scrapers.ccaa.{ccaa_code}.locales'
        class_name = self._derive_locales_class_name(ccaa_code)

        module = importlib.import_module(module_path)
        scraper_class = getattr(module, class_name)

        return scraper_class(year=year, municipio=municipio)

    def create_autonomicos_scraper(
        self,
        ccaa_code: str,
        year: int,
        municipio: Optional[str] = None
    ):
        """
        Importa dinámicamente e instancia un AutonomicosScraper.

        Solo 3 CCAA tienen scraper de autonómicos dedicado:
        madrid, canarias, navarra. El resto obtiene los autonómicos
        directamente de la tabla del BOE (BOEScraper.parse_tabla_ccaa).

        Returns:
            Instancia del AutonomicosScraper, o None si la CCAA no tiene uno
        """
        if ccaa_code not in _AUTONOMICOS_CCAA:
            return None

        module_path = f'scrapers.ccaa.{ccaa_code}.autonomicos'
        class_name = _AUTONOMICOS_CCAA[ccaa_code]

        module = importlib.import_module(module_path)
        scraper_class = getattr(module, class_name)

        # MadridAutonomicosScraper(year) no recibe municipio,
        # los otros dos sí: CanariasAutonomicosScraper(year, municipio),
        #                    NavarraAutonomicosScraper(year, municipio)
        if ccaa_code == 'madrid':
            return scraper_class(year=year)
        else:
            return scraper_class(year=year, municipio=municipio)

    def has_autonomicos_scraper(self, ccaa_code: str) -> bool:
        """Devuelve True si la CCAA tiene un scraper de autonómicos dedicado."""
        return ccaa_code in _AUTONOMICOS_CCAA
