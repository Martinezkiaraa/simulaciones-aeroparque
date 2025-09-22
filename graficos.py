from doctest import DocFileSuite
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import pandas as pd
from analisis import tiempo_ideal, analizar_congestion_promedio
import seaborn as sns
import numpy as np

def animar_fila_radar(historia, minutos, tail):
    # Construyo por tiempo: lista de (id, distancia) en cada minuto
    por_tiempo = [[] for _ in range(minutos)]
    for _id, h in historia.items():
        for tt, xx in zip(h["t"], h["x"]):
            if 0 <= tt < minutos:
                por_tiempo[tt].append((_id, xx))
    
    # Estilo visual base
    plt.style.use("default")
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.set_xlim(100, 0)   # de 100 mn a 0 mn
    ax.set_ylim(-1, 1)    # fila única
    ax.set_facecolor("black")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title("Aproximación a AEP - Simulación Monte Carlo", 
                 color="#66ccff", fontsize=16, pad=15, weight="bold")
    
    estelas = {}  # id -> lista de (t, x) recientes
    
    # Aviones
    heads = ax.scatter([], [], s=160, marker=">", 
                       color="#00c3ff", edgecolor="white", lw=0.8, alpha=0.95)
    txt = ax.text(0.02, 0.85, "", transform=ax.transAxes, 
                  color="#66ccff", fontsize=12, alpha=0.9, family="monospace")
    
    def init():
        heads.set_offsets(np.empty((0, 2)))
        txt.set_text("")
        return heads, txt
    
    def update(t):
        # actualizar estelas
        for (_id, x) in por_tiempo[t]:
            if _id not in estelas:
                estelas[_id] = []
            estelas[_id].append((t, x))
            if len(estelas[_id]) > tail:
                estelas[_id] = estelas[_id][-tail:]
        
        # borrar líneas viejas
        for ln in list(ax.lines):
            ln.remove()
        
        # dibujar estelas glow
        xs_head, ys_head = [], []
        for eid, pts in estelas.items():
            xs = [x for (_, x) in pts]
            ys = [0] * len(xs)
            
            # glow: segmentos más brillantes cerca de la cabeza
            for i in range(1, len(xs)):
                alpha = i / len(xs)
                ax.plot(xs[i-1:i+1], ys[i-1:i+1], 
                        color=(0.1, 0.7, 1, alpha*0.5), lw=3, solid_capstyle="round")
            
            xs_head.append(xs[-1])
            ys_head.append(0)
        
        # actualizar cabezas
        if xs_head:
            heads.set_offsets(np.column_stack([xs_head, ys_head]))
        else:
            heads.set_offsets(np.empty((0, 2)))
        
        # texto
        txt.set_text(f"Minuto: {t:3d}\n Aviones activos: {len(xs_head)}")
        return heads, txt
    
    anim = FuncAnimation(fig, update, frames=minutos, init_func=init,
                         interval=120, blit=False)
    plt.close(fig)  # evitar duplicados en Jupyter
    return anim

def plot_comparacion_tiempos(df: pd.DataFrame):
    """
    Grafica el tiempo total de viaje promedio vs el tiempo ideal (sin congestión)
    para cada λ.
    """
    t0 = tiempo_ideal() # TIEMPO BASE SIN CONGESTIÓN
    summary = df.groupby("lambda").agg(
        atraso_prom_mean = ("atraso_prom", "mean"),
        atraso_prom_sem = ("atraso_prom", "sem"),
    ).reset_index()
    summary["t_total_mean"] = summary["atraso_prom_mean"] + t0

    plt.figure(figsize = (7,4))
    plt.plot(summary["lambda"], [t0]*len(summary), label = "Tiempo ideal", marker = 's')
    plt.errorbar(summary["lambda"], summary["t_total_mean"], yerr = summary["atraso_prom_sem"], label = "Tiempo total promedio", marker = 'o')
    plt.xlabel("Lambda (aviones/min)")
    plt.ylabel("Tiempo total (min)")
    plt.title("Tiempo total de viaje promedio vs ideal por lambda")
    plt.grid(True, alpha = 0.3)
    plt.legend()
    plt.show()

def plot_desvios_y_congestion(metricas_, df):
    lambdas = [0.02, 0.1, 0.2, 0.5, 1]
    """
    Muestra dos gráficos lado a lado:
    - Promedio de aviones desviados a Montevideo por lambda
    - Congestión promedio por minuto de aviones que aterrizaron
    Espera un DataFrame con columnas 'lambda', 'desvios_montevideo', 'congestion_prom'.
    """

    data = []
    for l in lambdas:
        m = metricas_[l]
        data.append({
            "lambda": l,
            "desvios_montevideo": m.desvios_montevideo})
    df_resultados = pd.DataFrame(data)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Gráfico de desvíos a Montevideo
    sns.lineplot(data=df_resultados, x="lambda", y="desvios_montevideo", errorbar=('ci', 95), marker="o", ax=axes[0])
    axes[0].set_title("Promedio de aviones desviados a Montevideo por lambda")
    axes[0].set_xlabel("Lambda (aviones/min)")
    axes[0].set_ylabel("Desvíos a Montevideo (promedio)")
    axes[0].grid(alpha=0.3)

    # Gráfico de congestión con barras de error
    resumen_congestion = df.groupby("lambda")["congestion_prom"].agg(["mean", "std", "count"]).reset_index()
    resumen_congestion["se"] = resumen_congestion["std"] / np.sqrt(resumen_congestion["count"])
    resumen_congestion["ic_error"] = 1.96 * resumen_congestion["se"]  # IC 95%
    
    axes[1].errorbar(resumen_congestion["lambda"], resumen_congestion["mean"], 
                    yerr=resumen_congestion["ic_error"], marker="o", capsize=5, 
                    linewidth=2, markersize=6)
    axes[1].set_title("Minutos promedio de congestión de aviones que aterrizaron")
    axes[1].set_xlabel("Lambda")
    axes[1].set_ylabel("Minutos en congestión por avión")
    axes[1].grid(alpha=0.3)

    plt.tight_layout()
    plt.show()

def plot_congestion_montevideo(df):
    """
    Genera 4 gráficos:
    1. Aterrizajes en AEP vs Desvíos a Montevideo por lambda.
    2. Promedio de minutos en congestión: aterrizados vs desviados a Montevideo por lambda.
    3. Atraso promedio: aterrizados vs desviados a Montevideo por lambda.
    4. Frecuencia de desvíos a Montevideo por lambda.
    """
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    from analisis import tiempo_ideal

    lambdas = sorted(df["lambda"].unique())
    resultados = []
    t_ideal = tiempo_ideal()

    for lam, grupo in df.groupby("lambda"):
        aterrizados = 0
        montevideo = 0
        min_cong_aterrizados = []
        min_cong_montevideo = []
        atraso_aterrizados = []
        atraso_montevideo = []
        freq_montevideo = 0

        for historia in grupo["historia"]:
            total_aviones = len(historia)
            desvios_sim = 0
            for avion in historia.values():
                estado_final = avion["estado"][-1] if "estado" in avion and len(avion["estado"]) > 0 else None
                
                # Calcular minutos de congestión usando la misma lógica que otras funciones
                minutos_cong = 0
                if "estado" in avion and "v" in avion and "vmax" in avion:
                    for est, vel, vmax in zip(avion["estado"], avion["v"], avion["vmax"]):
                        if est in ["En fila", "Reinsertado"] and vel < vmax:
                            minutos_cong += 1
                
                # Calcular atraso usando la misma lógica que otras funciones
                atraso = 0
                if "t" in avion and len(avion["t"]) > 0:
                    minuto_aparicion = avion["t"][0]
                    if estado_final == "Aterrizó":
                        idx = avion["estado"].index("Aterrizó")
                        minuto_aterrizo = avion["t"][idx]
                        t_real = minuto_aterrizo - minuto_aparicion
                        atraso = t_real - t_ideal
                    elif estado_final == "Montevideo":
                        # Para aviones que van a Montevideo, calcular tiempo hasta que cambian a estado Montevideo
                        idx = avion["estado"].index("Montevideo")
                        minuto_montevideo = avion["t"][idx]
                        t_real = minuto_montevideo - minuto_aparicion
                        # El atraso es el tiempo real menos el tiempo ideal (sin congestión)
                        atraso = t_real - t_ideal
                
                if estado_final == "Aterrizó":
                    aterrizados += 1
                    min_cong_aterrizados.append(minutos_cong)
                    atraso_aterrizados.append(atraso)
                elif estado_final == "Montevideo":
                    montevideo += 1
                    min_cong_montevideo.append(minutos_cong)
                    atraso_montevideo.append(atraso)
                    desvios_sim += 1
            # Frecuencia de desvíos por simulación
            if total_aviones > 0:
                freq_montevideo += desvios_sim / total_aviones

        n_sim = len(grupo)
        resultados.append({
            "lambda": lam,
            "aterrizajes": aterrizados / n_sim,
            "desvios_montevideo": montevideo / n_sim,
            "prom_min_cong_aterrizados": np.mean(min_cong_aterrizados) if min_cong_aterrizados else 0,
            "prom_min_cong_montevideo": np.mean(min_cong_montevideo) if min_cong_montevideo else 0,
            "atraso_aterrizados": np.mean(atraso_aterrizados) if atraso_aterrizados else 0,
            "atraso_montevideo": np.mean(atraso_montevideo) if atraso_montevideo else 0,
            "freq_montevideo": freq_montevideo / n_sim
        })

    df_resultados = pd.DataFrame(resultados)

    fig, axs = plt.subplots(2, 2, figsize=(12, 10))

    # 1. Aterrizajes vs Desvíos a Montevideo
    axs[0, 0].plot(df_resultados["lambda"], df_resultados["aterrizajes"], marker='o', label="Aterrizajes en AEP", color="green")
    axs[0, 0].plot(df_resultados["lambda"], df_resultados["desvios_montevideo"], marker='s', label="Desvíos a Montevideo", color="red")
    axs[0, 0].set_xlabel("Lambda (aviones/min)")
    axs[0, 0].set_ylabel("Promedio por simulación")
    axs[0, 0].set_title("Aterrizajes vs Desvíos a Montevideo")
    axs[0, 0].legend()
    axs[0, 0].grid(alpha=0.3)

    # 2. Promedio de minutos en congestión: aterrizados vs Montevideo
    axs[0, 1].plot(df_resultados["lambda"], df_resultados["prom_min_cong_aterrizados"], marker='o', label="Aterrizados", color="blue")
    axs[0, 1].plot(df_resultados["lambda"], df_resultados["prom_min_cong_montevideo"], marker='s', label="Montevideo", color="orange")
    axs[0, 1].set_xlabel("Lambda (aviones/min)")
    axs[0, 1].set_ylabel("Minutos promedio en congestión")
    axs[0, 1].set_title("Congestión promedio: aterrizados vs Montevideo")
    axs[0, 1].legend()
    axs[0, 1].grid(alpha=0.3)

    # 3. Atraso promedio: aterrizados vs Montevideo
    axs[1, 0].plot(df_resultados["lambda"], df_resultados["atraso_aterrizados"], marker='o', label="Aterrizados", color="green")
    axs[1, 0].plot(df_resultados["lambda"], df_resultados["atraso_montevideo"], marker='s', label="Montevideo", color="red")
    axs[1, 0].set_xlabel("Lambda (aviones/min)")
    axs[1, 0].set_ylabel("Atraso promedio (min)")
    axs[1, 0].set_title("Atraso promedio: aterrizados vs Montevideo")
    axs[1, 0].legend()
    axs[1, 0].grid(alpha=0.3)

    # 4. Frecuencia de desvíos a Montevideo
    axs[1, 1].plot(df_resultados["lambda"], df_resultados["freq_montevideo"], marker='o', color="purple")
    axs[1, 1].set_xlabel("Lambda (aviones/min)")
    axs[1, 1].set_ylabel("Frecuencia de desvíos")
    axs[1, 1].set_title("Frecuencia de desvíos a Montevideo")
    axs[1, 1].grid(alpha=0.3)

    plt.tight_layout()
    plt.show()

def cambio_data(df):
    from analisis import tiempo_ideal
    import pandas as pd
    import numpy as np
    
    resultados = []
    t_ideal = tiempo_ideal()

    for lam, grupo in df.groupby("lambda"):
        aterrizados_total = 0
        min_cong_aterrizados = []
        atraso_aterrizados = []
        freq_montevideo_acum = 0.0
        mvd_rates = []  # desvíos a MVD por minuto por simulación

        for historia in grupo["historia"]:
            total_aviones = len(historia)
            desvios_sim = 0

            # Duración estimada de la simulación (en minutos)
            max_t = 0
            for datos in historia.values():
                if "t" in datos and len(datos["t"]) > 0:
                    max_t = max(max_t, max(datos["t"]))
            total_minutos_sim = max_t + 1 if max_t > 0 else 1

            for datos in historia.values():
                estado_final = datos["estado"][-1] if "estado" in datos and len(datos["estado"]) > 0 else None

                # Minutos de congestión (por avión aterrizado)
                minutos_cong = 0
                if "estado" in datos and "v" in datos and "vmax" in datos:
                    for est, vel, vmax in zip(datos["estado"], datos["v"], datos["vmax"]):
                        if est in ["En fila", "Reinsertado"] and vel < vmax:
                            minutos_cong += 1
                    
                # Atraso para aterrizados
                    atraso = 0
                if "t" in datos and len(datos["t"]) > 0:
                    minuto_aparicion = datos["t"][0]
                    if estado_final == "Aterrizó":
                        idx = datos["estado"].index("Aterrizó")
                        minuto_aterrizo = datos["t"][idx]
                        t_real = minuto_aterrizo - minuto_aparicion
                        atraso = t_real - t_ideal
                
                    if estado_final == "Aterrizó":
                        aterrizados_total += 1
                        min_cong_aterrizados.append(minutos_cong)
                        atraso_aterrizados.append(atraso)
                    elif estado_final == "Montevideo":
                        desvios_sim += 1

            # tasa de MVD por minuto en esta simulación
            mvd_rate = desvios_sim / total_minutos_sim if total_minutos_sim > 0 else 0.0
            mvd_rates.append(mvd_rate)

            # Frecuencia de desvíos (proporción sobre aviones) en esta simulación
            if total_aviones > 0:
                freq_montevideo_acum += desvios_sim / total_aviones

        n_sim = len(grupo)
        resultados.append({
            "lambda": lam,
            "aterrizajes": (aterrizados_total / n_sim) if n_sim else 0,
            "prom_min_cong_aterrizados": np.mean(min_cong_aterrizados) if min_cong_aterrizados else 0,
            "atraso_aterrizados": np.mean(atraso_aterrizados) if atraso_aterrizados else 0,
            "montevideo_prom": float(np.mean(mvd_rates)) if mvd_rates else 0.0,
            "freq_montevideo": (freq_montevideo_acum / n_sim) if n_sim else 0.0
        })
    
    return pd.DataFrame(resultados)

def plot_comparacion_mejoras(df_sin_mejora, df_con_mejora):
    """
    Compara los resultados entre simulación sin mejoras y con mejoras.
    Ambas simulaciones incluyen tormenta y viento.
    
    Parámetros:
    - df_sin_mejora: DataFrame con resultados sin mejoras (mejora=False)
    - df_con_mejora: DataFrame con resultados con mejoras (mejora=True)
    """
    import matplotlib.pyplot as plt
    import numpy as np
    
    df_sin_mejora = cambio_data(df_sin_mejora)
    df_con_mejora = cambio_data(df_con_mejora)


    fig, axes = plt.subplots(1, 2, figsize=(15, 10))
    
    # ==========================================
    # GRÁFICO 1: Comparación de Aterrizajes
    # ==========================================
    resumen_aterrizajes_sin = df_sin_mejora.groupby("lambda")["aterrizajes"].agg(["mean", "std", "count"]).reset_index()
    resumen_aterrizajes_sin["se"] = resumen_aterrizajes_sin["std"] / np.sqrt(resumen_aterrizajes_sin["count"])
    
    resumen_aterrizajes_con = df_con_mejora.groupby("lambda")["aterrizajes"].agg(["mean", "std", "count"]).reset_index()
    resumen_aterrizajes_con["se"] = resumen_aterrizajes_con["std"] / np.sqrt(resumen_aterrizajes_con["count"])
    
    axes[0].errorbar(resumen_aterrizajes_sin["lambda"], resumen_aterrizajes_sin["mean"], 
                      yerr=resumen_aterrizajes_sin["se"], marker='o', capsize=5, 
                      color='red', label='Sin Mejoras', linewidth=2)
    axes[0].errorbar(resumen_aterrizajes_con["lambda"], resumen_aterrizajes_con["mean"], 
                      yerr=resumen_aterrizajes_con["se"], marker='s', capsize=5, 
                      color='green', label='Con Mejoras', linewidth=2)
    axes[0].set_title('Aterrizajes: Comparación con y sin Mejoras')
    axes[0].set_xlabel('Lambda (aviones/min)')
    axes[0].set_ylabel('Aterrizajes promedio por simulación')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # ==========================================
    # GRÁFICO 2: Desvíos a Montevideo (promedio por minuto)
    # ==========================================
    resumen_montevideo_sin = df_sin_mejora.groupby("lambda")["montevideo_prom"].agg(["mean", "std", "count"]).reset_index()
    resumen_montevideo_sin["se"] = resumen_montevideo_sin["std"] / np.sqrt(resumen_montevideo_sin["count"])
    
    resumen_montevideo_con = df_con_mejora.groupby("lambda")["montevideo_prom"].agg(["mean", "std", "count"]).reset_index()
    resumen_montevideo_con["se"] = resumen_montevideo_con["std"] / np.sqrt(resumen_montevideo_con["count"])
    
    axes[1].errorbar(resumen_montevideo_sin["lambda"], resumen_montevideo_sin["mean"], 
                      yerr=resumen_montevideo_sin["se"], marker='o', capsize=5, 
                      color='red', label='Sin Mejoras', linewidth=2)
    axes[1].errorbar(resumen_montevideo_con["lambda"], resumen_montevideo_con["mean"], 
                      yerr=resumen_montevideo_con["se"], marker='s', capsize=5, 
                      color='green', label='Con Mejoras', linewidth=2)
    axes[1].set_title('Desvíos a Montevideo: Promedio por minuto')
    axes[1].set_xlabel('Lambda (aviones/min)')
    axes[1].set_ylabel('Promedio por minuto')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()

def plot_congestion_por_lambda(df):
    """
    Crea gráficos de congestión por lambda para aviones que aterrizan.
    
    Parámetros:
    - df: DataFrame con resultados de experimentos
    """
    import matplotlib.pyplot as plt
    
    # Calcular resumen de congestión por tramo
    resumen_tramo = analizar_congestion_promedio(df)
    if resumen_tramo is None:
        return
    
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    
    # Gráfico 1: Congestión por tramo (líneas separadas)
    tramos = ['congestion_lejos', 'congestion_medio', 'congestion_cerca']
    colores = ['blue', 'orange', 'red']
    labels = ['Lejos (>50 MN)', 'Medio (15-50 MN)', 'Cerca (<15 MN)']
    
    for i, tramo in enumerate(tramos):
        mean_col = f"{tramo}_mean"
        se_col = f"{tramo}_se"
        
        axes[0].errorbar(resumen_tramo['lambda'], resumen_tramo[mean_col], 
                        yerr=resumen_tramo[se_col], marker='o', capsize=5, 
                        color=colores[i], label=labels[i], linewidth=2)
    
    axes[0].set_title('Congestión por Tramo de Distancia (Aviones que Aterrizan)')
    axes[0].set_xlabel('Lambda (aviones/min)')
    axes[0].set_ylabel('Minutos de congestión por avión')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # Gráfico 2: Frecuencia de congestión
    axes[1].errorbar(resumen_tramo['lambda'], resumen_tramo['frecuencia_congestion_mean'], 
                    yerr=resumen_tramo['frecuencia_congestion_se'], marker='D', capsize=5, 
                    color='green', linewidth=2)
    axes[1].set_title('Frecuencia de Congestión por Lambda')
    axes[1].set_xlabel('Lambda (aviones/min)')
    axes[1].set_ylabel('Frecuencia de congestión')
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()

def plot_aviones_por_minuto(aviones, minutos = 1080):
    """
    MUESTRA CUÁNTOS AVIONES SE GENERARON EN CADA MINUTO
    (VISUALIZA EL PROCESO DE POISSON DE ARRIBOS).
    """
    conteo_por_minuto = [0] * minutos
    for a in aviones:
        if 0 <= a.minuto_aparicion < minutos:
            conteo_por_minuto[a.minuto_aparicion] += 1

    plt.figure(figsize = (12, 4))
    plt.scatter(range(minutos), conteo_por_minuto, s = 10) # puntos
    plt.title("Aviones generados por minuto")
    plt.xlabel("Minuto")
    plt.ylabel("Cantidad de aviones")
    plt.yticks([0, 1, 2])
    plt.grid(True, alpha = 0.3)
    plt.tight_layout()
    plt.show()

def plot_analisis_completo(df_normal, df_ventoso):
    """
    Crea gráficos de análisis completo incluyendo atrasos, desvíos y efectos del viento.
    
    Parámetros:
    - df_normal: DataFrame con resultados sin día ventoso
    - df_ventoso: DataFrame con resultados con día ventoso
    """
    import matplotlib.pyplot as plt
    import numpy as np
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    # ==========================================
    # GRÁFICO 1: Comparación Tiempo Total: Sin Viento vs Con Viento
    # ==========================================
    from analisis import tiempo_ideal
    t0 = tiempo_ideal()
    
    resumen_atraso_normal = df_normal.groupby("lambda")["atraso_prom"].agg(["mean", "std", "count"]).reset_index()
    resumen_atraso_normal["se"] = resumen_atraso_normal["std"] / np.sqrt(resumen_atraso_normal["count"])
    resumen_atraso_normal["t_total"] = resumen_atraso_normal["mean"] + t0
    
    resumen_atraso_ventoso = df_ventoso.groupby("lambda")["atraso_prom"].agg(["mean", "std", "count"]).reset_index()
    resumen_atraso_ventoso["se"] = resumen_atraso_ventoso["std"] / np.sqrt(resumen_atraso_ventoso["count"])
    resumen_atraso_ventoso["t_total"] = resumen_atraso_ventoso["mean"] + t0
    
    axes[0,0].errorbar(resumen_atraso_normal["lambda"], resumen_atraso_normal["t_total"], 
                      yerr=resumen_atraso_normal["se"], marker='o', capsize=5, 
                      color='blue', label='Sin Viento', linewidth=2)
    axes[0,0].errorbar(resumen_atraso_ventoso["lambda"], resumen_atraso_ventoso["t_total"], 
                      yerr=resumen_atraso_ventoso["se"], marker='s', capsize=5, 
                      color='red', label='Con Viento', linewidth=2)
    axes[0,0].set_title('Tiempo Total de Viaje: Comparación')
    axes[0,0].set_xlabel('Lambda (aviones/min)')
    axes[0,0].set_ylabel('Minutos totales por avión')
    axes[0,0].legend()
    axes[0,0].grid(True, alpha=0.3)
    
    # ==========================================
    # GRÁFICO 2: Comparación Desvíos a Montevideo: Sin Viento vs Con Viento
    # ==========================================
    resumen_montevideo_normal = df_normal.groupby("lambda")["montevideo_prom"].agg(["mean", "std", "count"]).reset_index()
    resumen_montevideo_normal["se"] = resumen_montevideo_normal["std"] / np.sqrt(resumen_montevideo_normal["count"])
    
    resumen_montevideo_ventoso = df_ventoso.groupby("lambda")["montevideo_prom"].agg(["mean", "std", "count"]).reset_index()
    resumen_montevideo_ventoso["se"] = resumen_montevideo_ventoso["std"] / np.sqrt(resumen_montevideo_ventoso["count"])
    
    axes[0,1].errorbar(resumen_montevideo_normal["lambda"], resumen_montevideo_normal["mean"], 
                      yerr=resumen_montevideo_normal["se"], marker='o', capsize=5, 
                      color='blue', label='Sin Viento', linewidth=2)
    axes[0,1].errorbar(resumen_montevideo_ventoso["lambda"], resumen_montevideo_ventoso["mean"], 
                      yerr=resumen_montevideo_ventoso["se"], marker='s', capsize=5, 
                      color='red', label='Con Viento', linewidth=2)
    axes[0,1].set_title('Desvíos a Montevideo: Comparación')
    axes[0,1].set_xlabel('Lambda (aviones/min)')
    axes[0,1].set_ylabel('Desvíos promedio por minuto')
    axes[0,1].legend()
    axes[0,1].grid(True, alpha=0.3)
    
    # ==========================================
    # GRÁFICO 3: Frecuencia de Desvíos por Viento
    # ==========================================
    resumen_freq_viento = df_ventoso.groupby("lambda")["viento_freq"].agg(["mean", "std", "count"]).reset_index()
    resumen_freq_viento["se"] = resumen_freq_viento["std"] / np.sqrt(resumen_freq_viento["count"])
    
    axes[1,0].errorbar(resumen_freq_viento["lambda"], resumen_freq_viento["mean"], 
                      yerr=resumen_freq_viento["se"], marker='^', capsize=5, 
                      color='purple', linewidth=2)
    axes[1,0].set_title('Frecuencia de Desvíos por Viento')
    axes[1,0].set_xlabel('Lambda (aviones/min)')
    axes[1,0].set_ylabel('Frecuencia de desvíos por viento')
    axes[1,0].grid(True, alpha=0.3)
    
    # ==========================================
    # GRÁFICO 4: Promedio de Aviones Desviados por Viento (que Aterrizaron)
    # ==========================================
    resumen_viento = df_ventoso.groupby("lambda")["viento_prom"].agg(["mean", "std", "count"]).reset_index()
    resumen_viento["se"] = resumen_viento["std"] / np.sqrt(resumen_viento["count"])
    
    axes[1,1].errorbar(resumen_viento["lambda"], resumen_viento["mean"], 
                      yerr=resumen_viento["se"], marker='D', capsize=5, 
                      color='green', linewidth=2)
    axes[1,1].set_title('Promedio de Aviones Desviados por Viento\n(De los que Aterrizaron)')
    axes[1,1].set_xlabel('Lambda (aviones/min)')
    axes[1,1].set_ylabel('Desvíos por viento promedio por minuto')
    axes[1,1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()

def animar_con_desvios(historia, minutos, tail=20):
    """
    Crea una animación que muestra aviones incluyendo los desviados y su búsqueda de hueco.
    
    Parámetros:
    - historia: Diccionario con la historia de cada avión O columna de DataFrame
    - minutos: Duración de la animación
    - tail: Longitud de la estela de cada avión
    """
    # Si historia es una columna de DataFrame, tomar la primera fila
    if hasattr(historia, 'iloc'):
        historia = historia.iloc[0]
    
    # Verificar que tenemos datos
    if not historia or len(historia) == 0:
        print("❌ No hay datos en 'historia' para animar.")
        return None

    # --- Construcción por tiempo ---
    por_tiempo = [[] for _ in range(minutos)]
    for _id, h in historia.items():
        if all(k in h for k in ["t", "x", "estado"]):
            for tt, estado in zip(h["t"], h["estado"]):
                # Si tiene coordenada x, usarla. Si aterrizó, x = 0
                if "x" in h and len(h["x"]) > 0:
                    if tt < len(h["x"]):
                        ax.axvline(x=50, color='orange', linestyle='--', alpha=0.5, label='> 50 MN')
                        ax.axvline(x=15, color='red', linestyle='--', alpha=0.5, label='< 15 MN')
                        ax.axvline(x=0, color='white', linestyle='-', alpha=0.8, label='AEP')

    # Diccionarios para estelas y AnnotationBbox
    estelas = {}
    aviones_ab = {}

    # Texto informativo
    txt = ax.text(0.02, 0.95, "", transform=ax.transAxes, fontsize=10,
                  bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))

    # --- Colores según estado ---
    def get_estado_color(estado):
        return {
            "En fila": "cyan",
            "Desviado": "red",
            "Reinsertado": "limegreen",
            "Aterrizó": "gold",
            "Montevideo": "violet"
        }.get(estado, "gray")

    # --- Crear AnnotationBbox (avión) ---
    def agregar_avion(ax, x, y):
        # Usar un símbolo de avión en lugar de imagen
        return ax.scatter([x], [y], s=100, marker=">", color="white", edgecolors="black", linewidth=1)

    # --- Inicialización ---
    def init():
        txt.set_text("Iniciando animación...")
        return []

    # --- Actualización por frame ---
    def update(frame):
        # Limpiar solo las estelas (no todos los collections)
        for ln in list(ax.lines):
            if ln.get_label() not in ['> 50 MN', '< 15 MN', 'AEP']:
                ln.remove()

        # Actualizar estelas
        for (_id, x, estado) in por_tiempo[frame]:
            if _id not in estelas:
                estelas[_id] = []
            estelas[_id].append((frame, x, estado))
            if len(estelas[_id]) > tail:
                estelas[_id] = estelas[_id][-tail:]

        # Ordenar por distancia (fila única)
        presentes = sorted([(eid, pts[-1][1], pts[-1][2]) for eid, pts in estelas.items()],
                           key=lambda z: z[1])

        # Dibujar estelas y aviones
        for idx, (eid, dist, estado_actual) in enumerate(presentes):
            y = 0 if estado_actual != "Desviado" else 2.5  # Desviados se separan en altura
            xs = [p[1] for p in estelas[eid]]
            ys = [y] * len(xs)

            # Estela
            ax.plot(xs, ys, color=get_estado_color(estado_actual), lw=1.5, alpha=0.6)

            # Avión
            if eid not in aviones_ab:
                aviones_ab[eid] = agregar_avion(ax, dist, y)
            else:
                # Actualizar posición del avión
                aviones_ab[eid].set_offsets([[dist, y]])

        # Conteo por estado
        conteos = {
            "En fila": sum(1 for _, _, e in presentes if e == "En fila"),
            "Desviado": sum(1 for _, _, e in presentes if e == "Desviado"),
            "Reinsertado": sum(1 for _, _, e in presentes if e == "Reinsertado"),
            "Aterrizó": sum(1 for _, _, e in presentes if e == "Aterrizó"),
            "Montevideo": sum(1 for _, _, e in presentes if e == "Montevideo"),
        }

        # Actualizar texto
        txt.set_text(
            f"Minuto: {frame}\n"
            f"En fila: {conteos['En fila']} | Desviados: {conteos['Desviado']}\n"
            f"Reinsertados: {conteos['Reinsertado']} | Aterrizados: {conteos['Aterrizó']}\n"
            f"Montevideo: {conteos['Montevideo']}"
        )

        return list(aviones_ab.values()) + [txt]

    # --- Crear animación ---
    anim = FuncAnimation(fig, update, frames=minutos, init_func=init,
                         interval=150, blit=False, repeat=True)

    plt.legend(loc='upper right')
    plt.tight_layout()
    plt.show()

    return anim

def plot_atraso_vs_desvios(df):
    # Tiempo ideal sin congestión
    from analisis import tiempo_ideal
    t0 = tiempo_ideal()
    
    # --- Atraso promedio solo de aterrizados (lo que ya calculás) ---
    resumen = df.groupby("lambda").agg(
        atraso_mean=("atraso_prom", "mean"),
        atraso_std=("atraso_prom", "std"),
        n=("atraso_prom", "count")
    ).reset_index()
    resumen["se"] = resumen["atraso_std"] / np.sqrt(resumen["n"])
    resumen["t_total"] = resumen["atraso_mean"] + t0
    
    # --- Atraso promedio penalizando desvíos ---
    # Si un avión se desvía, le asignamos "atraso infinito" → lo modelamos con un valor muy alto
    penalidad = 999  # minutos (prácticamente infinito en escala del problema)
    df["atraso_con_desvios"] = df["atraso_prom"] + penalidad * (df["montevideo_prom"] > 0)
    
    resumen_penal = df.groupby("lambda").agg(
        atraso_mean=("atraso_con_desvios", "mean"),
        atraso_std=("atraso_con_desvios", "std"),
        n=("atraso_con_desvios", "count")
    ).reset_index()
    resumen_penal["se"] = resumen_penal["atraso_std"] / np.sqrt(resumen_penal["n"])
    resumen_penal["t_total"] = resumen_penal["atraso_mean"] + t0
    
    # --- Gráfico comparativo ---
    plt.figure(figsize=(8,5))
    
    plt.errorbar(resumen["lambda"], resumen["t_total"], 
                 yerr=resumen["se"], marker="o", label="Solo aterrizados", color="blue")
    plt.errorbar(resumen_penal["lambda"], resumen_penal["t_total"], 
                 yerr=resumen_penal["se"], marker="s", label="Incluyendo desviados (penalidad)", color="red")
    
    plt.axhline(y=t0, color="gray", linestyle="--", label="Tiempo ideal")
    plt.xlabel("Lambda (aviones/min)")
    plt.ylabel("Tiempo total promedio (min)")
    plt.title("Comparación del atraso promedio con y sin penalizar desvíos")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.show()

def plot_analisis_completo_tormenta(df_normal, df_tormenta):
    """
    Crea gráficos de análisis completo incluyendo atrasos, desvíos y efectos de tormenta.
    Parámetros:
    - df_normal: DataFrame con resultados sin tormenta
    - df_tormenta: DataFrame con resultados con tormenta
    """
    import matplotlib.pyplot as plt
    import numpy as np

    fig, axes = plt.subplots(2, 2, figsize=(15, 10))

    # Gráfico 1: Tiempo total de viaje
    from analisis import tiempo_ideal
    t0 = tiempo_ideal()

    resumen_atraso_normal = df_normal.groupby("lambda")["atraso_prom"].agg(["mean", "std", "count"]).reset_index()
    resumen_atraso_normal["se"] = resumen_atraso_normal["std"] / np.sqrt(resumen_atraso_normal["count"])
    resumen_atraso_normal["t_total"] = resumen_atraso_normal["mean"] + t0

    resumen_atraso_tormenta = df_tormenta.groupby("lambda")["atraso_prom"].agg(["mean", "std", "count"]).reset_index()
    resumen_atraso_tormenta["se"] = resumen_atraso_tormenta["std"] / np.sqrt(resumen_atraso_tormenta["count"])
    resumen_atraso_tormenta["t_total"] = resumen_atraso_tormenta["mean"] + t0

    axes[0,0].errorbar(resumen_atraso_normal["lambda"], resumen_atraso_normal["t_total"], 
                      yerr=resumen_atraso_normal["se"], marker='o', capsize=5, 
                      color='blue', label='Normal', linewidth=2)
    axes[0,0].errorbar(resumen_atraso_tormenta["lambda"], resumen_atraso_tormenta["t_total"], 
                      yerr=resumen_atraso_tormenta["se"], marker='s', capsize=5, 
                      color='red', label='Con Tormenta', linewidth=2)
    axes[0,0].set_title('Tiempo Total de Viaje: Comparación')
    axes[0,0].set_xlabel('Lambda (aviones/min)')
    axes[0,0].set_ylabel('Minutos totales por avión')
    axes[0,0].legend()
    axes[0,0].grid(True, alpha=0.3)

    # Gráfico 2: Desvíos a Montevideo
    resumen_montevideo_normal = df_normal.groupby("lambda")["montevideo_prom"].agg(["mean", "std", "count"]).reset_index()
    resumen_montevideo_normal["se"] = resumen_montevideo_normal["std"] / np.sqrt(resumen_montevideo_normal["count"])
    
    resumen_montevideo_tormenta = df_tormenta.groupby("lambda")["montevideo_prom"].agg(["mean", "std", "count"]).reset_index()
    resumen_montevideo_tormenta["se"] = resumen_montevideo_tormenta["std"] / np.sqrt(resumen_montevideo_tormenta["count"])
    
    axes[0,1].errorbar(resumen_montevideo_normal["lambda"], resumen_montevideo_normal["mean"], 
                      yerr=resumen_montevideo_normal["se"], marker='o', capsize=5, 
                      color='blue', label='Normal', linewidth=2)
    axes[0,1].errorbar(resumen_montevideo_tormenta["lambda"], resumen_montevideo_tormenta["mean"], 
                      yerr=resumen_montevideo_tormenta["se"], marker='s', capsize=5, 
                      color='red', label='Con Tormenta', linewidth=2)
    axes[0,1].set_title('Desvíos a Montevideo: Comparación')
    axes[0,1].set_xlabel('Lambda (aviones/min)')
    axes[0,1].set_ylabel('Desvíos promedio por minuto')
    axes[0,1].legend()
    axes[0,1].grid(True, alpha=0.3)

    # Gráfico 3: Frecuencia de desvíos por tormenta (si tenés columna 'tormenta_freq')
    if "tormenta_freq" in df_tormenta.columns:
        resumen_freq_tormenta = df_tormenta.groupby("lambda")["tormenta_freq"].agg(["mean", "std", "count"]).reset_index()
        resumen_freq_tormenta["se"] = resumen_freq_tormenta["std"] / np.sqrt(resumen_freq_tormenta["count"])

        axes[1,0].errorbar(resumen_freq_tormenta["lambda"], resumen_freq_tormenta["mean"], 
                          yerr=resumen_freq_tormenta["se"], marker='^', capsize=5, 
                          color='purple', linewidth=2)
        axes[1,0].set_title('Frecuencia de Desvíos por Tormenta')
        axes[1,0].set_xlabel('Lambda (aviones/min)')
        axes[1,0].set_ylabel('Frecuencia de desvíos por tormenta')
        axes[1,0].grid(True, alpha=0.3)
    else:
        axes[1,0].axis('off')

    # Gráfico 4: Promedio de aviones desviados por tormenta (si tenés columna 'tormenta_prom')
    if "tormenta_prom" in df_tormenta.columns:
        resumen_tormenta = df_tormenta.groupby("lambda")["tormenta_prom"].agg(["mean", "std", "count"]).reset_index()
        resumen_tormenta["se"] = resumen_tormenta["std"] / np.sqrt(resumen_tormenta["count"])

        axes[1,1].errorbar(resumen_tormenta["lambda"], resumen_tormenta["mean"], 
                          yerr=resumen_tormenta["se"], marker='D', capsize=5, 
                          color='green', linewidth=2)
        axes[1,1].set_title('Promedio de Aviones Desviados por Tormenta\n(De los que Aterrizaron)')
        axes[1,1].set_xlabel('Lambda (aviones/min)')
        axes[1,1].set_ylabel('Desvíos por tormenta promedio por minuto')
        axes[1,1].grid(True, alpha=0.3)
    else:
        axes[1,1].axis('off')

    plt.tight_layout()
    plt.show()

def calcular_congestion_control_metrics(df_con_mejora):
    """
    Calcula métricas de congestión_control para el DataFrame con mejora.
    """
    import numpy as np
    from analisis import calcular_congestion_total
    
    resultados = []
    
    for _, fila in df_con_mejora.iterrows():
        if 'congestion_control' in fila:
            congestion_control_stats = calcular_congestion_total(fila['congestion_control'])
            resultados.append({
                'lambda': fila['lambda'],
                'frecuencia_congestion_control': congestion_control_stats['frecuencia_congestion'],
                'congestion_control_promedio': congestion_control_stats['congestion_promedio'],
                'congestion_control_maxima': congestion_control_stats['congestion_maxima']
            })
    
    if not resultados:
        return None
    
    df_control = pd.DataFrame(resultados)
    
    # Agrupar por lambda y calcular estadísticas
    resumen_control = df_control.groupby("lambda").agg({
        "frecuencia_congestion_control": ["mean", "std", "count"],
        "congestion_control_promedio": ["mean", "std"],
        "congestion_control_maxima": ["mean", "std"]
    }).reset_index()
    
    # Aplanar nombres de columnas
    resumen_control.columns = ['_'.join(col).strip() if col[1] else col[0] 
                              for col in resumen_control.columns.values]
    
    # Calcular error estándar
    for col in ['frecuencia_congestion_control', 'congestion_control_promedio', 'congestion_control_maxima']:
        mean_col = f"{col}_mean"
        std_col = f"{col}_std"
        count_col = f"{col}_count" if col == 'frecuencia_congestion_control' else 'frecuencia_congestion_control_count'
        
        if mean_col in resumen_control.columns and std_col in resumen_control.columns:
            resumen_control[f"{col}_se"] = resumen_control[std_col] / np.sqrt(resumen_control[count_col])
    
    return resumen_control

def comparar_congestion(df_sin_mejora, df_con_mejora):
    """
    Compara la congestión de los aviones que aterrizan con y sin la mejora.
    Genera gráficos comparativos de congestión incluyendo métricas de control.
    """
    import matplotlib.pyplot as plt
    import numpy as np
    from analisis import analizar_congestion_promedio
    
    # Calcular resúmenes de congestión para ambos DataFrames
    resumen_sin = analizar_congestion_promedio(df_sin_mejora)
    resumen_con = analizar_congestion_promedio(df_con_mejora)
    
    # Calcular métricas de congestión_control para el DataFrame con mejora
    resumen_control = calcular_congestion_control_metrics(df_con_mejora)
    
    if resumen_sin is None or resumen_con is None:
        print("No se pudieron calcular las métricas de congestión")
        return
    
    # Crear figura con subplots
    fig, axes = plt.subplots(1, 2, figsize=(15, 12))
    
    # ==========================================
    # GRÁFICO 1: Frecuencia de congestión
    # ==========================================
    axes[0].errorbar(resumen_sin['lambda'], resumen_sin['frecuencia_congestion_mean'], 
                      yerr=resumen_sin['frecuencia_congestion_se'], marker='o', capsize=5, 
                      color='red', label='Sin mejora', linewidth=2)
    axes[0].errorbar(resumen_con['lambda'], resumen_con['frecuencia_congestion_mean'], 
                      yerr=resumen_con['frecuencia_congestion_se'], marker='s', capsize=5, 
                      color='green', label='Con mejora', linewidth=2)
    
    # Agregar línea de congestión_control si está disponible
    if resumen_control is not None:
        axes[0].errorbar(resumen_control['lambda'], resumen_control['frecuencia_congestion_control_mean'], 
                          yerr=resumen_control['frecuencia_congestion_control_se'], marker='^', capsize=5, 
                          color='blue', label='Control (con mejora)', linewidth=2, linestyle='--')
    
    axes[0].set_title('Frecuencia de Congestión')
    axes[0].set_xlabel('Lambda (aviones/min)')
    axes[0].set_ylabel('Frecuencia de congestión')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # ==========================================
    # GRÁFICO 2: Congestión máxima
    # ==========================================
    axes[1].errorbar(resumen_sin['lambda'], resumen_sin['congestion_maxima_mean'], 
                      yerr=resumen_sin['congestion_maxima_se'], marker='o', capsize=5, 
                      color='red', label='Sin mejora', linewidth=2)
    axes[1].errorbar(resumen_con['lambda'], resumen_con['congestion_maxima_mean'], 
                      yerr=resumen_con['congestion_maxima_se'], marker='s', capsize=5, 
                      color='green', label='Con mejora', linewidth=2)
    
    # Agregar línea de congestión_control si está disponible
    if resumen_control is not None:
        axes[1].errorbar(resumen_control['lambda'], resumen_control['congestion_control_maxima_mean'], 
                          yerr=resumen_control['congestion_control_maxima_se'], marker='^', capsize=5, 
                          color='blue', label='Control (con mejora)', linewidth=2, linestyle='--')
    
    axes[1].set_title('Congestión Máxima')
    axes[1].set_xlabel('Lambda (aviones/min)')
    axes[1].set_ylabel('Congestión máxima')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.suptitle('Comparación de Congestión: Con vs Sin Mejora', fontsize=16, y=1.02)
    plt.show()

def plot_prioritarios_vs_normales(df_base, df_prio):
    """
    Compara sin prioridad (df_base) vs con prioridad (df_prio) para:
    - Atraso promedio por lambda (2 líneas)
    - Desvíos a Montevideo promedio por lambda (2 líneas)
    - Frecuencia de congestión y congestión máxima (4 líneas)
    Requiere columnas: 'lambda', 'atraso_prom', 'montevideo_prom',
    'frecuencia_congestion', 'congestion_maxima'.
    """
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd

    # Resúmenes por lambda
    def resumen(df, col):
        r = df.groupby("lambda")[col].agg(["mean", "std", "count"]).reset_index()
        r["se"] = r["std"] / np.sqrt(r["count"].replace(0, np.nan))
        return r

    r_atraso_base = resumen(df_base, "atraso_prom")
    r_atraso_prio = resumen(df_prio, "atraso_prom")

    r_mvd_base = resumen(df_base, "montevideo_prom")
    r_mvd_prio = resumen(df_prio, "montevideo_prom")

    r_freq_base = resumen(df_base, "frecuencia_congestion")
    r_freq_prio = resumen(df_prio, "frecuencia_congestion")

    r_max_base = resumen(df_base, "congestion_maxima")
    r_max_prio = resumen(df_prio, "congestion_maxima")

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    # 1) Atraso promedio
    axes[0].errorbar(r_atraso_base["lambda"], r_atraso_base["mean"], yerr=r_atraso_base["se"],
                     marker='o', capsize=4, label='Sin prioridad', color='tab:blue')
    axes[0].errorbar(r_atraso_prio["lambda"], r_atraso_prio["mean"], yerr=r_atraso_prio["se"],
                     marker='s', capsize=4, label='Con prioridad', color='tab:orange')
    axes[0].set_title('Atraso promedio por λ')
    axes[0].set_xlabel('Lambda (aviones/min)')
    axes[0].set_ylabel('Minutos')
    axes[0].grid(alpha=0.3)
    axes[0].legend()

    # 2) Desvíos a Montevideo
    axes[1].errorbar(r_mvd_base["lambda"], r_mvd_base["mean"], yerr=r_mvd_base["se"],
                     marker='o', capsize=4, label='Sin prioridad', color='tab:blue')
    axes[1].errorbar(r_mvd_prio["lambda"], r_mvd_prio["mean"], yerr=r_mvd_prio["se"],
                     marker='s', capsize=4, label='Con prioridad', color='tab:orange')
    axes[1].set_title('Desvíos a Montevideo por λ')
    axes[1].set_xlabel('Lambda (aviones/min)')
    axes[1].set_ylabel('Promedio por minuto')
    axes[1].grid(alpha=0.3)
    axes[1].legend()

    # 3) Frecuencia y máxima de congestión (4 líneas)
    axes[2].plot(r_freq_base["lambda"], r_freq_base["mean"], marker='o', label='Freq. sin prio', color='tab:blue')
    axes[2].plot(r_freq_prio["lambda"], r_freq_prio["mean"], marker='s', label='Freq. con prio', color='tab:orange')
    axes[2].plot(r_max_base["lambda"], r_max_base["mean"], marker='^', label='Máxima sin prio', color='tab:green')
    axes[2].plot(r_max_prio["lambda"], r_max_prio["mean"], marker='D', label='Máxima con prio', color='tab:red')
    axes[2].set_title('Congestión: frecuencia y máxima')
    axes[2].set_xlabel('Lambda (aviones/min)')
    axes[2].set_ylabel('Valor')
    axes[2].grid(alpha=0.3)
    axes[2].legend()

    plt.tight_layout()
    plt.show()

def plot_atraso_prioritarios_vs_normales(df):
    """
    Atraso y tiempo total promedio por lambda, separando prioritarios vs no prioritarios.
    Usa la columna 'historia' para calcular atrasos (solo aterrizados).
    """
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    from analisis import tiempo_ideal

    t0 = tiempo_ideal()
    registros = []

    for _, fila in df.iterrows():
        lam = fila["lambda"]
        historia = fila.get("historia", {})
        atrasos_prio, atrasos_norm = [], []

        for datos in historia.values():
            es_prio = datos.get("prio", False)
            estados = datos.get("estado", [])
            tiempos = datos.get("t", [])
            if not estados or not tiempos:
                continue
            if "Aterrizó" in estados:
                idx = estados.index("Aterrizó")
                minuto_aterrizo = tiempos[idx]
                minuto_aparicion = tiempos[0]
                t_real = minuto_aterrizo - minuto_aparicion
                atraso = t_real - t0
                (atrasos_prio if es_prio else atrasos_norm).append(atraso)

        # Usar el λ exacto que viene en el DataFrame
        registros.append({
            "lambda": lam,
            "atraso_prio": np.mean(atrasos_prio) if atrasos_prio else np.nan,
            "atraso_normal": np.mean(atrasos_norm) if atrasos_norm else np.nan
        })

    df_runs = pd.DataFrame(registros)

    def resumir(col):
        g = df_runs.groupby("lambda")[col].agg(["mean", "std", "count"]).reset_index()
        g["se"] = g["std"] / np.sqrt(g["count"].replace(0, np.nan))
        return g

    r_prio = resumir("atraso_prio")
    r_norm = resumir("atraso_normal")

    # Paneles: izquierda atraso, derecha tiempo total
    fig, axes = plt.subplots(1, 2, figsize=(14,5))

    # Atraso
    axes[0].errorbar(r_prio["lambda"], r_prio["mean"], yerr=r_prio["se"], marker='o', capsize=5, label='Prioritarios')
    axes[0].errorbar(r_norm["lambda"], r_norm["mean"], yerr=r_norm["se"], marker='s', capsize=5, label='No prioritarios')
    axes[0].set_title('Atraso promedio por λ')
    axes[0].set_xlabel('Lambda (aviones/min)')
    axes[0].set_ylabel('Atraso promedio (min)')
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()

    # Tiempo total = atraso + t0 (misma SE)
    axes[1].errorbar(r_prio["lambda"], r_prio["mean"] + t0, yerr=r_prio["se"], marker='o', capsize=5, label='Prioritarios')
    axes[1].errorbar(r_norm["lambda"], r_norm["mean"] + t0, yerr=r_norm["se"], marker='s', capsize=5, label='No prioritarios')
    axes[1].axhline(y=t0, color='gray', linestyle='--', linewidth=1, label='Tiempo ideal')
    axes[1].set_title('Tiempo total promedio por λ')
    axes[1].set_xlabel('Lambda (aviones/min)')
    axes[1].set_ylabel('Minutos totales')
    axes[1].grid(True, alpha=0.3)
    axes[1].legend()

    plt.tight_layout()
    plt.show()
