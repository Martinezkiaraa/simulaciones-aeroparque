import numpy as np

# ============================================================
# ENUNCIADO / SOPORTE GENERAL
# ESTA CLASE GUARDA TODAS LAS MÉTRICAS DE LA SIMULACIÓN
# ============================================================

class MetricasSimulacion:
    def __init__(self):
        
        # CONTADOR DE ATERRIZAJES
        self.aterrizajes = 0
        
        # CONTADOR DE AVIONES GENERADOS
        self.aviones = 0
        
        # CONTADOR DE REINSERCIONES EN LA FILA
        self.reinserciones = 0
        
        # CONJUNTO DE IDs DE AVIONES QUE SE REINSERTARON (PARA NO REPETIR)
        self.reinserciones_unicas = set() 
        
        # CONTADOR DE DESVÍOS A MONTEVIDEO
        self.desvios_montevideo = 0
        
        # CONTADOR DE AVIONES QUE QUEDAN VOLANDO AL FINAL DE LA SIMULACIÓN
        self.volando = 0
        
        # CONTADOR DE DESVÍOS AL RÍO (INTERRUPCIONES, PARTES 4 Y 5)
        self.desvios_rio = 0

    # REGISTRAR ATERRIZAJE
    def registrar_aterrizaje(self, cantidad = 1):
        self.aterrizajes += cantidad
    
    # REGISTRAR NUEVOS AVIONES GENERADOS
    def registrar_aviones(self, cantidad = 1):
        self.aviones += cantidad
    
    # GUARDAR CANTIDAD DE AVIONES QUE QUEDAN EN VUELO AL FINAL
    def en_vuelo(self, cantidad):
        self.volando += cantidad

     # REGISTRAR UNA REINSERCIÓN (CUANDO UN AVIÓN SE REINSERTA EN LA FILA)
    def registrar_reinsercion(self, id_avion):
        self.reinserciones += 1
        self.reinserciones_unicas.add(id_avion)

     # REGISTRAR DESVÍO A MONTEVIDEO
    def registrar_desvio_montevideo(self, cantidad = 1):
        self.desvios_montevideo += cantidad

    # REGISTRAR DESVÍO AL RÍO (INTERRUPCIÓN DE ATERRIZAJE, PARTES 4 Y 5)
    def registrar_desvio_rio(self, cantidad = 1):
        self.desvios_rio += cantidad
    
    def registrar_desvio_tormenta(self, cantidad=1):
        self.desvios_tormenta+=cantidad

    def registrar_desvio_viento_tormenta(self, cantidad=1):
        self.desvios_viento_tormenta+=cantidad
    
    def resumen(self):
        return {
            "aterrizajes": self.aterrizajes,
            "reinserciones": self.reinserciones,
            "desvios_montevideo": self.desvios_montevideo,
            "desvios_rio": self.desvios_rio,
            "aviones": self.aviones,
            "en vuelo": self.volando,
            "desvios_viento_totales": self.desvios_viento,
            "desvios_tormenta_totales": self.desvios_tormenta,
            "desvios_viento_tormenta_totales": self.desvio_viento_tormenta
        }

    # REPRESENTACIÓN DE TEXTO (ÚTIL PARA DEBUG)
    def __repr__(self):
        return f"<Métricas: aterrizajes={self.aterrizajes}, reinserciones={self.reinserciones}, desvíos_mvd={self.desvios_montevideo}, desvíos_rio={self.desvios_rio}>"

# ============================================================
# PARTE 4 Y 5: FUNCIONES DE ANÁLISIS DE MÉTRICAS
# ============================================================

# ANALIZA LA CONGESTIÓN:
# SE CONSIDERA CONGESTIÓN SI UN AVIÓN VUELA MÁS LENTO QUE SU VMAX.
# DEVUELVE FRECUENCIA (PROPORCIÓN DE MINUTOS CON CONGESTIÓN)
# Y PROMEDIO (CUÁNTOS AVIONES CONGESTIONADOS POR MINUTO EN PROMEDIO).

def analizar_congestion(congestion):
    minutos_totales = len(congestion)
    minutos_con_congestion = sum(1 for c in congestion.values() if c > 0)
    frecuencia = minutos_con_congestion / minutos_totales
    promedio = sum(congestion.values()) / minutos_totales
    return {"frecuencia": frecuencia, "promedio": promedio}

# ANALIZA DESVÍOS A MONTEVIDEO:
# DEVUELVE FRECUENCIA (PROPORCIÓN DE MINUTOS CON ALGÚN DESVÍO)
# Y PROMEDIO (CUÁNTOS AVIONES DESVIADOS POR MINUTO EN PROMEDIO).

def analizar_montevideo(desvios):
    minutos = len(desvios)
    minutos_con_desvio = sum(1 for c in desvios.values() if c > 0)
    frecuencia = minutos_con_desvio / minutos
    promedio = sum(desvios.values()) / minutos
    return {"frecuencia": frecuencia, "promedio": promedio}

# ANALIZA DESVÍOS AL RÍO (INTERRUPCIONES DE ATERRIZAJE, PARTES 4 Y 5):
# DEVUELVE FRECUENCIA Y PROMEDIO COMO EN LOS OTROS CASOS.

def analizar_rio(desvios):
    minutos = len(desvios)
    minutos_con_desvio = sum(1 for c in desvios.values() if c > 0)
    frecuencia = minutos_con_desvio / minutos
    promedio = sum(desvios.values()) / minutos
    return {"frecuencia": frecuencia, "promedio": promedio}

# CALCULA EL ATRASO PROMEDIO:
# COMPARA TIEMPO REAL DE VUELO VS TIEMPO IDEAL (SIN CONGESTIÓN).
# DEVUELVE CUÁNTOS MINUTOS EXTRA TARDARON LOS AVIONES EN PROMEDIO.

def calcular_atraso_promedio(historia, t_ideal):
    atrasos = []
    for avion_id, datos in historia.items():
        if len(datos["t"]) == 0:
            continue
        minuto_aparicion = datos["t"][0]
        if "Aterrizó" not in datos["estado"]:
            continue
        idx = datos["estado"].index("Aterrizó")
        minuto_aterrizo = datos["t"][idx]
        t_real = minuto_aterrizo - minuto_aparicion
        atrasos.append(t_real - t_ideal)
    return np.mean(atrasos) if atrasos else 0.0

# CALCULA EL TIEMPO IDEAL (SIN CONGESTIÓN):
# SUMA LOS TIEMPOS DE RECORRER CADA TRAMO A VELOCIDAD VMAX.
# SE USA COMO BASELINE PARA COMPARAR CONTRA EL TIEMPO REAL.

def tiempo_ideal():
    tramos = [(50, 500), (35, 300), (10, 250), (5, 150)]
    total_minutos = sum(dist / (v / 60.0) for dist, v in tramos)
    return total_minutos