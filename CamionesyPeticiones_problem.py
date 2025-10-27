# from aima.search import Problem, hill_climbing, simulated_annealing
from abia_Gasolina import Gasolineras, Gasolinera, CentrosDistribucion, Distribucion
from Camion_state import Camion



class Problema(object):
    def __init__(self, centros: CentrosDistribucion, gasolineras: Gasolineras):
        self.centros = centros
        self.gasolineras = gasolineras
        self.camiones = []
        
        # Crear un camión por cada centro de distribución
        # Si multiplicidad > 1, varios camiones estarán en la misma posición inicial
        for _ in range(len(centros.centros)):
            camion = Camion(centros, gasolineras, capacidad_maxima)
            self.camiones.append(camion)
        
        self.distancia_total = 0
        self.beneficio_total = 0

        self.pet_pendientes = []



    
    def coste_dist(self, ):



    def perdidas_pet(self, ):


    def beneficio(self, ):
        

    def 



max_km = 640
max_viajes = 5
valor_deposito = 1000
coste_km = 2
capacidad_maxima = 2
