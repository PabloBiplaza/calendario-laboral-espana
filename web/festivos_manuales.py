"""
Festivos añadidos manualmente por el usuario sobre un calendario generado.

Se guardan en la sesión aparte de los oficiales (``festivos_manuales``) para
poder quitarlos sin perder el festivo oficial que sustituyen. La vista, el PDF
y el CSV trabajan siempre con la lista combinada de ``combinar_festivos``.
"""

import uuid
from datetime import date
from typing import Dict, List, Optional, Tuple

# Tipos admitidos → texto para el usuario
TIPOS = {
    'nacional': 'Nacional',
    'autonomico': 'Autonómico',
    'local': 'Local',
    'empresa': 'Propio de empresa',
}

MAX_DESCRIPCION = 80
MAX_ETIQUETA = 40
MAX_FESTIVOS_MANUALES = 60

_MESES = [
    'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio',
    'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
]


class FestivoInvalido(ValueError):
    """Dato de formulario no válido; el mensaje se puede mostrar al usuario."""


def crear_festivo_manual(fecha: str, descripcion: str, tipo: str,
                         etiqueta: str, year: int,
                         existentes: List[Dict]) -> Dict:
    """
    Valida los datos del formulario y devuelve el festivo manual listo para
    guardar. Lanza FestivoInvalido con un mensaje legible si algo falla.
    """
    fecha = (fecha or '').strip()
    descripcion = ' '.join((descripcion or '').split())
    tipo = (tipo or '').strip()
    etiqueta = ' '.join((etiqueta or '').split())

    try:
        fecha_obj = date.fromisoformat(fecha)
    except ValueError:
        raise FestivoInvalido('La fecha no es válida.')

    if fecha_obj.year != year:
        raise FestivoInvalido(f'La fecha debe ser del año {year}.')

    if not descripcion:
        raise FestivoInvalido('Escribe una descripción para el festivo.')
    if len(descripcion) > MAX_DESCRIPCION:
        raise FestivoInvalido(
            f'La descripción no puede superar {MAX_DESCRIPCION} caracteres.')

    if tipo not in TIPOS:
        raise FestivoInvalido('Elige un tipo de festivo válido.')

    if len(etiqueta) > MAX_ETIQUETA:
        raise FestivoInvalido(
            f'La etiqueta no puede superar {MAX_ETIQUETA} caracteres.')

    if len(existentes) >= MAX_FESTIVOS_MANUALES:
        raise FestivoInvalido(
            f'Has alcanzado el máximo de {MAX_FESTIVOS_MANUALES} festivos añadidos.')

    if any(f['fecha'] == fecha_obj.isoformat() for f in existentes):
        raise FestivoInvalido(
            'Ya has añadido un festivo ese día. Quítalo antes de añadir otro.')

    festivo = {
        'id': uuid.uuid4().hex[:12],
        'fecha': fecha_obj.isoformat(),
        'fecha_texto': f'{fecha_obj.day} de {_MESES[fecha_obj.month - 1]}',
        'descripcion': descripcion,
        'tipo': tipo,
        'ambito': 'empresa' if tipo == 'empresa' else 'manual',
        'origen': 'manual',
        'year': year,
    }
    if etiqueta:
        festivo['etiqueta'] = etiqueta
    return festivo


def eliminar_festivo_manual(manuales: List[Dict], festivo_id: str) -> Tuple[List[Dict], bool]:
    """Devuelve la lista sin el festivo indicado y si se ha encontrado."""
    restantes = [f for f in manuales if f.get('id') != festivo_id]
    return restantes, len(restantes) != len(manuales)


def combinar_festivos(oficiales: List[Dict], manuales: Optional[List[Dict]]) -> List[Dict]:
    """
    Une oficiales y manuales ordenados por fecha. Si un manual cae en la misma
    fecha que un oficial, lo sustituye (y guarda su descripción en 'sustituye').
    """
    por_fecha = {f['fecha']: dict(f) for f in oficiales}

    for manual in manuales or []:
        combinado = dict(manual)
        oficial = por_fecha.get(manual['fecha'])
        if oficial and oficial.get('origen') != 'manual':
            combinado['sustituye'] = oficial.get('descripcion', '')
        por_fecha[manual['fecha']] = combinado

    return sorted(por_fecha.values(), key=lambda f: f['fecha'])


def es_dia_empresa(festivo: Dict) -> bool:
    """Los días propios de empresa no son fiestas laborales oficiales."""
    return festivo.get('tipo') == 'empresa'


def contar_festivos(festivos: List[Dict]) -> Dict[str, int]:
    """Cuenta fiestas laborales (oficiales o añadidas como tales) y días de empresa."""
    empresa = sum(1 for f in festivos if es_dia_empresa(f))
    return {'laborales': len(festivos) - empresa, 'empresa': empresa}


def tiene_locales(festivos: List[Dict]) -> bool:
    return any(f.get('tipo') == 'local' for f in festivos)
