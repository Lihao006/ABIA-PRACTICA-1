from abia_Gasolina import *
from Camion_parameters import ProblemParameters
from Camion_operators import CamionOperators

from typing import Generator, List

from bin_packing_state import StateRepresentation

params = ProblemParameters()
centros = CentrosDistribucion(params.num_centros, params.multiplicidad, params.seed)
gasolineras = Gasolineras(params.num_gasolineras, params.seed)

class Camion(object):

    def __init__(self, viajes: List[tuple]):
        self.capacidad = 2
        self.num_viajes = 0
        self.km_recorridos = 0

        self.viajes = viajes
        # Lista de ubicaciones de gasolineras asignadas y centros de distribución que debe pasar
        # y un integer que indique num de dias de retraso y también identifica si es centro (valor = -1) o gasolinera (valor > -1).
        
        # Puede haber ubicaciones duplicadas que representen las dos peticiones de la misma gasolinera.
        # Las ubicaciones de centros pueden repetirse si el camión tiene que volver a un centro varias veces.
        
        # Lo hacemos así para que se pueda permitir el servicio parcial (sirve una sola petición), el servicio completo (completa las 2 peticiones),
        # distinguir el orden de visitas a gasolineras y centros para poder calcular la distancia recorrida.

        # El primer elemento de la lista de viajes es siempre el centro de distribución inicial.


class Camiones(object):
    def __init__(self, params: ProblemParameters, camiones: List[Camion]):
        self.params = params

        # Crear un camión por cada centro de distribución si la lista de camiones está vacía
        # Si multiplicidad > 1, varios camiones estarán en la misma posición inicial
        if len(camiones) == 0:
            for _ in range(len(centros.centros)):
                camion = Camion([(centros.centros[0].cx, centros.centros[0].cy, -1)])
                self.camiones.append(camion)
        else:
            self.camiones = camiones


        
    def copy(self) -> Camiones:
        # Afegim el copy per cada llista de camions
        camiones_copy = [camion.copy() for camion in self.camiones]
        return Camiones(self.params, camiones_copy)

    def generate_actions(self) -> Generator[CamionOperators, None, None]:
        pass

    def apply_action(self, action: CamionOperators) -> Camiones:
        pass
    
    def heuristic(self) -> float:
        pass


def generar_sol_inicial_vacio(params: ProblemParameters) -> Camiones:
    return Camiones(params, [])


def generar_sol_inicial(params: ProblemParameters) -> Camiones:
    camiones = Camiones(params, [])
    c = 0
    g = 0
    while c < len(centros.centros):
        camion = camiones.camiones[c]
        x = gasolineras.gasolineras[g].cx
        y = gasolineras.gasolineras[g].cy

        # comprobamos que no supere el max_km y max_viajes
        for j in range(len(gasolineras.gasolineras[g].peticiones)):
            if camion.capacidad > 0:
            camiones.camiones[c].viajes.append((x, y, gasolineras.gasolineras[g].peticiones[j]))
            camion.capacidad -= 1
            # si el camión ha llegado a su capacidad máxima, vuelve al centro
            # miramos que un camión no vaya a una gasolinera con el depósito vacío
            if camion.capacidad == 0:
                camion.num_viajes += 1
                camion.capacidad = params.capacidad_maxima
                camion.viajes.append((centros.centros[0].cx, centros.centros[0].cy, -1))
        # pasamos a la siguiente gasolinera
        g += 1
            
        if calcular_distancia_camion(camion) + distancia((camion.viajes[-1][0], camion.viajes[-1][1]), (x, y)) <= params.max_km and camion.num_viajes < params.max_viajes:
            # si este camión no puede más, pasamos al siguiente camión
            c += 1



    for i in range(len(camiones.camiones)):
        x = gasolineras.gasolineras[i].cx
        y = gasolineras.gasolineras[i].cy
        
        for j in range(len(gasolineras.gasolineras[i].peticiones)):
            camiones.camiones[i].viajes.append((x, y, gasolineras.gasolineras[i].peticiones[j]))


def generar_sol_inicial_greedy(params: ProblemParameters) -> Camiones:
    pass


# funcion para calcular la distancia total recorrida por un solo camión
def calcular_distancia_camion(camion: Camion) -> float:
    total_distance = 0
    for i in range(1, len(camion.viajes)):
        total_distance += distancia(camion.viajes[i-1][:2], camion.viajes[i][:2])
    return total_distance

def distancia(p1: tuple, p2: tuple) -> float:
    return abs(p2[0] - p1[0]) + abs(p2[1] - p1[1])