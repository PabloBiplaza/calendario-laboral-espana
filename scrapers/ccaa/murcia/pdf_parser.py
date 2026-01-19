"""
Parser específico para PDFs del BORM (Boletín Oficial de la Región de Murcia)
"""

import re
from typing import List, Dict, Optional
from scrapers.parsers.base_pdf_parser import BasePDFParser


class BORMPDFParser(BasePDFParser):
    """Parser para extraer festivos locales del PDF del BORM"""

    def _parse_text(self, text: str) -> Dict[str, List[Dict]]:
        """
        Parsea el texto del PDF del BORM.

        Formato BORM (Murcia) - Tabla estructurada:
        1 ABANILLA Lunes 4 Mayo Lunes 14 Septiembre
        2 ABARÁN Martes 7 Abril Lunes 28 Septiembre
        ...

        Formato de columnas:
        - Número (1, 2, 3...)
        - MUNICIPIO
        - Día semana, D, Mes (primer festivo)
        - Día semana, D, Mes (segundo festivo)
        """
        # Reemplazar espacios Unicode especiales por espacios normales
        text = text.replace('\ufeff', ' ').replace('\xa0', ' ').replace('￿', ' ')

        lines = text.split('\n')
        festivos_por_municipio = {}

        for line in lines:
            line = line.strip()

            if not line:
                continue

            # Ignorar cabeceras y líneas administrativas
            if self._debe_ignorar_linea(line, [
                'boletín', 'borm', 'https://', 'página', 'núm', 'número',
                'consejería', 'resolución', 'dirección general', 'director',
                'artículo', 'decreto', 'región de murcia', 'comunidad autónoma',
                'calendario laboral', 'fiestas laborales', 'festivos',
                'año 2026', 'retribuidos', 'no recuperables', 'trabajadores',
                'municipio', '1.er festivo', '2.º festivo', 'día', 'semana'
            ]):
                continue

            # Patrón para líneas de la tabla:
            # Número MUNICIPIO DiaSemana Dia Mes DiaSemana Dia Mes
            # Ejemplo: "1 ABANILLA Lunes 4 Mayo Lunes 14 Septiembre"
            # Algunos municipios tienen un punto después del nombre: "41 TOTANA. Miércoles..."
            # El municipio puede tener varias palabras, por eso capturamos todo lo que no son días de la semana
            match = re.match(
                r'^(\d+)\s+([A-ZÁÉÍÓÚÑ\s,\-]+?)\.?\s+(Lunes|Martes|Miércoles|Jueves|Viernes|Sábado|Domingo)\s+(\d{1,2})\s+([A-Za-zñáéíóú]+)\s+(Lunes|Martes|Miércoles|Jueves|Viernes|Sábado|Domingo)\s+(\d{1,2})\s+([A-Za-zñáéíóú]+)',
                line,
                re.IGNORECASE
            )

            if match:
                numero = int(match.group(1))
                municipio_raw = match.group(2).strip()

                # Primer festivo
                dia1 = int(match.group(4))
                mes1_nombre = match.group(5).lower()

                # Segundo festivo
                dia2 = int(match.group(7))
                mes2_nombre = match.group(8).lower()

                # Normalizar municipio
                municipio = self._normalizar_municipio(municipio_raw)

                if not municipio:
                    continue

                # Crear festivos
                festivos = []

                if self._es_fecha_valida(dia1, mes1_nombre):
                    festivo1 = self._crear_festivo(dia1, self.MESES[mes1_nombre], "Fiesta local")
                    festivos.append(festivo1)

                if self._es_fecha_valida(dia2, mes2_nombre):
                    festivo2 = self._crear_festivo(dia2, self.MESES[mes2_nombre], "Fiesta local")
                    festivos.append(festivo2)

                if festivos:
                    festivos_por_municipio[municipio] = festivos

        return festivos_por_municipio

    def _parsear_fechas(self, texto: str) -> List[Dict]:
        """
        Extrae todas las fechas de un texto.

        Soporta formatos como:
        - "4 mayo y 14 septiembre"
        - "17 febrero y 27 marzo"
        - "31 agosto (Fiestas) y 8 septiembre (Virgen)"
        - "15 de mayo y 8 de septiembre" (con "de")

        Args:
            texto: Texto con las fechas

        Returns:
            Lista de diccionarios de festivos
        """
        festivos = []

        # Patrón para capturar fechas con "de" opcional y descripciones opcionales
        # Formato: "DIA (de)? MES (descripcion opcional)"
        patron = r'(\d{1,2})\s+(?:de\s+)?(\w+)(?:\s+\(([^)]+)\))?'

        matches = re.finditer(patron, texto, re.IGNORECASE)

        for match in matches:
            dia = int(match.group(1))
            mes_nombre = match.group(2).lower()
            descripcion = match.group(3) if match.group(3) else "Fiesta local"

            if self._es_fecha_valida(dia, mes_nombre):
                festivo = self._crear_festivo(
                    dia, self.MESES[mes_nombre], descripcion.strip()
                )
                festivos.append(festivo)

        return festivos

    def _normalizar_municipio(self, nombre: str) -> Optional[str]:
        """
        Normaliza el nombre del municipio para Murcia.

        Ejemplos:
            "Abanilla" -> "ABANILLA"
            "Los Alcázares" -> "LOS ALCÁZARES"
            "Alhama de Murcia" -> "ALHAMA DE MURCIA"
        """
        # Ignorar líneas muy cortas
        if len(nombre) < 3:
            return None

        # Ignorar si contiene números o caracteres extraños
        if re.search(r'\d|http|@|\.com', nombre):
            return None

        # Ignorar líneas que contienen ciertas palabras clave
        palabras_ignorar = [
            'boletín', 'oficial', 'borm', 'consejería', 'página',
            'núm', 'número', 'director', 'general', 'resolución',
            'festividad', 'festivo', 'fiestas', 'calendario',
            'retribuidos', 'recuperables', 'laboral', 'región'
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
        print("Ejemplo: python pdf_parser.py festivos_2026.pdf 2026 MURCIA")
        sys.exit(1)

    pdf_path = sys.argv[1]
    year = int(sys.argv[2])
    municipio = sys.argv[3] if len(sys.argv) > 3 else None

    parser = BORMPDFParser(pdf_path, year)

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
