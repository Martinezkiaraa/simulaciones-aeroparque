class heap:
    def __init__(self):
         # Lista de aviones ordenada por distancia a AEP (menor distancia primero)
        self.aviones = []

    def actualizar_orden(self):
        # Mantiene la lista ordenada por distancia al aeropuerto.
        self.aviones.sort(key=lambda avion: avion.distancia_mn_aep)
        
        # 2. Actualizar punteros next (líder inmediato en radar)
        for i, avion in enumerate(self.aviones):
            if i == 0:
                avion.next = None   # el más cercano no tiene líder
            else:
                avion.next = self.aviones[i - 1]


    def agregar_avion(self, avion):
        self.aviones.append(avion)
        self.actualizar_orden()

    def eliminar_avion(self, avion):
        self.aviones.remove(avion)
        self.actualizar_orden()  # <- importante para mantener next coherente
    def get_index(self, avion):
        return self.aviones.index(avion)