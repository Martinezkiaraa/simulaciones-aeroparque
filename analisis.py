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
        self.desvios_viento = 0                  # DESVÍOS POR GO-AROUND (día ventoso)

        # PARTE 6
        self.desvios_tormenta = 0             # DESVÍOS POR TORMENTA (AEP cerrado)

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

    def registrar_desvio_viento(self, cantidad=1):
        self.desvios_viento += cantidad

    def registrar_desvio_tormenta(self, cantidad=1):
        self.desvios_tormenta += cantidad


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
            "desvios_viento": self.desvios_viento,
            "desvios_tormenta": self.desvios_tormenta,
        }

    # REPRESENTACIÓN DE TEXTO (ÚTIL PARA DEBUG)
    
    def __repr__(self):
        return (f"<Métricas: aterrizajes={self.aterrizajes}, "
                f"reinserciones={self.reinserciones}, "
                f"desv_mvd={self.desvios_montevideo}, "
                f"desv_viento={self.desvios_viento}, "
                f"desv_tormenta={self.desvios_tormenta}, "
            )

# ============================================================
# FUNCIONES DE ANÁLISIS DE MÉTRICAS (PARTES 4, 5 y 6)
# ============================================================
def analizar_congestion(df):
    """
    PARTE 4
    Analiza congestión: 
    - frecuencia = proporción de minutos con al menos 1 avión en congestión
    - promedio = cuántos aviones en congestión en promedio por minuto
    """
    # Nuevo: promedio de minutos en congestión por avión aterrizado
    # congestion debe ser el diccionario de la simulación (data)
    minutos_por_avion = []
    historia = df["historia"]
    for datos in historia.values():
        if len(datos["estado"]) == 0 or "Aterrizó" not in datos["estado"]:
            continue
        # Minutos en congestión: estado en fila/reinsertado y velocidad < v_max
        minutos_cong = 0
        for est, vel, vmax in zip(datos["estado"], datos["v"], datos["vmax"]):
            if est in ["En fila", "Reinsertado"] and vel < vmax:
                minutos_cong += 1
        minutos_por_avion.append(minutos_cong)
    promedio = np.mean(minutos_por_avion) if minutos_por_avion else 0.0
    return {"promedio": promedio}

def IC_globales(df):
    # Agrupar por lambda
    grouped = df.groupby("lambda")["congestion_prom"]

    # Calcular promedio, desviación estándar y tamaño de muestra
    resumen = grouped.agg(["mean", "std", "count"]).reset_index()

    # Calcular error estándar y límites del intervalo de confianza al 95%
    resumen["Error MonteCarlo"] = resumen["std"] / np.sqrt(resumen["count"])
    resumen["IC95_lower"] = resumen["mean"] - 1.96 * resumen["Error MonteCarlo"]
    resumen["IC95_upper"] = resumen["mean"] + 1.96 * resumen["Error MonteCarlo"]

    return resumen

def analizar_montevideo(data):
    """
    PARTE 4
    Analiza desvíos a Montevideo:
    - frecuencia = proporción de minutos con al menos 1 desvío
    - promedio = desvíos promedio por minuto
    """
    desvios = data["desvios_montevideo"]
    minutos = len(desvios)
    minutos_con_desvio = sum(1 for c in desvios.values() if c > 0)
    frecuencia = minutos_con_desvio / minutos
    promedio = sum(desvios.values()) / minutos
    return {"frecuencia": frecuencia, "promedio": promedio}

def analizar_viento(data):
    """
    PARTE 5
    Analiza desvíos por viento (go-around → trayectoria río).
    """
    desvios = data["desvios_viento"]
    minutos = len(desvios)
    minutos_con_desvio = sum(1 for c in desvios.values() if c > 0)
    frecuencia = minutos_con_desvio / minutos
    promedio = sum(desvios.values()) / minutos
    return {"frecuencia": frecuencia, "promedio": promedio}

def analizar_tormenta(data):
    """
    PARTE 6
    Analiza desvíos por tormenta (cierre de AEP).
    """
    desvios = data.get("desvios_tormenta", {})
    minutos = len(desvios)
    minutos_con_desvio = sum(1 for c in desvios.values() if c > 0)
    frecuencia = minutos_con_desvio / minutos
    promedio = sum(desvios.values()) / minutos
    return {"frecuencia": frecuencia, "promedio": promedio}

def calcular_atraso_promedio(data, t_ideal):
    """
    Calcula el atraso promedio comparando tiempo real de vuelo 
    contra tiempo ideal (sin congestión).
    """
    historia = data["historia"]
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
    tramos = [(50, 300), (35, 250), (10, 200), (5, 150)]
    total_minutos = sum(dist / (v / 60.0) for dist, v in tramos)
    return total_minutos

def print_resumen(metricas_lambdas):
     for m in metricas_lambdas:
        print(metricas_lambdas[m].resumen())