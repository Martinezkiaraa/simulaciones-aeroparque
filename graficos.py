import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np
import pandas as pd
from analisis import tiempo_ideal
import seaborn as sns

# ============================================================
# PARTE 4, 5 y 6: GRÁFICO DE RESUMEN DE MÉTRICAS
# ============================================================

# ============================================================
# PARTE 4: COMPARACIÓN TIEMPO REAL VS TIEMPO IDEAL
# ============================================================

def plot_comparacion_tiempos(df: pd.DataFrame):
    """
    Grafica el tiempo real promedio vs el tiempo ideal (sin congestión)
    para cada λ.
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
    plt.title("Tiempo simulado de atraso promedio por avión vs ideal por lambda")
    plt.grid(True, alpha = 0.3)
    plt.legend()
    plt.show()

# =================================================================
# PARTE 4: CONGESTIÓN EN AVIONES ATERRIZADOS Y AVIONES A MONTEVIDEO
# =================================================================

def plot_desvios_y_congestion(metricas_, df):
    """
    Muestra dos gráficos lado a lado:
    - Promedio de aviones desviados a Montevideo por lambda
    - Congestión promedio por minuto de aviones que aterrizaron
    Espera un DataFrame con columnas 'lambda', 'desvios_montevideo', 'congestion_prom'.
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Gráfico de desvíos a Montevideo
    sns.lineplot(data=metricas_, x="lambda", y="desvios_montevideo", errorbar=('ci', 95), marker="o", ax=axes[0])
    axes[0].set_title("Promedio de aviones desviados a Montevideo por lambda")
    axes[0].set_xlabel("Lambda (aviones/min)")
    axes[0].set_ylabel("Desvíos a Montevideo (promedio)")
    axes[0].grid(alpha=0.3)

    # Gráfico de congestión
    sns.lineplot(data=df, x="lambda", y="congestion_prom", errorbar=('ci', 95), marker="o", ax=axes[1])
    axes[1].set_title("Congestión promedio por minuto de aviones que aterrizaron")
    axes[1].set_xlabel("Lambda")
    axes[1].set_ylabel("Minutos en congestión por avión")
    axes[1].grid(alpha=0.3)

    plt.tight_layout()
    plt.show()


# ============================================================
# PARTE 4, 5 y 6: ERROR DE ESTIMACIÓN
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