from plane import plane
from heap import heap
import random

# ============================================================
# ENUNCIADO / PARTE 1 y PARTE 3
# FUNCIÓN BÁSICA DE SIMULACIÓN: SOLO GENERA AVIONES
# Y LOS MANTIENE EN LA FILA, SIN GUARDAR HISTORIA COMPLETA.
# SE USA EN EL EJERCICIO 3 (probabilidad de 5 aviones en una hora).
# ============================================================

def run_simulacion(lambda_por_min, minutos = 1080, seed = None):
    if seed is not None:
        random.seed(seed)

    # FILAS DE AVIONES
    avs = heap()         # FILA PRINCIPAL
    desviados = heap()   # AVIONES DESVIADOS OUTBOUND
    montevideo = heap()  # AVIONES QUE SE VAN A MONTEVIDEO
    rio = heap()         # AVIONES QUE SE DESVIAN AL RÍO
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
                rio = rio
            )
            avs.agregar_avion(nuevo)
            next_id += 1

    # DEVUELVE SOLO LOS AVIONES EN FILA (se usa para contar arribos)
    return avs.aviones

# ============================================================
# ENUNCIADO / PARTE 1, PARTE 4 y PARTE 5
# FUNCIÓN COMPLETA DE SIMULACIÓN CON HISTORIA DETALLADA:
# GUARDA TIEMPOS, POSICIONES, VELOCIDADES Y ESTADOS DE CADA AVIÓN.
# SE USA EN EL EJERCICIO 1 (visualización), EJERCICIO 4 (congestión)
# Y EJERCICIO 5 (día ventoso, desvíos al Río).
# ============================================================

def simular_con_historia(lambda_por_min, minutos, seed = 42, dia_ventoso = True, metricas = None):

def simular_con_historia(lambda_por_min, minutos, seed=42, dia_ventoso = True, metricas = None, hay_tormenta = False): #AGREGAMOS hay_tormenta

    if seed is not None:
        random.seed(seed)
    #AGREGAMOS:
    if hay_tormenta:
        inicio_tormenta = random.randint(0, minutos - 30)
        fin_tormenta = inicio_tormenta + 30
    else:
        inicio_tormenta = None
        fin_tormenta = None

    # FILAS DE AVIONES
    avs = heap()
    desviados = heap()
    montevideo = heap()
    viento = heap()
    tormenta = heap()
    tormenta_viento = heap()

    next_id = 1
    historia = {}  # GUARDA LA TRAYECTORIA DE CADA AVIÓN

    # DICCIONARIOS PARA GUARDAR MÉTRICAS MINUTO A MINUTO
    congestion = {t: 0 for t in range(minutos)}         # cuántos aviones en congestión
    desvios_montevideo = {t: 0 for t in range(minutos)} # desvíos a Montevideo
    desvios_fila = {t: 0 for t in range(minutos)}       # desvíos por congestión (outbound)
    desvios_rio = {t: 0 for t in range(minutos)}        # desvíos por interrupción (Río)   

    # RECORRE TODOS LOS MINUTOS DE SIMULACIÓN
    historia = {}

    congestion = {t: 0 for t in range(minutos)} #La frecuencia se mide x cada minuto
    desvios_montevideo = {t: 0 for t in range(minutos)}
    desvios_fila = {t: 0 for t in range(minutos)}
    desvios_viento = {t: 0 for t in range(minutos)}    
    desvios_tormenta = {t: 0 for t in range(minutos)} 
    desvios_tormenta_viento = {t: 0 for t in range(minutos)} 

    for t in range(minutos):
        #AGREGAMOS:
        esta_cerrado = (inicio_tormenta is not None and fin_tormenta is not None and inicio_tormenta <= t < fin_tormenta)
        # Probabilidad de que llegue un avión en este minuto
        if random.random() < lambda_por_min:
            a = plane(id = next_id, 
                      minuto_aparicion = t, 
                      fila = avs, 
                      desviados = desviados, 
                      mtvd = montevideo, 
                      rio = rio
            )
            metricas.registrar_aviones()  # MÉTRICA: CUENTA AVIONES
            a = plane(id=next_id, minuto_aparicion=t, fila=avs, desviados= desviados, mtvd = montevideo, viento = viento, tormenta = tormenta, tormenta_viento = tormenta_viento)
            metricas.registrar_aviones()
            avs.agregar_avion(a)
            historia[a.id] = {"t": [], "x": [], "v": [], "estado": []}
            next_id += 1

        # ----------------------------------------------
        # ACTUALIZA EL ESTADO DE TODOS LOS AVIONES EN FILA
        # ----------------------------------------------
        
        for a in list(avs.aviones):
            a.avanzar(minuto_actual = t, dt = 1.0, hay_viento = dia_ventoso, metricas = metricas)

            a.avanzar(minuto_actual=t, dt=1.0, hay_viento = dia_ventoso, metricas = metricas, esta_cerrado = esta_cerrado)

            # Detectar congestión: si está en fila/reinsertado y su velocidad < v_max
            if (a.estado in ["En fila", "Reinsertado"]) and a.velocidad_actual < a.v_max:
                congestion[t] += 1

            # SI ATERRIZÓ → QUITARLO DE LA FILA Y REGISTRAR
            if a.estado == "Aterrizó":
                historia[a.id]["t"].append(t)
                historia[a.id]["estado"].append(a.estado)
                metricas.registrar_aterrizaje() #LO MOVEMOS A PLANE??
                avs.eliminar_avion(a) #ESTO TAMBIEN?
            
            # SI NO ATERRIZÓ → REGISTRAR SU POSICIÓN Y VELOCIDAD
            if a.estado != "Aterrizó":
                historia[a.id]["t"].append(t)
                historia[a.id]["x"].append(a.distancia_mn_aep)
                historia[a.id]["v"].append(a.velocidad_actual)
                historia[a.id]["estado"].append(a.estado)
        
        # ----------------------------------------------
        # ACTUALIZA AVIONES DESVIADOS (por congestión)
        # ----------------------------------------------
        
        for d in list(desviados.aviones):
            desvios_fila[t] += 1
            d.avanzar(minuto_actual = t, dt = 1.0, hay_viento = dia_ventoso, metricas = metricas, esta_cerrado = esta_cerrado)
            if d.estado == "Reinsertado":
                metricas.registrar_reinsercion(d.id)

        # ----------------------------------------------
        # ACTUALIZA AVIONES QUE YA SE FUERON A MONTEVIDEO
        # ----------------------------------------------
          
                metricas.registrar_reinsercion(d.id) #REGISTRA METRICA ACA O EN PLANE
            
        for av in list(montevideo.aviones):
            desvios_montevideo[t] += 1
            historia[av.id]["t"].append(t)
            historia[av.id]["estado"].append(av.estado)
        
        # ----------------------------------------------
        # ACTUALIZA AVIONES DESVIADOS AL RÍO
        # ----------------------------------------------
        
        for r in list(rio.aviones):
            desvios_rio[t] += 1
            r.avanzar(minuto_actual = t, dt = 1.0, hay_viento = dia_ventoso, metricas = metricas)
        for r in list(viento.aviones):
            desvios_viento[t] += 1
            r.avanzar(minuto_actual=t, dt=1.0, hay_viento = dia_ventoso, metricas = metricas, esta_cerrado = esta_cerrado)

        for z in list(tormenta.aviones):
            desvios_tormenta[t] += 1
            z.avanzar(minuto_actual=t, dt=1.0, hay_viento = dia_ventoso, metricas = metricas, esta_cerrado = esta_cerrado)

        for tv in list(tormenta_viento.aviones):
            desvios_tormenta_viento[t] += 1
            tv.avanzar(minuto_actual=t, dt=1.0, hay_viento = dia_ventoso, metricas = metricas, esta_cerrado = esta_cerrado)

    # AL FINAL: CUÁNTOS AVIONES QUEDARON EN EL AIRE
    metricas.en_vuelo(len(avs.aviones) + len(desviados.aviones) + len(rio.aviones))
    metricas.en_vuelo(len(avs.aviones) + len(desviados.aviones) + len(viento.aviones))

    # DEVUELVE LA HISTORIA COMPLETA + MÉTRICAS MINUTO A MINUTO
    return {
    "historia": historia,
    "congestion": congestion,
    "desvios_montevideo": desvios_montevideo,
    "desvios_fila": desvios_fila,
    "desvios_viento": desvios_viento
}