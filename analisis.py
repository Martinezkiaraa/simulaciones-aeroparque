import numpy as np
import pandas as pd

# ============================================================
# ENUNCIADO / SOPORTE GENERAL
# CLASE PARA GUARDAR TODAS LAS MÉTRICAS DE LA SIMULACIÓN
# ============================================================

class MetricasSimulacion:
    def __init__(self):
        # PARTE 1
        self.aterrizajes = 0                  # CANTIDAD DE ATERRIZAJES EXITOSOS
        self.aviones = 0                      # TOTAL DE AVIONES GENERADOS
        self.volando = 0                      # AVIONES QUE QUEDAN VOLANDO AL FINAL

        # PARTE 4
        self.reinserciones = 0                # TOTAL DE REINSERCIONES
        self.reinserciones_unicas = set()     # IDs de aviones reinsertados
        self.desvios_montevideo = 0           # TOTAL DE DESVÍOS A MONTEVIDEO
        self.desvios_viento = 0                  # DESVÍOS POR GO-AROUND (día ventoso)

        # PARTE 6
        self.desvios_tormenta = 0             # DESVÍOS POR TORMENTA (AEP cerrado)

    # ---------------- REGISTROS ----------------

    def registrar_aterrizaje(self, cantidad=1):
        self.aterrizajes += cantidad
    
    def registrar_aviones(self, cantidad=1):
        self.aviones += cantidad
    
    def en_vuelo(self, cantidad):
        self.volando += cantidad

    def registrar_reinsercion(self, id_avion):
        self.reinserciones += 1
        self.reinserciones_unicas.add(id_avion)

    def registrar_desvio_montevideo(self, cantidad=1):
        self.desvios_montevideo += cantidad

    def registrar_desvio_viento(self, cantidad=1):
        self.desvios_viento += cantidad

    def registrar_desvio_tormenta(self, cantidad=1):
        self.desvios_tormenta += cantidad


    # ---------------- RESUMEN ----------------

    def resumen(self):
        """
        Devuelve un diccionario con todas las métricas principales
        (sirve para imprimir resultados al final de cada experimento).
        """
        return {
            "aterrizajes": self.aterrizajes,
            "aviones": self.aviones,
            "en_vuelo": self.volando,
            "reinserciones": self.reinserciones,
            "desvios_montevideo": self.desvios_montevideo,
            "desvios_viento": self.desvios_viento,
            "desvios_tormenta": self.desvios_tormenta,
        }

    # REPRESENTACIÓN DE TEXTO (ÚTIL PARA DEBUG)
    
    def __repr__(self):
        return (f"<Métricas: aterrizajes={self.aterrizajes}, "
                f"reinserciones={self.reinserciones}, "
                f"desv_mvd={self.desvios_montevideo}, "
                f"desv_viento={self.desvios_viento}, "
                f"desv_tormenta={self.desvios_tormenta}, "
            )

# ============================================================
# FUNCIONES DE ANÁLISIS DE MÉTRICAS (PARTES 4, 5 y 6)
# ============================================================
def analizar_congestion(df):
    """
    PARTE 4
    Analiza congestión: 
    - frecuencia = proporción de minutos con al menos 1 avión en congestión
    - promedio = cuántos aviones en congestión en promedio por minuto
    """
    # Nuevo: promedio de minutos en congestión por avión aterrizado
    # congestion debe ser el diccionario de la simulación (data)
    minutos_por_avion = []
    historia = df["historia"]
    for datos in historia.values():
        if len(datos["estado"]) == 0 or "Aterrizó" not in datos["estado"]:
            continue
        # Minutos en congestión: estado en fila/reinsertado y velocidad < v_max
        minutos_cong = 0
        for est, vel, vmax in zip(datos["estado"], datos["v"], datos["vmax"]):
            if est in ["En fila", "Reinsertado"] and vel < vmax:
                minutos_cong += 1
        minutos_por_avion.append(minutos_cong)
    promedio = np.mean(minutos_por_avion) if minutos_por_avion else 0.0
    return {"promedio": promedio}

def analizar_congestion_control(df):
    """
    Analiza congestión_control específicamente para simulaciones con mejora.
    - frecuencia = proporción de minutos con al menos 1 avión en congestión de control
    - promedio = cuántos aviones en congestión de control en promedio por minuto
    """
    # Analizar congestión_control si está disponible
    if "congestion_control" not in df:
        return {"promedio": 0.0}
    
    congestion_control = df["congestion_control"]
    minutos = len(congestion_control)
    minutos_con_congestion = sum(1 for c in congestion_control.values() if c > 0)
    frecuencia = minutos_con_congestion / minutos
    promedio = sum(congestion_control.values()) / minutos
    
    return {
        "frecuencia": frecuencia,
        "promedio": promedio
    }

def calcular_congestion_total(congestion_por_minuto):
    """Calcula métricas de congestión del sistema completo"""
    minutos_con_congestion = sum(1 for c in congestion_por_minuto.values() if c > 0)
    total_minutos = len(congestion_por_minuto)
    congestion_total = sum(congestion_por_minuto.values())
    
    return {
        "frecuencia_congestion": minutos_con_congestion / total_minutos,
        "congestion_promedio": congestion_total / total_minutos,
        "congestion_maxima": max(congestion_por_minuto.values()),
        "minutos_totales_congestion": congestion_total
    }

def calcular_congestion_por_tramo(historia):
    """Analiza congestión según la distancia al AEP - promedio por avión que aterriza"""
    tramos = {
        "lejos": [],      # > 50 MN
        "medio": [],      # 15-50 MN  
        "cerca": []       # < 15 MN
    }
    
    for avion_id, datos in historia.items():
        if "Aterrizó" not in datos["estado"]:
            continue
        
        # Contar minutos de congestión por tramo para este avión
        minutos_por_tramo = {"lejos": 0, "medio": 0, "cerca": 0}
        
        for i, (distancia, estado, velocidad, vmax) in enumerate(
            zip(datos["x"], datos["estado"], datos["v"], datos["vmax"])
        ):
            if estado in ["En fila", "Reinsertado"] and velocidad < vmax:
                if distancia > 50:
                    minutos_por_tramo["lejos"] += 1
                elif distancia > 15:
                    minutos_por_tramo["medio"] += 1
                else:
                    minutos_por_tramo["cerca"] += 1
        
        # Agregar los minutos de este avión a cada tramo
        for tramo in tramos:
            tramos[tramo].append(minutos_por_tramo[tramo])
    
    # Calcular promedio por avión para cada tramo
    return {tramo: np.mean(valores) if valores else 0.0 for tramo, valores in tramos.items()}
    
def IC_globales(df):
    # Agrupar por lambda
    grouped = df.groupby("lambda")["congestion_prom"]

    # Calcular promedio, desviación estándar y tamaño de muestra
    resumen = grouped.agg(["mean", "std", "count"]).reset_index()

    # Calcular error estándar y límites del intervalo de confianza al 95%
    resumen["Error MonteCarlo"] = resumen["std"] / np.sqrt(resumen["count"])
    resumen["IC95_lower"] = resumen["mean"] - 1.96 * resumen["Error MonteCarlo"]
    resumen["IC95_upper"] = resumen["mean"] + 1.96 * resumen["Error MonteCarlo"]

    # Mostrar como tabla legible
    print("{:<10} {:<10} {:<10} {:<10} {:<15} {:<15} {:<15}".format(
        "Lambda", "Promedio", "Std", "N", "Error MC", "IC95_lower", "IC95_upper"
    ))
    print("-" * 85)
    for _, row in resumen.iterrows():
        print("{:<10.2f} {:<10.2f} {:<10.2f} {:<10} {:<15.4f} {:<15.4f} {:<15.4f}".format(
            row["lambda"], row["mean"], row["std"], int(row["count"]),
            row["Error MonteCarlo"], row["IC95_lower"], row["IC95_upper"]
        ))
    return resumen

def analizar_montevideo(data):
    """
    PARTE 4
    Analiza desvíos a Montevideo:
    - frecuencia = proporción de minutos con al menos 1 desvío
    - promedio = desvíos promedio por minuto
    """
    desvios = data["desvios_montevideo"]
    minutos = len(desvios)
    minutos_con_desvio = sum(1 for c in desvios.values() if c > 0)
    frecuencia = minutos_con_desvio / minutos
    promedio = sum(desvios.values()) / minutos
    return {"frecuencia": frecuencia, "promedio": promedio}

def analizar_viento(data):
    """
    PARTE 5
    Analiza desvíos por viento (go-around → trayectoria río).
    """
    desvios = data["desvios_viento"]
    minutos = len(desvios)
    minutos_con_desvio = sum(1 for c in desvios.values() if c > 0)
    frecuencia = minutos_con_desvio / minutos
    promedio = sum(desvios.values()) / minutos
    return {"frecuencia": frecuencia, "promedio": promedio}

def analizar_tormenta(data):
    """
    PARTE 6
    Analiza desvíos por tormenta (cierre de AEP).
    """
    desvios = data.get("desvios_tormenta", {})
    minutos = len(desvios)
    minutos_con_desvio = sum(1 for c in desvios.values() if c > 0)
    frecuencia = minutos_con_desvio / minutos
    promedio = sum(desvios.values()) / minutos
    return {"frecuencia": frecuencia, "promedio": promedio}

def calcular_atraso_promedio(data, t_ideal):
    """
    Calcula el atraso promedio comparando tiempo real de vuelo 
    contra tiempo ideal (sin congestión).
    """
    historia = data["historia"]
    atrasos = []
    for avion_id, datos in historia.items():
        if len(datos["t"]) == 0:
            continue
        minuto_aparicion = datos["t"][0]
        if "Aterrizó" not in datos["estado"]:
            continue
        idx = datos["estado"].index("Aterrizó")
        minuto_aterrizo = datos["t"][idx]
        t_real = minuto_aterrizo - minuto_aparicion
        atrasos.append(t_real - t_ideal)
    return np.mean(atrasos) if atrasos else 0.0

def tiempo_ideal():
    """
    Calcula el tiempo ideal (sin congestión, sin tormenta, sin viento),
    sumando tiempos de recorrer cada tramo a velocidad máxima.
    """
    tramos = [(50, 300), (35, 250), (10, 200), (5, 150)]
    total_minutos = sum(dist / (v / 60.0) for dist, v in tramos)
    return total_minutos

def analizar_congestion_promedio(df):
    """
    Analiza congestión promedio de todas las realizaciones por lambda.
    
    Parámetros:
    - df: DataFrame con resultados de experimentos que incluye columnas de congestión
    
    Devuelve:
    - DataFrame con métricas de congestión promedio y desviación estándar por lambda
    """
    # Verificar que las columnas necesarias existen
    columnas_requeridas = ['frecuencia_congestion', 'congestion_maxima', 
                          'congestion_lejos', 'congestion_medio', 'congestion_cerca']
    
    # Si no existen las columnas, calcularlas primero
    if not all(col in df.columns for col in columnas_requeridas):
        print("⚠️  Las columnas de congestión no están en el DataFrame.")
        print("   Ejecuta primero los experimentos con las métricas de congestión incluidas.")
        return None
    
    # Agrupar por lambda y calcular estadísticas
    resumen = df.groupby("lambda").agg({
        "frecuencia_congestion": ["mean", "std", "count"],
        "congestion_maxima": ["mean", "std"],
        "congestion_lejos": ["mean", "std"],
        "congestion_medio": ["mean", "std"], 
        "congestion_cerca": ["mean", "std"]
    }).reset_index()
    
    # Aplanar nombres de columnas
    resumen.columns = ['_'.join(col).strip() if col[1] else col[0] 
                      for col in resumen.columns.values]
    
    # Calcular intervalos de confianza al 95%
    for col in ['frecuencia_congestion', 'congestion_maxima', 'congestion_lejos', 
                'congestion_medio', 'congestion_cerca']:
        mean_col = f"{col}_mean"
        std_col = f"{col}_std"
        count_col = f"{col}_count" if col == 'frecuencia_congestion' else 'frecuencia_congestion_count'
        
        if mean_col in resumen.columns and std_col in resumen.columns:
            # Error estándar
            resumen[f"{col}_se"] = resumen[std_col] / np.sqrt(resumen[count_col])
            # Intervalo de confianza 95%
            resumen[f"{col}_ic_lower"] = resumen[mean_col] - 1.96 * resumen[f"{col}_se"]
            resumen[f"{col}_ic_upper"] = resumen[mean_col] + 1.96 * resumen[f"{col}_se"]
    
    return resumen

def analizar_congestion_montevideo(df):
    """
    Analiza congestión específicamente para aviones que van a Montevideo.
    
    Parámetros:
    - df: DataFrame con resultados de experimentos que incluye columnas de congestión
    
    Devuelve:
    - DataFrame con métricas de congestión promedio por lambda para aviones de Montevideo
    """
    # Verificar que las columnas necesarias existen
    if 'historia' not in df.columns:
        print("⚠️  La columna 'historia' no está en el DataFrame.")
        return None
    
    resultados = []
    
    for _, fila in df.iterrows():
        historia = fila['historia']
        lambda_val = fila['lambda']
        
        # Analizar solo aviones que van a Montevideo
        aviones_montevideo = []
        for avion_id, datos in historia.items():
            if "Montevideo" in datos["estado"]:
                aviones_montevideo.append((avion_id, datos))
        
        if not aviones_montevideo:
            # Si no hay aviones de Montevideo, agregar valores cero
            resultados.append({
                'lambda': lambda_val,
                'congestion_prom_montevideo': 0.0,
                'frecuencia_congestion_montevideo': 0.0,
                'congestion_lejos_montevideo': 0.0,
                'congestion_medio_montevideo': 0.0,
                'congestion_cerca_montevideo': 0.0
            })
            continue
        
        # Calcular congestión promedio para aviones de Montevideo
        minutos_por_avion = []
        minutos_con_congestion = 0
        total_minutos = 0
        for avion_id, datos in aviones_montevideo:
            minutos_cong = 0
            for est, vel, vmax in zip(datos["estado"], datos["v"], datos["vmax"]):
                total_minutos += 1
                if est in ["En fila", "Reinsertado"] and vel < vmax:
                    minutos_cong += 1
                    minutos_con_congestion += 1
            minutos_por_avion.append(minutos_cong)
        
        congestion_prom = np.mean(minutos_por_avion) if minutos_por_avion else 0.0
        frecuencia = minutos_con_congestion / total_minutos if total_minutos > 0 else 0.0

        tramos = {"lejos": [], "medio": [], "cerca": []}
        
        for avion_id, datos in aviones_montevideo:
            minutos_por_tramo = {"lejos": 0, "medio": 0, "cerca": 0}
            
            for i, (distancia, estado, velocidad, vmax) in enumerate(
                zip(datos["x"], datos["estado"], datos["v"], datos["vmax"])
            ):
                if estado in ["En fila", "Reinsertado"] and velocidad < vmax:
                    if distancia > 50:
                        minutos_por_tramo["lejos"] += 1
                    elif distancia > 15:
                        minutos_por_tramo["medio"] += 1
                    else:
                        minutos_por_tramo["cerca"] += 1
            
            for tramo in tramos:
                tramos[tramo].append(minutos_por_tramo[tramo])
        
        # Calcular promedios por tramo
        congestion_por_tramo = {
            tramo: np.mean(valores) if valores else 0.0 
            for tramo, valores in tramos.items()
        }
        
        resultados.append({
            'lambda': lambda_val,
            'congestion_prom_montevideo': congestion_prom,
            'frecuencia_congestion_montevideo': frecuencia,
            'congestion_lejos_montevideo': congestion_por_tramo['lejos'],
            'congestion_medio_montevideo': congestion_por_tramo['medio'],
            'congestion_cerca_montevideo': congestion_por_tramo['cerca']
        })
    
    return pd.DataFrame(resultados)

def print_resumen_congestion(df):
    resumen = analizar_congestion_promedio(df)
    if resumen is None:
        return

    # Encabezado de la tabla
    print("{:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10}".format(
        "Lambda", "Freq. Cong.", "IC Low", "IC Up", "Max Cong.", "IC Low", "IC Up",
        "Lejos", "Medio", "Cerca"
    ))
    print("-" * 100)

    for _, fila in resumen.iterrows():
        print("{:<10.2f} {:<10.3f} {:<10.3f} {:<10.3f} {:<10.1f} {:<10.1f} {:<10.1f} {:<10.1f} {:<10.1f} {:<10.1f}".format(
            fila['lambda'],
            fila['frecuencia_congestion_mean'],
            fila['frecuencia_congestion_ic_lower'],
            fila['frecuencia_congestion_ic_upper'],
            fila['congestion_maxima_mean'],
            fila['congestion_maxima_ic_lower'],
            fila['congestion_maxima_ic_upper'],
            fila['congestion_lejos_mean'],
            fila['congestion_medio_mean'],
            fila['congestion_cerca_mean']
        ))
    print("-" * 100)
    print("Lejos, Medio y Cerca son minutos promedio de congestión por tramo (>50MN, 15-50MN, <15MN).")

def print_resumen(metricas_lambdas):
    # Encabezado de la tabla
    print("{:<10} {:<12} {:<10} {:<15} {:<18} {:<15} {:<15} {:<15}".format(
        "Lambda", "Aterrizajes", "Aviones", "En vuelo", "Reinserciones", "Desv. MVD", "Desv. Viento", "Desv. Tormenta"
    ))
    print("-" * 105)
    for lambda_val, metricas in metricas_lambdas.items():
        resumen = metricas.resumen()
        print("{:<10} {:<12} {:<10} {:<15} {:<18} {:<15} {:<15} {:<15}".format(
            str(lambda_val),
            resumen["aterrizajes"],
            resumen["aviones"],
            resumen["en_vuelo"],
            resumen["reinserciones"],
            resumen["desvios_montevideo"],
            resumen["desvios_viento"],
            resumen["desvios_tormenta"]
        ))