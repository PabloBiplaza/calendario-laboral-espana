"""
Generador de calendarios HTML con festivos destacados
"""

from datetime import datetime, timedelta
from typing import List, Dict
import calendar


class CalendarGenerator:
    """Genera calendarios HTML visualmente atractivos"""
    
    # Meses en español
    MESES = [
        'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
        'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
    ]
    
    # Días de la semana en español
    DIAS_SEMANA = ['L', 'M', 'X', 'J', 'V', 'S', 'D']
    
    def __init__(self, year: int, festivos: List[Dict], municipio: str = "", ccaa: str = "", empresa: str = ""):
        self.year = year
        self.festivos = festivos
        self.municipio = municipio
        self.ccaa = ccaa
        self.empresa = empresa
        
        # Convertir festivos a set para búsqueda rápida
        self.festivos_set = {f['fecha'] for f in festivos}
        
        # Diccionario fecha → festivo para tooltips
        self.festivos_dict = {f['fecha']: f for f in festivos}
    
    def generate_html(self) -> str:
        """Genera el HTML completo del calendario"""
        
        html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Calendario Laboral {self.year}</title>
    <style>
        {self._get_css()}
    </style>
</head>
<body>
    {self._get_header()}
    {self._get_calendar_grid()}
    {self._get_footer()}
</body>
</html>
"""
        return html
    
    def _get_css(self) -> str:
        """CSS del calendario"""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Arial', sans-serif;
            padding: 20px;
            background: #f5f5f5;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 3px solid #FDB913;
        }
        
        .header h1 {
            color: #333;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header h2 {
            color: #666;
            font-size: 1.5em;
            font-weight: normal;
        }
        
        .calendar-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-top: 30px;
        }
        
        .month {
            background: #fff;
            border: 1px solid #ddd;
            border-radius: 5px;
            overflow: hidden;
        }
        
        .month-header {
            background: #FDB913;
            color: white;
            padding: 10px;
            font-weight: bold;
            text-align: center;
            font-size: 1.1em;
        }
        
        .weekdays {
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            background: #f8f8f8;
            border-bottom: 1px solid #ddd;
        }
        
        .weekday {
            padding: 8px 4px;
            text-align: center;
            font-weight: bold;
            font-size: 0.85em;
            color: #666;
        }
        
        .days {
            display: grid;
            grid-template-columns: repeat(7, 1fr);
        }
        
        .day {
            padding: 8px 4px;
            text-align: center;
            font-size: 0.9em;
            min-height: 35px;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
            cursor: default;
        }
        
        .day.empty {
            background: #fafafa;
        }
        
        .day.festivo {
            background: #FDB913;
            color: white;
            font-weight: bold;
        }
        
        .day.festivo:hover {
            background: #e5a711;
        }
        
        .day.festivo::after {
            content: attr(data-festivo);
            position: absolute;
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%);
            background: #333;
            color: white;
            padding: 5px 10px;
            border-radius: 4px;
            font-size: 0.75em;
            white-space: nowrap;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.3s;
            z-index: 10;
            margin-bottom: 5px;
        }
        
        .day.festivo:hover::after {
            opacity: 1;
        }
        
        .footer {
            margin-top: 30px;
            padding-top: 20px;
            border-top: 2px solid #eee;
        }
        
        .legend {
            display: flex;
            justify-content: center;
            gap: 30px;
            flex-wrap: wrap;
            margin-bottom: 20px;
        }
        
        .legend-item {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .legend-color {
            width: 30px;
            height: 20px;
            border-radius: 3px;
        }
        
        .legend-color.festivo {
            background: #FDB913;
        }
        
        .info {
            text-align: center;
            color: #666;
            font-size: 0.9em;
            margin-top: 20px;
        }
        
        @media print {
            body {
                background: white;
            }
            
            .container {
                box-shadow: none;
                padding: 0;
            }
            
            .day.festivo::after {
                display: none;
            }
        }
        
        @media (max-width: 1024px) {
            .calendar-grid {
                grid-template-columns: repeat(3, 1fr);
            }
        }
        
        @media (max-width: 768px) {
            .calendar-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }
        
        @media (max-width: 480px) {
            .calendar-grid {
                grid-template-columns: 1fr;
            }
        }
        """
    
    def _get_header(self) -> str:
        """Genera el header del calendario"""
        
        empresa_html = f"<p style='color: #999; margin-top: 10px;'>{self.empresa}</p>" if self.empresa else ""
        
        return f"""
    <div class="container">
        <div class="header">
            <h1>Calendario laboral</h1>
            <h2>{self.year}</h2>
            {empresa_html}
        </div>
"""
    
    def _get_calendar_grid(self) -> str:
        """Genera la cuadrícula de meses"""
        
        html = '<div class="calendar-grid">\n'
        
        for month in range(1, 13):
            html += self._generate_month(month)
        
        html += '</div>\n'
        return html
    
    def _generate_month(self, month: int) -> str:
        """Genera el HTML de un mes"""
        
        # Obtener información del mes
        month_name = self.MESES[month - 1]
        cal = calendar.monthcalendar(self.year, month)
        
        html = f"""
        <div class="month">
            <div class="month-header">{month_name}</div>
            <div class="weekdays">
"""
        
        # Días de la semana
        for day_name in self.DIAS_SEMANA:
            html += f'                <div class="weekday">{day_name}</div>\n'
        
        html += '            </div>\n            <div class="days">\n'
        
        # Días del mes
        for week in cal:
            for day in week:
                if day == 0:
                    # Día vacío
                    html += '                <div class="day empty"></div>\n'
                else:
                    # Construir fecha
                    fecha = f"{self.year:04d}-{month:02d}-{day:02d}"
                    
                    # Verificar si es festivo
                    if fecha in self.festivos_set:
                        festivo = self.festivos_dict[fecha]
                        descripcion = festivo.get('descripcion', 'Festivo')
                        html += f'                <div class="day festivo" data-festivo="{descripcion}">{day}</div>\n'
                    else:
                        html += f'                <div class="day">{day}</div>\n'
        
        html += '            </div>\n        </div>\n'
        return html
    
    def _get_footer(self) -> str:
        """Genera el footer con leyenda e información"""
        
        # Contar festivos por tipo
        tipos = {}
        for f in self.festivos:
            tipo = f.get('tipo', 'otro')
            tipos[tipo] = tipos.get(tipo, 0) + 1
        
        # Información del municipio
        municipio_info = f"<p><strong>Municipio:</strong> {self.municipio}, {self.ccaa.upper()}</p>" if self.municipio else ""
        
        # Resumen de festivos
        resumen = "<p><strong>Total festivos:</strong> " + str(len(self.festivos))
        if tipos:
            detalle = " (" + ", ".join([f"{v} {k}" for k, v in tipos.items()]) + ")"
            resumen += detalle
        resumen += "</p>"
        
        return f"""
        <div class="footer">
            <div class="legend">
                <div class="legend-item">
                    <div class="legend-color festivo"></div>
                    <span>Festivo laboral</span>
                </div>
            </div>
            <div class="info">
                {municipio_info}
                {resumen}
                <p style="margin-top: 10px; font-size: 0.85em;">
                    Generado el {datetime.now().strftime('%d/%m/%Y')}
                </p>
            </div>
        </div>
    </div>
"""
