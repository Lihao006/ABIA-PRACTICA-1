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
        """
        Generar operadores:
        - MoverPeticion: mover una petición (cualquier viaje con petición != -1) de un camión al final de otro camión.
        - AsignarPeticion: asignar peticiones no asignadas a un camión
        """
        # MoverPeticion
        for cam_i, camion in enumerate(self.camiones):
            # iteramos sobre los viajes; permitimos mover cualquier viaje que sea una petición
            for viaje_i, viaje in enumerate(camion.viajes):
                pet = viaje[2]
                if pet == -1:
                    continue
                # mover esta petición a cualquier camión
                for cam_j, camion_j in enumerate(self.camiones):
                    if cam_j == cam_i:
                        continue
                    # limite de la cisterna
                    if camion_j.capacidad <= 0:
                        continue
                    yield MoverPeticion((cam_i, viaje_i), cam_i, cam_j)

        # AsignarPeticion
        # primero construimos un set de peticiones asignadas
        asignado = set()
        for camion in self.camiones:
            for viaje in camion.viajes:
                if viaje[2] != -1:
                    asignado.add((viaje[0], viaje[1], viaje[2]))

        for gas_i, g in enumerate(gasolineras.gasolineras):
            for pet_i, pet in enumerate(g.peticiones):
                viaje_repr = (g.cx, g.cy, pet)
                if viaje_repr in asignado:
                    continue
                # intentamos asignar a cualquier camión que cumpla con los requisitos
                for cam_i, camion in enumerate(self.camiones):
                    # limite capacidad
                    if camion.capacidad <= 0:
                        continue

                    # miramos el limite de la cisterna (numero de peticiones consecutivas desde el último centro)
                    # buscamos el indice del ultimo centro
                    ult_centro = None
                    for x in range(len(camion.viajes)-1, -1, -1):
                        if camion.viajes[x][2] == -1:
                            ult_centro = x
                            break
                    consec_peticiones = 0
                    start_x = ult_centro + 1 if ult_centro is not None else 0
                    for x in range(start_x, len(camion.viajes)):
                        if camion.viajes[x][2] != -1:
                            consec_peticiones += 1
                    # saltamos si esta petición aumenta el limite
                    if consec_peticiones + 1 > self.params.capacidad_maxima:
                        continue

                    # caculamos la nueva distancia
                    distancia_actual = calcular_distancia_camion(camion)
                    last_pos = (camion.viajes[-1][0], camion.viajes[-1][1])
                    distancia_gasolinera = distancia(last_pos, (g.cx, g.cy))
                    distancia_vuelta = distancia((g.cx, g.cy), (camion.viajes[0][0], camion.viajes[0][1]))
                    distancia_total = distancia_actual + distancia_gasolinera + distancia_vuelta
                    if distancia_total > self.params.max_km:
                        continue
                    # si cumplimos todas las restricciones:
                    yield AsignarPeticion((gas_i, pet_i), cam_i)

    def apply_action(self, action: CamionOperators) -> Camiones:
        """
        Aplicar el operador dado:
         - MoverPeticion((cam_i, viaje_i), cam_i, cam_j)
         - AsignarPeticion((gas_i, pet_i), cam_i)
        """
        camiones_copy = self.copy()

        # MoverPeticion
        if isinstance(action, MoverPeticion):
            cam_org, viaje_i = action.pet_i
            org = camiones_copy.camiones[action.cam_i]
            dest = camiones_copy.camiones[action.cam_j]

            # validamos índices
            if viaje_i < 0 or viaje_i >= len(org.viajes):
                return camiones_copy
            trip = org.viajes[viaje_i]
            if trip[2] == -1:
                return camiones_copy

            # límite de la cisterna
            if dest.capacidad <= 0:
                return camiones_copy

            # eliminamos del camión origen
            org.viajes.pop(viaje_i)

            # añadimos al camión destino
            dest.viajes.append(trip)
            dest.capacidad -= 1
            # si la capacidad llega a cero, vuelve al centro
            if dest.capacidad == 0:
                volver_a_centro(dest)

            #  si la última entrada es un centro y no hay peticiones después del centro anterios,
            # eliminamos ese centro y disminuimos num_viajes
            # contar peticiones después del último centro 
            ult_centro = None
            for x in range(len(org.viajes)-1, -1, -1):
                if org.viajes[x][2] == -1:
                    ult_centro = x
                    break
            consec_peticiones = 0
            start_x = ult_centro + 1 if ult_centro is not None else 0
            for x in range(start_x, len(org.viajes)):
                if org.viajes[x][2] != -1:
                    consec_peticiones += 1
            if ult_centro is not None and consec_peticiones == 0:
                # eliminar el centro rebundante y modificar num_viajes si se puee
                if org.viajes and org.viajes[-1][2] == -1:
                    org.viajes.pop()
                    if org.num_viajes > 0:
                        org.num_viajes -= 1
                    org.capacidad = self.params.capacidad_maxima
            return camiones_copy

        # AsignarPeticion
        if isinstance(action, AsignarPeticion):
            (gas_i, pet_i) = action.pet_i
            camion = camiones_copy.camiones[action.cam_i]

            # validación 
            if camion.capacidad <= 0:
                return camiones_copy
            if gas_i < 0 or gas_i >= len(gasolineras.gasolineras):
                return camiones_copy
            gas = gasolineras.gasolineras[gas_i]
            if pet_i < 0 or pet_i >= len(gas.peticiones):
                return camiones_copy

            pet = gas.peticiones[pet_i]
            # añadir viaje
            camion.viajes.append((gas.cx, gas.cy, pet))
            camion.capacidad -= 1
            # si la capacidad llega a 0, devolvemos el camión al centro
            if camion.capacidad == 0:
                volver_a_centro(camion)
            return camiones_copy
        return camiones_copy
    
    def heuristic(self) -> float:
        pass



####################### Soluciones iniciales
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
                distancia_gasolinera = distancia((camion.viajes[-1][0], camion.viajes[-1][1]), (x, y))
                
                # también calculamos la distancia de la gasolinera hasta el centro de distribución porque el camión debe poder 
                # volver en cualquier momento sin sobrepasar el máximo de km
                distancia_vuelta = distancia((x, y), (camion.viajes[0][0], camion.viajes[0][1]))

                distancia_total = distancia_camion + distancia_gasolinera + distancia_vuelta
                if distancia_total > params.max_km:
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
    # los FALSE se ordenan antes que los TRUE en la función sort(), luego la parte de TRUE se ordena de mayor a menor
    peticiones.sort(key=lambda x: (x[0] != 0, -x[0]))

    # asignamos las peticiones a los camiones más cercanos
    for peticion, g in peticiones:
        x = gasolineras.gasolineras[g].cx
        y = gasolineras.gasolineras[g].cy

        # intentamos asignar la peticion al camión más cercano que pueda hacerla
        distancia_minima = float('inf')
        camion_seleccionado = None
        
        # miremos que los camiones tengan viajes disponibles
        # luego buscamos el camión más cercano
        # no podremos ahorrar cálculos de distancia como antes usando la propiedad de que los camiones sin viajes pueden 
        # servir al menos 2 peticiones sin problemas, porque necesitamos buscar el camión más cercano
        for camion in camiones.camiones:
          
            # Las distancias hasta la gasolinera se calculan con el penúltimo elemento de la lista de viajes
            # comprobamos si puede hacer más viajes y tiene capacidad
            # Igual que antes, comprobamos que el camión pueda volver al centro en cualquier momento
            if camion.num_viajes < params.max_viajes:
                distancia_gasolinera = distancia((camion.viajes[-2][0], camion.viajes[-2][1]), (x, y))
                distancia_volver = distancia((x, y), (camion.viajes[0][0], camion.viajes[0][1]))
                distancia_total = calcular_distancia_camion(camion) + distancia_gasolinera + distancia_volver

                # Buscamos el camión más cercano entre los que están disponibles
                if distancia_total <= params.max_km and distancia_gasolinera < distancia_minima:
                    distancia_minima = distancia_gasolinera
                    camion_seleccionado = camion

        # si hemos encontrado un camión adecuado, le asignamos la petición
        if camion_seleccionado is not None:
            camion_seleccionado.viajes.append((x, y, peticion))
            camion_seleccionado.capacidad -= 1

            # miramos que un camión no vaya a una gasolinera con el depósito vacío y que aún pueda hacer más viajes
            if camion_seleccionado.capacidad == 0:
                volver_a_centro(camion_seleccionado)
    
    # nos aseguramos de que todos los camiones terminen en el centro
    # tendrán distancia suficiente para volver
    for camion in camiones.camiones:
        if camion.viajes[-1][2] != -1:
            volver_a_centro(camion)
    
    return camiones

###########################




################################## Funciones auxiliares

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

# dist L1
def distancia(p1: tuple, p2: tuple) -> float:
    return abs(p2[0] - p1[0]) + abs(p2[1] - p1[1])

# funcion ganancias de la solucion inicial
# solo se llama una vez, para modificar las ganancias se usan otra funcion
def ganancias_inicial(camiones: Camiones) -> float:
    total_ganancias = 0
    for camion in camiones.camiones:
        for viaje in camion.viajes:
            if viaje[2] == 0:
                total_ganancias += 1000 * 1.02
            elif viaje[2] > 0:
                total_ganancias += 1000 * (1 - (2 ** viaje[2]) / 100)
    return total_ganancias

# modifica las ganancias a partir de las ganancias actuales
def ganancias_nueva(camiones: Camiones) -> float:
    pass

# coste por km de la solucion inicial
def coste_km_inicial(camiones: Camiones) -> float:
    total_coste = 0
    for camion in camiones.camiones:
        total_coste += calcular_distancia_camion(camion) * params.coste_km_max
    return total_coste

def coste_km_nueva(camiones: Camiones) -> float:
    total_coste = 0
    for camion in camiones.camiones:
        total_coste += calcular_distancia_camion(camion) * params.coste_km_max
    return total_coste

# coste de las peticiones no servidas en la solucion inicial
# definiremos como coste a las perdidas por dejar una peticion sin servir durante un día más
def coste_petno_inicial(camiones: Camiones) -> float:
    total_coste = 0
    for camion in camiones.camiones:
        for viaje in camion.viajes:
            if viaje[2] != -1:
                total_coste += (1000 * (1 - (2 ** viaje[2]) / 100)) - (1000 * (1 - (2 ** (viaje[2]+1)) / 100))
    return total_coste

def coste_petno_nueva(camiones: Camiones) -> float:
    pass
#######################################
