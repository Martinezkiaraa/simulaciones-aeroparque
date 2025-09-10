from Clases import plane
import random
import matplotlib.pyplot as plt


#la simulación depende del umbral de lambda no? por eso lo paso por parámetro
def run_simulacion(lambda_por_min):
    minutos = 1080
    aviones = []
    next_id = 1
    
    for minuto in range(minutos):
        U = random.random() #random.random() da un numero con distr uniforme entre 0 y 1
        if U < lambda_por_min: 
            nuevo = plane(id=next_id, minuto_aparicion=minuto)
            aviones.append(nuevo)
            next_id += 1
        
        #ESTO ES BASIC 
    
    return aviones


aviones1 = run_simulacion(1/60) # o sea un avión x hora

print(f"Se generaron {len(aviones1)} aviones")
print(aviones1[0].id, aviones1[0].minuto_aparicion)

def plot_aviones_por_minuto(aviones, minutos=1080):
    conteo_por_minuto = [0] * minutos
    for a in aviones:
        if 0 <= a.minuto_aparicion < minutos:
            conteo_por_minuto[a.minuto_aparicion] += 1
    plt.figure(figsize=(12, 4))
    plt.plot(range(minutos), conteo_por_minuto, drawstyle="steps-mid")
    plt.title("Aviones generados por minuto")
    plt.xlabel("Minuto")
    plt.ylabel("Cantidad de aviones")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    aviones1 = run_simulacion(1/60)  # un avión por hora en promedio
    plot_aviones_por_minuto(aviones1)
