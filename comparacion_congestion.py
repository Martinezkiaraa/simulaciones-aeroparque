import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from simulacion import simular_con_historia
from simulacion_mejorado import simular_con_historia_v2
from analisis import MetricasSimulacion, calcular_congestion_total, calcular_congestion_por_tramo
import random

def comparar_congestion(df_sin_mejora, df_con_mejora):
    """
    Compara la congestión entre simulaciones con y sin mejora.
    
    Parámetros:
    - df_sin_mejora: DataFrame con resultados de simulaciones sin mejora
    - df_con_mejora: DataFrame con resultados de simulaciones con mejora
    
    Devuelve:
    - DataFrame con métricas comparativas
    """
    
    resultados = []
    
    # Obtener lambdas únicos de ambos DataFrames
    lambdas_sin = df_sin_mejora['lambda'].unique()
    lambdas_con = df_con_mejora['lambda'].unique()
    lambdas_comunes = sorted(set(lambdas_sin) & set(lambdas_con))
    
    if not lambdas_comunes:
        raise ValueError("No hay valores de lambda comunes entre los DataFrames")
    
    for lambda_val in lambdas_comunes:
        # Filtrar por lambda
        df_sin_lambda = df_sin_mejora[df_sin_mejora['lambda'] == lambda_val]
        df_con_lambda = df_con_mejora[df_con_mejora['lambda'] == lambda_val]
        
        # Procesar cada realización
        for idx in range(len(df_sin_lambda)):
            fila_sin = df_sin_lambda.iloc[idx]
            fila_con = df_con_lambda.iloc[idx]
            
            # Calcular métricas de congestión para cada simulación
            congestion_sin = calcular_congestion_total(fila_sin['congestion'])
            congestion_con = calcular_congestion_total(fila_con['congestion'])
            
            # Congestión por tramo
            tramos_sin = calcular_congestion_por_tramo(fila_sin['historia'])
            tramos_con = calcular_congestion_por_tramo(fila_con['historia'])
            
            # Agregar resultados
            resultados.append({
                'realizacion': idx,
                'lambda': lambda_val,
                'tipo': 'Sin mejora',
                'frecuencia_congestion': congestion_sin['frecuencia_congestion'],
                'congestion_promedio': congestion_sin['congestion_promedio'],
                'congestion_maxima': congestion_sin['congestion_maxima'],
                'minutos_totales_congestion': congestion_sin['minutos_totales_congestion'],
                'congestion_lejos': tramos_sin['lejos'],
                'congestion_medio': tramos_sin['medio'],
                'congestion_cerca': tramos_sin['cerca'],
                'aterrizajes': fila_sin['aterrizajes'],
                'desvios_montevideo': fila_sin['montevideo'],
                'desvios_viento': fila_sin['viento'],
                'desvios_tormenta': fila_sin['tormenta'],
                'reinserciones': fila_sin['reinserciones']
            })
            
            resultados.append({
                'realizacion': idx,
                'lambda': lambda_val,
                'tipo': 'Con mejora',
                'frecuencia_congestion': congestion_con['frecuencia_congestion'],
                'congestion_promedio': congestion_con['congestion_promedio'],
                'congestion_maxima': congestion_con['congestion_maxima'],
                'minutos_totales_congestion': congestion_con['minutos_totales_congestion'],
                'congestion_lejos': tramos_con['lejos'],
                'congestion_medio': tramos_con['medio'],
                'congestion_cerca': tramos_con['cerca'],
                'aterrizajes': fila_con['aterrizajes'],
                'desvios_montevideo': fila_con['montevideo'],
                'desvios_viento': fila_con['viento'],
                'desvios_tormenta': fila_con['tormenta'],
                'reinserciones': fila_con['reinserciones']
            })
    
    return pd.DataFrame(resultados)

def analizar_diferencias(df):
    """
    Analiza las diferencias estadísticas entre simulaciones con y sin mejora.
    
    Parámetros:
    - df: DataFrame con resultados de comparar_congestion()
    
    Devuelve:
    - DataFrame con análisis estadístico de las diferencias
    """
    
    # Separar datos por tipo
    sin_mejora = df[df['tipo'] == 'Sin mejora']
    con_mejora = df[df['tipo'] == 'Con mejora']
    
    # Métricas a analizar
    metricas = [
        'frecuencia_congestion', 'congestion_promedio', 'congestion_maxima',
        'congestion_lejos', 'congestion_medio', 'congestion_cerca',
        'aterrizajes', 'desvios_montevideo', 'desvios_viento', 'reinserciones'
    ]
    
    resultados = []
    
    for metrica in metricas:
        valores_sin = sin_mejora[metrica].values
        valores_con = con_mejora[metrica].values
        
        # Calcular diferencias
        diferencias = valores_con - valores_sin
        reduccion_porcentual = (diferencias / valores_sin) * 100
        
        # Estadísticas
        media_dif = np.mean(diferencias)
        std_dif = np.std(diferencias)
        media_red = np.mean(reduccion_porcentual)
        std_red = np.std(reduccion_porcentual)
        
        # Test t de Student para diferencias
        from scipy import stats
        t_stat, p_value = stats.ttest_rel(valores_con, valores_sin)
        
        resultados.append({
            'metrica': metrica,
            'media_diferencia': media_dif,
            'std_diferencia': std_dif,
            'media_reduccion_porcentual': media_red,
            'std_reduccion_porcentual': std_red,
            't_statistic': t_stat,
            'p_value': p_value,
            'significativo': p_value < 0.05
        })
    
    return pd.DataFrame(resultados)

def graficar_comparacion(df, lambda_val, metricas_principales=None):
    """
    Crea gráficos comparativos entre simulaciones con y sin mejora.
    
    Parámetros:
    - df: DataFrame con resultados de comparar_congestion()
    - lambda_val: valor de lambda para filtrar
    - metricas_principales: lista de métricas a graficar (opcional)
    """
    
    if metricas_principales is None:
        metricas_principales = [
            'frecuencia_congestion', 'congestion_promedio', 'congestion_maxima',
            'congestion_lejos', 'congestion_medio', 'congestion_cerca'
        ]
    
    # Filtrar por lambda
    df_lambda = df[df['lambda'] == lambda_val]
    
    # Crear subplots
    n_metricas = len(metricas_principales)
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    axes = axes.flatten()
    
    for i, metrica in enumerate(metricas_principales):
        if i >= len(axes):
            break
            
        # Preparar datos para boxplot
        sin_mejora = df_lambda[df_lambda['tipo'] == 'Sin mejora'][metrica]
        con_mejora = df_lambda[df_lambda['tipo'] == 'Con mejora'][metrica]
        
        # Crear boxplot
        axes[i].boxplot([sin_mejora, con_mejora], 
                       labels=['Sin mejora', 'Con mejora'],
                       patch_artist=True)
        
        # Colorear las cajas
        axes[i].patches[0].set_facecolor('lightcoral')
        axes[i].patches[1].set_facecolor('lightblue')
        
        axes[i].set_title(f'{metrica.replace("_", " ").title()}')
        axes[i].set_ylabel('Valor')
        axes[i].grid(True, alpha=0.3)
    
    # Ocultar subplots vacíos
    for i in range(len(metricas_principales), len(axes)):
        axes[i].set_visible(False)
    
    plt.tight_layout()
    plt.suptitle(f'Comparación de Congestión - λ = {lambda_val}', fontsize=16, y=1.02)
    plt.show()

def graficar_congestion_directa(df_sin_mejora, df_con_mejora, lambda_val, titulo_sufijo=""):
    """
    Crea gráficos de comparación de congestión directamente desde DataFrames de experimentos.
    
    Parámetros:
    - df_sin_mejora: DataFrame con resultados sin mejora (de correr_experimentos)
    - df_con_mejora: DataFrame con resultados con mejora (de correr_experimentos)
    - lambda_val: valor de lambda para filtrar
    - titulo_sufijo: texto adicional para el título (ej: "Tormenta", "Viento")
    """
    
    # Filtrar por lambda
    df_sin_lambda = df_sin_mejora[df_sin_mejora['lambda'] == lambda_val]
    df_con_lambda = df_con_mejora[df_con_mejora['lambda'] == lambda_val]
    
    if len(df_sin_lambda) == 0 or len(df_con_lambda) == 0:
        print(f"No hay datos para lambda = {lambda_val}")
        return
    
    # Calcular métricas de congestión para cada realización
    metricas_sin = []
    metricas_con = []
    
    for _, fila in df_sin_lambda.iterrows():
        congestion_stats = calcular_congestion_total(fila['congestion'])
        tramos = calcular_congestion_por_tramo(fila['historia'])
        
        metricas_sin.append({
            'frecuencia_congestion': congestion_stats['frecuencia_congestion'],
            'congestion_promedio': congestion_stats['congestion_promedio'],
            'congestion_maxima': congestion_stats['congestion_maxima'],
            'congestion_lejos': tramos['lejos'],
            'congestion_medio': tramos['medio'],
            'congestion_cerca': tramos['cerca']
        })
    
    for _, fila in df_con_lambda.iterrows():
        congestion_stats = calcular_congestion_total(fila['congestion'])
        tramos = calcular_congestion_por_tramo(fila['historia'])
        
        metricas_con.append({
            'frecuencia_congestion': congestion_stats['frecuencia_congestion'],
            'congestion_promedio': congestion_stats['congestion_promedio'],
            'congestion_maxima': congestion_stats['congestion_maxima'],
            'congestion_lejos': tramos['lejos'],
            'congestion_medio': tramos['medio'],
            'congestion_cerca': tramos['cerca']
        })
    
    # Convertir a DataFrames
    df_metricas_sin = pd.DataFrame(metricas_sin)
    df_metricas_con = pd.DataFrame(metricas_con)
    
    # Crear gráficos
    metricas_principales = [
        'frecuencia_congestion', 'congestion_promedio', 'congestion_maxima',
        'congestion_lejos', 'congestion_medio', 'congestion_cerca'
    ]
    
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    axes = axes.flatten()
    
    for i, metrica in enumerate(metricas_principales):
        if i >= len(axes):
            break
            
        # Preparar datos para boxplot
        datos_sin = df_metricas_sin[metrica]
        datos_con = df_metricas_con[metrica]
        
        # Crear boxplot
        axes[i].boxplot([datos_sin, datos_con], 
                       labels=['Sin mejora', 'Con mejora'],
                       patch_artist=True)
        
        # Colorear las cajas
        axes[i].patches[0].set_facecolor('lightcoral')
        axes[i].patches[1].set_facecolor('lightblue')
        
        # Título de la métrica
        titulo_metrica = metrica.replace("_", " ").title()
        if metrica == 'frecuencia_congestion':
            titulo_metrica = 'Frecuencia de Congestión'
        elif metrica == 'congestion_promedio':
            titulo_metrica = 'Congestión Promedio'
        elif metrica == 'congestion_maxima':
            titulo_metrica = 'Congestión Máxima'
        elif metrica == 'congestion_lejos':
            titulo_metrica = 'Congestión Lejos (>50 MN)'
        elif metrica == 'congestion_medio':
            titulo_metrica = 'Congestión Medio (15-50 MN)'
        elif metrica == 'congestion_cerca':
            titulo_metrica = 'Congestión Cerca (<15 MN)'
        
        axes[i].set_title(titulo_metrica)
        axes[i].set_ylabel('Valor')
        axes[i].grid(True, alpha=0.3)
    
    # Ocultar subplots vacíos
    for i in range(len(metricas_principales), len(axes)):
        axes[i].set_visible(False)
    
    plt.tight_layout()
    titulo_principal = f'Comparación de Congestión - λ = {lambda_val}'
    if titulo_sufijo:
        titulo_principal += f' - {titulo_sufijo}'
    plt.suptitle(titulo_principal, fontsize=16, y=1.02)
    plt.show()
    
    # Mostrar estadísticas resumidas
    print(f"\n=== RESUMEN ESTADÍSTICO - λ = {lambda_val} ===")
    if titulo_sufijo:
        print(f"Escenario: {titulo_sufijo}")
    print()
    
    for metrica in metricas_principales:
        datos_sin = df_metricas_sin[metrica]
        datos_con = df_metricas_con[metrica]
        
        media_sin = datos_sin.mean()
        media_con = datos_con.mean()
        reduccion = ((media_con - media_sin) / media_sin) * 100 if media_sin != 0 else 0
        
        print(f"{metrica.replace('_', ' ').title()}:")
        print(f"  Sin mejora: {media_sin:.3f}")
        print(f"  Con mejora: {media_con:.3f}")
        print(f"  Diferencia: {media_con - media_sin:.3f} ({reduccion:+.1f}%)")
        print()

def resumen_comparacion(df, lambda_val):
    """
    Imprime un resumen de la comparación entre simulaciones con y sin mejora.
    
    Parámetros:
    - df: DataFrame con resultados de comparar_congestion()
    - lambda_val: valor de lambda para filtrar
    """
    
    # Filtrar por lambda
    df_lambda = df[df['lambda'] == lambda_val]
    
    # Separar por tipo
    sin_mejora = df_lambda[df_lambda['tipo'] == 'Sin mejora']
    con_mejora = df_lambda[df_lambda['tipo'] == 'Con mejora']
    
    print(f"\n{'='*60}")
    print(f"COMPARACIÓN DE CONGESTIÓN - λ = {lambda_val}")
    print(f"{'='*60}")
    
    # Métricas principales
    metricas = [
        ('Frecuencia de congestión', 'frecuencia_congestion'),
        ('Congestión promedio', 'congestion_promedio'),
        ('Congestión máxima', 'congestion_maxima'),
        ('Congestión lejos (>50 MN)', 'congestion_lejos'),
        ('Congestión medio (15-50 MN)', 'congestion_medio'),
        ('Congestión cerca (<15 MN)', 'congestion_cerca'),
        ('Aterrizajes', 'aterrizajes'),
        ('Desvíos a Montevideo', 'desvios_montevideo'),
        ('Reinserciones', 'reinserciones')
    ]
    
    print(f"\n{'Métrica':<25} {'Sin mejora':<12} {'Con mejora':<12} {'Diferencia':<12} {'Reducción %':<12}")
    print("-" * 80)
    
    for nombre, columna in metricas:
        sin_mean = sin_mejora[columna].mean()
        con_mean = con_mejora[columna].mean()
        diferencia = con_mean - sin_mean
        reduccion = (diferencia / sin_mean) * 100 if sin_mean != 0 else 0
        
        print(f"{nombre:<25} {sin_mean:<12.3f} {con_mean:<12.3f} {diferencia:<12.3f} {reduccion:<12.1f}%")
    
    print("-" * 80)
    
    # Análisis de significancia estadística
    print(f"\nANÁLISIS ESTADÍSTICO:")
    print("-" * 40)
    
    analisis = analizar_diferencias(df_lambda)
    
    for _, row in analisis.iterrows():
        if row['metrica'] in [col for _, col in metricas]:
            nombre = next(nombre for nombre, col in metricas if col == row['metrica'])
            significativo = "SÍ" if row['significativo'] else "NO"
            print(f"{nombre:<25} p-value: {row['p_value']:.4f} {'(Significativo)' if row['significativo'] else '(No significativo)'}")

def generar_dataframes_experimento(lambdas, minutos=1080, num_realizaciones=10, seed=None):
    """
    Genera los DataFrames necesarios para comparar congestión.
    
    Parámetros:
    - lambdas: lista de valores de lambda a probar
    - minutos: duración de cada simulación
    - num_realizaciones: número de realizaciones por lambda
    - seed: semilla para reproducibilidad
    
    Devuelve:
    - tupla (df_sin_mejora, df_con_mejora)
    """
    
    resultados_sin_mejora = []
    resultados_con_mejora = []
    
    for lambda_val in lambdas:
        print(f"Ejecutando experimentos para λ = {lambda_val}...")
        
        for realizacion in range(num_realizaciones):
            # Usar semilla diferente para cada realización si no se especifica una
            if seed is not None:
                current_seed = seed + realizacion
            else:
                current_seed = None
                
            # Simulación SIN mejora
            metricas_sin_mejora = MetricasSimulacion()
            data_sin_mejora = simular_con_historia(
                lambda_por_min=lambda_val,
                minutos=minutos,
                seed=current_seed,
                dia_ventoso=True,
                metricas=metricas_sin_mejora
            )
            
            # Simulación CON mejora
            metricas_con_mejora = MetricasSimulacion()
            data_con_mejora = simular_con_historia_v2(
                lambda_por_min=lambda_val,
                minutos=minutos,
                seed=current_seed,
                dia_ventoso=True,
                metricas=metricas_con_mejora
            )
            
            # Agregar resultados sin mejora
            resultados_sin_mejora.append({
                'lambda': lambda_val,
                'realizacion': realizacion,
                'aterrizajes': metricas_sin_mejora.aterrizajes,
                'montevideo': metricas_sin_mejora.desvios_montevideo,
                'viento': metricas_sin_mejora.desvios_viento,
                'tormenta': metricas_sin_mejora.desvios_tormenta,
                'reinserciones': metricas_sin_mejora.reinserciones,
                'congestion': data_sin_mejora['congestion'],
                'historia': data_sin_mejora['historia']
            })
            
            # Agregar resultados con mejora
            resultados_con_mejora.append({
                'lambda': lambda_val,
                'realizacion': realizacion,
                'aterrizajes': metricas_con_mejora.aterrizajes,
                'montevideo': metricas_con_mejora.desvios_montevideo,
                'viento': metricas_con_mejora.desvios_viento,
                'tormenta': metricas_con_mejora.desvios_tormenta,
                'reinserciones': metricas_con_mejora.reinserciones,
                'congestion': data_con_mejora['congestion'],
                'historia': data_con_mejora['historia']
            })
    
    return pd.DataFrame(resultados_sin_mejora), pd.DataFrame(resultados_con_mejora)

def experimento_completo(lambdas, minutos=1080, num_realizaciones=10, seed=None):
    """
    Ejecuta un experimento completo comparando congestión para múltiples valores de lambda.
    
    Parámetros:
    - lambdas: lista de valores de lambda a probar
    - minutos: duración de cada simulación
    - num_realizaciones: número de realizaciones por lambda
    - seed: semilla para reproducibilidad
    
    Devuelve:
    - DataFrame con todos los resultados comparativos
    """
    
    # Generar DataFrames de entrada
    df_sin_mejora, df_con_mejora = generar_dataframes_experimento(
        lambdas, minutos, num_realizaciones, seed
    )
    
    # Comparar congestión
    return comparar_congestion(df_sin_mejora, df_con_mejora)

# Ejemplo de uso
if __name__ == "__main__":
    # Ejemplo de uso básico
    print("Ejecutando comparación de congestión...")
    
    # Generar DataFrames de entrada
    df_sin_mejora, df_con_mejora = generar_dataframes_experimento(
        lambdas=[0.25],  # 15 aviones por hora
        minutos=1080,    # 18 horas
        num_realizaciones=5,  # 5 realizaciones Monte Carlo
        seed=42
    )
    
    # Comparar congestión
    resultados = comparar_congestion(df_sin_mejora, df_con_mejora)
    
    # Mostrar resumen
    resumen_comparacion(resultados, 0.25)
    
    # Crear gráficos
    graficar_comparacion(resultados, 0.25)
    
    # Análisis estadístico
    analisis = analizar_diferencias(resultados)
    print("\nAnálisis estadístico detallado:")
    print(analisis[['metrica', 'media_diferencia', 'media_reduccion_porcentual', 'p_value', 'significativo']])
