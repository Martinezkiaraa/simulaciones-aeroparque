from experimentos import correr_experimentos
from analisis import MetricasSimulacion
from graficos import plot_metricas
from simulacion import run_simulacion
import numpy as np
import matplotlib.pyplot as plt

# EJERCICIO 3 ACOMODAR RUN_SIMULACION

def estimar_prob_5(n_sim=200_000, seed=42):
    np.random.seed(seed)
    cuenta_5 = 0
    
    for i in range(n_sim):
        aviones = run_simulacion(lambda_por_min=1/60, minutos=60, seed=seed+i)
        if len(aviones) == 5:
            cuenta_5 += 1
    
    p_hat = cuenta_5 / n_sim
    se = np.sqrt(p_hat * (1 - p_hat) / n_sim)
    ic = (p_hat - 1.96 * se, p_hat + 1.96 * se)
    return p_hat, se, ic


if __name__ == "__main__":
    lambdas = [0.02, 0.1, 0.2, 0.5, 1]
    metricas_lambdas = {lam: MetricasSimulacion() for lam in lambdas}

    #n_rep + grande
    df = correr_experimentos(lambdas, n_rep=300, metricas_lambda = metricas_lambdas)

    # Guardar resultados
    df.to_csv("resultados_simulacion.csv", index=False)

    for m in metricas_lambdas:
        resumen = metricas_lambdas[m].resumen()
        print(resumen)

    # Graficar
    #plot_metricas(df, "congestion_prom", "Aviones en congestión", "Congestión promedio por lambda")
    #plot_metricas(df, "montevideo_prom", "Desvíos a Montevideo", "Desvíos promedio a Montevideo por lambda")
    #plot_metricas(df, "atraso_prom", "Atraso promedio (minutos)", "Atraso promedio por lambda")

    #Ejercicio 4
    