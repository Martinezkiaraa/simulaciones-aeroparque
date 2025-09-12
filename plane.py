from typing import Optional
from heap import eliminar_avion 

class plane:
    def __init__(self, id, minuto_aparicion, fila):
        self.id = id 
        self.estado = "en radar"
        self.minuto_aparicion = minuto_aparicion
        self.distancia_mn_aep = 100.0   # millas náuticas a AEP
        self.velocidad_actual = 300.0   # nudos (mn/h)
        self.tiempo_en_min_aep = (self.distancia_mn_aep / self.velocidad_actual) * 60
        self.landed_minute = None
        self.next: Optional["plane"] = None   # avión que tengo adelante
        self.v_max = 0.0
        self.v_min = 0.0
        self.fila = fila

    def _eta(self, dist_mn, vel_kn):
        # minutos hasta AEP con velocidad actual
        dist_mn / (vel_kn / 60.0)

    def distancia_AEP(self):
        return self.distancia_mn_aep 
                    
    def velocidad(self):
        return self.velocidad_actual
    
    def estado(self):
        return self.estado
    
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
            if self.next is not None and self.next.estado() in ("en radar"): # PREeUNTA: l next dírebe
                eta_self = self._eta(self.distancia_mn_aep, self.velocidad_actual)
                eta_next = self._eta(self.next.distancia_AEP(), self.next.velocidad())
                gap = eta_self - eta_next  # seguidor - líder
    
                if gap < 4.0:
                    # seguidor = vel_líder − 20; si cae por debajo de v_min → desvío
                    nueva_v = self.next.velocidad() - 20.0
                    if nueva_v < self.v_min:
                        self.estado = "desviado"
                        self.velocidad_actual = 200.0  # outbound
                        self.fila.eliminar_avion(self) # PREGUNTA: puede no estar en la fila?
                        return                    else:
                        self.velocidad_actual = self.next.velocidad() - 20.0

                


            if (eta_self - eta_next < 4.0):
                if (self.next.velocidad() - 20) < self.v_min:
                    self.estado = "desviado"
                    self.velocidad_actual = 200.0  # velocidad hacia atrás
                    self.fila.eliminar_avion(self)  # se quita de la cola

                    # Buscar posición donde reinsertarse
                    posicion = self.buscar_gap()
                    if posicion is not None:
                        self.fila.aviones.insert(posicion, self)
                        self.estado = "en radar"

                else:
                    # Simplemente reducir velocidad
                    self.velocidad_actual = self.next.velocidad() - 20.0

            elif ((eta_self - eta_next) >= 5.0 and self.velocidad_actual < self.v_max):
                # Vuelve a acelerar hasta su velocidad máxima para su tramo
                self.velocidad_actual = self.v_max                
               
            #FALTA ACTUALIZAR DISTANCIAS !!!
            return
        
        elif self.distancia_mn_aep <= 0:
            self.distancia_mn_aep = 0
            self.estado = "aterrizó"
            
            return 
        
        #Reduce 200 nudos hacia atras
        elif self.estado == "desviado":
            self.distancia_mn_aep += 200
            if self.distancia_mn_aep >= 100:
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

        for i in range(largo - 2):
            avion_a = self.fila.aviones[i]
            avion_b = self.fila.aviones[i + 1]

            # Calcular ETA de ambos
            eta_a = avion_a.distancia_mn_aep / (avion_a.velocidad_actual / 60)
            eta_b = avion_b.distancia_mn_aep / (avion_b.velocidad_actual / 60)

            # Si la diferencia temporal es >= 10, hay espacio
            if eta_b - eta_a >= 10:
                return i + 1  # posición donde insertarse

        if (self.distancia_mn_aep <= 100):
            return largo
        else:
            return None
