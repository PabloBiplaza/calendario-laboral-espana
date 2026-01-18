"""
Tests unitarios para el gestor de configuración centralizado
"""

import pytest
from config.config_manager import CCAaRegistry, registry


class TestCCAaRegistry:
    """Tests para el gestor de configuración centralizado"""

    def test_singleton_pattern(self):
        """Verifica que CCAaRegistry implementa el patrón Singleton"""
        instance1 = CCAaRegistry()
        instance2 = CCAaRegistry()

        assert instance1 is instance2, "Debe ser la misma instancia (Singleton)"

    def test_list_ccaa(self):
        """Verifica que lista las 11 CCAA correctamente"""
        ccaa_list = registry.list_ccaa()

        assert len(ccaa_list) == 11, "Debe haber 11 CCAA"
        assert 'canarias' in ccaa_list
        assert 'madrid' in ccaa_list
        assert 'andalucia' in ccaa_list
        assert 'valencia' in ccaa_list
        assert 'baleares' in ccaa_list
        assert 'cataluna' in ccaa_list
        assert 'galicia' in ccaa_list
        assert 'pais_vasco' in ccaa_list
        assert 'asturias' in ccaa_list
        assert 'cantabria' in ccaa_list
        assert 'rioja' in ccaa_list

    def test_get_url_canarias_2026(self):
        """Verifica que obtiene la URL de Canarias 2026 correctamente"""
        url = registry.get_url('canarias', 2026, 'locales')

        assert url is not None
        assert 'gobiernodecanarias.org/boc' in url
        assert url.startswith('http')

    def test_get_url_madrid_2026(self):
        """Verifica que obtiene la URL de Madrid 2026 correctamente"""
        url = registry.get_url('madrid', 2026, 'locales')

        assert url is not None
        assert 'bocm.es' in url
        assert url.endswith('.PDF') or url.endswith('.pdf')

    def test_get_url_nonexistent_ccaa(self):
        """Verifica que devuelve None para CCAA que no existe"""
        url = registry.get_url('murcia', 2026, 'locales')

        assert url is None

    def test_get_url_nonexistent_year(self):
        """Verifica que devuelve None para año que no existe"""
        url = registry.get_url('canarias', 2020, 'locales')

        assert url is None

    def test_get_ccaa_info_canarias(self):
        """Verifica que obtiene la información de Canarias"""
        info = registry.get_ccaa_info('canarias')

        assert info is not None
        assert info['name'] == 'Canarias'
        assert info['municipios_count'] == 88
        assert info['boletin'] == 'BOC'
        assert 'Las Palmas' in info['provincias']
        assert 'Santa Cruz de Tenerife' in info['provincias']

    def test_get_ccaa_info_pais_vasco(self):
        """Verifica que obtiene la información del País Vasco"""
        info = registry.get_ccaa_info('pais_vasco')

        assert info is not None
        assert info['name'] == 'Euskadi / País Vasco'
        assert info['municipios_count'] == 251
        assert info['formato'] == 'json'
        assert info['formato_especifico'] == 'opendata_api'

    def test_get_municipios_file(self):
        """Verifica que obtiene el path al archivo de municipios"""
        path = registry.get_municipios_file('asturias')

        assert path is not None
        assert 'asturias_municipios.json' in path

    def test_get_boletin_info(self):
        """Verifica que obtiene la información del boletín oficial"""
        info = registry.get_boletin_info('andalucia')

        assert info is not None
        assert info['boletin'] == 'BOJA'
        assert info['boletin_url'] == 'https://www.juntadeandalucia.es/boja'

    def test_get_discovery_info(self):
        """Verifica que obtiene la información de auto-discovery"""
        info = registry.get_discovery_info('galicia')

        assert info is not None
        assert info['auto_discovery'] is True
        assert info['discovery_method'] == 'rdf_metadata'

    def test_list_ccaa_with_discovery(self):
        """Verifica que lista solo CCAA con auto-discovery"""
        ccaa_with_discovery = registry.list_ccaa_with_discovery()

        # Según el YAML, hay 8 CCAA con auto_discovery=true
        assert len(ccaa_with_discovery) == 8

        # Verificar que Cataluña NO está (auto_discovery=false)
        assert 'cataluna' not in ccaa_with_discovery

        # Verificar que Baleares NO está (auto_discovery=false)
        assert 'baleares' not in ccaa_with_discovery

        # Verificar que las demás SÍ están
        assert 'canarias' in ccaa_with_discovery
        assert 'madrid' in ccaa_with_discovery
        assert 'galicia' in ccaa_with_discovery

    def test_get_total_municipios(self):
        """Verifica que obtiene el total de municipios"""
        total = registry.get_total_municipios()

        assert total == 3492  # Incluyendo La Rioja (164 municipios)

    def test_get_metadata(self):
        """Verifica que obtiene los metadatos globales"""
        metadata = registry.get_metadata()

        assert metadata is not None
        assert metadata['total_ccaa'] == 11  # Incluyendo La Rioja
        assert metadata['total_municipios'] >= 3480  # Aproximadamente, incluyendo La Rioja
        assert 'ultima_actualizacion' in metadata
        assert 'version' in metadata

    def test_has_urls_for_year(self):
        """Verifica que detecta qué URLs están disponibles para un año"""
        # Canarias tiene URLs para 2026
        urls_2026 = registry.has_urls_for_year('canarias', 2026)
        assert urls_2026['locales'] is True
        assert urls_2026['autonomicos'] is True

        # Canarias NO tiene URLs para 2020
        urls_2020 = registry.has_urls_for_year('canarias', 2020)
        assert urls_2020['locales'] is False
        assert urls_2020['autonomicos'] is False

    def test_get_ccaa_by_provincia_malaga(self):
        """Verifica que encuentra la CCAA por provincia (Málaga)"""
        ccaa = registry.get_ccaa_by_provincia('Málaga')

        assert ccaa == 'andalucia'

    def test_get_ccaa_by_provincia_barcelona(self):
        """Verifica que encuentra la CCAA por provincia (Barcelona)"""
        ccaa = registry.get_ccaa_by_provincia('Barcelona')

        assert ccaa == 'cataluna'

    def test_get_ccaa_by_provincia_case_insensitive(self):
        """Verifica que la búsqueda por provincia es case-insensitive"""
        ccaa1 = registry.get_ccaa_by_provincia('MADRID')
        ccaa2 = registry.get_ccaa_by_provincia('madrid')
        ccaa3 = registry.get_ccaa_by_provincia('Madrid')

        assert ccaa1 == ccaa2 == ccaa3 == 'madrid'

    def test_get_ccaa_by_provincia_nonexistent(self):
        """Verifica que devuelve None para provincia que no existe"""
        ccaa = registry.get_ccaa_by_provincia('Murcia')

        assert ccaa is None

    def test_all_ccaa_have_required_fields(self):
        """Verifica que todas las CCAA tienen los campos requeridos"""
        required_fields = ['name', 'municipios_count', 'provincias', 'boletin', 'formato']

        for ccaa_code in registry.list_ccaa():
            info = registry.get_ccaa_info(ccaa_code)

            for field in required_fields:
                assert field in info, f"{ccaa_code} debe tener el campo '{field}'"

    def test_all_ccaa_have_municipios_file(self):
        """Verifica que todas las CCAA tienen municipios_file"""
        for ccaa_code in registry.list_ccaa():
            municipios_file = registry.get_municipios_file(ccaa_code)

            assert municipios_file is not None, f"{ccaa_code} debe tener municipios_file"
            assert '.json' in municipios_file, f"{ccaa_code} municipios_file debe ser JSON"
