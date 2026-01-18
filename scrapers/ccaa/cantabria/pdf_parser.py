"""
Parser específico para PDFs del BOC (Boletín Oficial de Cantabria)
Refactorizado para usar BasePDFParser
"""

import re
from typing import List, Dict, Optional
from scrapers.parsers.base_pdf_parser import BasePDFParser


class BOCPDFParser(BasePDFParser):
    """Parser para extraer festivos locales del PDF del BOC"""

    def _get_pages_to_extract(self, pdf) -> List:
        """
        Cantabria: omitir página 1 que contiene festivos nacionales.

        Returns:
            Páginas 2 en adelante
        """
        return pdf.pages[1:]  # Saltar primera página

    def _parse_text(self, text: str) -> Dict[str, List[Dict]]:
        """
        Parsea el texto del PDF del BOC.

        Formato BOC (Cantabria):
        - Tabla con "FESTIVIDAD DÍA MES"
        - Ejemplo: "SAN ISIDRO LABRADOR 15 MAYO"
        - Luego el municipio en línea siguiente: "SANTANDER"
        """
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
            if self._debe_ignorar_linea(line, [
                'boletín oficial', 'boc núm', 'pág.',
                'ayuntamiento festividad día mes', 'cve-'
            ]):
                i += 1
                continue

            # Patrón de Cantabria: "FESTIVIDAD DÍA MES"
            # Ejemplo: "SAN ISIDRO LABRADOR 15 MAYO"
            festivo_match = re.match(r'^(.+?)\s+(\d{1,2})\s+([A-ZÑÁÉÍÓÚ]+)$', line, re.IGNORECASE)

            if festivo_match:
                descripcion = festivo_match.group(1).strip()
                dia = int(festivo_match.group(2))
                mes_nombre = festivo_match.group(3).lower()

                if self._es_fecha_valida(dia, mes_nombre):
                    # Crear festivo
                    festivo = self._crear_festivo(
                        dia,
                        self.MESES[mes_nombre],
                        descripcion if descripcion != '-' else 'Festivo local'
                    )

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

                                    festivo_match2 = re.match(
                                        r'^(.+?)\s+(\d{1,2})\s+([A-ZÑÁÉÍÓÚ]+)$',
                                        next_festivo_line,
                                        re.IGNORECASE
                                    )

                                    if festivo_match2:
                                        descripcion2 = festivo_match2.group(1).strip()
                                        dia2 = int(festivo_match2.group(2))
                                        mes_nombre2 = festivo_match2.group(3).lower()

                                        if self._es_fecha_valida(dia2, mes_nombre2):
                                            festivo2 = self._crear_festivo(
                                                dia2,
                                                self.MESES[mes_nombre2],
                                                descripcion2 if descripcion2 != '-' else 'Festivo local'
                                            )
                                            festivos_por_municipio[municipio_norm].append(festivo2)
                                            i += 1
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

    def _normalizar_municipio(self, nombre: str) -> Optional[str]:
        """
        Normaliza el nombre del municipio para Cantabria.

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

        if self._debe_ignorar_linea(nombre, palabras_ignorar):
            return None

        # Ignorar si es muy largo (más de 30 caracteres probablemente es descripción)
        if len(nombre) > 30:
            return None

        # Normalizar a mayúsculas
        return nombre.upper()


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
