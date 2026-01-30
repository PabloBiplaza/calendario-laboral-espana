"""
Calculadora de fechas relativas para festivos locales.

Este módulo proporciona funciones para calcular fechas que se expresan de forma relativa:
- Ordinales: "segundo viernes de septiembre", "último lunes de mayo"
- Litúrgicas: "Viernes de carnaval", "Lunes de Pentecostés"
- Santoral relativo: "viernes de la semana siguiente a San Lucas"

Diseñado para ser reutilizable entre años y CCAA.
"""

import calendar
import re
from datetime import datetime, timedelta
from typing import Optional, Tuple
from dateutil.easter import easter


# Mapeo de días de la semana en español a números (0=lunes, 6=domingo)
DIAS_SEMANA = {
    'lunes': 0,
    'martes': 1,
    'miércoles': 2,
    'miercoles': 2,  # Sin acento
    'jueves': 3,
    'viernes': 4,
    'sábado': 5,
    'sabado': 5,  # Sin acento
    'domingo': 6,
}

# Mapeo de ordinales en español a números
ORDINALES = {
    'primer': 1,
    'primero': 1,
    'primera': 1,
    'segundo': 2,
    'segunda': 2,
    'tercer': 3,
    'tercero': 3,
    'tercera': 3,
    'cuarto': 4,
    'cuarta': 4,
    'quinto': 5,
    'quinta': 5,
    'último': -1,
    'ultima': -1,
    'penúltimo': -2,
    'penultimo': -2,
}

# Mapeo de meses en español a números
MESES = {
    'enero': 1,
    'febrero': 2,
    'marzo': 3,
    'abril': 4,
    'mayo': 5,
    'junio': 6,
    'julio': 7,
    'agosto': 8,
    'septiembre': 9,
    'setiembre': 9,  # Variante
    'octubre': 10,
    'noviembre': 11,
    'diciembre': 12,
}

# Mapeo de santos con fechas fijas conocidas
SANTORAL = {
    'san lucas': (10, 18),  # 18 de octubre
    'san francisco javier': (12, 3),  # 3 de diciembre
    'san josé': (3, 19),  # 19 de marzo
    'santa lucía': (12, 13),  # 13 de diciembre
    'san juan': (6, 24),  # 24 de junio
    'san pedro': (6, 29),  # 29 de junio
    'santiago': (7, 25),  # 25 de julio
    'san martín': (11, 11),  # 11 de noviembre
    'san andrés': (11, 30),  # 30 de noviembre
}


def calcular_pascua(year: int) -> datetime:
    """
    Calcula la fecha de Pascua para un año dado.

    Args:
        year: Año

    Returns:
        Fecha de Pascua (domingo de Resurrección)
    """
    return easter(year)


def calcular_carnaval(year: int, dia_semana: str) -> Optional[datetime]:
    """
    Calcula fechas de Carnaval relativas a Pascua.

    Carnaval termina el martes antes del Miércoles de Ceniza.
    Miércoles de Ceniza = 46 días antes de Pascua.

    Args:
        year: Año
        dia_semana: 'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo'

    Returns:
        Fecha del día de carnaval solicitado, o None si no es válido
    """
    pascua = calcular_pascua(year)

    # Miércoles de Ceniza = Pascua - 46 días
    miercoles_ceniza = pascua - timedelta(days=46)

    # Días antes del Miércoles de Ceniza
    dias_antes = {
        'domingo': 2,   # Domingo de Carnaval
        'lunes': 1,     # Lunes de Carnaval
        'martes': 0,    # Martes de Carnaval (último día)
        'miércoles': -1,
        'jueves': 3,    # Jueves Lardero
        'viernes': 4,   # Viernes antes de Carnaval
        'sábado': 5,
    }

    dia_normalizado = dia_semana.lower()
    if dia_normalizado not in dias_antes:
        return None

    return miercoles_ceniza - timedelta(days=dias_antes[dia_normalizado])


def calcular_pentecostes(year: int, dia: str = 'lunes') -> Optional[datetime]:
    """
    Calcula fechas de Pentecostés.

    Pentecostés = 50 días después de Pascua (domingo).
    Lunes de Pentecostés = 51 días después de Pascua.

    Args:
        year: Año
        dia: 'domingo', 'lunes', 'segundo día' (martes)

    Returns:
        Fecha solicitada de Pentecostés
    """
    pascua = calcular_pascua(year)

    dia_normalizado = dia.lower().strip()

    if dia_normalizado in ['domingo', 'pentecostés', 'pentecostes']:
        return pascua + timedelta(days=49)  # Domingo de Pentecostés
    elif dia_normalizado == 'lunes':
        return pascua + timedelta(days=50)  # Lunes de Pentecostés
    elif dia_normalizado in ['segundo día', 'segundo dia', 'martes']:
        return pascua + timedelta(days=51)  # Martes de Pentecostés

    return None


def calcular_ascension(year: int) -> datetime:
    """
    Calcula la fecha de la Ascensión.

    Ascensión = 39 días después de Pascua (jueves).

    Args:
        year: Año

    Returns:
        Fecha de la Ascensión
    """
    pascua = calcular_pascua(year)
    return pascua + timedelta(days=39)


def calcular_corpus_christi(year: int) -> datetime:
    """
    Calcula la fecha del Corpus Christi.

    Corpus Christi = 60 días después de Pascua (jueves).

    Args:
        year: Año

    Returns:
        Fecha del Corpus Christi
    """
    pascua = calcular_pascua(year)
    return pascua + timedelta(days=60)


def obtener_nth_dia_semana_del_mes(year: int, month: int, dia_semana: int, n: int) -> Optional[datetime]:
    """
    Obtiene el N-ésimo día de la semana de un mes.

    Ejemplos:
        - 2º viernes de septiembre
        - Último lunes de mayo
        - 1er domingo de junio

    Args:
        year: Año
        month: Mes (1-12)
        dia_semana: Día de la semana (0=lunes, 6=domingo)
        n: Ordinal (1=primero, 2=segundo, -1=último, -2=penúltimo)

    Returns:
        Fecha del día solicitado, o None si no existe
    """
    # Validar entrada
    if not (1 <= month <= 12):
        return None
    if not (0 <= dia_semana <= 6):
        return None

    # Obtener todos los días de ese día de la semana en el mes
    cal = calendar.monthcalendar(year, month)
    dias_del_mes = []

    for semana in cal:
        dia = semana[dia_semana]
        if dia != 0:  # 0 significa que ese día no pertenece al mes
            dias_del_mes.append(dia)

    # Seleccionar el N-ésimo
    if n > 0:
        # Positivo: contar desde el principio
        if n <= len(dias_del_mes):
            return datetime(year, month, dias_del_mes[n - 1])
    else:
        # Negativo: contar desde el final
        if abs(n) <= len(dias_del_mes):
            return datetime(year, month, dias_del_mes[n])

    return None


def calcular_ordinal_simple(year: int, texto: str) -> Optional[Tuple[datetime, str]]:
    """
    Calcula fecha de patrón ordinal simple.

    Patrones:
        - "Primer sábado de septiembre"
        - "Segundo viernes de noviembre"
        - "Último lunes de mayo"
        - "Tercer domingo de julio"

    Args:
        year: Año
        texto: Texto con el patrón

    Returns:
        Tupla (fecha, método) o None si no coincide
    """
    # Patrón: ORDINAL + DIA_SEMANA + de + MES
    patron = r'(primer|primero|primera|segundo|segunda|tercer|tercero|tercera|cuarto|cuarta|quinto|quinta|último|ultima|penúltimo|penultimo)\s+(lunes|martes|miércoles|miercoles|jueves|viernes|sábado|sabado|domingo)\s+de\s+(\w+)'

    match = re.search(patron, texto.lower(), re.IGNORECASE)

    if not match:
        return None

    ordinal_str = match.group(1)
    dia_semana_str = match.group(2)
    mes_str = match.group(3)

    # Convertir a números
    ordinal = ORDINALES.get(ordinal_str)
    dia_semana = DIAS_SEMANA.get(dia_semana_str)
    mes = MESES.get(mes_str)

    if ordinal is None or dia_semana is None or mes is None:
        return None

    fecha = obtener_nth_dia_semana_del_mes(year, mes, dia_semana, ordinal)

    if fecha:
        return (fecha, f'ordinal_simple: {ordinal_str} {dia_semana_str} de {mes_str}')

    return None


def calcular_ordinal_compuesto(year: int, texto: str) -> Optional[Tuple[datetime, str]]:
    """
    Calcula fecha de patrón ordinal compuesto (con modificadores anterior/siguiente).

    Patrones:
        - "Lunes siguiente al primer domingo de mayo"
        - "Viernes anterior al tercer domingo de septiembre"

    Args:
        year: Año
        texto: Texto con el patrón

    Returns:
        Tupla (fecha, método) o None si no coincide
    """
    # Patrón: DIA_SEMANA + (anterior|siguiente) + al + ORDINAL + DIA_SEMANA + de + MES
    patron = r'(lunes|martes|miércoles|miercoles|jueves|viernes|sábado|sabado|domingo)\s+(anterior|siguiente)\s+al\s+(primer|primero|primera|segundo|segunda|tercer|tercero|tercera|cuarto|cuarta|último|ultima)\s+(lunes|martes|miércoles|miercoles|jueves|viernes|sábado|sabado|domingo)\s+de\s+(\w+)'

    match = re.search(patron, texto.lower(), re.IGNORECASE)

    if not match:
        return None

    dia_objetivo_str = match.group(1)
    modificador = match.group(2)  # 'anterior' o 'siguiente'
    ordinal_str = match.group(3)
    dia_base_str = match.group(4)
    mes_str = match.group(5)

    # Convertir a números
    dia_objetivo = DIAS_SEMANA.get(dia_objetivo_str)
    ordinal = ORDINALES.get(ordinal_str)
    dia_base = DIAS_SEMANA.get(dia_base_str)
    mes = MESES.get(mes_str)

    if None in [dia_objetivo, ordinal, dia_base, mes]:
        return None

    # Primero obtener la fecha base (ej: "primer domingo de mayo")
    fecha_base = obtener_nth_dia_semana_del_mes(year, mes, dia_base, ordinal)

    if not fecha_base:
        return None

    # Ahora buscar el día objetivo anterior o siguiente
    if modificador == 'siguiente':
        # Buscar el siguiente día_objetivo después de fecha_base
        dias_adelante = (dia_objetivo - fecha_base.weekday()) % 7
        if dias_adelante == 0:
            dias_adelante = 7  # Si coincide, ir a la siguiente semana
        fecha = fecha_base + timedelta(days=dias_adelante)
    else:  # 'anterior'
        # Buscar el día_objetivo anterior a fecha_base
        dias_atras = (fecha_base.weekday() - dia_objetivo) % 7
        if dias_atras == 0:
            dias_atras = 7  # Si coincide, ir a la semana anterior
        fecha = fecha_base - timedelta(days=dias_atras)

    return (fecha, f'ordinal_compuesto: {dia_objetivo_str} {modificador} al {ordinal_str} {dia_base_str} de {mes_str}')


def calcular_liturgico(year: int, texto: str) -> Optional[Tuple[datetime, str]]:
    """
    Calcula fecha litúrgica móvil.

    Patrones:
        - "Viernes de carnaval"
        - "Lunes de Pentecostés"
        - "Festividad de la Ascensión"
        - "Corpus Christi"

    Args:
        year: Año
        texto: Texto con el patrón

    Returns:
        Tupla (fecha, método) o None si no coincide
    """
    texto_lower = texto.lower()

    # Carnaval
    if 'carnaval' in texto_lower:
        patron_dia = r'(lunes|martes|miércoles|miercoles|jueves|viernes|sábado|sabado|domingo)\s+de\s+carnaval'
        match = re.search(patron_dia, texto_lower)

        if match:
            dia_semana_str = match.group(1)
            fecha = calcular_carnaval(year, dia_semana_str)

            if fecha:
                return (fecha, f'liturgico_carnaval: {dia_semana_str}')

    # Pentecostés
    if 'pentecostés' in texto_lower or 'pentecostes' in texto_lower:
        if 'segundo día' in texto_lower or 'segundo dia' in texto_lower:
            fecha = calcular_pentecostes(year, 'segundo día')
            if fecha:
                return (fecha, 'liturgico_pentecostes: segundo día')
        elif 'lunes' in texto_lower:
            fecha = calcular_pentecostes(year, 'lunes')
            if fecha:
                return (fecha, 'liturgico_pentecostes: lunes')
        else:
            fecha = calcular_pentecostes(year, 'domingo')
            if fecha:
                return (fecha, 'liturgico_pentecostes: domingo')

    # Ascensión
    if 'ascensión' in texto_lower or 'ascension' in texto_lower:
        fecha = calcular_ascension(year)
        return (fecha, 'liturgico_ascension')

    # Corpus Christi
    if 'corpus' in texto_lower:
        fecha = calcular_corpus_christi(year)
        return (fecha, 'liturgico_corpus')

    return None


def calcular_santoral_relativo(year: int, texto: str) -> Optional[Tuple[datetime, str]]:
    """
    Calcula fecha relativa a un santo.

    Patrones:
        - "Viernes de la semana siguiente a San Lucas"
        - "Lunes posterior a Santa Lucía"

    Args:
        year: Año
        texto: Texto con el patrón

    Returns:
        Tupla (fecha, método) o None si no coincide
    """
    texto_lower = texto.lower()

    # Patrón: DIA_SEMANA + de la (semana)? + (siguiente|posterior|anterior) + a? + SAN/SANTA + NOMBRE
    patron = r'(lunes|martes|miércoles|miercoles|jueves|viernes|sábado|sabado|domingo)\s+de\s+la\s+(?:semana\s+)?(siguiente|posterior|anterior)\s+a\s+(san|santa)\s+(\w+)'

    match = re.search(patron, texto_lower)

    if not match:
        return None

    dia_objetivo_str = match.group(1)
    modificador = match.group(2)  # 'siguiente', 'posterior', 'anterior'
    prefijo_santo = match.group(3)  # 'san' o 'santa'
    nombre_santo = match.group(4)

    # Construir nombre completo del santo
    santo_completo = f'{prefijo_santo} {nombre_santo}'

    # Buscar en el santoral
    fecha_santo = SANTORAL.get(santo_completo)

    if not fecha_santo:
        return None

    mes, dia = fecha_santo
    fecha_base = datetime(year, mes, dia)

    # Convertir día objetivo
    dia_objetivo = DIAS_SEMANA.get(dia_objetivo_str)

    if dia_objetivo is None:
        return None

    # Buscar el día objetivo
    if modificador in ['siguiente', 'posterior']:
        # Buscar el siguiente día_objetivo después de fecha_base
        dias_adelante = (dia_objetivo - fecha_base.weekday()) % 7
        if dias_adelante == 0:
            dias_adelante = 7  # Si coincide, ir a la siguiente semana
        fecha = fecha_base + timedelta(days=dias_adelante)
    else:  # 'anterior'
        # Buscar el día_objetivo anterior a fecha_base
        dias_atras = (fecha_base.weekday() - dia_objetivo) % 7
        if dias_atras == 0:
            dias_atras = 7  # Si coincide, ir a la semana anterior
        fecha = fecha_base - timedelta(days=dias_atras)

    return (fecha, f'santoral_relativo: {dia_objetivo_str} {modificador} a {santo_completo}')


def calcular_fecha_relativa(year: int, texto: str) -> Optional[Tuple[datetime, str]]:
    """
    Función principal que intenta calcular cualquier tipo de fecha relativa.

    Prueba en orden:
    1. Ordinales compuestos (con anterior/siguiente)
    2. Ordinales simples
    3. Litúrgicas
    4. Santoral relativo

    Args:
        year: Año
        texto: Texto descriptivo de la fecha

    Returns:
        Tupla (fecha, método) o None si no se puede calcular
    """
    # Intentar ordinales compuestos primero (son más específicos)
    resultado = calcular_ordinal_compuesto(year, texto)
    if resultado:
        return resultado

    # Intentar ordinales simples
    resultado = calcular_ordinal_simple(year, texto)
    if resultado:
        return resultado

    # Intentar litúrgicas
    resultado = calcular_liturgico(year, texto)
    if resultado:
        return resultado

    # Intentar santoral relativo
    resultado = calcular_santoral_relativo(year, texto)
    if resultado:
        return resultado

    return None


if __name__ == "__main__":
    # Tests con ejemplos de Navarra
    year = 2026

    ejemplos = [
        "Lunes siguiente al primer domingo de mayo",
        "Tercer sábado de septiembre",
        "Segundo viernes de septiembre",
        "Viernes de carnaval",
        "Martes de carnaval",
        "Lunes de Pentecostés",
        "Festividad de la Ascensión",
        "Viernes de la semana siguiente a San Lucas",
        "Último viernes de septiembre",
        "Viernes anterior al tercer domingo de septiembre",
    ]

    print(f"Calculando fechas relativas para {year}:\n")

    for texto in ejemplos:
        resultado = calcular_fecha_relativa(year, texto)

        if resultado:
            fecha, metodo = resultado
            print(f"✓ {texto:<55} → {fecha.strftime('%d/%m/%Y')} ({metodo})")
        else:
            print(f"✗ {texto:<55} → NO CALCULADA")
