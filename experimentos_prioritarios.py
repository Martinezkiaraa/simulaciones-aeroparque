import numpy as np
import pandas as pd
from analisis import (
    analizar_congestion,
    analizar_montevideo,
    analizar_viento,
    analizar_tormenta,
    calcular_atraso_promedio,
    calcular_congestion_total,
    calcular_congestion_por_tramo,
    tiempo_ideal)
from simulacion_prioritarios import simular_con_historia_prioritarios


def correr_experimentos_prioritarios(lambdas, n_rep = 100, minutos = 1080, p_prioritario = 0.05, seed = 0, dia_ventoso = False, hay_tormenta = False, metricas_lambda = {}):
    t_ideal = tiempo_ideal()
    resultados = []

    inicio_tormenta = None
    if hay_tormenta:
        import random
        random.seed()
        inicio_tormenta = random.uniform(0, minutos)

    for lam in lambdas:
        for rep in range(n_rep):
            sim_data = simular_con_historia_prioritarios(
                lambda_por_min = lam,
                minutos = minutos,
                seed = seed + rep,
                dia_ventoso = dia_ventoso,
                inicio_tormenta = inicio_tormenta,
                metricas = metricas_lambda,
                p_prioritario = p_prioritario
            )

            congestion_stats = analizar_congestion(sim_data)
            montevideo_stats = analizar_montevideo(sim_data)
            viento_stats = analizar_viento(sim_data)
            tormenta_stats = analizar_tormenta(sim_data)
            atraso_prom = calcular_atraso_promedio(sim_data, t_ideal)
            congestion_total = calcular_congestion_total(sim_data["congestion"])
            congestion_tramo = calcular_congestion_por_tramo(sim_data["historia"])

            # Proporción de aterrizajes prioritarios vs no prioritarios
            prio_landed = 0
            prio_total = 0
            for avion in sim_data["historia"].values():
                if avion.get("prio", False):
                    prio_total += 1
                    if "Aterrizó" in avion["estado"]:
                        prio_landed += 1

            resultados.append({
                "lambda": lam,
                "rep": rep,
                "congestion_prom": congestion_stats["promedio"],
                "montevideo_prom": montevideo_stats["promedio"],
                "montevideo_freq": montevideo_stats["frecuencia"],
                "viento_prom": viento_stats["promedio"],
                "viento_freq": viento_stats["frecuencia"],
                "tormenta_prom": tormenta_stats["promedio"],
                "tormenta_freq": tormenta_stats["frecuencia"],
                "atraso_prom": atraso_prom,
                "frecuencia_congestion": congestion_total["frecuencia_congestion"],
                "congestion_maxima": congestion_total["congestion_maxima"],
                "congestion_lejos": congestion_tramo["lejos"],
                "congestion_medio": congestion_tramo["medio"],
                "congestion_cerca": congestion_tramo["cerca"],
                "historia": sim_data["historia"],
                "prio_landed_rate": (prio_landed / prio_total) if prio_total > 0 else 0.0,
                "prio_share": prio_total / max(1, len(sim_data["historia"]))
            })

    return pd.DataFrame(resultados)


