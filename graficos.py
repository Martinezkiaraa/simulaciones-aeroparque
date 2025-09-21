import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import pandas as pd
from analisis import tiempo_ideal, analizar_congestion_montevideo, analizar_congestion_promedio
import seaborn as sns
import numpy as np
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

# ============================================================
# PARTE 4: COMPARACIÓN TIEMPO REAL VS TIEMPO IDEAL
# ============================================================

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

# =================================================================
# PARTE 4: CONGESTIÓN EN AVIONES ATERRIZADOS Y AVIONES A MONTEVIDEO
# =================================================================

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
    axes[1].set_title("Congestión promedio por minuto de aviones que aterrizaron")
    axes[1].set_xlabel("Lambda")
    axes[1].set_ylabel("Minutos en congestión por avión")
    axes[1].grid(alpha=0.3)

    plt.tight_layout()
    plt.show()

def plot_congestion_montevideo(df):
    """
    Crea gráficos de congestión específicamente para aviones que van a Montevideo.
    
    Parámetros:
    - df: DataFrame con resultados de experimentos
    """
    import matplotlib.pyplot as plt
    
    # Calcular resumen de congestión para aviones de Montevideo
    resumen_montevideo = analizar_congestion_montevideo(df)
    if resumen_montevideo is None:
        return
    
    # Agrupar por lambda y calcular estadísticas
    resumen = resumen_montevideo.groupby("lambda").agg({
        "congestion_prom_montevideo": ["mean", "std", "count"],
        "frecuencia_congestion_montevideo": ["mean", "std"],
        "congestion_lejos_montevideo": ["mean", "std"],
        "congestion_medio_montevideo": ["mean", "std"],
        "congestion_cerca_montevideo": ["mean", "std"]
    }).reset_index()
    
    # Aplanar nombres de columnas
    resumen.columns = ['_'.join(col).strip() if col[1] else col[0] 
                      for col in resumen.columns.values]
    
    # Calcular intervalos de confianza al 95%
    for col in ['congestion_prom_montevideo', 'frecuencia_congestion_montevideo', 
                'congestion_lejos_montevideo', 'congestion_medio_montevideo', 'congestion_cerca_montevideo']:
        mean_col = f"{col}_mean"
        std_col = f"{col}_std"
        count_col = f"{col}_count" if col == 'congestion_prom_montevideo' else 'congestion_prom_montevideo_count'
        
        if mean_col in resumen.columns and std_col in resumen.columns:
            # Error estándar
            resumen[f"{col}_se"] = resumen[std_col] / np.sqrt(resumen[count_col])
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    # Gráfico 1: Congestión promedio por avión de Montevideo
    axes[0,0].errorbar(resumen['lambda'], resumen['congestion_prom_montevideo_mean'], 
                      yerr=resumen['congestion_prom_montevideo_se'], marker='o', capsize=5, 
                      color='red', linewidth=2)
    axes[0,0].set_title('Congestión Promedio por Avión de Montevideo')
    axes[0,0].set_xlabel('Lambda (aviones/min)')
    axes[0,0].set_ylabel('Minutos de congestión por avión')
    axes[0,0].grid(True, alpha=0.3)
    
    # Gráfico 2: Frecuencia de congestión para aviones de Montevideo
    axes[0,1].errorbar(resumen['lambda'], resumen['frecuencia_congestion_montevideo_mean'], 
                      yerr=resumen['frecuencia_congestion_montevideo_se'], marker='s', capsize=5, 
                      color='blue', linewidth=2)
    axes[0,1].set_title('Frecuencia de Congestión - Aviones de Montevideo')
    axes[0,1].set_xlabel('Lambda (aviones/min)')
    axes[0,1].set_ylabel('Frecuencia de congestión')
    axes[0,1].grid(True, alpha=0.3)
    
    # Gráfico 3: Congestión por tramo para aviones de Montevideo
    tramos = ['congestion_lejos_montevideo', 'congestion_medio_montevideo', 'congestion_cerca_montevideo']
    colores = ['blue', 'orange', 'red']
    labels = ['Lejos (>50 MN)', 'Medio (15-50 MN)', 'Cerca (<15 MN)']
    
    for i, tramo in enumerate(tramos):
        mean_col = f"{tramo}_mean"
        se_col = f"{tramo}_se"
        
        axes[1,0].errorbar(resumen['lambda'], resumen[mean_col], 
                          yerr=resumen[se_col], marker='o', capsize=5, 
                          color=colores[i], label=labels[i], linewidth=2)
    
    axes[1,0].set_title('Congestión por Tramo - Aviones de Montevideo')
    axes[1,0].set_xlabel('Lambda (aviones/min)')
    axes[1,0].set_ylabel('Minutos de congestión por avión')
    axes[1,0].legend()
    axes[1,0].grid(True, alpha=0.3)
    
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

def animar_con_estelas(historia, minutos, tail = 20):
    """
    CREA UNA ANIMACIÓN ESTILO "RADAR":
    - MUESTRA LA ESTELA DE CADA AVIÓN EN LOS ÚLTIMOS 'tail' MINUTOS
    - MUESTRA LA CABEZA DE CADA AVIÓN AVANZANDO
    """
    # Construyo por tiempo: lista de (x,id) presentes en cada t
    por_tiempo = [[] for _ in range(minutos)]
    for _id, h in historia.items():
        for tt, xx in zip(h["t"], h["x"]):
            if 0 <= tt < minutos:
                por_tiempo[tt].append((_id, xx))

    fig, ax = plt.subplots(figsize = (12, 5))
    ax.set_xlim(100, 0)
    ax.set_ylim(-1, 30)  # “carriles” Y
    ax.set_xlabel("Distancia a AEP (mn)")
    ax.set_title("Aproximación a AEP — animación con estelas")
    ax.grid(True, alpha = 0.3)

    # Estado de estelas: id -> lista de (t,x) recientes
    estelas = {}
    # artistas
    heads = ax.scatter([], [], s = 60, marker = "<", color = "C0")
    txt = ax.text(0.02, 0.95, "", transform = ax.transAxes)

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
            # recortar cola
            if len(estelas[_id]) > tail:
                estelas[_id] = estelas[_id][-tail:]

        # dibujar estelas como líneas finas
        # primero borro líneas viejas
        for ln in list(ax.lines):
            ln.remove()
        # asigno carriles por orden de distancia
        presentes = sorted([(eid, pts[-1][1]) for eid, pts in estelas.items()], key = lambda z: z[1])
        y_por_id = {eid: (i % 28) for i, (eid, _) in enumerate(presentes)}

        # dibujo
        xs_head, ys_head = [], []
        for eid, pts in estelas.items():
            xs = [x for (_, x) in pts]
            ys = [y_por_id[eid]] * len(xs)
            ax.plot(xs, ys, color = "C0", lw = 1.2, alpha = 0.6)  # estela
            # cabeza
            xs_head.append(xs[-1])
            ys_head.append(ys[-1])

        # actualizar “cabezas”
        if xs_head:
            heads.set_offsets(np.column_stack([xs_head, ys_head]))
        else:
            heads.set_offsets(np.empty((0, 2)))

        txt.set_text(f"Minuto: {t}  |  Aviones en pantalla: {len(xs_head)}")
        return heads, txt

    anim = FuncAnimation(fig, update, frames = minutos, init_func = init,
                         interval = 120, blit = False)
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
                        xx = h["x"][tt] if tt < len(h["x"]) else 0
                    else:
                        xx = 0
                else:
                    xx = 0
                if 0 <= tt < minutos:
                    por_tiempo[tt].append((_id, xx, estado))

    # --- Configuración de la figura ---
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.set_xlim(100, 0)  # Distancia desde radar (100 MN) hasta AEP (0 MN)
    ax.set_ylim(-5, 8)
    ax.set_xlabel("Distancia a AEP (MN)")
    ax.set_title("Simulación de Aterrizajes y Desvíos en AEP", fontsize=14)
    ax.grid(True, alpha=0.3)
    ax.set_facecolor("#0c1a2b")  # Fondo tipo radar

    # Líneas de referencia
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