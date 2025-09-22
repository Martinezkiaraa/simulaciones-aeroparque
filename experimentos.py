import pandas as pd
import random
from simulacion import simular_con_historia
from simulacion_mejorado import simular_con_historia_v2
from simulacion_prioritarios import simular_con_historia_prioritarios
from analisis import (
    MetricasSimulacion,
    analizar_congestion,
    analizar_congestion_control,
    analizar_montevideo,
    analizar_viento,
    analizar_tormenta,
    calcular_atraso_promedio,
    calcular_congestion_total,
    calcular_congestion_por_tramo,
    tiempo_ideal
)

# ============================================================
# PARTE 4, 5 y 6: CORRER EXPERIMENTOS PARA VARIOS λ
# ============================================================

def correr_experimentos(lambdas, n_rep = 100, p_prioritario = 0, minutos = 1080, metricas_lambda = {}, dia_ventoso = False, hay_tormenta = False, seed = 0, mejora = False):

    t_ideal = tiempo_ideal()
    resultados = []

    if hay_tormenta:
        random.seed()
        inicio_tormenta = random.uniform(0,minutos)
    else:
        inicio_tormenta = None

    #CASO NORMAL
    if not mejora and p_prioritario == 0:

        # RECORRE CADA VALOR DE λ 
        for lam in lambdas:
            metrica_ = metricas_lambda[lam]

            # REPITE LA SIMULACIÓN n_rep VECES
            for rep in range(n_rep):
                seed_actual = seed + rep
                sim_data = simular_con_historia(
                lambda_por_min = lam,
                minutos = minutos,seed = seed_actual,
                dia_ventoso = dia_ventoso,
                inicio_tormenta = inicio_tormenta,  # o un número si querés simular tormenta
                metricas = metrica_)
                            
                congestion_stats = analizar_congestion(sim_data)
                montevideo_stats = analizar_montevideo(sim_data)
                viento_stats = analizar_viento(sim_data)
                tormenta_stats = analizar_tormenta(sim_data)
                atraso_prom = calcular_atraso_promedio(sim_data, t_ideal)
                congestion_total = calcular_congestion_total(sim_data["congestion"])
                congestion_tramo = calcular_congestion_por_tramo(sim_data["historia"])

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
                    "historia": sim_data["historia"] 
                })

    #CASO PRIORITARIO
    elif p_prioritario > 0 and not mejora:

        for lam in lambdas:
            for rep in range(n_rep):
                metrica_ = metricas_lambda[lam]
                sim_data = simular_con_historia_prioritarios(
                    lambda_por_min = lam,
                    minutos = minutos,
                    seed = seed + rep,
                    dia_ventoso = dia_ventoso,
                    inicio_tormenta = inicio_tormenta,
                    metricas = metrica_,
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
    
    #CASO CON MEJORA
    else:
        for lam in lambdas:
            metrica_ = metricas_lambda[lam]

            # REPITE LA SIMULACIÓN n_rep VECES
            for rep in range(n_rep):
                seed_actual = seed + rep
                sim_data = simular_con_historia_v2(
                lambda_por_min = lam,
                minutos = minutos,seed = seed_actual,
                dia_ventoso = dia_ventoso,
                inicio_tormenta = inicio_tormenta,  # o un número si querés simular tormenta
                metricas = metrica_)
                            
                congestion_stats = analizar_congestion(sim_data)
                montevideo_stats = analizar_montevideo(sim_data)
                viento_stats = analizar_viento(sim_data)
                tormenta_stats = analizar_tormenta(sim_data)
                atraso_prom = calcular_atraso_promedio(sim_data, t_ideal)
                congestion_total = calcular_congestion_total(sim_data["congestion"])
                congestion_tramo = calcular_congestion_por_tramo(sim_data["historia"])
                congestion_control_stats = analizar_congestion_control(sim_data)
                congestion_control_total = calcular_congestion_total(sim_data["congestion_control"]) if "congestion_control" in sim_data else None

                resultado = {
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
                    "congestion": sim_data["congestion"]
                }
                
                if congestion_control_total is not None:
                    resultado.update({
                        "congestion_control": sim_data["congestion_control"],
                        "frecuencia_congestion_control": congestion_control_total["frecuencia_congestion"],
                        "congestion_control_maxima": congestion_control_total["congestion_maxima"]
                    })
                
                resultados.append(resultado)

    return pd.DataFrame(resultados)
