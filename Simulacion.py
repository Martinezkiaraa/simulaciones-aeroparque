from PLANE_NUEVO import plane
from heap import heap
import random
from analisis import MetricasSimulacion

def run_simulacion(lambda_por_min, minutos=1080, seed=None):
    if seed is not None:
        random.seed(seed)

    avs = heap()
    next_id = 1

    for minuto in range(minutos):
        if random.random() < lambda_por_min:
            nuevo = plane(id=next_id, minuto_aparicion=minuto, fila=avs) #QUEDÓ VIEJO
            avs.agregar_avion(nuevo)
            next_id += 1

    return avs.aviones



def simular_con_historia(lambda_por_min, minutos, seed=42, dia_ventoso = True, metricas = None):

    if seed is not None:
        random.seed(seed)

    avs = heap()
    desviados = heap()
    montevideo = heap()
    rio = heap()

    next_id = 1
    historia = {}

    congestion = {t: 0 for t in range(minutos)} #La frecuencia se mide x cada minuto
    desvios_montevideo = {t: 0 for t in range(minutos)}
    desvios_fila = {t: 0 for t in range(minutos)}
    desvios_rio = {t: 0 for t in range(minutos)}    

    for t in range(minutos):

        # Probabilidad de que llegue un avión en este minuto
        if random.random() < lambda_por_min:
            a = plane(id=next_id, minuto_aparicion=t, fila=avs, desviados= desviados, mtvd = montevideo, rio = rio)
            metricas.registrar_aviones()
            avs.agregar_avion(a)
            historia[a.id] = {"t": [], "x": [], "estado": []}
            next_id += 1

        # Avanzar dinámica de todos los aviones
        for a in list(avs.aviones):

            a.avanzar(minuto_actual=t, dt=1.0, hay_viento = dia_ventoso)

            # Detectar congestión: si está en fila/reinsertado y su velocidad < v_max
            if a.estado == "En fila" or a.estado == "Reinsertado" and a.velocidad_actual < a.v_max:
                congestion[t] += 1

            # Registrar si no aterrizó aún
            if a.estado != "Aterrizó":
                historia[a.id]["t"].append(t)
                historia[a.id]["x"].append(a.distancia_mn_aep)
                historia[a.id]["estado"].append(a.estado)

            # Si aterrizó, lo quitamos de la fila
            if a.estado == "Aterrizó":
                historia[a.id]["t"].append(t)
                historia[a.id]["estado"].append(a.estado)
                metricas.registrar_aterrizaje()
                avs.eliminar_avion(a)
        
        for d in list(desviados.aviones):
            desvios_fila[t] += 1
            d.avanzar(minuto_actual = t, dt = 1.0, hay_viento = dia_ventoso)
            if d.estado == "Reinsertado":
                metricas.registrar_reinsercion()
            
        for av in list(montevideo.aviones):
            desvios_montevideo[t] += 1
            av.avanzar(minuto_actual=t, dt=1.0, hay_viento = dia_ventoso)
            metricas.registrar_desvio_montevideo()
            historia[a.id]["t"].append(t)
            historia[a.id]["estado"].append(a.estado)
        
        for r in list(rio.aviones):
            desvios_rio[t] += 1
            r.avanzar(minuto_actual=t, dt=1.0, hay_viento = dia_ventoso)
            metricas.registrar_desvio_rio

    total_en_vuelo = len(avs.aviones) + len(desviados.aviones) + len(rio.aviones)
    metricas.en_vuelo(total_en_vuelo)
    return {
    "historia": historia,
    "congestion": congestion,
    "desvios_montevideo": desvios_montevideo,
    "desvios_fila": desvios_fila,
    "desvios_rio": desvios_rio
}


