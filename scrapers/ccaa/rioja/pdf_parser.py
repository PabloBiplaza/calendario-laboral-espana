"""
Parser específico para PDFs del BOR (Boletín Oficial de La Rioja)
"""

import re
from typing import List, Dict, Optional
from scrapers.parsers.base_pdf_parser import BasePDFParser


class BORPDFParser(BasePDFParser):
    """Parser para extraer festivos locales del PDF del BOR"""

    def _parse_text(self, text: str) -> Dict[str, List[Dict]]:
        """
        Parsea el texto del PDF del BOR.

        Formato BOR:
        - Municipio: fecha1 (descripcion1) y fecha2 (descripcion2)
        - Ejemplo: "Logroño: 11 de junio (San Bernabé) y 21 de septiembre (San Mateo)"
        - Ejemplo: "Ábalos: 3 de agosto y 8 de septiembre (Fiestas Locales)"
        """
        # Reemplazar espacios Unicode especiales por espacios normales
        text = text.replace('\ufeff', ' ').replace('\xa0', ' ').replace('￿', ' ')

        lines = text.split('\n')
        festivos_por_municipio = {}

        for line in lines:
            line = line.strip()

            if not line:
                continue

            # Ignorar líneas administrativas
            if self._debe_ignorar_linea(line, [
                'boletín', 'https://', 'consejería', 'resolución',
                'núm.', 'página', 'rioja', 'autoridad', 'laboral',
                'artículo', 'decreto', 'retribuidos', 'logroño, a',
                'directora general', 'pilar simón', 'estatuto',
                'calendario laboral', 'fiestas locales 2026'
            ]):
                continue

            # Buscar líneas con el patrón: "Municipio: fecha1 y fecha2"
            # Ejemplo: "Ábalos: 3 de agosto y 8 de septiembre (Fiestas Locales)"
            match = re.match(r'^([^:]+):\s*(.+)$', line)

            if match:
                municipio_raw = match.group(1).strip()
                fechas_text = match.group(2).strip()

                # Normalizar municipio
                municipio = self._normalizar_municipio(municipio_raw)

                if not municipio:
                    continue

                # Parsear las fechas
                festivos = self._parsear_fechas(fechas_text)

                if festivos:
                    if municipio not in festivos_por_municipio:
                        festivos_por_municipio[municipio] = []
                    festivos_por_municipio[municipio].extend(festivos)

        return festivos_por_municipio

    def _parsear_fechas(self, texto: str) -> List[Dict]:
        """
        Extrae todas las fechas de un texto.

        Soporta formatos como:
        - "3 de agosto y 8 de septiembre (Fiestas Locales)"
        - "11 de junio (San Bernabé) y 21 de septiembre (San Mateo)"
        - "15 de mayo (San Isidro) y 8 de septiembre (Virgen del Valle)"
        - "28 de abril (San Prudencio) y 28 de agosto (Viernes de Fiestas de Verano)"

        Args:
            texto: Texto con las fechas

        Returns:
            Lista de diccionarios de festivos
        """
        festivos = []

        # Patrón para capturar fechas con descripciones opcionales
        # Formato: "DIA de MES (descripcion opcional)"
        patron = r'(\d{1,2})\s+de\s+(\w+)(?:\s+\(([^)]+)\))?'

        matches = re.finditer(patron, texto, re.IGNORECASE)

        for match in matches:
            dia = int(match.group(1))
            mes_nombre = match.group(2).lower()
            descripcion = match.group(3) if match.group(3) else "Fiesta Local"

            if self._es_fecha_valida(dia, mes_nombre):
                festivo = self._crear_festivo(
                    dia, self.MESES[mes_nombre], descripcion.strip()
                )
                festivos.append(festivo)

        return festivos

    def _normalizar_municipio(self, nombre: str) -> Optional[str]:
        """
        Normaliza el nombre del municipio para La Rioja.

        Ejemplos:
            "Logroño" -> "LOGROÑO"
            "Santo Domingo de la Calzada" -> "SANTO DOMINGO DE LA CALZADA"
        """
        # Ignorar líneas muy cortas
        if len(nombre) < 3:
            return None

        # Ignorar si contiene números o caracteres extraños
        if re.search(r'\d|http|@|\.com', nombre):
            return None

        # Ignorar líneas que contienen ciertas palabras clave
        palabras_ignorar = [
            'boletín', 'oficial', 'consejería', 'página',
            'núm', 'director', 'general', 'resolución',
            'festividad', 'fiestas locales', 'calendario',
            'retribuidos', 'recuperables'
        ]

        if self._debe_ignorar_linea(nombre, palabras_ignorar):
            return None

        # Limpiar caracteres extraños del inicio/fin
        nombre = nombre.strip(' :-')

        # Normalizar a mayúsculas
        return nombre.upper()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Uso: python pdf_parser.py <pdf_path> <year> [municipio]")
        print("Ejemplo: python pdf_parser.py festivos_2026.pdf 2026 LOGROÑO")
        sys.exit(1)

    pdf_path = sys.argv[1]
    year = int(sys.argv[2])
    municipio = sys.argv[3] if len(sys.argv) > 3 else None

    parser = BORPDFParser(pdf_path, year)

    if municipio:
        festivos = parser.get_festivos_municipio(municipio)
        print(f"\nFestivos de {municipio} en {year}:")
        for f in festivos:
            print(f"  - {f['fecha']}: {f['descripcion']}")
    else:
        festivos_todos = parser.parse()
        print(f"\nTotal municipios parseados: {len(festivos_todos)}")
        print("\nPrimeros 10 municipios:")
        for idx, (mun, fests) in enumerate(list(festivos_todos.items())[:10]):
            print(f"  {idx+1}. {mun}: {len(fests)} festivos")
            for f in fests:
                print(f"     - {f['fecha']}: {f['descripcion']}")
