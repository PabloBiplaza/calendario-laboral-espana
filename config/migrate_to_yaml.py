"""
Script de migración y validación del YAML centralizado.

Este script:
1. Verifica que el YAML tiene toda la información de los JSONs existentes
2. Genera un reporte de diferencias/faltantes
3. Permite actualizar el YAML con datos de los JSONs (si es necesario)

Uso:
    python config/migrate_to_yaml.py --validate
    python config/migrate_to_yaml.py --update
"""

import json
import yaml
import argparse
from pathlib import Path
from typing import Dict, List, Tuple


class YAMLMigrationValidator:
    """Valida y migra la configuración de JSONs a YAML"""

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).parent.parent
        self.config_dir = self.project_root / "config"
        self.yaml_path = self.config_dir / "ccaa_registry.yaml"

        self.yaml_data = None
        self.errors = []
        self.warnings = []

    def load_yaml(self) -> None:
        """Carga el archivo YAML"""
        with open(self.yaml_path, 'r', encoding='utf-8') as f:
            self.yaml_data = yaml.safe_load(f)

    def load_json(self, file_path: Path) -> Dict:
        """Carga un archivo JSON"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def validate_municipios_files_exist(self) -> None:
        """Verifica que todos los archivos de municipios existan"""
        print("\n🔍 Validando archivos de municipios...")

        for ccaa_code, ccaa_data in self.yaml_data['ccaa'].items():
            municipios_file = ccaa_data.get('municipios_file')

            if not municipios_file:
                self.errors.append(
                    f"❌ {ccaa_code}: No tiene 'municipios_file' definido"
                )
                continue

            full_path = self.project_root / municipios_file

            if not full_path.exists():
                self.errors.append(
                    f"❌ {ccaa_code}: Archivo no existe: {municipios_file}"
                )
            else:
                # Verificar que el JSON es válido
                try:
                    municipios = self.load_json(full_path)

                    # Verificar estructura
                    if isinstance(municipios, dict):
                        municipios_count = len(municipios)
                    elif isinstance(municipios, list):
                        municipios_count = len(municipios)
                    else:
                        self.errors.append(
                            f"❌ {ccaa_code}: JSON con formato inválido"
                        )
                        continue

                    # Comparar con el count declarado
                    declared_count = ccaa_data.get('municipios_count', 0)

                    if municipios_count != declared_count:
                        self.warnings.append(
                            f"⚠️  {ccaa_code}: Municipios en JSON ({municipios_count}) "
                            f"!= declarado en YAML ({declared_count})"
                        )
                    else:
                        print(f"   ✅ {ccaa_code}: {municipios_count} municipios OK")

                except json.JSONDecodeError:
                    self.errors.append(
                        f"❌ {ccaa_code}: JSON inválido: {municipios_file}"
                    )

    def validate_urls_format(self) -> None:
        """Valida que todas las URLs tengan formato correcto"""
        print("\n🔍 Validando URLs...")

        for ccaa_code, ccaa_data in self.yaml_data['ccaa'].items():
            urls = ccaa_data.get('urls', {})

            if not urls:
                self.warnings.append(
                    f"⚠️  {ccaa_code}: No tiene URLs definidas"
                )
                continue

            # Verificar que tenga al menos locales o autonómicos
            has_locales = bool(urls.get('locales'))
            has_autonomicos = bool(urls.get('autonomicos'))

            if not (has_locales or has_autonomicos):
                self.errors.append(
                    f"❌ {ccaa_code}: No tiene URLs de locales ni autonómicos"
                )

            # Verificar formato de URLs
            for tipo in ['locales', 'autonomicos']:
                if tipo in urls:
                    for year, url in urls[tipo].items():
                        if not url.startswith('http'):
                            self.errors.append(
                                f"❌ {ccaa_code}: URL inválida ({tipo}/{year}): {url}"
                            )

        if not self.errors:
            print("   ✅ Todas las URLs tienen formato válido")

    def validate_required_fields(self) -> None:
        """Valida que todas las CCAA tengan los campos requeridos"""
        print("\n🔍 Validando campos requeridos...")

        required_fields = ['name', 'municipios_count', 'provincias', 'boletin', 'formato']

        for ccaa_code, ccaa_data in self.yaml_data['ccaa'].items():
            missing_fields = []

            for field in required_fields:
                if field not in ccaa_data:
                    missing_fields.append(field)

            if missing_fields:
                self.errors.append(
                    f"❌ {ccaa_code}: Faltan campos: {', '.join(missing_fields)}"
                )
            else:
                print(f"   ✅ {ccaa_code}: Todos los campos requeridos presentes")

    def validate_metadata(self) -> None:
        """Valida que los metadatos globales sean correctos"""
        print("\n🔍 Validando metadatos globales...")

        metadata = self.yaml_data.get('metadata', {})

        # Contar CCAA
        declared_ccaa = metadata.get('total_ccaa', 0)
        actual_ccaa = len(self.yaml_data['ccaa'])

        if declared_ccaa != actual_ccaa:
            self.errors.append(
                f"❌ Metadatos: total_ccaa declarado ({declared_ccaa}) "
                f"!= real ({actual_ccaa})"
            )
        else:
            print(f"   ✅ Total CCAA: {actual_ccaa}")

        # Contar municipios totales
        declared_municipios = metadata.get('total_municipios', 0)
        actual_municipios = sum(
            ccaa_data.get('municipios_count', 0)
            for ccaa_data in self.yaml_data['ccaa'].values()
        )

        if declared_municipios != actual_municipios:
            self.warnings.append(
                f"⚠️  Metadatos: total_municipios declarado ({declared_municipios}) "
                f"!= suma de CCAA ({actual_municipios})"
            )
        else:
            print(f"   ✅ Total municipios: {actual_municipios}")

        # Verificar fecha de actualización
        if 'ultima_actualizacion' in metadata:
            print(f"   ✅ Última actualización: {metadata['ultima_actualizacion']}")

    def validate_discovery_methods(self) -> None:
        """Valida que los métodos de auto-discovery estén bien configurados"""
        print("\n🔍 Validando métodos de auto-discovery...")

        valid_methods = [
            'boe_rdf', 'bocm_search', 'boja_sequential', 'dogv_search',
            'predictable_urls', 'manual', 'rdf_metadata', 'opendata_euskadi',
            'bopa_direct', 'boc_search'
        ]

        for ccaa_code, ccaa_data in self.yaml_data['ccaa'].items():
            auto_discovery = ccaa_data.get('auto_discovery', False)
            method = ccaa_data.get('discovery_method')

            if auto_discovery and not method:
                self.warnings.append(
                    f"⚠️  {ccaa_code}: auto_discovery=true pero sin discovery_method"
                )
            elif method and method not in valid_methods:
                self.warnings.append(
                    f"⚠️  {ccaa_code}: discovery_method desconocido: {method}"
                )

        ccaa_with_discovery = sum(
            1 for ccaa_data in self.yaml_data['ccaa'].values()
            if ccaa_data.get('auto_discovery', False)
        )

        print(f"   ✅ {ccaa_with_discovery} CCAA con auto-discovery habilitado")

    def print_report(self) -> None:
        """Imprime el reporte de validación"""
        print("\n" + "=" * 70)
        print("📊 REPORTE DE VALIDACIÓN")
        print("=" * 70)

        if self.errors:
            print(f"\n❌ ERRORES ({len(self.errors)}):")
            for error in self.errors:
                print(f"   {error}")

        if self.warnings:
            print(f"\n⚠️  ADVERTENCIAS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   {warning}")

        if not self.errors and not self.warnings:
            print("\n✅ ¡TODO CORRECTO! El YAML está perfectamente configurado.")
        elif not self.errors:
            print("\n✅ Sin errores críticos. Solo advertencias menores.")
        else:
            print(f"\n❌ Se encontraron {len(self.errors)} errores que deben corregirse.")

        print("=" * 70 + "\n")

    def run_validation(self) -> bool:
        """Ejecuta todas las validaciones"""
        print("🚀 Iniciando validación del YAML centralizado...")

        self.load_yaml()

        self.validate_required_fields()
        self.validate_municipios_files_exist()
        self.validate_urls_format()
        self.validate_metadata()
        self.validate_discovery_methods()

        self.print_report()

        return len(self.errors) == 0


def main():
    parser = argparse.ArgumentParser(
        description="Validador de migración a YAML centralizado"
    )
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Valida el YAML contra los JSONs existentes'
    )
    parser.add_argument(
        '--update',
        action='store_true',
        help='Actualiza el YAML con datos de los JSONs (TODO)'
    )

    args = parser.parse_args()

    validator = YAMLMigrationValidator()

    if args.validate or not (args.validate or args.update):
        # Por defecto, validar
        success = validator.run_validation()
        exit(0 if success else 1)

    if args.update:
        print("⚠️  Función --update aún no implementada")
        print("   Por ahora, el YAML se mantiene manualmente")
        exit(1)


if __name__ == "__main__":
    main()
