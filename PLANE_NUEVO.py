from typing import Optional

class plane:
    def __init__(self, id, minuto_aparicion, fila):
        self.id = id 
        self.estado = "en radar"
        self.minuto_aparicion = minuto_aparicion
        self.distancia_mn_aep = 100.0   # millas náuticas a AEP
        self.velocidad_actual = 300.0   # nudos (mn/h)
        self.landed_minute = None
        self.next: Optional["plane"] = None   # avión que tengo adelante
        self.v_max = 0.0
        self.v_min = 0.0
        self.fila = fila

    def _eta(self, dist_mn, vel_kn):
        # minutos hasta AEP con velocidad actual
        return dist_mn / (vel_kn / 60.0)

    def distancia_AEP(self):
        return self.distancia_mn_aep 
                    
    def velocidad(self):
        return self.velocidad_actual
    
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

    def velocidad_por_min(self, d):
        d = max(0.0, min(100.0, d))
        if 50 < d <= 100:
            return 200 + d # formula de la velocidad en funcion de la distancia V(d)
        elif 15 < d <= 50:
            return 250 - (50/35)*(50-d)
        elif 5 < d <= 15:
            return 125 + 5*d
        else:
            return 120 + 6*d
    
    '''
    def paso_un_minuto(self, minuto):
        v = self.velocidad_por_min(self.distancia_mn_aep)            # 1) Calcula la velocidad actual (nudos) según la distancia d
        self.distancia_mn_aep = max(0.0, self.distancia_mn_aep - v/60.0)            # 2) Avanza: resta la distancia recorrida en 1 min
        self.velocidad_actual = self.velocidad_por_min(self.distancia_mn_aep)    # 3) Calcula la nueva velocidad con la nueva distancia
        self.tiempo_en_min_aep = self.distancia_mn_aep / (self.velocidad_actual) * 60
        if self.distancia_mn_aep <= 0 and self.landed_minute is None:
            self.landed_minute = minuto
    '''

    def avanzar(self, minuto_actual: int = None, dt: float = 1.0):
        # 1) Actualizar límites de tramo
        self.calcular_rango_velocidad()

        # 2) Inbound: aplicar reglas si está en radar
        if self.estado == "en radar":

            # Si hay líder válido, aplicar regla líder−20 / buffer 5
            if self.next is not None and self.next.estado == "en radar":
                eta_self = self._eta(self.distancia_mn_aep, self.velocidad_actual)
                eta_next = self._eta(self.next.distancia_AEP(), self.next.velocidad())
                gap = eta_self - eta_next  # seguidor - líder
    
                if gap < 4.0:
                    # seguidor = vel_líder − 20; si cae por debajo de v_min → desvío
                    nueva_v = self.next.velocidad() - 20.0
                    if nueva_v < self.v_min:
                        idx = self.fila.get_index(self)      # guardá tu índice antes de sacar
                        leader = self.next                   # guardá quién era tu líder
                        self.estado = "desviado"
                        self.velocidad_actual = 200.0 # outbound
                        self.fila.eliminar_avion(self)       # te vas de la fila
                        self.next = None                     # vos ya no tenés líder
                        # actualizar el seguidor (si existe): ahora su líder pasa a ser 'leader'
                        if idx < len(self.fila.aviones):     # ojo: la lista ya se corrió a la izquierda
                            follower = self.fila.aviones[idx]
                            follower.next = leader           
                    else:
                        self.velocidad_actual = nueva_v

                elif gap >= 5.0:
                    # colchón logrado: volver inmediatamente a vmax del tramo
                    self.velocidad_actual = self.v_max
                # si 4 <= gap < 5, mantenemos la velocidad_actual
            else:
                # sin líder: ir a techo del tramo
                self.velocidad_actual = self.v_max

            # Avanzar hacia AEP este minuto
            self.distancia_mn_aep = max(0.0, self.distancia_mn_aep - (self.velocidad_actual / 60.0) * dt)
            self.tiempo_en_min_aep = self._eta(self.distancia_mn_aep, self.velocidad_actual)

            if self.distancia_mn_aep <= 0.0:
                self.distancia_mn_aep = 0.0
                self.estado = "aterrizó"
                if self.landed_minute is None and minuto_actual is not None:
                    self.landed_minute = minuto_actual
            else:
                self.estado = "en radar"

            # Mantener orden en la fila si corresponde
            self.fila.actualizar_orden()
            return

        # 3) Aterrizado: nada que hacer
        if self.estado == "aterrizó":
            return

        # 4) Desviado: outbound a 200 kn y reintentos de reinserción
        if self.estado == "desviado":
            # Intentar reinsertar (gap >= 10' según tu buscar_gap)
            posicion = self.buscar_gap()
            
            if posicion is not None:
                # 1) Insertar en la fila en la posición calculada
                self.fila.aviones.insert(posicion, self)
                
                # 2) Actualizar punteros de liderazgo localmente
                leader = self.fila.aviones[posicion - 1] if posicion > 0 else None
                self.next = leader  # el insertado ve como líder al que queda adelante
                # el que queda detrás del insertado ahora ve al insertado como líder
                if posicion + 1 < len(self.fila.aviones):
                    follower = self.fila.aviones[posicion + 1]
                    follower.next = self

                # 3) Velocidad de reingreso: usar tu perfil y respetar límites del tramo
                self.calcular_rango_velocidad()
                self.velocidad_actual = self.v_max

                # 4) Estado y ordenar por distancia para mantener la fila prolija
                self.fila.actualizar_orden()
                self.estado = "en radar"
                return

            # Si no hay gap, seguir saliendo a 200 kn (= 200/60 mn por minuto)
            self.distancia_mn_aep += (200.0 / 60.0) * dt
            if self.distancia_mn_aep >= 100.0:
                self.estado = "montevideo"
            return

    def buscar_gap(self):
        """
        Busca un gap >= 10 minutos en la fila.
        Devuelve la posición donde el avión puede reinsertarse.
        Si no hay gap, devuelve None.
        """
        self.fila.actualizar_orden()
        largo = len(self.fila.aviones)

        # Recorremos TODOS los pares adyacentes: (0,1), (1,2), ... (largo-2, largo-1)
        for i in range(largo - 1):  # <- fix: antes estaba largo - 2 y te perdías el último par
            avion_a = self.fila.aviones[i]
            avion_b = self.fila.aviones[i + 1]

            # ETAs con velocidades actuales
            eta_a = self._eta(avion_a.distancia_mn_aep, avion_a.velocidad_actual)
            eta_b = self._eta(avion_b.distancia_mn_aep, avion_b.velocidad_actual)

            # gap >= 10 minutos
            if eta_b - eta_a >= 10.0:
                return i + 1  # posición donde insertarse (entre A y B)

        # Si no encontró gap interno: si todavía no salió de 100 mn, podés insertarlo al final
        if self.distancia_mn_aep <= 100.0:
            return largo

        # Si ya salió (>100), que siga outbound; eventualmente "montevideo"
        return None