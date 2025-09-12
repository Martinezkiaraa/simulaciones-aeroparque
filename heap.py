class heap:
    def __init__(self):
         # Lista de aviones ordenada por distancia a AEP (menor distancia primero)
        self.aviones = []

    def actualizar_orden(self):
        # Mantiene la lista ordenada por distancia al aeropuerto.
        self.aviones.sort(key=lambda avion: avion.distancia_mn_aep)

    def agregar_avion(self, avion):
        self.aviones.append(avion)
        self.actualizar_orden()

    def eliminar_avion(self, avion):
        self.aviones.remove(avion)

    def get_index(self, avion):
        return self.aviones.index(avion)