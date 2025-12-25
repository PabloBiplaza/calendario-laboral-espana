"""
BOE Discovery - Sistema híbrido mantenible
Prioriza URLs conocidas, con auto-discovery como fallback opcional
"""

import requests
from typing import Optional
import json


class BOEAutoDiscovery:
    """
    Sistema de descubrimiento de URLs del BOE
    Enfoque pragmático: URLs conocidas + auto-discovery opcional
    """
    
    # URLs conocidas (actualizar manualmente cada año)
    KNOWN_URLS = {
        2026: "https://www.boe.es/diario_boe/txt.php?id=BOE-A-2025-21667",
        2025: "https://www.boe.es/diario_boe/txt.php?id=BOE-A-2024-21234",
        # Añadir nuevos años aquí cuando se publiquen
    }
    
    def __init__(self):
        self.base_url = "https://www.boe.es"
        self.api_url = f"{self.base_url}/datosabiertos/api"
    
    def get_url(self, year: int, try_auto_discovery: bool = False) -> str:
        """
        Obtiene la URL de la Resolución de festivos.
        
        Args:
            year: Año del calendario
            try_auto_discovery: Intentar auto-discovery si no está en KNOWN_URLS
            
        Returns:
            URL válida
            
        Raises:
            ValueError: Si no se encuentra URL
        """
        # 1. Primero, intentar URLs conocidas
        if year in self.KNOWN_URLS:
            url = self.KNOWN_URLS[year]
            print(f"✅ URL conocida para {year}: {url}")
            
            # Validar que sigue siendo válida
            if self.validate_url(url, year):
                return url
            else:
                print(f"⚠️  URL conocida no válida, buscando alternativa...")
        
        # 2. Si no está en conocidas y se permite, intentar auto-discovery
        if try_auto_discovery:
            print(f"🔍 Intentando auto-discovery para {year}...")
            url = self._try_auto_discovery(year)
            if url and self.validate_url(url, year):
                print(f"✅ URL encontrada por auto-discovery: {url}")
                print(f"💡 Tip: Añádela a KNOWN_URLS en boe_discovery.py")
                return url
        
        # 3. Si todo falla, dar instrucciones
        raise ValueError(
            f"\n❌ No se encontró URL para {year}.\n\n"
            f"Para añadirla manualmente:\n"
            f"1. Busca en https://www.boe.es 'fiestas laborales {year}'\n"
            f"2. Encuentra la Resolución (suele publicarse en octubre-noviembre del año {year-1})\n"
            f"3. Copia el ID del documento (ej: BOE-A-{year-1}-XXXXX)\n"
            f"4. Añade a scrapers/discovery/boe_discovery.py:\n"
            f"   {year}: 'https://www.boe.es/diario_boe/txt.php?id=BOE-A-{year-1}-XXXXX'\n"
        )
    
    def _try_auto_discovery(self, year: int) -> Optional[str]:
        """
        Intenta auto-discovery usando la API del BOE
        Busca en TODOS los días de septiembre-diciembre del año anterior
        """
        try:
            search_year = year - 1
            
            print(f"   🔍 Buscando en API del BOE (sept-dic {search_year})...")
            print(f"   ⏱️  Esto puede tardar ~30-60 segundos...")
            
            # Buscar en TODOS los días de septiembre a diciembre
            for mes in [9, 10, 11, 12]:  # Sept, Oct, Nov, Dic
                # Determinar días del mes
                if mes == 2:
                    max_day = 29 if search_year % 4 == 0 else 28
                elif mes in [4, 6, 9, 11]:
                    max_day = 30
                else:
                    max_day = 31
                
                print(f"   → Buscando en {search_year}/{mes:02d}...", end=" ", flush=True)
                
                # Buscar TODOS los días del mes (de más reciente a más antiguo)
                for dia in range(max_day, 0, -1):
                    fecha = f"{search_year}{mes:02d}{dia:02d}"
                    api_url = f"{self.api_url}/boe/sumario/{fecha}"
                    
                    try:
                        response = requests.get(api_url, timeout=5, headers={'Accept': 'application/json'})
                        if response.status_code != 200:
                            continue
                        
                        data = response.json()
                        doc_id = self._search_in_json(data, year)
                        
                        if doc_id:
                            print(f"✅ (día {dia})")
                            return f"{self.base_url}/diario_boe/txt.php?id={doc_id}"
                    
                    except:
                        continue
                
                print("❌")
            
            print(f"   ❌ No encontrado en sept-dic {search_year}")
            
            # Fallback: enero-febrero del año objetivo (publicación muy tardía)
            print(f"   🔄 Intentando en enero-febrero {year} (publicación tardía)...")
            
            for mes in [1, 2]:
                max_day = 29 if mes == 2 and year % 4 == 0 else (28 if mes == 2 else 31)
                
                print(f"   → Buscando en {year}/{mes:02d}...", end=" ", flush=True)
                
                for dia in range(max_day, 0, -1):
                    fecha = f"{year}{mes:02d}{dia:02d}"
                    api_url = f"{self.api_url}/boe/sumario/{fecha}"
                    
                    try:
                        response = requests.get(api_url, timeout=5, headers={'Accept': 'application/json'})
                        if response.status_code != 200:
                            continue
                        
                        data = response.json()
                        doc_id = self._search_in_json(data, year)
                        
                        if doc_id:
                            print(f"✅ (día {dia})")
                            return f"{self.base_url}/diario_boe/txt.php?id={doc_id}"
                    
                    except:
                        continue
                
                print("❌")
            
            return None
            
        except Exception as e:
            print(f"   ⚠️  Error en auto-discovery: {e}")
            return None
    
    def _search_in_json(self, data: dict, year: int) -> Optional[str]:
        """
        Busca el documento en el JSON del sumario
        Enfoque simple: busca en el JSON completo como string
        """
        try:
            # Convertir todo el JSON a string lowercase
            json_str = json.dumps(data, ensure_ascii=False).lower()
            
            # Buscar "fiestas laborales" + año
            if 'fiestas laborales' not in json_str or str(year) not in json_str:
                return None
            
            # Encontrar todas las ocurrencias de IDs BOE
            import re
            pattern = r'"identificador"\s*:\s*"(boe-a-\d{4}-\d{5})"'
            matches = re.findall(pattern, json_str)
            
            # Para cada ID encontrado, verificar si su contexto habla de festivos
            for boe_id in matches:
                # Buscar el contexto alrededor de este ID (±500 chars)
                idx = json_str.find(f'"{boe_id}"')
                if idx == -1:
                    continue
                
                context = json_str[max(0, idx-500):min(len(json_str), idx+500)]
                
                # Verificar que en ese contexto está "fiestas laborales" + año
                if 'fiestas laborales' in context and str(year) in context:
                    # Verificar que sea resolución/relación
                    if 'resolución' in context or 'relación' in context:
                        return boe_id.upper()
            
            return None
            
        except Exception as e:
            return None
    
    def validate_url(self, url: str, year: int) -> bool:
        """Valida que una URL contiene la Resolución de festivos"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            content = response.text.lower()
            
            # Verificar palabras clave
            required = ['fiestas laborales', str(year), 'año nuevo']
            
            return all(kw in content for kw in required)
            
        except:
            return False
    
    @classmethod
    def add_known_url(cls, year: int, url: str):
        """Añade una URL conocida (para uso programático)"""
        cls.KNOWN_URLS[year] = url
        print(f"✅ Añadida URL para {year}")


def main():
    """Test del discovery"""
    discovery = BOEAutoDiscovery()
    
    # Probar con 2026 (está en KNOWN_URLS)
    print("="*80)
    print("TEST 1: Año con URL conocida (2026)")
    print("="*80)
    try:
        url = discovery.get_url(2026)
        print(f"\n✅ Éxito: {url}\n")
    except ValueError as e:
        print(f"\n❌ Error: {e}\n")
    
    # Probar con 2027 (no está en KNOWN_URLS)
    print("="*80)
    print("TEST 2: Año sin URL conocida (2027)")
    print("="*80)
    try:
        url = discovery.get_url(2027, try_auto_discovery=False)
        print(f"\n✅ Éxito: {url}\n")
    except ValueError as e:
        print(f"\n❌ Esperado: {e}\n")


if __name__ == "__main__":
    main()