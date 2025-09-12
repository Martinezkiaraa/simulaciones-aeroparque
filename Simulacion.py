from PLANE_NUEVO import plane
from heap import heap
import random
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

def run_simulacion(lambda_por_min, minutos=1080, seed=None):
    if seed is not None:
        random.seed(seed)

    avs = heap()
    next_id = 1

    for minuto in range(minutos):
        if random.random() < lambda_por_min:
            nuevo = plane(id=next_id, minuto_aparicion=minuto, fila=avs)
            avs.agregar_avion(nuevo)
            next_id += 1

    return avs.aviones

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

def simular_con_historia(lambda_por_min=1/60, minutos=600, seed=42):

    if seed is not None:
        random.seed(seed)

    avs = heap()
    next_id = 1
    historia = {}

    for t in range(minutos):
        # Probabilidad de que llegue un avión en este minuto
        if random.random() < lambda_por_min:
            a = plane(id=next_id, minuto_aparicion=t, fila=avs)
            avs.agregar_avion(a)
            historia[a.id] = {"t": [], "x": [], "estado": []}
            next_id += 1

        # Avanzar dinámica de todos los aviones
        for a in list(avs.aviones):
            a.avanzar(minuto_actual=t, dt=1.0)

            # Registrar si no aterrizó aún
            if a.estado != "aterrizó":
                historia[a.id]["t"].append(t)
                historia[a.id]["x"].append(a.distancia_mn_aep)
                historia[a.id]["estado"].append(a.estado)

            # Si aterrizó, lo quitamos de la fila
            if a.estado == "aterrizó":
                avs.eliminar_avion(a)

    return historia


# ---------------------------
# Main
# ---------------------------
if __name__ == "__main__":
    # Opción 1: gráfico de arribos discretos
    aviones1 = run_simulacion(lambda_por_min=1/60, minutos=1080, seed=42)
    plot_aviones_por_minuto(aviones1, minutos=1080)

    # Opción 2: animación de la aproximación
    historia = simular_con_historia(lambda_por_min=1/60, minutos=1080, seed=7)
    animar_con_estelas(historia, minutos=1080, tail=25)