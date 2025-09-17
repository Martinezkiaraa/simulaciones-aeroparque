from experimentos import correr_experimentos
from analisis import MetricasSimulacion
from graficos import plot_resumen_metricas, plot_error_estimacion, visualizar_simulacion_monte_carlo, animar_simulacion_monte_carlo, plot_comparacion_tiempos
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
    # Ejercicio 1: Simulación Monte Carlo con visualización
    print("=== EJERCICIO 1: Simulación Monte Carlo ===")
    print("Ejecutando simulación detallada con lambda=0.1...")
    
    # Simulación Monte Carlo detallada
    # Reutilizamos simular_con_historia para obtener historia completa con velocidades
    from simulacion import simular_con_historia
    datos_mc = simular_con_historia(lambda_por_min=0.1, minutos=200, seed=42, dia_ventoso=False, metricas=MetricasSimulacion())
    
    print(f"Aviones finales: {datos_mc['aviones_finales']}")
    print("Generando visualizaciones...")
    
    # Visualización estática (x vs t y v vs t)
    visualizar_simulacion_monte_carlo(datos_mc, mostrar_ultimos_minutos=100)
    
    # Visualización animada (opcional - comentar si es muy lenta)
    print("Generando animación...")
    anim = animar_simulacion_monte_carlo({"historia": datos_mc["historia"]}, mostrar_ultimos_minutos=100, intervalo=200)
    
    print("=== FIN EJERCICIO 1 ===\n")
    
    # Ejercicio 3: prob de 5 aviones en una hora
    print("=== EJERCICIO 3: Probabilidad de 5 aviones en una hora ===")
    p_hat, se, ic = estimar_prob_5(n_sim=200_000, seed=42)
    print(f"p(5 en 1h) ≈ {p_hat:.5f}  |  SE={se:.5f}  |  IC95%=({ic[0]:.5f}, {ic[1]:.5f})")
    print("=== FIN EJERCICIO 3 ===\n")


    # Ejercicio 4
    print("=== EJERCICIO 4: Congestión y atrasos con distintos lambdas SIN dia ventoso ===")
    print("Ejecutando simulación detallada distintos lambdas SIN dia ventoso")
    
    lambdas = [0.02, 0.1, 0.2, 0.5, 1]
    metricas_lambdas = {lam: MetricasSimulacion() for lam in lambdas}

    #n_rep + grande
    df = correr_experimentos(lambdas, n_rep=2000, dia_ventoso=False, metricas_lambda = metricas_lambdas)

    # Guardar resultados
    df.to_csv("resultados_simulacion.csv", index=False)

    for m in metricas_lambdas:
        resumen = metricas_lambdas[m].resumen()
        print(resumen)

   
    plot_resumen_metricas(df)
    plot_comparacion_tiempos(df)

    # Error de estimación (SEM) por métrica
    plot_error_estimacion(df, "congestion_freq", "SEM de frecuencia de congestión")
    plot_error_estimacion(df, "montevideo_freq", "SEM de frecuencia de desvíos a Montevideo")
    plot_error_estimacion(df, "atraso_prom", "SEM de atraso promedio")

    print("=== FIN EJERCICIO 4 ===\n")

    