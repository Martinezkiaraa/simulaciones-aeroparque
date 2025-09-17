import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np
import pandas as pd
from analisis import tiempo_ideal

# ============================================================
# PARTE 4 Y 5: GRÁFICO DE RESUMEN DE MÉTRICAS
# ============================================================

def plot_resumen_metricas(df: pd.DataFrame):
    # AGRUPA LOS RESULTADOS POR λ Y CALCULA PROMEDIOS Y ERROR ESTÁNDAR
    summary = df.groupby("lambda").agg(
        congestion_freq_mean = ("congestion_freq", "mean"),
        congestion_freq_sem = ("congestion_freq", "sem"),
        montevideo_freq_mean = ("montevideo_freq", "mean"),
        montevideo_freq_sem = ("montevideo_freq", "sem"),
        rio_freq_mean=("rio_freq", "mean"),  # PARTE 5
        rio_freq_sem=("rio_freq", "sem"),    # PARTE 5
        atraso_prom_mean = ("atraso_prom", "mean"),
        atraso_prom_sem = ("atraso_prom", "sem"),
    ).reset_index()

    # CREA CUATRO SUBGRÁFICOS: CONGESTIÓN, MONTEVIDEO, RÍO Y ATRASO
    fig, axes = plt.subplots(1, 4, figsize = (20, 4))

    # 1) FRECUENCIA DE CONGESTIÓN
    axes[0].errorbar(summary["lambda"], summary["congestion_freq_mean"], yerr = summary["congestion_freq_sem"], marker = 'o')
    axes[0].set_title("Frecuencia de congestión")
    axes[0].set_xlabel("Lambda (aviones/min)")
    axes[0].set_ylabel("Frecuencia")
    axes[0].grid(True, alpha = 0.3)

    # 2) FRECUENCIA DE DESVÍOS A MONTEVIDEO
    axes[1].errorbar(summary["lambda"], summary["montevideo_freq_mean"], yerr = summary["montevideo_freq_sem"], marker = 'o', color = "C1")
    axes[1].set_title("Frecuencia de desvíos a Montevideo")
    axes[1].set_xlabel("Lambda (aviones/min)")
    axes[1].set_ylabel("Frecuencia")
    axes[1].grid(True, alpha = 0.3)

    # 3) FRECUENCIA DE DESVÍOS AL RÍO (PARTE 5)
    axes[2].errorbar(summary["lambda"], summary["rio_freq_mean"], yerr = summary["rio_freq_sem"], marker = 'o', color = "C3")
    axes[2].set_title("Frecuencia de desvíos al Río")
    axes[2].set_xlabel("Lambda (aviones/min)")
    axes[2].set_ylabel("Frecuencia")
    axes[2].grid(True, alpha = 0.3)

    # 4) ATRASO PROMEDIO VS SIN CONGESTIÓN
    axes[3].axhline(0, color = 'k', lw = 1, alpha = 0.4)
    axes[3].errorbar(summary["lambda"], summary["atraso_prom_mean"], yerr = summary["atraso_prom_sem"], marker = 'o', color = "C2")
    axes[3].set_title("Atraso promedio vs sin congestión")
    axes[3].set_xlabel("Lambda (aviones/min)")
    axes[3].set_ylabel("Minutos de atraso")
    axes[3].grid(True, alpha = 0.3)

    plt.tight_layout()
    plt.show()

# ============================================================
# PARTE 4: COMPARACIÓN TIEMPO REAL VS TIEMPO IDEAL
# ============================================================

def plot_comparacion_tiempos(df: pd.DataFrame):
    """
    GRAFICA EL TIEMPO REAL PROMEDIO VS EL TIEMPO IDEAL PARA CADA λ.
    """
    t0 = tiempo_ideal() # TIEMPO BASE SIN CONGESTIÓN
    summary = df.groupby("lambda").agg(
        atraso_prom_mean = ("atraso_prom", "mean"),
        atraso_prom_sem = ("atraso_prom", "sem"),
    ).reset_index()
    summary["t_real_mean"] = summary["atraso_prom_mean"] + t0

    plt.figure(figsize = (7,4))
    plt.plot(summary["lambda"], [t0]*len(summary), label = "Tiempo ideal", marker = 's')
    plt.errorbar(summary["lambda"], summary["t_real_mean"], yerr = summary["atraso_prom_sem"], label = "Tiempo real promedio", marker = 'o')
    plt.xlabel("Lambda (aviones/min)")
    plt.ylabel("Tiempo (min)")
    plt.title("Tiempo real vs ideal por lambda")
    plt.grid(True, alpha = 0.3)
    plt.legend()
    plt.show()

# ============================================================
# PARTE 5: ERROR DE ESTIMACIÓN (SEM) DE MÉTRICAS
# ============================================================

def plot_error_estimacion(df: pd.DataFrame, metrica: str, title: str):
    summary = df.groupby("lambda")[metrica].agg(["sem"]).reset_index()
    plt.plot(summary["lambda"], summary["sem"], marker = 'o')
    plt.xlabel("Lambda (aviones/min)")
    plt.ylabel("Error de estimación (SEM)")
    plt.title(title)
    plt.grid(True, alpha = 0.3)
    plt.show()

# ============================================================
# PARTE 1: VISUALIZACIÓN ESTÁTICA DE UNA SIMULACIÓN
# ============================================================

def visualizar_simulacion_monte_carlo(datos_simulacion, mostrar_ultimos_minutos = 100):
    """
    MUESTRA LA SIMULACIÓN:
    - POSICIÓN DE AVIONES EN EL TIEMPO (DISPERSIÓN)
    - TRAYECTORIAS INDIVIDUALES DE ALGUNOS AVIONES
    - VELOCIDAD DE ESOS AVIONES EN EL TIEMPO
    """
    historia = datos_simulacion["historia"]
    
    # FIGURA CON 2 GRÁFICOS (POSICIONES + TRAYECTORIAS)
    fig, axes = plt.subplots(2, 1, figsize = (12, 9))
    
    # 1) DISPERSIÓN (t vs distancia x)
    ax1 = axes[0]
    todos_t, todos_x = [], []
    max_t = 0
    for _id, h in historia.items():
        if len(h["t"]) == 0:
            continue
        max_t = max(max_t, max(h["t"]))
        idxs = [i for i, tt in enumerate(h["t"]) if tt >= max_t - mostrar_ultimos_minutos]
        todos_t.extend([h["t"][i] for i in idxs])
        todos_x.extend([h["x"][i] for i in idxs])
    
    ax1.scatter(todos_t, todos_x, s = 10, alpha = 0.6, c = "C0")
    ax1.set_xlabel("Tiempo (minutos)")
    ax1.set_ylabel("Distancia a AEP (mn)")
    ax1.set_title("Posiciones de aviones en el tiempo")
    ax1.grid(True, alpha = 0.3)
    ax1.invert_yaxis() # 0 ARRIBA = PISTA
    
    # 2) TRAYECTORIAS INDIVIDUALES DE ALGUNOS AVIONES (x vs t)
    ax2 = axes[1]
    aviones_ejemplo = list(historia.keys())[:10]
    for _id in aviones_ejemplo:
        h = historia.get(_id, None)
        if h and len(h["t"]) > 0:
            ax2.plot(h["t"], h["x"], alpha = 0.6, linewidth = 1)
    ax2.set_xlabel("Tiempo (minutos)")
    ax2.set_ylabel("Distancia a AEP (mn)")
    ax2.set_title("Trayectorias (x vs t)")
    ax2.grid(True, alpha = 0.3)
    
    # AGREGAR VELOCIDADES COMO LÍNEA DISCONTINUA
    ax_vel = ax2.twinx()
    for _id in aviones_ejemplo:
        h = historia.get(_id, None)
        if h and len(h["t"]) > 0 and "v" in h:
            ax_vel.plot(h["t"], h["v"], alpha = 0.5, linewidth = 1.0, linestyle = '--', color = 'C3')
    ax_vel.set_ylabel("Velocidad (kn)")
    
    plt.tight_layout()
    plt.show()

# ============================================================
# PARTE 1: ANIMACIÓN DE LA SIMULACIÓN
# ============================================================

def animar_simulacion_monte_carlo(datos_simulacion, mostrar_ultimos_minutos = 200, intervalo = 100):
    """
    CREA UNA ANIMACIÓN QUE MUESTRA:
    - LA EVOLUCIÓN DE LA POSICIÓN DE LOS AVIONES EN EL TIEMPO
    - LA DISTRIBUCIÓN ESPACIAL DE LOS AVIONES EN CADA INSTANTE
    """
    datos_viz = datos_simulacion["datos_visualizacion"]
    
    tiempos_mostrar = datos_viz["tiempos"][-mostrar_ultimos_minutos:]
    posiciones_mostrar = datos_viz["posiciones"][-mostrar_ultimos_minutos:]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize = (15, 6))
    
    # CONFIGURACIÓN DE EJES (ESTADO INICIAL)
    ax1.set_xlim(min(tiempos_mostrar), max(tiempos_mostrar))
    ax1.set_ylim(0, 100)
    ax1.set_xlabel("Tiempo (minutos)")
    ax1.set_ylabel("Distancia a AEP (mn)")
    ax1.set_title("Evolución temporal de posiciones")
    ax1.grid(True, alpha = 0.3)
    
    ax2.set_xlim(0, 100)
    ax2.set_ylim(0, 20)
    ax2.set_xlabel("Distancia a AEP (mn)")
    ax2.set_ylabel("Cantidad de aviones")
    ax2.set_title("Distribución espacial actual")
    ax2.grid(True, alpha = 0.3)
    
    # COLORES SEGÚN ESTADO DEL AVIÓN (USADO EN DISPERSIÓN)
    colores_estado = {
        "En fila": "blue",
        "Reinsertado": "green", 
        "Desviado": "orange",
        "Viento": "red",
        "Montevideo": "purple",
        "Aterrizó": "black"
    }
    
    # FUNCIONES DE INICIALIZACIÓN Y ACTUALIZACIÓN DEL FRAME
    def init():
        ax1.clear()
        ax2.clear()
        return ax1, ax2
    
    def update(frame):
        ax1.clear()
        ax2.clear()

        # Subgráfico 1: dispersión t vs distancia
        ax1.set_xlim(min(tiempos_mostrar), max(tiempos_mostrar))
        ax1.set_ylim(0, 100)
        ax1.set_xlabel("Tiempo (minutos)")
        ax1.set_ylabel("Distancia a AEP (mn)")
        ax1.set_title(f"Evolución temporal - Minuto {tiempos_mostrar[frame]}")
        ax1.grid(True, alpha = 0.3)
        
        # Subgráfico 2: histograma de distancias
        ax2.set_xlim(0, 100)
        ax2.set_ylim(0, 20)
        ax2.set_xlabel("Distancia a AEP (mn)")
        ax2.set_ylabel("Cantidad de aviones")
        ax2.set_title(f"Distribución espacial - Minuto {tiempos_mostrar[frame]}")
        ax2.grid(True, alpha = 0.3)
        
        # Mostrar trayectorias hasta el frame actual
        for t_idx in range(frame + 1):
            t = tiempos_mostrar[t_idx]
            posiciones = posiciones_mostrar[t_idx]
            
            for avion_data in posiciones:
                id_avion, x, estado, velocidad = avion_data
                color = colores_estado.get(estado, "gray")
                alpha = 0.3 if t_idx < frame else 1.0
                ax1.scatter(t, x, c = color, s = 20, alpha = alpha)
        
        # Mostrar distribución espacial actual
        posiciones_actuales = posiciones_mostrar[frame]
        distancias = [avion_data[1] for avion_data in posiciones_actuales]
        if distancias:
            ax2.hist(distancias, bins = 20, alpha = 0.7, color = 'skyblue', edgecolor = 'black')
        
        return ax1, ax2
    
    anim = FuncAnimation(fig, update, frames = len(tiempos_mostrar), 
                        init_func = init, interval = intervalo, blit = False)
    
    plt.tight_layout()
    plt.show()
    
    return anim

# ============================================================
# PARTE 1: AVIONES GENERADOS POR MINUTO
# ============================================================

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

# ============================================================
# PARTE 1: ANIMACIÓN CON ESTELAS
# ============================================================

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