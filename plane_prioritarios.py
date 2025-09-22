from typing import Optional
import random

# ============================================================
# OTRAS DIMENSIONES DEL PROBLEMA
# CLASE CON PRIORIDAD: AVIONES PRIORITARIOS TIENEN REGLAS MÁS FLEXIBLES
# - Separación mínima efectiva de 3 min vs 4 min (solo para el seguidor prioritario)
# - Evitan desvío por congestión cuando es marginal, reduciendo menos la velocidad
# - Se registran como prioritarios en la historia para análisis/plots
# No modifica la clase original `plane`.
# ============================================================


class plane_prioritario:
    def __init__(self, id, minuto_aparicion, fila, desviados, mtvd, viento, tormenta, historia=None, prioritario=False):
        self.id = id
        self.estado = "En fila"
        self.minuto_aparicion = minuto_aparicion
        self.distancia_mn_aep = 100.0
        self.velocidad_actual = 300.0
        self.landed_minute = None
        self.next: Optional["plane_prioritario"] = None
        self.v_max = 0.0
        self.v_min = 0.0
        self.tiempo_en_min_aep = None
        self.fila = fila
        self.desviados = desviados
        self.mtvd = mtvd
        self.viento = viento
        self.tormenta = tormenta
        self.historia = historia
        self.prioritario = prioritario

        # Día ventoso (go-around) - misma semántica que el modelo base
        self.goaround_evaluado = False
        self.goaround_decidido = False
        self.goaround_trigger_dist = None

    # ---------------- Utilitarios ----------------
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

    # ---------------- Dinámica minuto a minuto ----------------
    def avanzar(self, minuto_actual: int = None, dt: float = 1.0, hay_viento = True, tormenta_activa = False, metricas = None):
        self.calcular_rango_velocidad()

        if self.estado == "En fila" or self.estado == "Reinsertado":
            # Regla de separación: 3 min si el seguidor es prioritario, 5 min si es normal
            sep_req = 3.0 if self.prioritario else 5.0

            if self.next is not None and self.next.estado in ("En fila", "Reinsertado"):
                eta_self = self._eta(self.distancia_mn_aep, self.velocidad_actual)
                eta_next = self._eta(self.next.distancia_mn_aep, self.next.velocidad_actual)
                gap = eta_self - eta_next

                if gap < sep_req:
                    # Ajuste de velocidad: priorizado reduce menos (ventaja) antes de desviar
                    reduction = 10.0 if self.prioritario else 20.0
                    nueva_v = self.next.velocidad_actual - reduction
                    if nueva_v < self.v_min:
                        # Para prioritarios: último intento a v_min antes de desviar
                        if self.prioritario and self.v_min > 0:
                            self.velocidad_actual = self.v_min
                    else:
                        self.velocidad_actual = nueva_v

                    # Si el seguidor es prioritario y aún no llega a 3 minutos de gap,
                    # pedirle al líder que acelere (reduzca su gap adelante) para abrir espacio.
                    if self.prioritario:
                        # Recalcular gap tras el ajuste propio
                        eta_self2 = self._eta(self.distancia_mn_aep, self.velocidad_actual)
                        eta_next2 = self._eta(self.next.distancia_mn_aep, self.next.velocidad_actual)
                        gap2 = eta_self2 - eta_next2
                        if gap2 < 3.0:
                            leader = self.next
                            leader.calcular_rango_velocidad()
                            # Acelerar respetando gap del líder con su propio líder
                            leader_next = getattr(leader, 'next', None)
                            if leader_next is not None and leader_next.estado in ("En fila", "Reinsertado"):
                                eta_lead = self._eta(leader.distancia_mn_aep, max(leader.velocidad_actual, 1.0))
                                eta_lead_next = self._eta(leader_next.distancia_mn_aep, max(leader_next.velocidad_actual, 1.0))
                                gap_lead = eta_lead - eta_lead_next
                                if gap_lead < 5.0:
                                    # no violar el gap del líder → como mucho acompaño
                                    leader.velocidad_actual = min(leader.v_max, leader_next.velocidad_actual - 20.0)
                                else:
                                    leader.velocidad_actual = leader.v_max
                            else:
                                leader.velocidad_actual = leader.v_max

                            # Recalcular nuevamente con líder ajustado
                            eta_self3 = self._eta(self.distancia_mn_aep, self.velocidad_actual)
                            eta_lead3 = self._eta(leader.distancia_mn_aep, leader.velocidad_actual)
                            gap3 = eta_self3 - eta_lead3

                            # Si aún no alcanza y el líder NO es prioritario → líder se desvía, prioritario avanza
                            leader_prioritario = leader.prioritario
                            if gap3 < 3.0 and not leader_prioritario:
                                # Registrar traza del líder antes de moverlo
                                if self.historia is not None:
                                    if leader.id not in self.historia:
                                        self.historia[leader.id] = {"t": [], "x": [], "v": [], "estado": [], "vmax": []}
                                    self.historia[leader.id]["t"].append(minuto_actual if minuto_actual is not None else 0)
                                    self.historia[leader.id]["x"].append(leader.distancia_mn_aep)
                                    self.historia[leader.id]["v"].append(leader.velocidad_actual)
                                    self.historia[leader.id]["estado"].append("Desviado")
                                    self.historia[leader.id]["vmax"].append(leader.v_max)

                                leader.estado = "Desviado"
                                leader.velocidad_actual = 200.0
                                self.desviados.agregar_avion(leader)
                                # Descolar líder de la fila, mantener punteros
                                leader._descolar_y_reenlazar()
                                # El prioritario puede ir a su velocidad máxima
                                self.calcular_rango_velocidad()
                                self.velocidad_actual = self.v_max
                                # Reordenar fila tras cambios
                                self.fila.actualizar_orden()
                                # Salir temprano del paso actual
                                return
                elif gap >= (sep_req + 1.0):
                    # Recuperar a v_max si hay margen suficiente
                    self.velocidad_actual = self.v_max
                # Si sep_req <= gap < sep_req+1 se mantiene velocidad
            else:
                # Sin líder: v_max
                self.velocidad_actual = self.v_max

            # Avanzar en distancia
            self.distancia_mn_aep = max(0.0, self.distancia_mn_aep - (self.velocidad_actual / 60.0) * dt)
            self.tiempo_en_min_aep = self._eta(self.distancia_mn_aep, self.velocidad_actual)

            # Final: intentos de aterrizaje y eventos
            if 0.0 < self.distancia_mn_aep <= 5.0:
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
                        self.goaround_decidido = (random.random() < 0.1)
                        if self.goaround_decidido:
                            self.goaround_trigger_dist = random.uniform(0.0, 5.0)

                if self.goaround_decidido and self.goaround_trigger_dist is not None \
                   and self.distancia_mn_aep <= self.goaround_trigger_dist:
                    self.estado = "Rio"
                    if metricas: metricas.registrar_desvio_viento()
                    self.viento.agregar_avion(self)
                    self.velocidad_actual = 200.0
                    self._descolar_y_reenlazar()
                    return

            # Aterrizaje real
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

            self.fila.actualizar_orden()
            return

        # Outbound (desviado/viento/tormenta)
        if self.estado in ["Desviado", "Rio", "Tormenta"]:
            posicion = self.buscar_gap()
            if posicion is not None:
                self.reinsertarse(posicion)
                self.calcular_rango_velocidad()
                self.velocidad_actual = self.v_max
                self.fila.actualizar_orden()
                self.estado = "Reinsertado"
                return
            else:
                self.distancia_mn_aep += (200.0 / 60.0) * dt
                if self.distancia_mn_aep >= 100.0:
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

    # ---------------- Reinserción/gaps ----------------
    def reinsertarse(self, posicion):
        self.fila.aviones.insert(posicion, self)
        if self.estado == "Desviado":
            self.desviados.eliminar_avion(self)
        elif self.estado == "Rio":
            self.viento.eliminar_avion(self)
        elif self.estado == "Tormenta":
            self.tormenta.eliminar_avion(self)
        leader = self.fila.aviones[posicion - 1] if posicion > 0 else None
        self.next = leader
        if posicion + 1 < len(self.fila.aviones):
            follower = self.fila.aviones[posicion + 1]
            follower.next = self

    def buscar_gap(self):
        self.fila.actualizar_orden()
        largo = len(self.fila.aviones)
        for i in range(largo - 1):
            a = self.fila.aviones[i]
            b = self.fila.aviones[i + 1]
            eta_a = self._eta(a.distancia_mn_aep, a.velocidad_actual)
            eta_b = self._eta(b.distancia_mn_aep, b.velocidad_actual)
            if self.estado in ["Desviado", "Rio", "Tormenta"] and eta_b - eta_a >= 10.0 and self.distancia_mn_aep > 5.0:
                return i + 1
        if largo > 0:
            eta_1 = self._eta(self.distancia_mn_aep, self.velocidad_actual)
            eta_2 = self._eta(self.fila.aviones[-1].distancia_mn_aep, self.fila.aviones[-1].velocidad_actual)
            if self.estado in ["Desviado", "Rio", "Tormenta"] and self.distancia_mn_aep <= 100.0 and eta_1 - eta_2 >= 10.0:
                return largo
            else:
                return None
        else:
            return 0


