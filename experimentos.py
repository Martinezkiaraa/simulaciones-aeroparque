import numpy as np
import pandas as pd
from simulacion import simular_con_historia
from analisis import analizar_congestion, analizar_montevideo, calcular_atraso_promedio, tiempo_ideal

def correr_experimentos(lambdas, n_rep=100, minutos=1080, metricas_lambda = {}):
    t_ideal = tiempo_ideal()
    resultados = []
    for lam in lambdas:
        metrica_ = metricas_lambda[lam]
        for rep in range(n_rep):
            sim_data = simular_con_historia(lambda_por_min=lam, minutos=minutos, metricas= metrica_)

            congestion_stats = analizar_congestion(sim_data["congestion"])
            montevideo_stats = analizar_montevideo(sim_data["desvios_montevideo"])
            atraso_prom = calcular_atraso_promedio(sim_data["historia"], t_ideal)

            resultados.append({
                "lambda": lam,
                "rep": rep,
                "congestion_prom": congestion_stats["promedio"],
                "congestion_freq": congestion_stats["frecuencia"],
                "montevideo_prom": montevideo_stats["promedio"],
                "montevideo_freq": montevideo_stats["frecuencia"],
                "atraso_prom": atraso_prom
            })

    return pd.DataFrame(resultados)
