max_km = 640
max_viajes = 5
valor_deposito = 1000
coste_km = 2
capacidad_maxima = 2


class ProblemParameters(object):
    def __init__(self, max_km: int, max_viajes: int, valor_deposito: int, coste_km_max: int, capacidad_maxima: int):
        self.max_km = max_km
        self.max_viajes = max_viajes
        self.valor_deposito = valor_deposito
        self.coste_km_max = coste_km_max
        self.capacidad_maxima = capacidad_maxima

    def __repr__(self):
        return f"Params(max_km={self.max_km}, max_viajes={self.max_viajes}, valor_deposito={self.valor_deposito}, coste_km_max={self.coste_km_max}, capacidad_maxima={self.capacidad_maxima})"