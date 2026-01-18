"""
Parser específico para PDFs del BOC (Boletín Oficial de Cantabria)
"""

import re
from typing import List, Dict
import pdfplumber


class BOCPDFParser:
    """Parser para extraer festivos locales del PDF del BOC"""

    MESES = {
        'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
        'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
        'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
    }

    def __init__(self, pdf_path: str, year: int):
        self.pdf_path = pdf_path
        self.year = year

    def parse(self) -> Dict[str, List[Dict]]:
        """
        Extrae festivos del PDF del BOC.

        Returns:
            Dict con municipio como clave y lista de festivos como valor
        """

        with pdfplumber.open(self.pdf_path) as pdf:
            # Extraer todo el texto (saltando página 1 que tiene festivos nacionales)
            all_text = ''
            for page in pdf.pages[1:]:  # Página 2 en adelante
                all_text += page.extract_text() + '\n'

        return self._parse_text(all_text)

    def _parse_text(self, text: str) -> Dict[str, List[Dict]]:
        """Parsea el texto del PDF"""

        lines = text.split('\n')

        # Buscar el inicio de la lista de festivos locales
        start_idx = 0
        for i, line in enumerate(lines):
            if 'FIESTAS LOCALES' in line:
                start_idx = i + 2  # Saltar también la cabecera "AYUNTAMIENTO FESTIVIDAD DÍA MES"
                break

        festivos_por_municipio = {}
        i = start_idx

        while i < len(lines):
            line = lines[i].strip()

            if not line:
                i += 1
                continue

            # Ignorar líneas administrativas/cabeceras repetidas
            if any(x in line.lower() for x in ['boletín oficial', 'boc núm', 'pág.',
                                                  'ayuntamiento festividad día mes', 'cve-']):
                i += 1
                continue

            # Patrón de Cantabria: "FESTIVIDAD DÍA MES"
            # Ejemplo: "SAN ISIDRO LABRADOR 15 MAYO"
            festivo_match = re.match(r'^(.+?)\s+(\d{1,2})\s+([A-ZÑÁÉÍÓÚ]+)$', line, re.IGNORECASE)

            if festivo_match:
                descripcion = festivo_match.group(1).strip()
                dia = int(festivo_match.group(2))
                mes_nombre = festivo_match.group(3).lower()

                if mes_nombre in self.MESES and 1 <= dia <= 31:
                    # Guardar este festivo temporalmente
                    festivo = {
                        'fecha': f'{self.year}-{self.MESES[mes_nombre]:02d}-{dia:02d}',
                        'descripcion': descripcion if descripcion != '-' else 'Festivo local',
                        'fecha_texto': f'{dia} de {mes_nombre}'
                    }

                    # Mirar la siguiente línea - debería ser el municipio
                    i += 1
                    if i < len(lines):
                        next_line = lines[i].strip()

                        # Ignorar líneas vacías
                        while i < len(lines) and not next_line:
                            i += 1
                            if i < len(lines):
                                next_line = lines[i].strip()

                        if i < len(lines):
                            municipio_norm = self._normalizar_municipio(next_line)

                            if municipio_norm:
                                # Encontramos el municipio
                                if municipio_norm not in festivos_por_municipio:
                                    festivos_por_municipio[municipio_norm] = []

                                festivos_por_municipio[municipio_norm].append(festivo)

                                # Ahora buscar el segundo festivo (siguiente línea)
                                i += 1
                                if i < len(lines):
                                    next_festivo_line = lines[i].strip()

                                    festivo_match2 = re.match(r'^(.+?)\s+(\d{1,2})\s+([A-ZÑÁÉÍÓÚ]+)$',
                                                             next_festivo_line, re.IGNORECASE)

                                    if festivo_match2:
                                        descripcion2 = festivo_match2.group(1).strip()
                                        dia2 = int(festivo_match2.group(2))
                                        mes_nombre2 = festivo_match2.group(3).lower()

                                        if mes_nombre2 in self.MESES and 1 <= dia2 <= 31:
                                            festivo2 = {
                                                'fecha': f'{self.year}-{self.MESES[mes_nombre2]:02d}-{dia2:02d}',
                                                'descripcion': descripcion2 if descripcion2 != '-' else 'Festivo local',
                                                'fecha_texto': f'{dia2} de {mes_nombre2}'
                                            }
                                            festivos_por_municipio[municipio_norm].append(festivo2)
                                            i += 1
                                        else:
                                            # No es un festivo válido, retroceder
                                            pass
                                    else:
                                        # La siguiente línea no es un festivo, retroceder
                                        pass
                            else:
                                # La siguiente línea no era un municipio válido
                                # Podría ser que el festivo y municipio estén en la misma línea (casos raros)
                                continue
                else:
                    i += 1
            else:
                # No es un festivo, podría ser un municipio sin festivo previo o basura
                i += 1

        return festivos_por_municipio

    def _normalizar_municipio(self, nombre: str) -> str:
        """
        Normaliza el nombre del municipio.

        Ejemplos:
            "ASTILLERO, EL" -> "ASTILLERO, EL"
            "castro urdiales" -> "CASTRO URDIALES"
        """

        # Ignorar líneas muy cortas
        if len(nombre) < 3:
            return None

        # Ignorar si contiene números
        if re.search(r'\d', nombre):
            return None

        # Ignorar líneas que son claramente descripciones de festivos
        palabras_ignorar = [
            'festividad', 'día', 'siguiente', 'fiesta', 'fiestas',
            'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo',
            'san ', 'santa ', 'ntra', 'virgen', 'carmen', 'cruz',
            'boletín', 'oficial', 'boc', 'núm', 'pág',
            'exaltación', 'natividad', 'labrador'
        ]

        nombre_lower = nombre.lower()

        # Verificar palabras ignoradas
        for palabra in palabras_ignorar:
            if palabra in nombre_lower:
                return None

        # Ignorar si es muy largo (más de 30 caracteres probablemente es descripción)
        if len(nombre) > 30:
            return None

        # Normalizar a mayúsculas
        nombre_norm = nombre.upper()

        return nombre_norm

    def get_festivos_municipio(self, municipio: str) -> List[Dict]:
        """
        Obtiene los festivos de un municipio específico.

        Args:
            municipio: Nombre del municipio (case-insensitive)

        Returns:
            Lista de festivos del municipio
        """

        festivos_todos = self.parse()

        # Buscar el municipio (case-insensitive, fuzzy)
        municipio_upper = municipio.upper()

        # Primero buscar match exacto
        for key, festivos in festivos_todos.items():
            if key == municipio_upper:
                return festivos

        # Luego buscar match parcial
        for key, festivos in festivos_todos.items():
            if municipio_upper in key or key in municipio_upper:
                return festivos

        return []


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Uso: python pdf_parser.py <pdf_path> <year> [municipio]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    year = int(sys.argv[2])
    municipio = sys.argv[3] if len(sys.argv) > 3 else None

    parser = BOCPDFParser(pdf_path, year)

    if municipio:
        festivos = parser.get_festivos_municipio(municipio)
        print(f"\nFestivos de {municipio}:")
        for f in festivos:
            print(f"  - {f['fecha']}: {f['descripcion']}")
    else:
        festivos_todos = parser.parse()
        print(f"\nTotal municipios: {len(festivos_todos)}")
        print("\nPrimeros 10 municipios:")
        for idx, (mun, fests) in enumerate(list(festivos_todos.items())[:10]):
            print(f"  {mun}: {len(fests)} festivos")
