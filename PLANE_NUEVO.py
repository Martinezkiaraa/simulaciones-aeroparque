from typing import Optional
import random


class plane:
    def __init__(self, id, minuto_aparicion, fila, desviados, mtvd, rio):
        self.id = id 
        self.estado = "En fila"
        self.minuto_aparicion = minuto_aparicion
        self.distancia_mn_aep = 100.0   # millas náuticas a AEP
        self.velocidad_actual = 300.0   # nudos (mn/h)
        self.landed_minute = None
        self.next: Optional["plane"] = None   # avión que tengo adelante
        self.v_max = 0.0
        self.v_min = 0.0
        self.fila = fila
        self.desviados = desviados
        self.mtvd = mtvd
        self.rio = rio

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

    def avanzar(self, minuto_actual: int = None, dt: float = 1.0, hay_viento = True, metricas = None):
        # 1) Actualizar límites de tramo
        self.calcular_rango_velocidad()

        # 2) Inbound: aplicar reglas si está en fila
        if self.estado == "En fila" or self.estado == "Reinsertado":

            # Si hay líder válido, aplicar regla líder−20 / buffer 5
            if self.next is not None and self.next.estado == "En fila":
                eta_self = self._eta(self.distancia_mn_aep, self.velocidad_actual)
                eta_next = self._eta(self.next.distancia_AEP(), self.next.velocidad())
                gap = eta_self - eta_next  # seguidor - líder
    
                if gap < 4.0:
                    # seguidor = vel_líder − 20; si cae por debajo de v_min → desvío
                    nueva_v = self.next.velocidad() - 20.0
                    if nueva_v < self.v_min:
                        idx = self.fila.get_index(self)      # guardá tu índice antes de sacar
                        leader = self.next                   # guardá quién era tu líder
                        self.estado = "Desviado"
                        self.velocidad_actual = 200.0 # outbound
                        self.fila.eliminar_avion(self)       # te vas de la fila
                        self.desviados.agregar_avion(self)
                        self.next = None                     # vos ya no tenés líder
                        # actualizar el seguidor (si existe): ahora su líder pasa a ser 'leader'
                        if idx < len(self.fila.aviones):     # ojo: la lista ya se corrió a la izquierda
                            follower = self.fila.aviones[idx]
                            follower.next = leader  
                        return         
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
            
            if self.distancia_mn_aep <= 5.0:
                
                p_evento = 0.1 if hay_viento else 0.0
                
                #VEMOS SI HAY UNA INTERRUPCIÓN DE ATERRIZAJE
                if random.random() < p_evento:
                    self.estado = "Rio"
                    metricas.registrar_desvio_rio()
                    self.velocidad_actual = 200.0
                    lider = self.next 
                    ind = self.fila.get_index(self)
                    self.next = None
                    self.fila.eliminar_avion(self)       # te vas de la fila
                    self.rio.agregar_avion(self)
                    if ind < len(self.fila.aviones):     # ojo: la lista ya se corrió a la izquierda
                            seguidor = self.fila.aviones[ind]
                            seguidor.next = lider
                else:
                    self.distancia_mn_aep = 0.0 # ASUMIMOS QUE SI NO ESTA EN UN DIA VENTOSO Y ESTA A MENOS DE 5MN ENTONCES ATERRIZA CON EXITO
                    self.estado = "Aterrizó" 
                    if self.landed_minute is None and minuto_actual is not None:
                        self.landed_minute = minuto_actual
            else:
                self.estado = "En fila"

            # Mantener orden en la fila si corresponde
            self.fila.actualizar_orden()
            return

        # 3) Aterrizado: nada que hacer
        if self.estado == "Aterrizó":
            self.fila.eliminar_avion(self)
            return

        # 4) Desviado: outbound a 200 kn y reintentos de reinserción
        if self.estado == "Desviado" or self.estado == "Rio":
            # Intentar reinsertar 
            posicion = self.buscar_gap()
            
            if posicion is not None:

                #Lo integro a la fila
                self.reinsertarse(posicion)

                # Velocidad de reingreso: usar tu perfil y respetar límites del tramo
                self.calcular_rango_velocidad()
                self.velocidad_actual = self.v_max

                # Estado y ordenar por distancia para mantener la fila prolija
                self.fila.actualizar_orden()
                self.estado = "Reinsertado"
                return
            
            else:
                # Si no hay gap, seguir saliendo a 200 kn (= 200/60 mn por minuto)
                self.distancia_mn_aep += (200.0 / 60.0) * dt
                if self.distancia_mn_aep >= 100.0:
                    if (self.estado == "Desviado"):
                        self.desviados.eliminar_avion(self)
                    else:
                        self.rio.eliminar_avion(self)
                    self.estado = "Montevideo"
                    self.mtvd.agregar_avion(self)
                    metricas.registrar_desvio_montevideo()
                return
        
    def reinsertarse(self, posicion):
        # 1) Insertar en la fila en la posición calculada
        self.fila.aviones.insert(posicion, self)
        if (self.estado == "Desviado"):
            self.desviados.eliminar_avion(self)
        else:
            self.rio.eliminar_avion(self)
        # 2) Actualizar punteros de liderazgo localmente
        leader = self.fila.aviones[posicion - 1] if posicion > 0 else None
        self.next = leader  # el insertado ve como líder al que queda adelante
        # el que queda detrás del insertado ahora ve al insertado como líder
        if posicion + 1 < len(self.fila.aviones):
            follower = self.fila.aviones[posicion + 1]
            follower.next = self

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
            if self.estado == "Desviado" and eta_b - eta_a >= 10.0:
                return i + 1  # posición donde insertarse (entre A y B)
            elif eta_b - eta_a >= 10.0 and self.distancia_mn_aep > 5.0:
                return i + 1  # posición donde insertarse (entre A y B)
            
        if largo > 0:
            eta_1 = self._eta(self.distancia_mn_aep, self.velocidad_actual)
            eta_2 = self._eta(self.fila.aviones[-1].distancia_mn_aep, self.fila.aviones[-1].velocidad_actual)
            
            if self.estado == "Desviado" and self.distancia_mn_aep <= 100.0 and eta_1 - eta_2 >= 10.0:
                # Si no encontró gap interno: si todavía no salió de 100 mn, podés insertarlo al final
                return largo                
            else:
                # Si ya salió (>100), que siga outbound; eventualmente "montevideo"
                return None
        else: #Si no hay nadie
            return 0
