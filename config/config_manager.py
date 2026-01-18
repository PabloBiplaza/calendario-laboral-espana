"""
Gestor de configuración centralizado para todas las CCAA.

Este módulo implementa el patrón Singleton para acceder a la configuración
unificada en config/ccaa_registry.yaml, mientras mantiene compatibilidad
con el código legacy que lee JSONs individuales.

Uso:
    from config.config_manager import CCAaRegistry

    registry = CCAaRegistry()

    # Obtener URLs
    url = registry.get_url('canarias', 2026, 'locales')

    # Obtener metadatos
    info = registry.get_ccaa_info('madrid')

    # Listar todas las CCAA
    ccaa_list = registry.list_ccaa()
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any


class CCAaRegistry:
    """Registry centralizado de todas las CCAA con patrón Singleton"""

    _instance = None
    _config: Optional[Dict] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # Solo cargar una vez
        if self._config is None:
            self._load_config()

    def _load_config(self) -> None:
        """Carga el archivo YAML de configuración"""
        config_path = Path(__file__).parent / "ccaa_registry.yaml"

        if not config_path.exists():
            raise FileNotFoundError(
                f"No se encuentra el archivo de configuración: {config_path}"
            )

        with open(config_path, 'r', encoding='utf-8') as f:
            self._config = yaml.safe_load(f)

    def get_url(
        self,
        ccaa: str,
        year: int,
        tipo: str = 'locales'
    ) -> Optional[str]:
        """
        Obtiene la URL para una CCAA, año y tipo específicos.

        Args:
            ccaa: Código de la CCAA (ej: 'canarias', 'madrid')
            year: Año (ej: 2026)
            tipo: Tipo de festivos ('locales' o 'autonomicos')

        Returns:
            URL si existe, None en caso contrario

        Examples:
            >>> registry = CCAaRegistry()
            >>> registry.get_url('canarias', 2026, 'locales')
            'https://www.gobiernodecanarias.org/boc/2025/165/3029.html'
        """
        ccaa_data = self._config['ccaa'].get(ccaa)
        if not ccaa_data:
            return None

        urls = ccaa_data.get('urls', {}).get(tipo, {})
        return urls.get(year)

    def get_ccaa_info(self, ccaa: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene toda la información de una CCAA.

        Args:
            ccaa: Código de la CCAA

        Returns:
            Diccionario con toda la info, o None si no existe
        """
        return self._config['ccaa'].get(ccaa)

    def get_municipios_file(self, ccaa: str) -> Optional[str]:
        """
        Obtiene el path al archivo de municipios de una CCAA.

        Args:
            ccaa: Código de la CCAA

        Returns:
            Path al archivo JSON de municipios
        """
        ccaa_data = self.get_ccaa_info(ccaa)
        if not ccaa_data:
            return None

        return ccaa_data.get('municipios_file')

    def get_boletin_info(self, ccaa: str) -> Optional[Dict[str, str]]:
        """
        Obtiene información del boletín oficial de una CCAA.

        Args:
            ccaa: Código de la CCAA

        Returns:
            Dict con 'boletin' (nombre) y 'boletin_url'
        """
        ccaa_data = self.get_ccaa_info(ccaa)
        if not ccaa_data:
            return None

        return {
            'boletin': ccaa_data.get('boletin'),
            'boletin_url': ccaa_data.get('boletin_url')
        }

    def get_discovery_info(self, ccaa: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene información sobre auto-discovery de una CCAA.

        Args:
            ccaa: Código de la CCAA

        Returns:
            Dict con 'auto_discovery' (bool) y 'discovery_method' (str)
        """
        ccaa_data = self.get_ccaa_info(ccaa)
        if not ccaa_data:
            return None

        return {
            'auto_discovery': ccaa_data.get('auto_discovery', False),
            'discovery_method': ccaa_data.get('discovery_method')
        }

    def list_ccaa(self) -> List[str]:
        """
        Lista todas las CCAA disponibles.

        Returns:
            Lista de códigos de CCAA
        """
        return list(self._config['ccaa'].keys())

    def list_ccaa_with_discovery(self) -> List[str]:
        """
        Lista solo las CCAA que tienen auto-discovery habilitado.

        Returns:
            Lista de códigos de CCAA con auto-discovery
        """
        return [
            ccaa_code
            for ccaa_code, ccaa_data in self._config['ccaa'].items()
            if ccaa_data.get('auto_discovery', False)
        ]

    def get_total_municipios(self) -> int:
        """
        Obtiene el total de municipios de todas las CCAA.

        Returns:
            Total de municipios
        """
        return self._config['metadata']['total_municipios']

    def get_metadata(self) -> Dict[str, Any]:
        """
        Obtiene los metadatos globales del proyecto.

        Returns:
            Diccionario con metadatos
        """
        return self._config['metadata']

    def has_urls_for_year(self, ccaa: str, year: int) -> Dict[str, bool]:
        """
        Verifica qué tipos de URLs están disponibles para un año.

        Args:
            ccaa: Código de la CCAA
            year: Año a verificar

        Returns:
            Dict con 'locales' y 'autonomicos' (bool)
        """
        ccaa_data = self.get_ccaa_info(ccaa)
        if not ccaa_data:
            return {'locales': False, 'autonomicos': False}

        urls = ccaa_data.get('urls', {})

        return {
            'locales': year in urls.get('locales', {}),
            'autonomicos': year in urls.get('autonomicos', {})
        }

    def get_ccaa_by_provincia(self, provincia: str) -> Optional[str]:
        """
        Encuentra la CCAA a la que pertenece una provincia.

        Args:
            provincia: Nombre de la provincia

        Returns:
            Código de la CCAA o None si no se encuentra

        Examples:
            >>> registry.get_ccaa_by_provincia('Málaga')
            'andalucia'
        """
        provincia_lower = provincia.lower()

        for ccaa_code, ccaa_data in self._config['ccaa'].items():
            provincias = ccaa_data.get('provincias', [])
            if any(p.lower() == provincia_lower for p in provincias):
                return ccaa_code

        return None

    def reload(self) -> None:
        """Recarga el archivo de configuración (útil para desarrollo/testing)"""
        self._config = None
        self._load_config()


# Instancia global (singleton)
# Usar esto en vez de crear instancias nuevas cada vez
registry = CCAaRegistry()


# Funciones de conveniencia para compatibilidad con código legacy
def get_ccaa_url(ccaa: str, year: int, tipo: str = 'locales') -> Optional[str]:
    """Función legacy-compatible para obtener URLs"""
    return registry.get_url(ccaa, year, tipo)


def get_ccaa_municipios_file(ccaa: str) -> Optional[str]:
    """Función legacy-compatible para obtener archivo de municipios"""
    return registry.get_municipios_file(ccaa)
