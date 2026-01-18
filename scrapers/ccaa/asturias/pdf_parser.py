"""
Parser específico para PDFs del BOPA (Boletín Oficial del Principado de Asturias)
Refactorizado para usar BasePDFParser
"""

import re
from typing import List, Dict, Optional
from scrapers.parsers.base_pdf_parser import BasePDFParser


class BOPAPDFParser(BasePDFParser):
    """Parser para extraer festivos locales del PDF del BOPA"""

    def _parse_text(self, text: str) -> Dict[str, List[Dict]]:
        """
        Parsea el texto del PDF del BOPA.

        Formato BOPA:
        - Fecha: "15 de mayo San Isidro"
        - Luego el municipio en la siguiente línea: "OVIEDO"
        """
        lines = text.split('\n')

        # Buscar el inicio de la lista de festivos
        start_idx = 0
        for i, line in enumerate(lines):
            if 'las siguientes:' in line.lower():
                start_idx = i + 1
                break

        festivos_por_municipio = {}
        i = start_idx

        while i < len(lines):
            line = lines[i].strip()

            if not line:
                i += 1
                continue

            # Ignorar líneas administrativas
            if self._debe_ignorar_linea(line, [
                'boletín', 'https://', 'consejería', 'resolución',
                'principado', 'bopa', 'en oviedo, a', 'núm.'
            ]):
                i += 1
                continue

            # ¿Es una fecha?
            fecha_match = re.match(r'^(\d{1,2})\s+de\s+(\w+)\s+(.+)', line, re.IGNORECASE)

            if fecha_match:
                # Es una fecha sin municipio aún - mirar la siguiente línea
                dia = int(fecha_match.group(1))
                mes_nombre = fecha_match.group(2).lower()
                descripcion = fecha_match.group(3).strip()

                if self._es_fecha_valida(dia, mes_nombre):
                    # Crear festivo
                    festivo_previo = self._crear_festivo(
                        dia, self.MESES[mes_nombre], descripcion
                    )

                    # Mirar la siguiente línea - debería ser el municipio
                    i += 1
                    if i < len(lines):
                        next_line = lines[i].strip()
                        municipio_norm = self._normalizar_municipio(next_line)

                        if municipio_norm:
                            # Encontramos el municipio - asignar el festivo previo
                            if municipio_norm not in festivos_por_municipio:
                                festivos_por_municipio[municipio_norm] = []
                            festivos_por_municipio[municipio_norm].append(festivo_previo)

                            # Ahora buscar los festivos que siguen a este municipio
                            i += 1
                            while i < len(lines):
                                line2 = lines[i].strip()

                                if not line2:
                                    i += 1
                                    continue

                                # ¿Es otra fecha?
                                fecha_match2 = re.match(
                                    r'^(\d{1,2})\s+de\s+(\w+)\s+(.+)',
                                    line2,
                                    re.IGNORECASE
                                )

                                if fecha_match2:
                                    dia2 = int(fecha_match2.group(1))
                                    mes_nombre2 = fecha_match2.group(2).lower()
                                    descripcion2 = fecha_match2.group(3).strip()

                                    if self._es_fecha_valida(dia2, mes_nombre2):
                                        festivo2 = self._crear_festivo(
                                            dia2, self.MESES[mes_nombre2], descripcion2
                                        )
                                        festivos_por_municipio[municipio_norm].append(festivo2)
                                        i += 1
                                    else:
                                        break
                                else:
                                    # No es una fecha, probablemente es el siguiente municipio
                                    break
                        else:
                            # La siguiente línea no es un municipio válido, continuar
                            continue
                else:
                    i += 1
            else:
                # No es una fecha, ¿es un municipio?
                municipio_norm = self._normalizar_municipio(line)

                if municipio_norm:
                    # Es un municipio sin festivo previo
                    if municipio_norm not in festivos_por_municipio:
                        festivos_por_municipio[municipio_norm] = []

                    # Buscar festivos que siguen
                    i += 1
                    while i < len(lines):
                        line2 = lines[i].strip()

                        if not line2:
                            i += 1
                            continue

                        fecha_match2 = re.match(
                            r'^(\d{1,2})\s+de\s+(\w+)\s+(.+)',
                            line2,
                            re.IGNORECASE
                        )

                        if fecha_match2:
                            dia2 = int(fecha_match2.group(1))
                            mes_nombre2 = fecha_match2.group(2).lower()
                            descripcion2 = fecha_match2.group(3).strip()

                            if self._es_fecha_valida(dia2, mes_nombre2):
                                festivo2 = self._crear_festivo(
                                    dia2, self.MESES[mes_nombre2], descripcion2
                                )
                                festivos_por_municipio[municipio_norm].append(festivo2)
                                i += 1
                            else:
                                break
                        else:
                            # No es una fecha, salir del loop
                            break
                else:
                    i += 1

        return festivos_por_municipio

    def _normalizar_municipio(self, nombre: str) -> Optional[str]:
        """
        Normaliza el nombre del municipio para Asturias.

        Ejemplos:
            "oviedo" -> "OVIEDO"
            "avilÉs" -> "AVILÉS"
            "CaBrales" -> "CABRALES"
        """
        # Ignorar líneas muy cortas
        if len(nombre) < 3:
            return None

        # Ignorar si contiene números o puntos al inicio
        if re.match(r'^[\d\.\-]+', nombre):
            return None

        # Ignorar líneas que contienen ciertas palabras clave
        palabras_ignorar = [
            'festividad', 'día', 'siguiente', 'fiesta', 'fiestas',
            'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo',
            'en todo', 'excepto', 'parroquia', 'concejo', 'municipio',
            'boletín', 'oficial', 'https', 'bopa', 'núm'
        ]

        if self._debe_ignorar_linea(nombre, palabras_ignorar):
            return None

        # Ignorar si contiene más de 4 palabras (probablemente es una descripción)
        if len(nombre.split()) > 4:
            return None

        # Normalizar a mayúsculas (mantiene tildes correctamente)
        return nombre.upper()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Uso: python pdf_parser.py <pdf_path> <year> [municipio]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    year = int(sys.argv[2])
    municipio = sys.argv[3] if len(sys.argv) > 3 else None

    parser = BOPAPDFParser(pdf_path, year)

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
