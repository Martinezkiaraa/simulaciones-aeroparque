from typing import Optional
import random

# ============================================================
# ENUNCIADO / PARTES 1–6
# CLASE QUE REPRESENTA A CADA AVIÓN EN LA SIMULACIÓN
# ============================================================

class plane:
    def __init__(self, id, minuto_aparicion, fila, desviados, mtvd, viento, tormenta, historia=None):
        self.id = id 
        self.estado = "En fila"             # ESTADO INICIAL
        self.minuto_aparicion = minuto_aparicion
        self.distancia_mn_aep = 100.0       # ENUNCIADO: APARECE A 100 MN DE AEP
        self.velocidad_actual = 300.0       # VELOCIDAD INICIAL
        self.landed_minute = None           # MINUTO DE ATERRIZAJE
        self.next: Optional["plane"] = None # AVIÓN LÍDER INMEDIATO EN LA FILA
        self.v_max = 0.0
        self.v_min = 0.0
        self.tiempo_en_min_aep = None       # ETA, SE ACTUALIZA EN avanzar()
        # REFERENCIAS A LAS DIFERENTES FILAS/HEAPS
        self.fila = fila               # Fila principal de aproximación
        self.desviados = desviados     # Desvíos por congestión (parte 4)
        self.mtvd = mtvd               # Aviones que se fueron a Montevideo
        self.viento = viento           # Desvíos por día ventoso (parte 5)
        self.tormenta = tormenta       # Desvíos por tormenta (parte 6)
        self.historia = historia       # Referencia a la historia para registrar datos
        #NOS ASEGURAMOS DE SOLO REVISAR UNA VEZ QUE EL AVION DEBE INTERRUMPIR ATERRIZAJE EN DIA VENTOSO, USAMOS:
        self.goaround_evaluado = False
        self.goaround_decidido = False
        self.goaround_trigger_dist = None  # en millas, entre 0 y 5

    # ========================================================
    # ENUNCIADO / PARTE 1
    # CALCULA EL ETA (MINUTOS HASTA LLEGAR A AEP) A VELOCIDAD DADA
    # ========================================================
    
    def _eta(self, dist_mn, vel_kn):
        return dist_mn / (vel_kn / 60.0)
    
    def _descolar_y_reenlazar(self):
        leader = self.next
        idx = self.fila.get_index(self)
        self.next = None
        self.fila.eliminar_avion(self)
        if 0 <= idx < len(self.fila.aviones):
            follower = self.fila.aviones[idx]
            follower.next = leader
        
    # ========================================================
    # ENUNCIADO / PARTE 1
    # DEFINE EL RANGO DE VELOCIDADES PERMITIDO SEGÚN DISTANCIA
    # ========================================================

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

    # ========================================================
    # ENUNCIADO / PARTES 1, 4, 5 y 6
    # AVANZA EL ESTADO DEL AVIÓN UN MINUTO (DINÁMICA COMPLETA)
    # ========================================================
    
    def avanzar(self, minuto_actual: int = None, dt: float = 1.0, hay_viento = True, tormenta_activa = False, metricas = None):
        # ACTUALIZA VMIN Y VMAX SEGÚN TRAMO
        self.calcular_rango_velocidad()

        # ----------------------------------------------------
        # CASO 1: AVIÓN EN FILA O REINSERTADO
        # ----------------------------------------------------
        
        if self.estado in ("En fila","Reinsertado"):

            # SI TIENE LÍDER ADELANTE, APLICAR LA REGLA DE SEPARACIÓN
            if self.next is not None and self.next.estado == "En fila":
                eta_self = self._eta(self.distancia_mn_aep, self.velocidad_actual)
                eta_next = self._eta(self.next.distancia_mn_aep, self.next.velocidad_actual)
                gap = eta_self - eta_next  # DIFERENCIA DE ETA EN MINUTOS
    
                if gap < 4.0:
                    # SI GAP < 4 → REDUZCO VELOCIDAD A VEL_LÍDER - 20
                    nueva_v = self.next.velocidad_actual - 20.0
                    if nueva_v < self.v_min:
                        # SI ESO CAE DEBAJO DE VMIN → DESVÍO A OUTBOUND (congestión)
                        self.estado = "Desviado"
                        self.velocidad_actual = 200.0        # outbound
                        self.desviados.agregar_avion(self)
                        self._descolar_y_reenlazar() 
                        return         
                    else:
                        self.velocidad_actual = nueva_v

                elif gap >= 5.0:
                    # SI GAP ≥ 5 → VOLVER A VMAX
                    self.velocidad_actual = self.v_max
            else:
                # SI NO TIENE LÍDER → VMAX
                self.velocidad_actual = self.v_max

            # AVANZA DISTANCIA HACIA AEP
            self.distancia_mn_aep = max(0.0, self.distancia_mn_aep - (self.velocidad_actual / 60.0) * dt)
            self.tiempo_en_min_aep = self._eta(self.distancia_mn_aep, self.velocidad_actual)
            
            # CUANDO ESTÁ A MENOS DE 5 MN → INTENTA ATERRIZAR
            if 0.0 < self.distancia_mn_aep <= 5.0:

                # -------------------------------------------------
                # PARTE 5: DÍA VENTOSO (10% DE GO-AROUND)
                # PARTE 6: TORMENTA (CERRADO EL AEP)
                # -------------------------------------------------
                
                if tormenta_activa:
                    self.estado = "Tormenta"
                    if metricas: metricas.registrar_desvio_tormenta()
                    self.tormenta.agregar_avion(self)
                    self.velocidad_actual = 200.0
                    self._descolar_y_reenlazar()
                    return
                if not self.goaround_evaluado:
                    self.goaround_evaluado = True
                    if hay_viento:
                        # Chequeamos una sola vez
                        self.goaround_decidido = (random.random() < 0.1)
                        if self.goaround_decidido:
                            # Elegimos dónde se gatilla dentro de 0-5 mn (puede ser bien cerca del suelo)
                            self.goaround_trigger_dist = random.uniform(0.0, 5.0)
                if self.goaround_decidido and self.goaround_trigger_dist is not None \
                and self.distancia_mn_aep <= self.goaround_trigger_dist:
                    self.estado = "Rio"
                    if metricas: metricas.registrar_desvio_viento()
                    self.viento.agregar_avion(self)
                    self.velocidad_actual = 200.0
                    self._descolar_y_reenlazar()
                    return
                
            # Aterrizaje real: cuando llegó a 0 mn
            if self.distancia_mn_aep <= 0.0:
                self.distancia_mn_aep = 0.0
                self.estado = "Aterrizó"
                if metricas: metricas.registrar_aterrizaje()
                self.fila.eliminar_avion(self)
                if self.landed_minute is None and minuto_actual is not None:
                    self.landed_minute = minuto_actual
                return
            
            else:
                self.estado = "En fila"

            # REORDENA LA FILA
            self.fila.actualizar_orden()
            return

        # ----------------------------------------------------
        # CASO 3: DESVIADO, VIENTO O TORMENTA (OUTBOUND)
        # ----------------------------------------------------
        
        if self.estado in ["Desviado", "Rio", "Tormenta"]:
            # BUSCAR UN GAP ≥ 10 MIN PARA REINSERTARSE 
            posicion = self.buscar_gap()
            
            if posicion is not None:

                # SI HAY GAP → SE REINSERTA
                self.reinsertarse(posicion)

                # Velocidad de reingreso: usar tu perfil y respetar límites del tramo
                self.calcular_rango_velocidad()
                self.velocidad_actual = self.v_max

                # Estado y ordenar por distancia para mantener la fila prolija
                self.fila.actualizar_orden()
                self.estado = "Reinsertado"
                return
            
            else:
                # SI NO HAY GAP → SIGUE SALIENDO OUTBOUND A 200 KN
                self.distancia_mn_aep += (200.0 / 60.0) * dt
                if self.distancia_mn_aep >= 100.0:
                    # SI YA PASÓ 100 MN → SE VA A MONTEVIDEO
                    # Registrar historia completa antes de ir a Montevideo
                    if self.historia is not None:
                        self.historia[self.id]["t"].append(minuto_actual)
                        self.historia[self.id]["x"].append(self.distancia_mn_aep)
                        self.historia[self.id]["v"].append(self.velocidad_actual)
                        self.historia[self.id]["vmax"].append(self.v_max)
                        
                    if self.estado == "Desviado":
                        self.desviados.eliminar_avion(self)
                    elif self.estado == "Rio":
                        self.viento.eliminar_avion(self)
                    elif self.estado == "Tormenta":
                        self.tormenta.eliminar_avion(self)

                    self.estado = "Montevideo"
                    self.mtvd.agregar_avion(self)
                    if metricas: metricas.registrar_desvio_montevideo()
                return

    # ========================================================
    # PARTE 4
    # REINSERCIÓN DEL AVIÓN EN LA FILA EN LA POSICIÓN CALCULADA
    # ========================================================
        
    def reinsertarse(self, posicion):
        self.fila.aviones.insert(posicion, self)
        
        # ELIMINA DE SU HEAP ORIGINAL
        if self.estado == "Desviado":
            self.desviados.eliminar_avion(self)
        elif self.estado == "Rio":
            self.viento.eliminar_avion(self)
        elif self.estado == "Tormenta":
            self.tormenta.eliminar_avion(self)

        # ACTUALIZA PUNTEROS
        leader = self.fila.aviones[posicion - 1] if posicion > 0 else None
        self.next = leader
        if posicion + 1 < len(self.fila.aviones):
            follower = self.fila.aviones[posicion + 1]
            follower.next = self

    # ========================================================
    # PARTE 4
    # BUSCA GAPS ≥ 10 MINUTOS ENTRE AVIONES PARA REINSERTARSE
    # ========================================================
    
    def buscar_gap(self):
        self.fila.actualizar_orden()
        largo = len(self.fila.aviones)

        # RECORRE TODOS LOS PARES ADYACENTES (AVIONES SEGUIDOS EN LA FILA)
        for i in range(largo - 1):
            avion_a = self.fila.aviones[i]
            avion_b = self.fila.aviones[i + 1]

            eta_a = self._eta(avion_a.distancia_mn_aep, avion_a.velocidad_actual)
            eta_b = self._eta(avion_b.distancia_mn_aep, avion_b.velocidad_actual)

            # SI GAP ≥ 10 → DEVUELVE POSICIÓN
            if self.estado in ["Desviado", "Rio", "Tormenta"] and eta_b - eta_a >= 10.0 and self.distancia_mn_aep > 5.0:
                return i + 1
            
        # SI NO ENCONTRÓ GAP INTERNO → CHEQUEA FINAL DE LA FILA
        if largo > 0:
            eta_1 = self._eta(self.distancia_mn_aep, self.velocidad_actual)
            eta_2 = self._eta(self.fila.aviones[-1].distancia_mn_aep, self.fila.aviones[-1].velocidad_actual)
            
            if self.estado in ["Desviado", "Rio", "Tormenta"] and self.distancia_mn_aep <= 100.0 and eta_1 - eta_2 >= 10.0:
                # Si no encontró gap interno: si todavía no salió de 100 mn, podés insertarlo al final
                return largo                
            else:
                # Si ya salió (>100), que siga outbound; eventualmente "montevideo"
                return None
        else:
            # SI LA FILA ESTÁ VACÍA → REINSERTARSE EN POSICIÓN 0
            return 0