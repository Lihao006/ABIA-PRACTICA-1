from abia_Gasolina import Gasolineras, Gasolinera, CentrosDistribucion, Distribucion
from Camion_parameters import ProblemParameters
from Camion_operators import CamionOperators

from typing import Generator

class Camion(object):

    def __init__(self, centros: CentrosDistribucion):
        self.capacidad = 2
        self.num_viajes = 0
        self.km_recorridos = 0

        self.viajes = [(centros.centros[0].cx, centros.centros[0].cy, -1)]  
        # Lista de ubicaciones de gasolineras asignadas y centros de distribución que debe pasar
        # y un integer que indique num de dias de retraso y también identifica si es centro (valor = -1) o gasolinera (valor > -1).
        
        # Puede haber ubicaciones duplicadas que representen las dos peticiones de la misma gasolinera.
        # Las ubicaciones de centros pueden repetirse si el camión tiene que volver a un centro varias veces.
        
        # Lo hacemos así para que se pueda permitir el servicio parcial (sirve una sola petición), el servicio completo (completa las 2 peticiones),
        # distinguir el orden de visitas a gasolineras y centros para poder calcular la distancia recorrida.

        # El primer elemento de la lista de viajes es siempre el centro de distribución inicial.


class Camiones(object):
    def __init__(self, centros: CentrosDistribucion, gasolineras: Gasolineras):
        self.centros = centros
        self.gasolineras = gasolineras
        self.camiones = []
        # Crear un camión por cada centro de distribución
        # Si multiplicidad > 1, varios camiones estarán en la misma posición inicial
        for _ in range(len(centros.centros)):
            camion = Camion(centros)
            self.camiones.append(camion)

        
        
    
    def generate_actions(self) -> Generator[CamionOperators, None, None]:
        pass

    def apply_action(self, action: CamionOperators) -> Camiones:
        pass
    
    def heuristic(self) -> float:
        pass


def generar_sol_inicial(params: ProblemParameters) -> Camiones:
    pass



def distancia(p1: tuple, p2: tuple) -> float:
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])