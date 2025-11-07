from abia_Gasolina import *
from Camion_parameters import ProblemParameters
from Camion_operators import CamionOperators

from typing import Generator, List


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
            for c in range(len(centros.centros)):
                camion = Camion([(centros.centros[c].cx, centros.centros[c].cy, -1)])
                for _ in range(params.multiplicidad):
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
    camion = camiones.camiones[c]

    # hacemos un bucle para cada camión
    while c < len(camiones.camiones):
        x = gasolineras.gasolineras[g].cx
        y = gasolineras.gasolineras[g].cy
        
        # Asignamos las peticiones de la gasolinera g al camión c
        for p in range(len(gasolineras.gasolineras[g].peticiones)):
            
            # si el camión ha llegado al máximo de viajes, no hace falta calcular distancias
            # podemos estar seguros de que si el camión no puede hacer más viajes, ya está en el centro
            if camion.num_viajes == params.max_viajes:
                # pasamos al siguiente camión
                c += 1
                # comprobamos que no nos salgamos del rango de camiones
                if c >= len(camiones.camiones):
                    break
                camion = camiones.camiones[c]

            # esto servira para ahorrarnos un calculo de distancia para cada camión
            # ya hemos comprobado que un camión puede hacer al menos 2 peticiones o 1 viaje sin problemas
            if camion.num_viajes != 0:
                # distancia acumulada del camión hasta el momento
                distancia_camion = calcular_distancia_camion(camion)
                
                # distancia desde la última posición del camión hasta la gasolinera
                distancia_nueva = distancia((camion.viajes[-1][0], camion.viajes[-1][1]), (x, y))
                
                # también calculamos la distancia de la gasolinera hasta el centro de distribución porque el camión debe poder 
                # volver en cualquier momento sin sobrepasar el máximo de km
                distancia_vuelta = distancia((x, y), (camion.viajes[0][0], camion.viajes[0][1]))
                
                if distancia_camion + distancia_nueva + distancia_vuelta > params.max_km:
                    # si este camión no puede más, lo enviamos de vuelta al centro
                    # estamos seguros de que tiene distancia suficiente para volver porque sinó debería haberse detenido en la iteración anterior
                    volver_a_centro(camion)
                    # pasamos al siguiente camión
                    c += 1
                    # comprobamos que no nos salgamos del rango de camiones
                    if c >= len(camiones.camiones):
                        break
                    camion = camiones.camiones[c]

            camiones.camiones[c].viajes.append((x, y, gasolineras.gasolineras[g].peticiones[p]))
            camion.capacidad -= 1

            # miramos que un camión no vaya a una gasolinera con el depósito vacío y que aún pueda hacer más viajes
            # ya habremos comprobado que el camión puede volver al centro sin sobrepasar el máximo de km
            if camion.capacidad == 0:
                volver_a_centro(camion)
        
        # pasamos a la siguiente gasolinera
        g += 1
    
    return camiones
          

def generar_sol_inicial_greedy(params: ProblemParameters) -> Camiones:
    camiones = Camiones(params, [])
    peticiones = []

    # creamos una lista con todas las peticiones de las gasolineras y su indice de gasolinera
    for g in range(len(gasolineras.gasolineras)):
        for p in range(len(gasolineras.gasolineras[g].peticiones)):
            peticiones.append((gasolineras.gasolineras[g].peticiones[p], g))

    # ordenamos las peticiones de mayor a menor número de días de retraso, excepto las de 0 días, que iran al principio
    peticiones.sort(key=lambda x: (x[0] != 0, -x[0]))
    
    # asignamos las peticiones a los camiones más cercanos
    for peticion, g in peticiones:
        x = gasolineras.gasolineras[g].cx
        y = gasolineras.gasolineras[g].cy

        # intentamos asignar la peticion al camión más cercano que pueda hacerla
        distancia_minima = float('inf')
        camion_seleccionado = None
        
        # miremos que los camiones puedan hacer la peticion
        # luego buscamos el camión más cercano
        # no podremos ahorrar cálculos de distancia como antes usando la propiedad de que los camiones sin viajes pueden 
        # servir al menos 2 peticiones sin problemas, porque necesitamos buscar el camión más cercano
        for camion in camiones.camiones:
            # Si puede hacer más viajes y tiene capacidad, calculamos la distancia al siguiente punto
            # igual que antes, comprobamos que el camión pueda volver al centro en cualquier momento
            if camion.num_viajes < params.max_viajes and camion.capacidad > 0:
                distancia_actual = distancia((camion.viajes[-1][0], camion.viajes[-1][1]), (x, y))
                distancia_volver = distancia((x, y), (camion.viajes[0][0], camion.viajes[0][1]))
                distancia_total = calcular_distancia_camion(camion) + distancia_actual + distancia_volver

                if distancia_total <= params.max_km and distancia_actual < distancia_minima:
                    distancia_minima = distancia_actual
                    camion_seleccionado = camion

        if camion_seleccionado is not None:
            camion_seleccionado.viajes.append((x, y, peticion))
            camion_seleccionado.capacidad -= 1

            if camion_seleccionado.capacidad == 0 and camion_seleccionado.num_viajes < params.max_viajes:
                volver_a_centro(camion_seleccionado)
    
        else:
            # si no hay ningún camión que pueda hacer la petición, detenemos las asignaciones
            break
        
    return camiones



def volver_a_centro(camion: Camion) -> None:
    # Añadir un viaje de vuelta al centro de distribución, las restricciones se comprueban antes de llamar a esta función
    centro_origen = camion.viajes[0]
    camion.viajes.append((centro_origen[0], centro_origen[1], -1))
    camion.num_viajes += 1
    camion.capacidad = params.capacidad_maxima


# funcion para calcular la distancia total recorrida por un solo camión
def calcular_distancia_camion(camion: Camion) -> float:
    total_distance = 0
    for i in range(1, len(camion.viajes)):
        total_distance += distancia(camion.viajes[i-1][:2], camion.viajes[i][:2])
    return total_distance

def distancia(p1: tuple, p2: tuple) -> float:
    return abs(p2[0] - p1[0]) + abs(p2[1] - p1[1])