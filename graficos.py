import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np
import pandas as pd
from analisis import tiempo_ideal

def plot_resumen_metricas(df: pd.DataFrame):
    summary = df.groupby("lambda").agg(
        congestion_freq_mean=("congestion_freq", "mean"),
        congestion_freq_sem=("congestion_freq", "sem"),
        montevideo_freq_mean=("montevideo_freq", "mean"),
        montevideo_freq_sem=("montevideo_freq", "sem"),
        atraso_prom_mean=("atraso_prom", "mean"),
        atraso_prom_sem=("atraso_prom", "sem"),
    ).reset_index()

    fig, axes = plt.subplots(1, 3, figsize=(15, 4))

    # Frecuencia de congestión
    axes[0].errorbar(summary["lambda"], summary["congestion_freq_mean"], yerr=summary["congestion_freq_sem"], marker='o')
    axes[0].set_title("Frecuencia de congestión")
    axes[0].set_xlabel("Lambda (aviones/min)")
    axes[0].set_ylabel("Frecuencia")
    axes[0].grid(True, alpha=0.3)

    # Frecuencia de idas a Montevideo
    axes[1].errorbar(summary["lambda"], summary["montevideo_freq_mean"], yerr=summary["montevideo_freq_sem"], marker='o', color="C1")
    axes[1].set_title("Frecuencia de desvíos a Montevideo")
    axes[1].set_xlabel("Lambda (aviones/min)")
    axes[1].set_ylabel("Frecuencia")
    axes[1].grid(True, alpha=0.3)

    # Atraso promedio vs sin congestión (baseline 0)
    axes[2].axhline(0, color='k', lw=1, alpha=0.4)
    axes[2].errorbar(summary["lambda"], summary["atraso_prom_mean"], yerr=summary["atraso_prom_sem"], marker='o', color="C2")
    axes[2].set_title("Atraso promedio vs sin congestión")
    axes[2].set_xlabel("Lambda (aviones/min)")
    axes[2].set_ylabel("Minutos de atraso")
    axes[2].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()

def plot_comparacion_tiempos(df: pd.DataFrame):
    """
    Compara tiempo real promedio vs tiempo ideal por lambda.
    """
    t0 = tiempo_ideal()
    summary = df.groupby("lambda").agg(
        atraso_prom_mean=("atraso_prom", "mean"),
        atraso_prom_sem=("atraso_prom", "sem"),
    ).reset_index()
    summary["t_real_mean"] = summary["atraso_prom_mean"] + t0

    plt.figure(figsize=(7,4))
    plt.plot(summary["lambda"], [t0]*len(summary), label="Tiempo ideal", marker='s')
    plt.errorbar(summary["lambda"], summary["t_real_mean"], yerr=summary["atraso_prom_sem"], label="Tiempo real promedio", marker='o')
    plt.xlabel("Lambda (aviones/min)")
    plt.ylabel("Tiempo (min)")
    plt.title("Tiempo real vs ideal por lambda")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.show()

def plot_error_estimacion(df: pd.DataFrame, metrica: str, title: str):
    summary = df.groupby("lambda")[metrica].agg(["sem"]).reset_index()
    plt.plot(summary["lambda"], summary["sem"], marker='o')
    plt.xlabel("Lambda (aviones/min)")
    plt.ylabel("Error de estimación (SEM)")
    plt.title(title)
    plt.grid(True, alpha=0.3)
    plt.show()

def visualizar_simulacion_monte_carlo(datos_simulacion, mostrar_ultimos_minutos=100):
    """
    Visualiza la simulación usando historia completa (t, x, v) por avión.
    """
    historia = datos_simulacion["historia"]
    
    # Crear figura con subplots (2 filas x 1 columna)
    fig, axes = plt.subplots(2, 1, figsize=(12, 9))
    
    # 1. Posiciones de aviones en el tiempo (últimos minutos)
    ax1 = axes[0]
    # construir matriz dispersión (t,x) por avión desde historia
    todos_t, todos_x = [], []
    max_t = 0
    for _id, h in historia.items():
        if len(h["t"]) == 0:
            continue
        max_t = max(max_t, max(h["t"]))
        # tomar últimos minutos
        idxs = [i for i, tt in enumerate(h["t"]) if tt >= max_t - mostrar_ultimos_minutos]
        todos_t.extend([h["t"][i] for i in idxs])
        todos_x.extend([h["x"][i] for i in idxs])
    
    # Colores por estado
    colores_estado = {
        "En fila": "blue",
        "Reinsertado": "green", 
        "Desviado": "orange",
        "Viento": "red",
        "Montevideo": "purple",
        "Aterrizó": "black"
    }
    
    ax1.scatter(todos_t, todos_x, s=10, alpha=0.6, c="C0")
    
    ax1.set_xlabel("Tiempo (minutos)")
    ax1.set_ylabel("Distancia a AEP (mn)")
    ax1.set_title("Posiciones de aviones en el tiempo")
    ax1.grid(True, alpha=0.3)
    ax1.invert_yaxis()  # Distancia 0 arriba
    
    # 2. Trayectorias individuales de algunos aviones (x vs t)
    ax2 = axes[1]
    aviones_ejemplo = list(historia.keys())[:10]
    for _id in aviones_ejemplo:
        h = historia.get(_id, None)
        if h and len(h["t"]) > 0:
            ax2.plot(h["t"], h["x"], alpha=0.6, linewidth=1)
    ax2.set_xlabel("Tiempo (minutos)")
    ax2.set_ylabel("Distancia a AEP (mn)")
    ax2.set_title("Trayectorias (x vs t)")
    ax2.grid(True, alpha=0.3)
    
    # Añadimos al segundo gráfico las curvas de velocidad vs tiempo para los mismos aviones
    ax_vel = ax2.twinx()
    for _id in aviones_ejemplo:
        h = historia.get(_id, None)
        if h and len(h["t"]) > 0 and "v" in h:
            ax_vel.plot(h["t"], h["v"], alpha=0.5, linewidth=1.0, linestyle='--', color='C3')
    ax_vel.set_ylabel("Velocidad (kn)")
    
    plt.tight_layout()
    plt.show()

def animar_simulacion_monte_carlo(datos_simulacion, mostrar_ultimos_minutos=200, intervalo=100):
    """
    Anima la simulación Monte Carlo mostrando la evolución temporal.
    """
    datos_viz = datos_simulacion["datos_visualizacion"]
    
    # Preparar datos para animación
    tiempos_mostrar = datos_viz["tiempos"][-mostrar_ultimos_minutos:]
    posiciones_mostrar = datos_viz["posiciones"][-mostrar_ultimos_minutos:]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Configurar ejes
    ax1.set_xlim(min(tiempos_mostrar), max(tiempos_mostrar))
    ax1.set_ylim(0, 100)
    ax1.set_xlabel("Tiempo (minutos)")
    ax1.set_ylabel("Distancia a AEP (mn)")
    ax1.set_title("Evolución temporal de posiciones")
    ax1.grid(True, alpha=0.3)
    
    ax2.set_xlim(0, 100)
    ax2.set_ylim(0, 20)
    ax2.set_xlabel("Distancia a AEP (mn)")
    ax2.set_ylabel("Cantidad de aviones")
    ax2.set_title("Distribución espacial actual")
    ax2.grid(True, alpha=0.3)
    
    # Colores por estado
    colores_estado = {
        "En fila": "blue",
        "Reinsertado": "green", 
        "Desviado": "orange",
        "Viento": "red",
        "Montevideo": "purple",
        "Aterrizó": "black"
    }
    
    def init():
        ax1.clear()
        ax2.clear()
        ax1.set_xlim(min(tiempos_mostrar), max(tiempos_mostrar))
        ax1.set_ylim(0, 100)
        ax1.set_xlabel("Tiempo (minutos)")
        ax1.set_ylabel("Distancia a AEP (mn)")
        ax1.set_title("Evolución temporal de posiciones")
        ax1.grid(True, alpha=0.3)
        
        ax2.set_xlim(0, 100)
        ax2.set_ylim(0, 20)
        ax2.set_xlabel("Distancia a AEP (mn)")
        ax2.set_ylabel("Cantidad de aviones")
        ax2.set_title("Distribución espacial actual")
        ax2.grid(True, alpha=0.3)
        return ax1, ax2
    
    def update(frame):
        ax1.clear()
        ax2.clear()
        
        # Configurar ejes
        ax1.set_xlim(min(tiempos_mostrar), max(tiempos_mostrar))
        ax1.set_ylim(0, 100)
        ax1.set_xlabel("Tiempo (minutos)")
        ax1.set_ylabel("Distancia a AEP (mn)")
        ax1.set_title(f"Evolución temporal - Minuto {tiempos_mostrar[frame]}")
        ax1.grid(True, alpha=0.3)
        
        ax2.set_xlim(0, 100)
        ax2.set_ylim(0, 20)
        ax2.set_xlabel("Distancia a AEP (mn)")
        ax2.set_ylabel("Cantidad de aviones")
        ax2.set_title(f"Distribución espacial - Minuto {tiempos_mostrar[frame]}")
        ax2.grid(True, alpha=0.3)
        
        # Mostrar trayectorias hasta el frame actual
        for t_idx in range(frame + 1):
            t = tiempos_mostrar[t_idx]
            posiciones = posiciones_mostrar[t_idx]
            
            for avion_data in posiciones:
                id_avion, x, estado, velocidad = avion_data
                color = colores_estado.get(estado, "gray")
                alpha = 0.3 if t_idx < frame else 1.0
                ax1.scatter(t, x, c=color, s=20, alpha=alpha)
        
        # Mostrar distribución espacial actual
        posiciones_actuales = posiciones_mostrar[frame]
        distancias = [avion_data[1] for avion_data in posiciones_actuales]
        if distancias:
            ax2.hist(distancias, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
        
        return ax1, ax2
    
    from matplotlib.animation import FuncAnimation
    anim = FuncAnimation(fig, update, frames=len(tiempos_mostrar), 
                        init_func=init, interval=intervalo, blit=False)
    
    plt.tight_layout()
    plt.show()
    
    return anim

def plot_aviones_por_minuto(aviones, minutos=1080):
    conteo_por_minuto = [0] * minutos
    for a in aviones:
        if 0 <= a.minuto_aparicion < minutos:
            conteo_por_minuto[a.minuto_aparicion] += 1

    plt.figure(figsize=(12, 4))
    plt.scatter(range(minutos), conteo_por_minuto, s=10)  # puntos
    plt.title("Aviones generados por minuto")
    plt.xlabel("Minuto")
    plt.ylabel("Cantidad de aviones")
    plt.yticks([0, 1, 2])
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()

def animar_con_estelas(historia, minutos, tail=20):
    """
    Anima la última 'tail' posiciones de cada avión (estela) y su cabeza.
    """
    # Construyo por tiempo: lista de (x,id) presentes en cada t
    por_tiempo = [[] for _ in range(minutos)]
    for _id, h in historia.items():
        for tt, xx in zip(h["t"], h["x"]):
            if 0 <= tt < minutos:
                por_tiempo[tt].append((_id, xx))

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.set_xlim(100, 0)
    ax.set_ylim(-1, 30)  # “carriles” Y
    ax.set_xlabel("Distancia a AEP (mn)")
    ax.set_title("Aproximación a AEP — animación con estelas")
    ax.grid(True, alpha=0.3)

    # Estado de estelas: id -> lista de (t,x) recientes
    estelas = {}
    # artistas
    heads = ax.scatter([], [], s=60, marker="<", color="C0")
    txt = ax.text(0.02, 0.95, "", transform=ax.transAxes)

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
        presentes = sorted([(eid, pts[-1][1]) for eid, pts in estelas.items()], key=lambda z: z[1])
        y_por_id = {eid: (i % 28) for i, (eid, _) in enumerate(presentes)}

        # dibujo
        xs_head, ys_head = [], []
        for eid, pts in estelas.items():
            xs = [x for (_, x) in pts]
            ys = [y_por_id[eid]] * len(xs)
            ax.plot(xs, ys, color="C0", lw=1.2, alpha=0.6)  # estela
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

    anim = FuncAnimation(fig, update, frames=minutos, init_func=init,
                         interval=120, blit=False)
    plt.tight_layout()
    plt.show()
