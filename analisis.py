import numpy as np

class MetricasSimulacion:
    def __init__(self):
        self.aterrizajes = 0

        self.aviones = 0

        self.reinserciones = 0
        self.reinserciones_unicas = set() 

        self.desvios_montevideo = 0
        self.volando = 0

        self.desvios_viento = 0
        self.desvios_tormenta = 0
        self.desvio_viento_tormenta = 0

        self.desvios_totales = 0 #ESTO SE USA?

    def registrar_aterrizaje(self, cantidad=1):
        self.aterrizajes += cantidad

    def registrar_aviones(self, cantidad=1):
        self.aviones += cantidad
    
    def en_vuelo(self, cantidad):
        self.volando+=cantidad

    def registrar_reinsercion(self, id_avion):
        self.reinserciones += 1
        self.reinserciones_unicas.add(id_avion)

    def registrar_desvio_montevideo(self, cantidad=1):
        self.desvios_montevideo += cantidad

    def registrar_desvio_viento(self, cantidad=1):
        self.desvios_viento+=cantidad
    
    def registrar_desvio_tormenta(self, cantidad=1):
        self.desvios_tormenta+=cantidad

    def registrar_desvio_viento_tormenta(self, cantidad=1):
        self.desvios_viento_tormenta+=cantidad
    
    def resumen(self):
        return {
            "aterrizajes": self.aterrizajes,
            "reinserciones": self.reinserciones,
            "desvios_montevideo": self.desvios_montevideo,
            "aviones": self.aviones,
            "en vuelo": self.volando,
            "desvios_viento_totales": self.desvios_viento,
            "desvios_tormenta_totales": self.desvios_tormenta,
            "desvios_viento_tormenta_totales": self.desvio_viento_tormenta
        }

    def __repr__(self):
        return f"<Métricas: aterrizajes={self.aterrizajes}, reinserciones={self.reinserciones}, desvíos={self.desvios_montevideo}>"


# Ejercicio 4

def analizar_congestion(congestion):
    minutos_totales = len(congestion)
    minutos_con_congestion = sum(1 for c in congestion.values() if c > 0)
    frecuencia = minutos_con_congestion / minutos_totales
    promedio = sum(congestion.values()) / minutos_totales
    return {"frecuencia": frecuencia, "promedio": promedio}

def analizar_montevideo(desvios):
    minutos = len(desvios)
    minutos_con_desvio = sum(1 for c in desvios.values() if c > 0)
    frecuencia = minutos_con_desvio / minutos
    promedio = sum(desvios.values()) / minutos
    return {"frecuencia": frecuencia, "promedio": promedio}

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

def tiempo_ideal():
    tramos = [(50, 500), (35, 300), (10, 250), (5, 150)]
    total_minutos = sum(dist / (v / 60.0) for dist, v in tramos)
    return total_minutos
