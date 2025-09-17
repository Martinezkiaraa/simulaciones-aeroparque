import pandas as pd
from simulacion import simular_con_historia
from analisis import (
    analizar_congestion,
    analizar_montevideo,
    analizar_rio,                 # PARTE 5
    calcular_atraso_promedio,
    tiempo_ideal
)

# ============================================================
# PARTE 4 Y 5: CORRER EXPERIMENTOS PARA VARIOS λ
# ============================================================

def correr_experimentos(lambdas, n_rep = 100, minutos = 1080, metricas_lambda = {}, dia_ventoso = True):
    # CALCULA EL TIEMPO IDEAL (SIN CONGESTIÓN) PARA USAR COMO BASELINE
    t_ideal = tiempo_ideal()
    # LISTA DONDE SE VAN A GUARDAR LOS RESULTADOS DE TODAS LAS REPETICIONES
    resultados = []
    
    # RECORRE CADA VALOR DE λ QUE QUEREMOS SIMULAR
    for lam in lambdas:
        # OBTIENE EL OBJETO DE MÉTRICAS ASOCIADO A ESTE λ
        metrica_ = metricas_lambda[lam]

        # CORRE N_REP VECES LA SIMULACIÓN PARA ESTE λ
        for rep in range(n_rep):
            # EJECUTA UNA SIMULACIÓN DE MONTE CARLO COMPLETA
            sim_data = simular_con_historia(
                lambda_por_min = lam,
                dia_ventoso = dia_ventoso,
                minutos = minutos,
                metricas = metrica_
            )

            # CALCULA ESTADÍSTICAS DE CONGESTIÓN (PARTE 4)
            congestion_stats = analizar_congestion(sim_data["congestion"])
            
            # CALCULA ESTADÍSTICAS DE DESVÍOS A MONTEVIDEO (PARTE 4)
            montevideo_stats = analizar_montevideo(sim_data["desvios_montevideo"])
            
            # CALCULA ESTADÍSTICAS DE DESVÍOS AL RÍO (PARTE 5)
            rio_stats = analizar_rio(sim_data["desvios_rio"])
            
            # CALCULA ATRASO PROMEDIO RESPECTO AL TIEMPO IDEAL (PARTE 4 y 5)
            atraso_prom = calcular_atraso_promedio(sim_data["historia"], t_ideal)

            # GUARDA LOS RESULTADOS DE ESTA REPETICIÓN EN UNA FILA
            resultados.append({
                "lambda": lam,                          # λ usado
                "rep": rep,                             # número de repetición
                "congestion_prom": congestion_stats["promedio"],   # congestión promedio
                "congestion_freq": congestion_stats["frecuencia"], # frecuencia de congestión
                "montevideo_prom": montevideo_stats["promedio"],   # desvío promedio
                "montevideo_freq": montevideo_stats["frecuencia"], # frecuencia de desvíos
                "rio_prom": rio_stats["promedio"],                 # NUEVO (parte 5)
                "rio_freq": rio_stats["frecuencia"],               # NUEVO (parte 5)
                "atraso_prom": atraso_prom                         # atraso promedio
            })

    # DEVUELVE LOS RESULTADOS COMO UN DATAFRAME DE PANDAS
    return pd.DataFrame(resultados)