import numpy as np
import pandas as pd
import random
from simulacion import simular_con_historia
from simulacion_mejorado import simular_con_historia_v2
from analisis import (
    analizar_congestion,
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

def correr_experimentos(lambdas, n_rep = 100, minutos = 1080, metricas_lambda = {}, dia_ventoso = False, hay_tormenta = False, seed = 0, mejora = False):

    t_ideal = tiempo_ideal()
    resultados = []

    if hay_tormenta:
        random.seed()
        inicio_tormenta = random.uniform(0,1080)
        print(f"======== La tormenta iniciará en el tiempo ======= {inicio_tormenta}")
    else:
        inicio_tormenta = None

    if not mejora:

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
                            
                # ESTADÍSTICAS DE CONGESTIÓN
                congestion_stats = analizar_congestion(sim_data)
                
                # ESTADÍSTICAS DE DESVÍOS A MONTEVIDEO
                montevideo_stats = analizar_montevideo(sim_data)
                
                # ESTADÍSTICAS DE DESVÍOS POR VIENTO (PARTE 5)
                viento_stats = analizar_viento(sim_data)

                # ESTADÍSTICAS DE DESVÍOS POR TORMENTA (PARTE 6)
                tormenta_stats = analizar_tormenta(sim_data)
                
                # ATRASO PROMEDIO RESPECTO AL TIEMPO IDEAL
                atraso_prom = calcular_atraso_promedio(sim_data, t_ideal)
                
                # NUEVAS MÉTRICAS DE CONGESTIÓN POR REALIZACIÓN
                congestion_total = calcular_congestion_total(sim_data["congestion"])
                congestion_tramo = calcular_congestion_por_tramo(sim_data["historia"])

                # GUARDA RESULTADOS DE ESTA REPETICIÓN
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
                            
                # ESTADÍSTICAS DE CONGESTIÓN
                congestion_stats = analizar_congestion(sim_data)
                
                # ESTADÍSTICAS DE DESVÍOS A MONTEVIDEO
                montevideo_stats = analizar_montevideo(sim_data)
                
                # ESTADÍSTICAS DE DESVÍOS POR VIENTO (PARTE 5)
                viento_stats = analizar_viento(sim_data)

                # ESTADÍSTICAS DE DESVÍOS POR TORMENTA (PARTE 6)
                tormenta_stats = analizar_tormenta(sim_data)
                
                # ATRASO PROMEDIO RESPECTO AL TIEMPO IDEAL
                atraso_prom = calcular_atraso_promedio(sim_data, t_ideal)
                
                # NUEVAS MÉTRICAS DE CONGESTIÓN POR REALIZACIÓN
                congestion_total = calcular_congestion_total(sim_data["congestion"])
                congestion_tramo = calcular_congestion_por_tramo(sim_data["historia"])

                # GUARDA RESULTADOS DE ESTA REPETICIÓN
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

    return pd.DataFrame(resultados)
