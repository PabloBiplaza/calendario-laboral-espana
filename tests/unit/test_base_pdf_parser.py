"""
Tests unitarios para el BasePDFParser y sus utilidades
"""

import pytest
from scrapers.parsers.base_pdf_parser import BasePDFParser


class TestHelperMethods:
    """Tests para los métodos helper de BasePDFParser"""

    def test_crear_festivo(self):
        """Verifica que _crear_festivo genera el formato correcto"""
        # Crear un parser de prueba (mock)
        class MockParser(BasePDFParser):
            def _parse_text(self, text):
                return {}
            def _normalizar_municipio(self, nombre):
                return nombre.upper()

        parser = MockParser('dummy.pdf', 2026)

        festivo = parser._crear_festivo(15, 5, 'San Isidro')

        assert festivo['fecha'] == '2026-05-15'
        assert festivo['descripcion'] == 'San Isidro'
        assert festivo['fecha_texto'] == '15 de mayo'

    def test_crear_festivo_navidad(self):
        """Verifica festivo de diciembre"""
        class MockParser(BasePDFParser):
            def _parse_text(self, text):
                return {}
            def _normalizar_municipio(self, nombre):
                return nombre.upper()

        parser = MockParser('dummy.pdf', 2026)

        festivo = parser._crear_festivo(25, 12, 'Navidad')

        assert festivo['fecha'] == '2026-12-25'
        assert festivo['descripcion'] == 'Navidad'
        assert festivo['fecha_texto'] == '25 de diciembre'

    def test_es_fecha_valida_correcta(self):
        """Verifica que detecta fechas válidas"""
        class MockParser(BasePDFParser):
            def _parse_text(self, text):
                return {}
            def _normalizar_municipio(self, nombre):
                return nombre.upper()

        parser = MockParser('dummy.pdf', 2026)

        assert parser._es_fecha_valida(15, 'mayo') is True
        assert parser._es_fecha_valida(1, 'enero') is True
        assert parser._es_fecha_valida(31, 'diciembre') is True

    def test_es_fecha_valida_incorrecta(self):
        """Verifica que rechaza fechas inválidas"""
        class MockParser(BasePDFParser):
            def _parse_text(self, text):
                return {}
            def _normalizar_municipio(self, nombre):
                return nombre.upper()

        parser = MockParser('dummy.pdf', 2026)

        assert parser._es_fecha_valida(32, 'enero') is False
        assert parser._es_fecha_valida(0, 'mayo') is False
        assert parser._es_fecha_valida(15, 'mesfalso') is False

    def test_parsear_fecha_formato_completo(self):
        """Verifica que parsea fecha con 'de'"""
        class MockParser(BasePDFParser):
            def _parse_text(self, text):
                return {}
            def _normalizar_municipio(self, nombre):
                return nombre.upper()

        parser = MockParser('dummy.pdf', 2026)

        resultado = parser._parsear_fecha('15 de mayo San Isidro')

        assert resultado is not None
        assert resultado[0] == 15  # día
        assert resultado[1] == 5   # mes
        assert resultado[2] == 'San Isidro'  # descripción

    def test_parsear_fecha_sin_de(self):
        """Verifica que parsea fecha sin 'de'"""
        class MockParser(BasePDFParser):
            def _parse_text(self, text):
                return {}
            def _normalizar_municipio(self, nombre):
                return nombre.upper()

        parser = MockParser('dummy.pdf', 2026)

        resultado = parser._parsear_fecha('15 mayo San Isidro')

        assert resultado is not None
        assert resultado[0] == 15
        assert resultado[1] == 5
        assert resultado[2] == 'San Isidro'

    def test_parsear_fecha_invalida(self):
        """Verifica que devuelve None para texto sin fecha"""
        class MockParser(BasePDFParser):
            def _parse_text(self, text):
                return {}
            def _normalizar_municipio(self, nombre):
                return nombre.upper()

        parser = MockParser('dummy.pdf', 2026)

        resultado = parser._parsear_fecha('SANTANDER')

        assert resultado is None

    def test_debe_ignorar_linea_vacia(self):
        """Verifica que ignora líneas vacías"""
        class MockParser(BasePDFParser):
            def _parse_text(self, text):
                return {}
            def _normalizar_municipio(self, nombre):
                return nombre.upper()

        parser = MockParser('dummy.pdf', 2026)

        assert parser._debe_ignorar_linea('', ['boletín']) is True
        assert parser._debe_ignorar_linea('  ', ['boletín']) is True

    def test_debe_ignorar_linea_con_palabra_clave(self):
        """Verifica que ignora líneas con palabras clave"""
        class MockParser(BasePDFParser):
            def _parse_text(self, text):
                return {}
            def _normalizar_municipio(self, nombre):
                return nombre.upper()

        parser = MockParser('dummy.pdf', 2026)

        assert parser._debe_ignorar_linea('Boletín Oficial', ['boletín']) is True
        assert parser._debe_ignorar_linea('BOPA núm 123', ['núm']) is True
        assert parser._debe_ignorar_linea('SANTANDER', ['boletín']) is False


class TestCaching:
    """Tests para el caching de resultados"""

    def test_parse_cachea_resultados(self):
        """Verifica que parse() cachea los resultados"""

        class CountingParser(BasePDFParser):
            parse_count = 0

            def _load_pdf(self):
                return "texto de prueba"

            def _parse_text(self, text):
                CountingParser.parse_count += 1
                return {'OVIEDO': [{'fecha': '2026-05-15', 'descripcion': 'Test'}]}

            def _normalizar_municipio(self, nombre):
                return nombre.upper()

        parser = CountingParser('dummy.pdf', 2026)

        # Primera llamada: debe parsear
        result1 = parser.parse()
        assert CountingParser.parse_count == 1

        # Segunda llamada: debe usar caché
        result2 = parser.parse()
        assert CountingParser.parse_count == 1  # No incrementa

        # Verificar que los resultados son los mismos
        assert result1 == result2

    def test_get_festivos_municipio_usa_cache(self):
        """Verifica que get_festivos_municipio usa el caché"""

        class CountingParser(BasePDFParser):
            parse_count = 0

            def _load_pdf(self):
                return "texto de prueba"

            def _parse_text(self, text):
                CountingParser.parse_count += 1
                return {
                    'OVIEDO': [{'fecha': '2026-05-15', 'descripcion': 'San Isidro'}],
                    'GIJÓN': [{'fecha': '2026-08-15', 'descripcion': 'Asunción'}]
                }

            def _normalizar_municipio(self, nombre):
                return nombre.upper()

        parser = CountingParser('dummy.pdf', 2026)

        # Primera consulta
        festivos_oviedo = parser.get_festivos_municipio('OVIEDO')
        assert CountingParser.parse_count == 1
        assert len(festivos_oviedo) == 1

        # Segunda consulta (otro municipio): debe usar caché
        festivos_gijon = parser.get_festivos_municipio('GIJÓN')
        assert CountingParser.parse_count == 1  # No incrementa
        assert len(festivos_gijon) == 1


class TestGetFestivosMunicipio:
    """Tests para búsqueda de municipios"""

    def test_busqueda_exacta(self):
        """Verifica búsqueda exacta (case-insensitive)"""

        class MockParser(BasePDFParser):
            def _load_pdf(self):
                return ""

            def _parse_text(self, text):
                return {
                    'OVIEDO': [{'fecha': '2026-05-15', 'descripcion': 'San Isidro'}],
                }

            def _normalizar_municipio(self, nombre):
                return nombre.upper()

        parser = MockParser('dummy.pdf', 2026)

        festivos = parser.get_festivos_municipio('oviedo')
        assert len(festivos) == 1

        festivos = parser.get_festivos_municipio('OVIEDO')
        assert len(festivos) == 1

        festivos = parser.get_festivos_municipio('Oviedo')
        assert len(festivos) == 1

    def test_busqueda_parcial(self):
        """Verifica búsqueda parcial"""

        class MockParser(BasePDFParser):
            def _load_pdf(self):
                return ""

            def _parse_text(self, text):
                return {
                    'CASTRO URDIALES': [{'fecha': '2026-06-26', 'descripcion': 'San Pelayo'}],
                }

            def _normalizar_municipio(self, nombre):
                return nombre.upper()

        parser = MockParser('dummy.pdf', 2026)

        # Búsqueda parcial "CASTRO" debe encontrar "CASTRO URDIALES"
        festivos = parser.get_festivos_municipio('CASTRO')
        assert len(festivos) == 1

    def test_busqueda_no_encontrada(self):
        """Verifica que devuelve lista vacía si no encuentra"""

        class MockParser(BasePDFParser):
            def _load_pdf(self):
                return ""

            def _parse_text(self, text):
                return {
                    'OVIEDO': [{'fecha': '2026-05-15', 'descripcion': 'San Isidro'}],
                }

            def _normalizar_municipio(self, nombre):
                return nombre.upper()

        parser = MockParser('dummy.pdf', 2026)

        festivos = parser.get_festivos_municipio('MADRID')
        assert festivos == []


class TestMesesDiccionario:
    """Tests para el diccionario de meses"""

    def test_meses_completo(self):
        """Verifica que el diccionario de meses tiene 12 entradas"""

        class MockParser(BasePDFParser):
            def _parse_text(self, text):
                return {}
            def _normalizar_municipio(self, nombre):
                return nombre.upper()

        parser = MockParser('dummy.pdf', 2026)

        assert len(parser.MESES) == 12

    def test_meses_valores_correctos(self):
        """Verifica que los meses tienen los valores correctos"""

        class MockParser(BasePDFParser):
            def _parse_text(self, text):
                return {}
            def _normalizar_municipio(self, nombre):
                return nombre.upper()

        parser = MockParser('dummy.pdf', 2026)

        assert parser.MESES['enero'] == 1
        assert parser.MESES['junio'] == 6
        assert parser.MESES['diciembre'] == 12
