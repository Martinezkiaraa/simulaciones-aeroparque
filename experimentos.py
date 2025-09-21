import numpy as np
import pandas as pd
import random
from simulacion import simular_con_historia
from analisis import (
    analizar_congestion,
    analizar_montevideo,
    analizar_viento,
    analizar_tormenta,
    calcular_atraso_promedio,
    tiempo_ideal
)

# ============================================================
# PARTE 4, 5 y 6: CORRER EXPERIMENTOS PARA VARIOS λ
# ============================================================

def correr_experimentos(lambdas, n_rep = 100, minutos = 1080, metricas_lambda = {}, dia_ventoso = True, hay_tormenta = False, seed = 0):
    """
    Corre simulaciones Monte Carlo para una lista de valores de λ.
    
    Parámetros:
    - lambdas: lista de tasas de arribo λ (aviones por minuto)
    - n_rep: cantidad de repeticiones por λ
    - minutos: duración de cada simulación (por defecto 18h = 1080 min)
    - metricas_lambda: diccionario {λ: objeto MetricasSimulacion()}
    - dia_ventoso: si True, existe probabilidad de go-around al río (parte 5)
    - hay_tormenta: si True, se simula un cierre de AEP por 30 min (parte 6)
    
    Devuelve:
    - DataFrame con resultados agregados de cada repetición
    """
    t_ideal = tiempo_ideal()
    resultados = []

    if hay_tormenta:
        inicio_tormenta = random.uniform(0,1080)
        print(f"======== La tormenta iniciará en el tiempo ======= {inicio_tormenta}")
    else:
        inicio_tormenta = None
    
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
                "atraso_prom": atraso_prom
            })

    
    return pd.DataFrame(resultados)