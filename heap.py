# ============================================================
# ENUNCIADO / PARTE 1
# ESTA CLASE REPRESENTA LA FILA DE AVIONES EN APROXIMACIÓN.
# MANTIENE LOS AVIONES ORDENADOS POR DISTANCIA AL AEROPUERTO.
# ============================================================

class heap:
    def __init__(self):
        # LISTA ORDENADA DE AVIONES (MENOR DISTANCIA PRIMERO)
        self.aviones = []

    def actualizar_orden(self):
        # ORDENA LA LISTA DE AVIONES POR DISTANCIA AL AEP
        self.aviones.sort(key = lambda avion: avion.distancia_mn_aep)
        
        # ACTUALIZA LOS PUNTEROS "next":
        # cada avión apunta a su líder inmediato (el que está justo adelante en la fila).
        for i, avion in enumerate(self.aviones):
            if i == 0:
                avion.next = None  # EL MÁS CERCANO A AEP NO TIENE LÍDER
            else:
                avion.next = self.aviones[i - 1]

    def agregar_avion(self, avion):
        # AGREGA UN NUEVO AVIÓN A LA FILA Y REORDENA LA LISTA.
        self.aviones.append(avion)
        self.actualizar_orden()

    def eliminar_avion(self, avion):
        # ELIMINA UN AVIÓN DE LA FILA Y REORDENA LA LISTA.
        # IMPORTANTE: SE ACTUALIZAN LOS PUNTEROS NEXT PARA MANTENER COHERENCIA.
        self.aviones.remove(avion)
        self.actualizar_orden()
        
    def get_index(self, avion):
        # DEVUELVE EL ÍNDICE (POSICIÓN) DE UN AVIÓN EN LA FILA.
        return self.aviones.index(avion)