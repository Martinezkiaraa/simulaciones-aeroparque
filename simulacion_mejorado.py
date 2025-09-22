from plane_mejorado import plane
from heap import heap
import random
from analisis import MetricasSimulacion

def simular_con_historia_v2(lambda_por_min, minutos, seed = None, dia_ventoso = True,
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
    congestion = {t: 0 for t in range(minutos)}
    congestion_control = {t: 0 for t in range(minutos)}
    desvios_montevideo = {t: 0 for t in range(minutos)}
    desvios_fila = {t: 0 for t in range(minutos)}
    desvios_viento = {t: 0 for t in range(minutos)}
    desvios_tormenta = {t: 0 for t in range(minutos)}  

    #PARA LA POLÍTICA DE MEJORA:
    #Agregamos atributos a los aviones
    avs.delta = 0.0   # 0, 10, 20 (kts)
    avs.i_max = 0     # 0-4
    avs.consec_3 = 0         # minutos consecutivos con >=5 congestionados
    avs.consec_2 = 0         # minutos consecutivos con >=3 congestionados
    avs.consec_1 = 0         # minutos consecutivos con <=2 congestionados
 
    # EJERCICIO 6 
    duracion_tormenta = 30

    # RECORRE TODOS LOS MINUTOS DE SIMULACIÓN
    for t in range(minutos):

        # CHEQUEA SI LA TORMENTA ESTÁ ACTIVA (PARTE 6)
        tormenta_activa = (
            inicio_tormenta is not None and 
            inicio_tormenta <= t < inicio_tormenta + duracion_tormenta
        )

        #VEMOS LA CONGESTIÓN DEL MINUTO ANTERIOR:
        cong_prev = congestion_control[t-1] if t > 0 else 0 

        #ACTUALIZAMOS CONTADORES:
        if cong_prev >= 3:
            avs.consec_3 += 1
        else:
            avs.consec_3 = 0

        if cong_prev >= 2:
            avs.consec_2 += 1
        else:
            avs.consec_2 = 0

        if cong_prev < 2:
            avs.consec_1 += 1
        else:
            avs.consec_1 = 0
        
        #REGLAS DE ACTIVACIÓN DE LA POLÍTICA:
        # Encender fuerte si hay alta congestión sostenida (duró más de 2min)
        if avs.consec_3 >= 2:
            avs.delta, avs.i_max = 20.0, 4    # fuerte
        
        # Si no fuerte, quizá suave si hay congestión moderada sostenida
        elif avs.consec_2 >= 2:
            avs.delta, avs.i_max = 10.0, 3    # suave

        # Apagar sólo si estuvo tranquilo un buen rato
        elif avs.consec_1 >= 3:
            avs.delta, avs.i_max = 0.0, 0     # sin reducir velocidad
        # Si no se cumple nada, mantiene el estado anterior (no toca delta/i_max)

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
                      tormenta = tormenta,
                      historia = historia
            )

            metricas.registrar_aviones()
            avs.agregar_avion(a)
            historia[a.id] = {"t": [], "x": [], "v": [], "estado": [], "vmax": []}
            next_id += 1

            a.calcular_rango_velocidad()
            a.velocidad_actual = a.v_max_objetivo() 
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
            if (a.estado in ["En fila", "Reinsertado"]):
                # Necesitamos el techo del minuto:
                v_cap = a.v_max_objetivo()
                # 1) Señal de CONTROL (solo compresión real, por debajo del techo)
                if a.velocidad_actual < v_cap - 1e-6:
                    congestion_control[t] += 1 

                # 2) Señal de REPORTE (como antes, para plots/trade-off)
                if a.velocidad_actual < a.v_max - 1e-6: #INCLUYE EFECTO DE LA POLÍTICA
                    congestion[t] += 1

            # SI ATERRIZÓ 
            if a.estado == "Aterrizó":
                historia[a.id]["t"].append(t)
                historia[a.id]["estado"].append(a.estado)
        
            
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
            montevideo.aviones.remove(av)
        
    # AL FINAL: CUÁNTOS AVIONES QUEDARON EN EL AIRE
    metricas.en_vuelo(len(avs.aviones) + len(desviados.aviones) + len(viento.aviones) + len(tormenta.aviones))

    # DEVUELVE LA HISTORIA COMPLETA + MÉTRICAS MINUTO A MINUTO
    return {
        "historia": historia,
        "congestion": congestion,
        "congestion_control":  congestion_control,
        "desvios_montevideo": desvios_montevideo,
        "desvios_fila": desvios_fila,
        "desvios_viento": desvios_viento,
        "desvios_tormenta": desvios_tormenta
        }