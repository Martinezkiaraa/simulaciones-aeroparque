import numpy as np

# ============================================================
# ENUNCIADO / SOPORTE GENERAL
# CLASE PARA GUARDAR TODAS LAS MÉTRICAS DE LA SIMULACIÓN
# ============================================================

class MetricasSimulacion:
    def __init__(self):
        # PARTE 1
        self.aterrizajes = 0                  # CANTIDAD DE ATERRIZAJES EXITOSOS
        self.aviones = 0                      # TOTAL DE AVIONES GENERADOS
        self.volando = 0                      # AVIONES QUE QUEDAN VOLANDO AL FINAL

        # PARTE 4
        self.reinserciones = 0                # TOTAL DE REINSERCIONES
        self.reinserciones_unicas = set()     # IDs de aviones reinsertados
        self.desvios_montevideo = 0           # TOTAL DE DESVÍOS A MONTEVIDEO
        self.desvios_rio = 0                  # DESVÍOS POR GO-AROUND (día ventoso)

        # PARTE 5
        # (Ya contemplado en desvios_rio)

        # PARTE 6
        self.desvios_tormenta = 0             # DESVÍOS POR TORMENTA (AEP cerrado)
        self.desvios_tormenta_viento = 0      # DESVÍOS COMBINADOS (tormenta + viento)

    # ---------------- REGISTROS ----------------

    def registrar_aterrizaje(self, cantidad=1):
        self.aterrizajes += cantidad
    
    def registrar_aviones(self, cantidad=1):
        self.aviones += cantidad
    
    def en_vuelo(self, cantidad):
        self.volando += cantidad

    def registrar_reinsercion(self, id_avion):
        self.reinserciones += 1
        self.reinserciones_unicas.add(id_avion)

    def registrar_desvio_montevideo(self, cantidad=1):
        self.desvios_montevideo += cantidad

    def registrar_desvio_rio(self, cantidad=1):
        self.desvios_rio += cantidad

    def registrar_desvio_tormenta(self, cantidad=1):
        self.desvios_tormenta += cantidad

    def registrar_desvio_tormenta_viento(self, cantidad=1):
        self.desvios_tormenta_viento += cantidad

    # ---------------- RESUMEN ----------------

    def resumen(self):
        """
        Devuelve un diccionario con todas las métricas principales
        (sirve para imprimir resultados al final de cada experimento).
        """
        return {
            "aterrizajes": self.aterrizajes,
            "aviones": self.aviones,
            "en_vuelo": self.volando,
            "reinserciones": self.reinserciones,
            "desvios_montevideo": self.desvios_montevideo,
            "desvios_rio": self.desvios_rio,
            "desvios_tormenta": self.desvios_tormenta,
            "desvios_tormenta_viento": self.desvios_tormenta_viento,
        }

    # REPRESENTACIÓN DE TEXTO (ÚTIL PARA DEBUG)
    
    def __repr__(self):
        return (f"<Métricas: aterrizajes={self.aterrizajes}, "
                f"reinserciones={self.reinserciones}, "
                f"desv_mvd={self.desvios_montevideo}, "
                f"desv_rio={self.desvios_rio}, "
                f"desv_tormenta={self.desvios_tormenta}, "
                f"desv_tormenta_viento={self.desvios_tormenta_viento}>")

# ============================================================
# FUNCIONES DE ANÁLISIS DE MÉTRICAS (PARTES 4, 5 y 6)
# ============================================================

def analizar_congestion(congestion):
    """
    PARTE 4
    Analiza congestión: 
    - frecuencia = proporción de minutos con al menos 1 avión en congestión
    - promedio = cuántos aviones en congestión en promedio por minuto
    """
    minutos_totales = len(congestion)
    minutos_con_congestion = sum(1 for c in congestion.values() if c > 0)
    frecuencia = minutos_con_congestion / minutos_totales
    promedio = sum(congestion.values()) / minutos_totales
    return {"frecuencia": frecuencia, "promedio": promedio}

def analizar_montevideo(desvios):
    """
    PARTE 4
    Analiza desvíos a Montevideo:
    - frecuencia = proporción de minutos con al menos 1 desvío
    - promedio = desvíos promedio por minuto
    """
    minutos = len(desvios)
    minutos_con_desvio = sum(1 for c in desvios.values() if c > 0)
    frecuencia = minutos_con_desvio / minutos
    promedio = sum(desvios.values()) / minutos
    return {"frecuencia": frecuencia, "promedio": promedio}

def analizar_rio(desvios):
    """
    PARTE 5
    Analiza desvíos al Río (go-around por viento).
    """
    minutos = len(desvios)
    minutos_con_desvio = sum(1 for c in desvios.values() if c > 0)
    frecuencia = minutos_con_desvio / minutos
    promedio = sum(desvios.values()) / minutos
    return {"frecuencia": frecuencia, "promedio": promedio}

def analizar_tormenta(desvios):
    """
    PARTE 6
    Analiza desvíos por tormenta (cierre de AEP).
    """
    minutos = len(desvios)
    minutos_con_desvio = sum(1 for c in desvios.values() if c > 0)
    frecuencia = minutos_con_desvio / minutos
    promedio = sum(desvios.values()) / minutos
    return {"frecuencia": frecuencia, "promedio": promedio}

def calcular_atraso_promedio(historia, t_ideal):
    """
    Calcula el atraso promedio comparando tiempo real de vuelo 
    contra tiempo ideal (sin congestión).
    """
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

def tiempo_ideal():
    """
    Calcula el tiempo ideal (sin congestión, sin tormenta, sin viento),
    sumando tiempos de recorrer cada tramo a velocidad máxima.
    """
    tramos = [(50, 500), (35, 300), (10, 250), (5, 150)]
    total_minutos = sum(dist / (v / 60.0) for dist, v in tramos)
    return total_minutos