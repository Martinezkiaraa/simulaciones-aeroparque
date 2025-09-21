from plane import plane
from heap import heap
import random
from analisis import MetricasSimulacion

# ============================================================
# ENUNCIADO / PARTE 1 y PARTE 3
# FUNCIÓN BÁSICA DE SIMULACIÓN: SOLO GENERA AVIONES
# SE USA EN EL EJERCICIO 3 (probabilidad de 5 aviones en una hora).
# ============================================================

def run_simulacion(lambda_por_min, minutos = 1080, seed = None):
    if seed is not None:
        random.seed(seed)

    # FILAS DE AVIONES
    avs = heap()         # FILA PRINCIPAL
    desviados = heap()   # DESVIADOS POR CONGESTIÓN
    montevideo = heap()  # AVIONES QUE SE VAN A MONTEVIDEO
    viento = heap()      # DESVIADOS POR DÍA VENTOSO
    tormenta = heap()    # DESVIADOS POR TORMENTA
    next_id = 1

    # RECORRE CADA MINUTO DEL PERIODO SIMULADO
    for minuto in range(minutos):
        # CON PROBABILIDAD λ APARECE UN NUEVO AVIÓN
        if random.random() < lambda_por_min:
            nuevo = plane(
                id = next_id, 
                minuto_aparicion = minuto, 
                fila = avs,
                desviados = desviados,
                mtvd = montevideo,
                viento = viento,
                tormenta = tormenta
            )
            avs.agregar_avion(nuevo)
            next_id += 1

    # DEVUELVE SOLO LOS AVIONES EN FILA (se usa para contar arribos)
    return avs.aviones

# ============================================================
# ENUNCIADO / PARTES 1, 4, 5 y 6
# FUNCIÓN COMPLETA DE SIMULACIÓN CON HISTORIA DETALLADA:
# GUARDA TIEMPOS, POSICIONES, VELOCIDADES Y ESTADOS DE CADA AVIÓN.
# SE USA EN EL EJERCICIO 1 (visualización), EJERCICIO 4 (congestión),
# EJERCICIO 5 (día ventoso) y EJERCICIO 6 (tormenta).
# ============================================================

def simular_con_historia(lambda_por_min, minutos, seed = None, dia_ventoso = True,
                         inicio_tormenta = None, metricas = MetricasSimulacion()):
    
    if seed is not None:
        random.seed(seed)
        
    # FILAS DE AVIONES
    avs = heap()
    desviados = heap()
    montevideo = heap()
    viento = heap()
    tormenta = heap()
    next_id = 1
    historia = {}  # GUARDA LA TRAYECTORIA DE CADA AVIÓN

    # DICCIONARIOS PARA GUARDAR MÉTRICAS MINUTO A MINUTO
    congestion_actual = {t: 0 for t in range(minutos)}
    congestion_final = {t: 0 for t in range(minutos)}
    desvios_montevideo = {t: 0 for t in range(minutos)}
    desvios_fila = {t: 0 for t in range(minutos)}
    desvios_viento = {t: 0 for t in range(minutos)}
    desvios_tormenta = {t: 0 for t in range(minutos)}  
 

    # EJERCICIO 6 
    duracion_tormenta = 30

    # RECORRE TODOS LOS MINUTOS DE SIMULACIÓN
    for t in range(minutos):

        # CHEQUEA SI LA TORMENTA ESTÁ ACTIVA (PARTE 6)
        tormenta_activa = (
            inicio_tormenta is not None and 
            inicio_tormenta <= t < inicio_tormenta + duracion_tormenta
        )

        # ----------------------------------------------
        # GENERACIÓN DE NUEVOS AVIONES SEGÚN λ
        # ----------------------------------------------

        if random.random() < lambda_por_min:
            a = plane(id = next_id, 
                      minuto_aparicion = t, 
                      fila = avs, 
                      desviados = desviados, 
                      mtvd = montevideo, 
                      viento = viento, 
                      tormenta = tormenta
            )

            metricas.registrar_aviones()
            avs.agregar_avion(a)
            historia[a.id] = {"t": [], "x": [], "v": [], "estado": [], "vmax": []}
            next_id += 1

        # ----------------------------------------------
        # ACTUALIZA EL ESTADO DE TODOS LOS AVIONES EN FILA
        # ----------------------------------------------
        
        for a in list(avs.aviones):
            a.avanzar(minuto_actual = t, 
                      dt = 1.0, 
                      hay_viento = dia_ventoso,  
                      tormenta_activa = tormenta_activa, 
                      metricas = metricas
            )

            # MÉTRICA DE CONGESTIÓN: velocidad < vmax
            if (a.estado in ["En fila", "Reinsertado"]) and a.velocidad_actual < a.v_max:
                congestion_actual[t] += 1

            # SI ATERRIZÓ 
            if a.estado == "Aterrizó":
                historia[a.id]["t"].append(t)
                historia[a.id]["estado"].append(a.estado)
                congestion_final = congestion_actual
            
            # SI NO ATERRIZÓ → REGISTRAR SU POSICIÓN Y VELOCIDAD
            if a.estado != "Aterrizó":
                historia[a.id]["t"].append(t)
                historia[a.id]["x"].append(a.distancia_mn_aep)
                historia[a.id]["v"].append(a.velocidad_actual)
                historia[a.id]["estado"].append(a.estado)
                historia[a.id]["vmax"].append(a.v_max)
        # ----------------------------------------------
        # ACTUALIZA AVIONES DESVIADOS (congestión)
        # ----------------------------------------------
        
        for d in list(desviados.aviones):
            desvios_fila[t] += 1
            d.avanzar(t, dt = 1.0, hay_viento = dia_ventoso, tormenta_activa = tormenta_activa, metricas = metricas)
            if d.estado == "Reinsertado":
                metricas.registrar_reinsercion(d.id)

        # ----------------------------------------------
        # ACTUALIZA AVIONES DESVIADOS POR VIENTO
        # ----------------------------------------------
        
        for v in list(viento.aviones):
            desvios_viento[t] += 1
            v.avanzar(t, dt = 1.0, hay_viento = dia_ventoso,
                      tormenta_activa = tormenta_activa, metricas = metricas)

        # ----------------------------------------------
        # ACTUALIZA AVIONES DESVIADOS POR TORMENTA
        # ----------------------------------------------
        
        for r in list(tormenta.aviones):
            desvios_tormenta[t] += 1
            r.avanzar(t, dt = 1.0, hay_viento = dia_ventoso,
                      tormenta_activa = tormenta_activa, metricas = metricas)
        
        # ----------------------------------------------
        # ACTUALIZA AVIONES QUE YA SE FUERON A MONTEVIDEO
        # ----------------------------------------------
            
        for av in list(montevideo.aviones):
            desvios_montevideo[t] += 1
            historia[av.id]["t"].append(t)
            historia[av.id]["estado"].append(av.estado)
        
    # AL FINAL: CUÁNTOS AVIONES QUEDARON EN EL AIRE
    metricas.en_vuelo(len(avs.aviones) + len(desviados.aviones) + len(viento.aviones) + len(tormenta.aviones))

    # DEVUELVE LA HISTORIA COMPLETA + MÉTRICAS MINUTO A MINUTO
    return {
        "historia": historia,
        "congestion": congestion_final,
        "desvios_montevideo": desvios_montevideo,
        "desvios_fila": desvios_fila,
        "desvios_viento": desvios_viento,
        "desvios_tormenta": desvios_tormenta
        }