#!/usr/bin/env python3
"""
Script de validación end-to-end para todas las CCAA.

Verifica que:
1. Todos los scrapers se pueden importar sin errores
2. La configuración YAML tiene info de todas las CCAA
3. Los parsers de PDF funcionan con fixtures locales
4. No hay regresiones después del refactor

Uso:
    python scripts/validate_all_ccaa.py
    python scripts/validate_all_ccaa.py --verbose
    python scripts/validate_all_ccaa.py --test-parsers
"""

import sys
import argparse
from pathlib import Path
from typing import Dict, List, Tuple

# Añadir el directorio raíz al PYTHONPATH
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class CCAaValidator:
    """Validador de CCAA implementadas"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.errors = []
        self.warnings = []
        self.success_count = 0

    def log(self, message: str, level: str = "INFO"):
        """Log message con nivel"""
        if level == "ERROR":
            print(f"❌ {message}")
            self.errors.append(message)
        elif level == "WARNING":
            print(f"⚠️  {message}")
            self.warnings.append(message)
        elif level == "SUCCESS":
            print(f"✅ {message}")
            self.success_count += 1
        elif self.verbose:
            print(f"ℹ️  {message}")

    def validate_config_registry(self) -> bool:
        """Valida que el registro de CCAA existe y es válido"""
        print("\n🔍 Validando configuración centralizada...")

        try:
            from config.config_manager import registry

            ccaa_list = registry.list_ccaa()
            self.log(f"Registro cargado: {len(ccaa_list)} CCAA encontradas")

            if len(ccaa_list) != 10:
                self.log(
                    f"Esperado 10 CCAA, encontradas {len(ccaa_list)}",
                    "WARNING"
                )

            # Verificar que cada CCAA tiene metadata básica
            for ccaa_code in ccaa_list:
                info = registry.get_ccaa_info(ccaa_code)

                required_fields = ['name', 'municipios_count', 'provincias', 'boletin']

                for field in required_fields:
                    if field not in info:
                        self.log(
                            f"{ccaa_code}: Falta campo '{field}'",
                            "ERROR"
                        )

            self.log("Configuración centralizada válida", "SUCCESS")
            return True

        except Exception as e:
            self.log(f"Error cargando configuración: {e}", "ERROR")
            return False

    def validate_scraper_imports(self) -> bool:
        """Valida que todos los scrapers se pueden importar"""
        print("\n🔍 Validando imports de scrapers...")

        ccaa_scrapers = [
            ('canarias', 'CanariasLocalesScraper'),
            ('madrid', 'MadridLocalesScraper'),
            ('andalucia', 'AndaluciaLocalesScraper'),
            ('valencia', 'ValenciaLocalesScraper'),
            ('baleares', 'BalearesLocalesScraper'),
            ('cataluna', 'CatalunaLocalesScraper'),
            ('galicia', 'GaliciaLocalesScraper'),
            ('pais_vasco', 'PaisVascoLocalesScraper'),
            ('asturias', 'AsturiasLocalesScraper'),
            ('cantabria', 'CantabriaLocalesScraper'),
            ('rioja', 'RiojaLocalesScraper'),
        ]

        for ccaa_code, scraper_class in ccaa_scrapers:
            try:
                module = __import__(
                    f'scrapers.ccaa.{ccaa_code}.locales',
                    fromlist=[scraper_class]
                )
                scraper = getattr(module, scraper_class)

                # Intentar instanciar (no ejecutar)
                instance = scraper(year=2026)

                self.log(f"{ccaa_code}: Import OK ({scraper_class})", "SUCCESS")

            except Exception as e:
                self.log(
                    f"{ccaa_code}: Error importando {scraper_class}: {e}",
                    "ERROR"
                )

        return len(self.errors) == 0

    def validate_pdf_parsers(self) -> bool:
        """Valida que los parsers de PDF funcionan con fixtures"""
        print("\n🔍 Validando parsers de PDF...")

        fixtures_dir = PROJECT_ROOT / "tests" / "fixtures"

        # Asturias
        try:
            from scrapers.ccaa.asturias.pdf_parser import BOPAPDFParser

            asturias_pdf = fixtures_dir / "asturias" / "locales_2026.pdf"

            if asturias_pdf.exists():
                parser = BOPAPDFParser(str(asturias_pdf), 2026)
                festivos = parser.get_festivos_municipio("OVIEDO")

                if len(festivos) == 2:
                    self.log("Asturias (BOPAPDFParser): OK - 2 festivos", "SUCCESS")
                else:
                    self.log(
                        f"Asturias: Esperado 2 festivos, obtenido {len(festivos)}",
                        "WARNING"
                    )
            else:
                self.log("Asturias: Fixture PDF no encontrado", "WARNING")

        except Exception as e:
            self.log(f"Asturias: Error en parser: {e}", "ERROR")

        # Cantabria
        try:
            from scrapers.ccaa.cantabria.pdf_parser import BOCPDFParser

            cantabria_pdf = fixtures_dir / "cantabria" / "locales_2026.pdf"

            if cantabria_pdf.exists():
                parser = BOCPDFParser(str(cantabria_pdf), 2026)
                festivos = parser.get_festivos_municipio("SANTANDER")

                if len(festivos) == 2:
                    self.log("Cantabria (BOCPDFParser): OK - 2 festivos", "SUCCESS")
                else:
                    self.log(
                        f"Cantabria: Esperado 2 festivos, obtenido {len(festivos)}",
                        "WARNING"
                    )
            else:
                self.log("Cantabria: Fixture PDF no encontrado", "WARNING")

        except Exception as e:
            self.log(f"Cantabria: Error en parser: {e}", "ERROR")

        return len(self.errors) == 0

    def validate_base_pdf_parser(self) -> bool:
        """Valida que BasePDFParser existe y funciona"""
        print("\n🔍 Validando BasePDFParser...")

        try:
            from scrapers.parsers.base_pdf_parser import BasePDFParser

            # Verificar que tiene los métodos esperados
            required_methods = [
                'parse', '_load_pdf', '_parse_text', '_normalizar_municipio',
                'get_festivos_municipio', '_crear_festivo', '_es_fecha_valida'
            ]

            for method in required_methods:
                if not hasattr(BasePDFParser, method):
                    self.log(
                        f"BasePDFParser: Falta método '{method}'",
                        "ERROR"
                    )

            self.log("BasePDFParser: Clase base OK", "SUCCESS")
            return True

        except Exception as e:
            self.log(f"BasePDFParser: Error: {e}", "ERROR")
            return False

    def print_summary(self):
        """Imprime resumen de validación"""
        print("\n" + "=" * 70)
        print("📊 RESUMEN DE VALIDACIÓN")
        print("=" * 70)

        print(f"\n✅ Validaciones exitosas: {self.success_count}")

        if self.warnings:
            print(f"\n⚠️  Advertencias ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   - {warning}")

        if self.errors:
            print(f"\n❌ Errores ({len(self.errors)}):")
            for error in self.errors:
                print(f"   - {error}")

        print("\n" + "=" * 70)

        if self.errors:
            print("\n❌ VALIDACIÓN FALLIDA")
            return False
        elif self.warnings:
            print("\n⚠️  VALIDACIÓN COMPLETA CON ADVERTENCIAS")
            return True
        else:
            print("\n✅ VALIDACIÓN EXITOSA - TODO OK")
            return True

    def run_all_validations(self, test_parsers: bool = True) -> bool:
        """Ejecuta todas las validaciones"""
        print("🚀 Iniciando validación de CCAA...")

        # 1. Validar configuración
        self.validate_config_registry()

        # 2. Validar imports
        self.validate_scraper_imports()

        # 3. Validar BasePDFParser
        self.validate_base_pdf_parser()

        # 4. Validar parsers de PDF (opcional)
        if test_parsers:
            self.validate_pdf_parsers()

        # 5. Imprimir resumen
        return self.print_summary()


def main():
    parser = argparse.ArgumentParser(
        description="Valida que todas las CCAA están correctamente implementadas"
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Mostrar información detallada'
    )
    parser.add_argument(
        '--test-parsers', '-p',
        action='store_true',
        default=True,
        help='Probar parsers de PDF con fixtures (default: True)'
    )
    parser.add_argument(
        '--no-test-parsers',
        action='store_false',
        dest='test_parsers',
        help='No probar parsers de PDF'
    )

    args = parser.parse_args()

    validator = CCAaValidator(verbose=args.verbose)
    success = validator.run_all_validations(test_parsers=args.test_parsers)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
