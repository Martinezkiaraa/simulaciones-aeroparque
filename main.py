from experimentos import correr_experimentos
from analisis import MetricasSimulacion, IC_globales
import pandas as pd
#matplotlib.use('Agg')
from graficos import (
    plot_desvios_y_congestion,
    animar_con_estelas,
    plot_comparacion_tiempos)
from simulacion import run_simulacion, simular_con_historia
import numpy as np
#matplotlib.use("Agg")  # para que no bloquee, usa backend no interactivo

# ============================================================
# PARTE 3 DE LA CONSIGNA
# ESTIMA LA PROBABILIDAD DE QUE LLEGUEN EXACTAMENTE 5 AVIONES EN UNA HORA
# USANDO SIMULACIÓN MONTE CARLO (CON λ = 1/60).
# ============================================================

def estimar_prob_5(n_sim = 200_000, seed = 42):
    np.random.seed(seed)
    cuenta_5 = 0
    
    for i in range(n_sim):
        # CORRE UNA SIMULACIÓN DE 60 MINUTOS CON λ = 1/60
        aviones = run_simulacion(lambda_por_min = 1/60, minutos = 60, seed = seed + i)
        # CUENTA SI HUBO EXACTAMENTE 5 AVIONES EN ESE PERIODO
        if len(aviones) == 5:
            cuenta_5 += 1
    
    # ESTIMACIÓN MONTE CARLO DE P(N=5)
    p_hat = cuenta_5 / n_sim
    # ERROR ESTÁNDAR DE LA PROPORCIÓN
    se = np.sqrt(p_hat * (1 - p_hat) / n_sim)
    # INTERVALO DE CONFIANZA 95%
    ic = (p_hat - 1.96 * se, p_hat + 1.96 * se)
    return p_hat, se, ic

# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

if __name__ == "__main__":
    
    # --------------------------------------------------------
    # PARTE 1: SIMULACIÓN DE MONTE CARLO CON VISUALIZACIÓN
    # --------------------------------------------------------

    print("=== EJERCICIO 1: Simulación Monte Carlo ===")
    print("Ejecutando simulación detallada con lambda = 0.1...")
    
    datos_mc = simular_con_historia(
        lambda_por_min = 0.1, 
        minutos = 200, 
        seed = 42, 
        dia_ventoso = False, 
        metricas = MetricasSimulacion()
    )
    
    print(f"Aviones finales registrados: {len(datos_mc['historia'])}")
    print("Generando visualizaciones...")
    
    animar_con_estelas(datos_mc["historia"], minutos=200, tail=20)

    print("=== FIN EJERCICIO 1 ===\n")
    
    # --------------------------------------------------------
    # PARTE 3: PROBABILIDAD DE 5 AVIONES EN 1 HORA
    # --------------------------------------------------------

    print("=== EJERCICIO 3: Probabilidad de 5 aviones en una hora ===")
    p_hat, se, ic = estimar_prob_5(n_sim = 200_000, seed = 42)
    print(f"p(5 en 1h) ≈ {p_hat:.5f}  |  SE={se:.5f}  |  IC95%=({ic[0]:.5f}, {ic[1]:.5f})")
    print("=== FIN EJERCICIO 3 ===\n")

    # --------------------------------------------------------
    # PARTE 4: SIMULACIÓN CON DISTINTOS λ (SIN DÍA VENTOSO)
    # --------------------------------------------------------

    print("=== EJERCICIO 4: Congestión y atrasos con distintos lambdas SIN dia ventoso ===")
    
    lambdas = [0.02, 0.1, 0.2, 0.5, 1]
    metricas_lambdas = {lam: MetricasSimulacion() for lam in lambdas}

    # HAY QUE CAMBIAR N_REP A 2000, PERO PARA PROBAR TARDA MUCHO
    df = correr_experimentos(lambdas, n_rep = 50, dia_ventoso = False, metricas_lambda = metricas_lambdas, seed = 2025)
    df.to_csv("resultados_simulacion.csv", index = False)

    data = []
    for l in lambdas:
        m = metricas_lambdas[l]
        data.append({
            "lambda": l,
            "desvios_montevideo": m.desvios_montevideo})

    df_resultados = pd.DataFrame(data)

    for m in metricas_lambdas:
        print(metricas_lambdas[m].resumen())

    #GRÁFICOS DE CONGESTIÓN Y CANTIDAD DE AVIONES A MONTEVIDEO POR LAMBDA
    plot_desvios_y_congestion(df_resultados,df)
    print(IC_globales(df))

    #ATRASO CON Y SIN CONGESTIÓN
    plot_comparacion_tiempos(df)
    
    print("=== FIN EJERCICIO 4 ===\n") 

    # --------------------------------------------------------
    # PARTE 5: SIMULACIÓN CON DISTINTOS λ (CON DÍA VENTOSO)
    # --------------------------------------------------------

    print("=== EJERCICIO 5: Atrasos y desvíos con distintos λ CON día ventoso ===")

    metricas_lambdas_ventoso = {lam: MetricasSimulacion() for lam in lambdas}

    # HAY QUE CAMBIAR N_REP A 2000, PERO PARA PROBAR TARDA MUCHO
    df_ventoso = correr_experimentos(lambdas, n_rep = 50, dia_ventoso = True, metricas_lambda = metricas_lambdas_ventoso)
    df_ventoso.to_csv("resultados_simulacion_ventoso.csv", index = False)

    for m in metricas_lambdas_ventoso:
        print(metricas_lambdas_ventoso[m].resumen())

    plot_comparacion_tiempos(df_ventoso)

    print("=== FIN EJERCICIO 5 ===\n")

    # --------------------------------------------------------
    # PARTE 6: SIMULACIÓN CON TORMENTA (CIERRE SORPRESIVO AEP)
    # --------------------------------------------------------
    
    print("=== EJERCICIO 6: Solo tormenta de 30 minutos ===")

    metricas_lambdas_tormenta = {lam: MetricasSimulacion() for lam in lambdas}

    # HAY QUE CAMBIAR N_REP A 2000, PERO PARA PROBAR TARDA MUCHO
    df_tormenta = correr_experimentos(lambdas, n_rep = 50, dia_ventoso = False, metricas_lambda = metricas_lambdas_tormenta, hay_tormenta = True)
    df_tormenta.to_csv("resultados_simulacion_tormenta.csv", index = False)

    for m in metricas_lambdas_tormenta:
        print(metricas_lambdas_tormenta[m].resumen())

    plot_comparacion_tiempos(df_tormenta)

    print("=== FIN EJERCICIO 6 ===\n")