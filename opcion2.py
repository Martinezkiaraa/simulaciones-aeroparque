def v_objetivo(self, d: float) -> float:
    d = max(0.0, min(100.0, d))
    if 50 < d <= 100:      # 300 -> 250
        return 200 + d
    elif 15 < d <= 50:     # 250 -> 200
        return 250 - (50/35)*(50 - d)
    elif 5 < d <= 15:      # 200 -> 150
        return 125 + 5*d
    else:                  # 150 -> 120
        return 120 + 6*d

def calcular_rango_velocidad(self):
    d = self.distancia_mn_aep
    if d > 100:
        self.v_min, self.v_max = 300, 500
    elif d > 50:
        self.v_min, self.v_max = 250, 300
    elif d > 15:
        self.v_min, self.v_max = 200, 250
    elif d > 5:
        self.v_min, self.v_max = 150, 200
    else:
        self.v_min, self.v_max = 120, 150

def paso_un_minuto(self, minuto):
    # 0) límites del tramo
    self.calcular_rango_velocidad()

    # 1) velocidad base por distancia
    v = self.v_objetivo(self.distancia_mn_aep)  # kt

    # 2) aplicar reglas de separación si hay líder
    if self.estado == "en radar" and self.next is not None and self.next.estado != "montevideo":
        # ETAs instantáneos (min) con las velocidades actuales
        eta_self = (self.distancia_mn_aep / max(self.velocidad_actual, 1e-6)) * 60
        eta_next = (self.next.distancia_AEP() / max(self.next.velocidad(), 1e-6)) * 60
        gap = eta_self - eta_next

        if gap < 4.0:
            # intento ir 20 kt menos que el líder, respetando vmin
            v_follow = max(self.v_min, self.next.velocidad() - 20.0)
            if v_follow < self.v_min:
                # congestión extrema -> desvío
                self.estado = "desviado"
            else:
                v = min(v, v_follow)
        elif gap >= 5.0:
            # si estaba frenado, puede volver a vmax del tramo
            v = min(v, self.v_max)

    # 3) mover según estado
    if self.estado == "desviado":
        # va "para atrás" a 200 kt
        v_back = 200.0
        self.distancia_mn_aep = min(100.0, self.distancia_mn_aep + v_back/60.0)
        self.velocidad_actual = v_back
        if self.distancia_mn_aep >= 100.0:
            self.estado = "montevideo"
    else:
        # avance normal hacia AEP
        self.distancia_mn_aep = max(0.0, self.distancia_mn_aep - v/60.0)
        self.velocidad_actual = v

    # 4) ETA y aterrizaje
    if self.velocidad_actual > 0:
        self.tiempo_en_min_aep = (self.distancia_mn_aep / self.velocidad_actual) * 60
    else:
        self.tiempo_en_min_aep = float("inf")

    if self.distancia_mn_aep <= 0 and self.landed_minute is None:
        self.landed_minute = minuto
        self.estado = "aterrizado"
