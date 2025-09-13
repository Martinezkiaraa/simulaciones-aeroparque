from PLANE_NUEVO import plane
from heap import heap
import random
import numpy as np
import pandas as pd
import seaborn as sns
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

def simular_con_historia(lambda_por_min, minutos=600, seed=42):

    if seed is not None:
        random.seed(seed)

    avs = heap()
    next_id = 1
    historia = {}
    congestion = {t: 0 for t in range(minutos)} #La frecuencia se mide x cada minuto
    desvios_montevideo = {t: 0 for t in range(minutos)}


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

            # Detectar congestión: si está en radar y su velocidad < v_max
            if a.estado == "en radar" and a.velocidad_actual < a.v_max:
                congestion[t] += 1

            # Registrar desvíos a Montevideo
            if a.estado == "montevideo":
                desvios_montevideo[t] += 1

            # Registrar si no aterrizó aún
            if a.estado != "aterrizó":
                historia[a.id]["t"].append(t)
                historia[a.id]["x"].append(a.distancia_mn_aep)
                historia[a.id]["estado"].append(a.estado)

            # Si aterrizó, lo quitamos de la fila
            if a.estado == "aterrizó":
                historia[a.id]["t"].append(t)
                historia[a.id]["estado"].append(a.estado)
                avs.eliminar_avion(a)


    return historia, congestion, desvios_montevideo

# <--- EJERCICIO 4 ---- >

def analizar_congestion(congestion, lambda_):

    minutos_totales = len(congestion)
    minutos_con_congestion = sum(1 for c in congestion.values() if c > 0)
    promedio_aviones_congestion = sum(congestion.values()) / minutos_totales

    frecuencia = minutos_con_congestion / minutos_totales

    # Convertir a numpy para redimensionar
    data = np.array(list(congestion.values()))

    # Suponiendo simulación de 18 horas = 1080 minutos
    data_reshaped = data.reshape(18, 60)  # 18 filas (horas) x 60 columnas (minutos)

    plt.figure(figsize=(12,6))
    sns.heatmap(data_reshaped, cmap="YlOrRd", cbar_kws={'label': 'Aviones en congestión'})
    plt.xlabel("Minuto dentro de la hora")
    plt.ylabel("Hora de simulación")
    plt.title(f"Mapa de calor de congestión por hora y minuto, con lambda =  {lambda_}")
    plt.show()

    return {
        "frecuencia_congestion": frecuencia,
        "minutos_con_congestion": minutos_con_congestion,
        "promedio_aviones_congestion": promedio_aviones_congestion
    }

def analizar_desvios(desvios, lambda_):
    minutos = len(desvios)
    minutos_con_desvio = sum(1 for c in desvios.values() if c > 0)
    frecuencia_desvio = minutos_con_desvio / minutos
    promedio_desvios = sum(desvios.values()) / minutos

    plt.figure(figsize=(12,4))
    plt.plot(list(desvios.keys()), list(desvios.values()))
    plt.xlabel("Minuto")
    plt.ylabel("Aviones desviados a Montevideo")
    plt.title(f"Desvíos a Montevideo por minuto con lambda = {lambda_}")
    plt.grid(True, alpha=0.3)
    plt.show()

    return{
        "frecuencia_desvios": frecuencia_desvio,
        "promedio_desvios":promedio_desvios
    }


def calcular_atraso_promedio(historia, t_ideal):
    atrasos = []
    for avion_id, datos in historia.items():
        # minuto de aparición es el primer registro en "t"
        if len(datos["t"]) == 0:
            continue  # avión no llegó a entrar a la simulación
        
        minuto_aparicion = datos["t"][0]
        
        # Buscar el minuto en que aterrizó
        if "aterrizó" in datos["estado"]:
            idx = datos["estado"].index("aterrizó")
            minuto_aterrizo = datos["t"][idx]
        else:
            continue  # si no aterrizó, lo ignoramos

        # Tiempo real de vuelo
        t_real = minuto_aterrizo - minuto_aparicion

        # Atraso
        atraso = t_real - t_ideal
        atrasos.append(atraso)

    # Promedio de atrasos
    return sum(atrasos) / len(atrasos) if atrasos else 0.0


def tiempo_ideal():
    tramos = [
        (50, 500),
        (35, 300),
        (10, 250),
        (5, 150)
    ]
    
    total_minutos = 0
    for distancia, v_max in tramos:
        total_minutos += distancia / (v_max / 60.0)
    return total_minutos


# ---------------------------
# Main
# ---------------------------
if __name__ == "__main__":
    # Opción 1: gráfico de arribos discretos
    aviones1 = run_simulacion(lambda_por_min=1/60, minutos=1080, seed=42)
    plot_aviones_por_minuto(aviones1, minutos=1080)

    # Opción 2: animación de la aproximación
    #historia = simular_con_historia(1/60, 1080, 7)
    #animar_con_estelas(historia, minutos=1080, tail=25)

    lambdas = [0.02, 0.1, 0.2, 0.5, 1]

    t_ideal = tiempo_ideal()

    resultados_congestion_total = []
    resultados_desvios_total = []
    atrasos = []

    for i in lambdas:
        #Congestión x cada lambda
        historia_, congestion, desvios = simular_con_historia(i, 1080, 7)
        resultados_congestion = analizar_congestion(congestion, i)
        resultados_congestion["lambda"] = i
        resultados_congestion_total.append(resultados_congestion)
        
        #atraso x cada lambda
        atraso_promedio = calcular_atraso_promedio(historia_, t_ideal)
        atrasos.append(atraso_promedio)
        print(f"Atraso promedio por avión: {atraso_promedio:.2f} minutos")

        #desvio x cada lambda
        desvio_promedio = analizar_desvios(desvios, i)
        desvio_promedio["lambda"] = i
        resultados_desvios_total.append(desvio_promedio)


    
    df_congestion = pd.DataFrame(resultados_congestion_total)
    print(df_congestion)

    df_desvios = pd.DataFrame(resultados_desvios_total)
    print(df_desvios)

    #VISUALIZACIÓN CON ÁREA - SACAR SI NO SIRVE
    plt.figure(figsize=(10,5))
    plt.fill_between(df_congestion["minutos_con_congestion"], df_congestion["promedio_aviones_congestion"], color="red", alpha=0.5)
    plt.xlabel("Minutos con congestión")
    plt.ylabel("Aviones en congestión")
    plt.title("Evolución de la congestión (gráfico de área)")
    plt.show()

    # ATRASO DE PROMEDIO DE AVIONES CON VS SIN CONGESTIÓN

    "TIEMPO IDEAL = Es el tiempo que habría tardado el avión si pudiera volar siempre a la velocidad máxima "
    "(v_max) de cada tramo, sin restricciones por otros aviones. Esto se calcula como la suma del"
    "tiempo mínimo de vuelo en cada tramo, según la distancia inicial y el perfil de velocidad."

    plt.figure(figsize=(8,5))
    plt.plot(lambdas, atrasos, marker='o', label="Atraso promedio por avión")
    plt.axhline(t_ideal, color='r', linestyle='--', label="Tiempo ideal sin congestión")
    plt.xlabel("Lambda (aviones/minuto)")
    plt.ylabel("Atraso promedio (minutos)")
    plt.title("Atraso promedio vs tiempo ideal según λ")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.show()

    #el gráfico no es “incorrecto”, pero sí sugiere que el modelo de congestión aún no produce retrasos realistas.
    # Si quieres que los retrasos reflejen mejor la densidad de tráfico, el modelo de cola y velocidad de aproximación
    # necesita ajustes.






    