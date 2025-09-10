class plane:
    def __init__(self, id, minuto_aparicion):
        self.id = id 
        self.estado = "en radar"
        self.minuto_aparicion = minuto_aparicion
        self.distancia_mn_aep = 100
        self.velocidad_actual = 300
        self.tiempo_en_min_aep = self.distancia_mn_aep / (self.velocidad_actual / 60)
        self.landed_minute = None
    
    """
Se inicia cada avión cuando entra al radar (por eso los valores default)
El ID es para identificar los distintos aviones
El estado para saber la situación del avión: en radar, volando, esperando, aterrizando, desviado, montevideo (chequear)
Se resgitra en que minuto de las 18 horas apareció
La distancia en millas náuticas al AEP (en principio 100mn)
La velocidad actual en nudos (a máxima velocidad va a 300 nudos): Sirve para:
- Calcular cuánto avanza cada minuto (`distancia -= velocidad/60`).
- Aplicar reglas de congestión (reducir 20 nudos, respetar mínimos y máximos por tramo).
- Simular desvíos a 200 nudos.
El tiempo que le falta para llegar a AEP (se calcula en base a la distancia y velocidad)
Se registra el minuto en que aterrizó. Sirve para:
- Saber cuánto tardó en llegar (`landed_minute - minuto_aparicion`).  
- Calcular atrasos comparando con el tiempo ideal.  
- Controlar la separación mínima con el último avión que aterrizó.

pendiente de subida/bajada de velocidad: 
    """


    def avanzar(self, dt=1):
        
    #Avanza el avión dt minutos hacia AEP, según su velocidad actual.
    
        if self.estado == "en radar" or self.estado == "volando":
            mn_por_min = self.velocidad_actual / 60
            self.distancia_mn_aep = max(0.0, self.distancia_mn_aep - mn_por_min * dt)
            if self.distancia_mn_aep == 0:
                self.estado = "aterrizó"
        elif self.estado == "desviado":
            mn_por_min = 200 / 60
            self.distancia_mn_aep += mn_por_min * dt
            if self.distancia_mn_aep >= 100:
                self.estado = "montevideo"

    def cambiar_velocidad(self, nueva_velocidad):
        # COMPLETAR
        pass
  