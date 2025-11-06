# Normas inmutables
max_km = 640
max_viajes = 5
valor_deposito = 1000
coste_km = 2
capacidad_maxima = 2

# Parámetros variables
seed = 1234
num_gasolineras = 100
num_centros = 10
multiplicidad = 1


class ProblemParameters(object):
    def __init__(self, max_km: int=max_km, max_viajes: int=max_viajes, valor_deposito: int=valor_deposito, coste_km_max: int=coste_km, capacidad_maxima: int=capacidad_maxima):
        self.max_km = max_km
        self.max_viajes = max_viajes
        self.valor_deposito = valor_deposito
        self.coste_km_max = coste_km_max
        self.capacidad_maxima = capacidad_maxima
        self.seed = seed
        self.num_gasolineras = num_gasolineras
        self.num_centros = num_centros
        self.multiplicidad = multiplicidad

    def __repr__(self):
        return f"Params(max_km={self.max_km}, max_viajes={self.max_viajes}, \
        valor_deposito={self.valor_deposito}, coste_km_max={self.coste_km_max}, \
        capacidad_maxima={self.capacidad_maxima}, seed={self.seed}, \
        num_gasolineras={self.num_gasolineras}, num_centros={self.num_centros}, \
        multiplicidad={self.multiplicidad})"