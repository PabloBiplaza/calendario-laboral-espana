"""
Parser base para PDFs de boletines oficiales.

Este parser abstrae la lógica común de extraer festivos locales
de PDFs de diferentes CCAA, eliminando duplicación.
"""

import re
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import pdfplumber


class BasePDFParser(ABC):
    """
    Clase base abstracta para parsers de PDF.

    Los parsers específicos de cada CCAA heredan de esta clase
    e implementan los métodos abstractos con lógica específica.
    """

    # Diccionario de meses en español (compartido por todos)
    MESES = {
        'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
        'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
        'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
    }

    def __init__(self, pdf_path: str, year: int):
        """
        Inicializa el parser.

        Args:
            pdf_path: Ruta al archivo PDF
            year: Año de los festivos
        """
        self.pdf_path = pdf_path
        self.year = year
        self._cached_festivos: Optional[Dict[str, List[Dict]]] = None

    def parse(self) -> Dict[str, List[Dict]]:
        """
        Extrae todos los festivos del PDF.

        Returns:
            Dict con municipio como clave y lista de festivos como valor

        Note:
            Los resultados se cachean para evitar reparsear múltiples veces
        """
        if self._cached_festivos is not None:
            return self._cached_festivos

        text = self._load_pdf()
        self._cached_festivos = self._parse_text(text)
        return self._cached_festivos

    def _load_pdf(self) -> str:
        """
        Carga el PDF y extrae todo el texto.

        Returns:
            Texto completo del PDF
        """
        with pdfplumber.open(self.pdf_path) as pdf:
            all_text = ''

            # Determinar qué páginas extraer
            pages_to_extract = self._get_pages_to_extract(pdf)

            for page in pages_to_extract:
                all_text += page.extract_text() + '\n'

        return all_text

    def _get_pages_to_extract(self, pdf) -> List:
        """
        Determina qué páginas del PDF extraer.

        Por defecto extrae todas, pero las subclases pueden personalizar
        (ej: Cantabria omite la página 1 que tiene festivos nacionales)

        Args:
            pdf: Objeto pdfplumber.PDF

        Returns:
            Lista de páginas a extraer
        """
        return pdf.pages

    @abstractmethod
    def _parse_text(self, text: str) -> Dict[str, List[Dict]]:
        """
        Parsea el texto del PDF y extrae festivos.

        Este método DEBE ser implementado por cada subclase con
        la lógica específica del formato de su CCAA.

        Args:
            text: Texto completo del PDF

        Returns:
            Dict con municipio como clave y lista de festivos como valor
        """
        pass

    @abstractmethod
    def _normalizar_municipio(self, nombre: str) -> Optional[str]:
        """
        Normaliza el nombre de un municipio.

        Cada CCAA tiene reglas ligeramente diferentes para filtrar
        líneas que no son municipios (descripciones, fechas, etc.)

        Args:
            nombre: Nombre del municipio sin normalizar

        Returns:
            Nombre normalizado en mayúsculas, o None si debe ignorarse
        """
        pass

    def get_festivos_municipio(self, municipio: str) -> List[Dict]:
        """
        Obtiene los festivos de un municipio específico.

        Búsqueda case-insensitive con fallback a búsqueda parcial.

        Args:
            municipio: Nombre del municipio

        Returns:
            Lista de festivos del municipio
        """
        festivos_todos = self.parse()
        municipio_upper = municipio.upper()

        # Primero: búsqueda exacta
        if municipio_upper in festivos_todos:
            return festivos_todos[municipio_upper]

        # Segundo: búsqueda case-insensitive exacta
        for key, festivos in festivos_todos.items():
            if key.upper() == municipio_upper:
                return festivos

        # Tercero: búsqueda parcial
        for key, festivos in festivos_todos.items():
            if municipio_upper in key.upper() or key.upper() in municipio_upper:
                return festivos

        return []

    def _crear_festivo(self, dia: int, mes: int, descripcion: str) -> Dict:
        """
        Helper para crear un diccionario de festivo con formato estándar.

        Args:
            dia: Día del mes (1-31)
            mes: Mes (1-12)
            descripcion: Descripción del festivo

        Returns:
            Dict con formato estándar de festivo
        """
        mes_nombre = [k for k, v in self.MESES.items() if v == mes][0]

        return {
            'fecha': f'{self.year}-{mes:02d}-{dia:02d}',
            'descripcion': descripcion,
            'fecha_texto': f'{dia} de {mes_nombre}'
        }

    def _es_fecha_valida(self, dia: int, mes_nombre: str) -> bool:
        """
        Verifica si una fecha es válida.

        Args:
            dia: Día del mes
            mes_nombre: Nombre del mes en español (minúsculas)

        Returns:
            True si es válida
        """
        return mes_nombre in self.MESES and 1 <= dia <= 31

    def _parsear_fecha(self, texto: str) -> Optional[tuple]:
        """
        Intenta extraer una fecha del texto.

        Args:
            texto: Texto que podría contener una fecha

        Returns:
            Tupla (dia, mes, descripcion) o None si no encuentra fecha
        """
        # Patrón común: "15 de mayo" o "15 mayo"
        match = re.match(r'^(\d{1,2})\s+(?:de\s+)?(\w+)\s*(.*)$', texto, re.IGNORECASE)

        if match:
            dia = int(match.group(1))
            mes_nombre = match.group(2).lower()
            descripcion = match.group(3).strip()

            if self._es_fecha_valida(dia, mes_nombre):
                return (dia, self.MESES[mes_nombre], descripcion)

        return None

    def _debe_ignorar_linea(self, linea: str, palabras_ignorar: List[str]) -> bool:
        """
        Verifica si una línea debe ser ignorada.

        Args:
            linea: Línea a verificar
            palabras_ignorar: Lista de palabras clave a buscar

        Returns:
            True si la línea debe ignorarse
        """
        if not linea or not linea.strip():
            return True

        linea_lower = linea.lower()

        for palabra in palabras_ignorar:
            if palabra in linea_lower:
                return True

        return False


class SimplePDFTableParser(BasePDFParser):
    """
    Parser para PDFs con formato de tabla simple.

    Este parser es útil para PDFs que tienen una estructura clara
    de tabla con columnas: MUNICIPIO | FESTIVO | FECHA
    """

    def _parse_text(self, text: str) -> Dict[str, List[Dict]]:
        """
        Implementación para tablas simples.

        Las subclases pueden sobrescribir este método o usar el patrón
        de template method sobrescribiendo métodos más específicos.
        """
        raise NotImplementedError(
            "SimplePDFTableParser es una clase base. "
            "Implementa _parse_text o usa un parser más específico."
        )
