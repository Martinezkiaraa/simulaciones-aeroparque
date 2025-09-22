from plane_prioritarios import plane_prioritario
from heap import heap
import random
from analisis import MetricasSimulacion

# ============================================================
# SIMULACIÓN CON AVIONES PRIORITARIOS
# - Proporción p_prioritario de aviones con prioridad alta
# - Solo los prioritarios usan separación efectiva de 3 minutos
# - Historia incluye marca 'prio' por avión para análisis posterior
# ============================================================


def simular_con_historia_prioritarios(lambda_por_min, minutos, seed = None, dia_ventoso = True,
                                      inicio_tormenta = None, metricas = MetricasSimulacion(),
                                      p_prioritario: float = 0.05):

    if seed is not None:
        random.seed(seed)

    avs = heap()
    desviados = heap()
    montevideo = heap()
    viento = heap()
    tormenta = heap()
    next_id = 1
    historia = {}

    congestion = {t: 0 for t in range(minutos)}
    desvios_montevideo = {t: 0 for t in range(minutos)}
    desvios_fila = {t: 0 for t in range(minutos)}
    desvios_viento = {t: 0 for t in range(minutos)}
    desvios_tormenta = {t: 0 for t in range(minutos)}

    duracion_tormenta = 30

    for t in range(minutos):
        tormenta_activa = (
            inicio_tormenta is not None and
            inicio_tormenta <= t < inicio_tormenta + duracion_tormenta
        )

        # Generación de aviones
        if random.random() < lambda_por_min:
            es_prio = (random.random() < p_prioritario)
            a = plane_prioritario(
                id = next_id,
                minuto_aparicion = t,
                fila = avs,
                desviados = desviados,
                mtvd = montevideo,
                viento = viento,
                tormenta = tormenta,
                historia = historia,
                prioritario = es_prio
            )
            metricas.registrar_aviones()
            avs.agregar_avion(a)
            historia[a.id] = {"t": [], "x": [], "v": [], "estado": [], "vmax": [], "prio": es_prio}
            next_id += 1

        # Avances en la fila principal
        for a in list(avs.aviones):
            a.avanzar(minuto_actual = t,
                      dt = 1.0,
                      hay_viento = dia_ventoso,
                      tormenta_activa = tormenta_activa,
                      metricas = metricas)

            if (a.estado in ["En fila", "Reinsertado"]) and a.velocidad_actual < a.v_max:
                congestion[t] += 1

            if a.estado == "Aterrizó":
                historia[a.id]["t"].append(t)
                historia[a.id]["estado"].append(a.estado)

            if a.estado != "Aterrizó":
                historia[a.id]["t"].append(t)
                historia[a.id]["x"].append(a.distancia_mn_aep)
                historia[a.id]["v"].append(a.velocidad_actual)
                historia[a.id]["estado"].append(a.estado)
                historia[a.id]["vmax"].append(a.v_max)

        # Desviados por congestión
        for d in list(desviados.aviones):
            desvios_fila[t] += 1
            d.avanzar(t, dt = 1.0, hay_viento = dia_ventoso, tormenta_activa = tormenta_activa, metricas = metricas)
            if d.estado == "Reinsertado":
                metricas.registrar_reinsercion(d.id)

        # Desvíos por viento
        for v in list(viento.aviones):
            desvios_viento[t] += 1
            v.avanzar(t, dt = 1.0, hay_viento = dia_ventoso, tormenta_activa = tormenta_activa, metricas = metricas)

        # Desvíos por tormenta
        for r in list(tormenta.aviones):
            desvios_tormenta[t] += 1
            r.avanzar(t, dt = 1.0, hay_viento = dia_ventoso, tormenta_activa = tormenta_activa, metricas = metricas)

        # Montevideo
        for av in list(montevideo.aviones):
            desvios_montevideo[t] += 1
            historia[av.id]["t"].append(t)
            historia[av.id]["estado"].append(av.estado)
            montevideo.aviones.remove(av)

    metricas.en_vuelo(len(avs.aviones) + len(desviados.aviones) + len(viento.aviones) + len(tormenta.aviones))

    return {
        "historia": historia,
        "congestion": congestion,
        "desvios_montevideo": desvios_montevideo,
        "desvios_fila": desvios_fila,
        "desvios_viento": desvios_viento,
        "desvios_tormenta": desvios_tormenta
    }


