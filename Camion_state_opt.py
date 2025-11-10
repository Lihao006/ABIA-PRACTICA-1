from abia_Gasolina import *
from Camion_parameters import ProblemParameters
from Camion_operators import CamionOperators, MoverPeticion, AsignarPeticion, SwapPeticiones, EliminarPeticiones, MoverAntes, MoverDespues

from typing import Generator, List


params = ProblemParameters()
centros = CentrosDistribucion(params.num_centros, params.multiplicidad, params.seed)
gasolineras = Gasolineras(params.num_gasolineras, params.seed)

class Camion(object):

    def __init__(self, viajes: List[tuple]):
        self.capacidad = params.capacidad_maxima
        self.num_viajes = 0
        self.km_recorridos = 0.0

        self.viajes = viajes
        # Lista de ubicaciones de gasolineras asignadas y centros de distribucion que debe pasar
        # y un integer que indique num de dias de retraso y también identifica si es centro (valor = -1) o gasolinera (valor > -1).
        
        # Puede haber ubicaciones duplicadas que representen las dos peticiones de la misma gasolinera.
        # Las ubicaciones de centros pueden repetirse si el camion tiene que volver a un centro varias veces.
        
        # Lo hacemos asi para que se pueda permitir el servicio parcial (sirve una sola peticion), el servicio completo (completa las 2 peticiones),
        # distinguir el orden de visitas a gasolineras y centros para poder calcular la distancia recorrida.

        # El primer elemento de la lista de viajes es siempre el centro de distribucion inicial.
    
    # tenemos que definir un copy también para la clase Camion
    def copy(self) -> 'Camion':
            nuevo = Camion(self.viajes.copy())
            nuevo.capacidad = self.capacidad
            nuevo.num_viajes = self.num_viajes
            nuevo.km_recorridos = self.km_recorridos
            return nuevo

class Camiones(object):
    def __init__(self, params: ProblemParameters, camiones: List[Camion], lista_pet_no_asig: List[tuple] = [], ganancias: float = 0, coste_km: float = 0, coste_petno: float = 0):
        self.params = params
        self.camiones = camiones
        self.lista_pet_no_asig = lista_pet_no_asig
        self.ganancias = ganancias
        self.coste_km = coste_km
        self.coste_petno = coste_petno
        # Crear un camion por cada centro de distribucion si la lista de camiones está vacia
        # Si multiplicidad > 1, varios camiones estarán en la misma posicion inicial
        if len(self.camiones) == 0:
            for c in range(len(centros.centros)):
                camion = Camion([(centros.centros[c].cx, centros.centros[c].cy, -1)])
                for _ in range(params.multiplicidad):
                    self.camiones.append(camion)

    def copy(self) -> 'Camiones':
        # Afegim el copy per cada llista de camions
        camiones_copy = [camion.copy() for camion in self.camiones]
        lista_pet_no_asig_copy = [tuple(pet) for pet in self.lista_pet_no_asig]
        return Camiones(self.params, camiones_copy, lista_pet_no_asig_copy, self.ganancias, self.coste_km, self.coste_petno)

    def generate_actions(self) -> Generator[CamionOperators, None, None]:
        """
        Generar operadores:
        - MoverPeticion: mover una peticion, ya sea asignada o no, detrás de cualquier viaje de un camion (incluye a si mismo).
        - AsignarPeticion: asignar peticiones no asignadas a un camion
        """
        # MoverPeticion
        # para cada peticion no asignada en cada camion, puede ir a cualquier camion cumpliendo restricciones
        for pet in self.lista_pet_no_asig:
            for cam_j, camion_j in enumerate(self.camiones):
                for pos_j in range(len(camion_j.viajes) + 1):
                    # comprobamos que no se convierta en 3 peticiones consecutivas
                    # solo se podra insertar si:
                    # la pos_j es un centro y pos_j + 2 tambien es centro, aplicamos el operador para insetar depués de pos_j y pos_j + 1
                    if camion_j.viajes[pos_j][2] == -1:
                        if pos_j + 2 < len(camion_j.viajes) and camion_j.viajes[pos_j + 2][2] == -1:
                            # comprobamos km max
                            distancia_1_a_nueva_j = distancia((camion_j.viajes[pos_j + 1][0], camion_j.viajes[pos_j + 1][1]), (pet[0], pet[1]))
                            distancia_nueva_a_centro_j = distancia((pet[0], pet[1]), (camion_j.viajes[0][0], camion_j.viajes[0][1]))

                            distancia_1_a_centro = distancia((camion_j.viajes[pos_j + 1][0], camion_j.viajes[pos_j + 1][1]), (camion_j.viajes[0][0], camion_j.viajes[0][1]))

                            distancia_nueva_j = camion_j.km_recorridos + distancia_1_a_nueva_j + distancia_nueva_a_centro_j - distancia_1_a_centro
                            if distancia_nueva_j <= params.max_km:
                                # -1 indica que la peticion no esta asignada a ningun camion
                                yield MoverPeticion(pet, -1, cam_j, -1, pos_j + 1)
                                yield MoverPeticion(pet, -1, cam_j, -1, pos_j + 2)

                        # si estamos en el último centro, miramos si podemos anadir viajes
                        else:
                            if camion_j.num_viajes < params.max_viajes:
                                distancia_nueva_a_centro_j = distancia((pet[0], pet[1]), (camion_j.viajes[0][0], camion_j.viajes[0][1]))
                                # tiene que ir y volver
                                distancia_nueva_j = camion_j.km_recorridos + 2 * distancia_nueva_a_centro_j
                                if distancia_nueva_j <= params.max_km:
                                    yield MoverPeticion(pet, -1, cam_j, -1, pos_j + 1)

        # precaclular los indices de las peticiones por camion
        # por cada peticion asignada en cada camion, puede ir a cualquier otro camion cumpliendo restricciones
        # necesitaremos indentificar los camiones, por lo que usaremos enumerate
        for cam_i, camion_i in enumerate(self.camiones):
            for pet_i in range(len(camion_i.viajes)):
                pet = camion_i.viajes[pet_i]
                if pet[2] != -1:
                    # es una peticion
                    for cam_j, camion_j in enumerate(self.camiones):
                        for pos_j in range(len(camion_j.viajes) + 1):
                            if cam_j == cam_i and (pos_j == pet_i or pos_j == pet_i + 1):
                                # no mover dentro del mismo camion a la misma posicion
                                continue
                            # comprobamos que no se convierta en 3 peticiones consecutivas
                            # solo se podra insertar si:
                            # la pos_j es un centro y pos_j + 2 tambien es centro, aplicamos el operador para insetar depués de pos_j y pos_j + 1
                            if camion_j.viajes[pos_j][2] == -1:
                                if pos_j + 2 < len(camion_j.viajes) and camion_j.viajes[pos_j + 2][2] == -1:
                                    # comprobamos km max
                                    distancia_1_a_nueva_j = distancia((camion_j.viajes[pos_j + 1][0], camion_j.viajes[pos_j + 1][1]), (pet[0], pet[1]))
                                    distancia_nueva_a_centro_j = distancia((pet[0], pet[1]), (camion_j.viajes[0][0], camion_j.viajes[0][1]))

                                    distancia_1_a_centro = distancia((camion_j.viajes[pos_j + 1][0], camion_j.viajes[pos_j + 1][1]), (camion_j.viajes[0][0], camion_j.viajes[0][1]))

                                    distancia_nueva_j = camion_j.km_recorridos + distancia_1_a_nueva_j + distancia_nueva_a_centro_j - distancia_1_a_centro
                                    if distancia_nueva_j <= params.max_km:
                                        yield MoverPeticion(pet, cam_i, cam_j, pet_i, pos_j + 1)
                                        yield MoverPeticion(pet, cam_i, cam_j, pet_i, pos_j + 2)

                                # si estamos en el último centro, miramos si podemos anadir viajes
                                else:
                                    if camion_j.num_viajes < params.max_viajes:
                                        # si se puede, comprovamos max km
                                        distancia_centro_nueva_j = distancia((camion_j.viajes[0][0], camion_j.viajes[0][1]), (pet[0], pet[1]))
                                        # tiene que ir y volver
                                        distancia_nueva_j = camion_j.km_recorridos + 2 * distancia_centro_nueva_j
                                        if distancia_nueva_j <= params.max_km:
                                            # si se puede lo anadimos al final del todo, y en apply_actions forzamos volver al centro
                                            yield MoverPeticion(pet, cam_i, cam_j, pet_i, pos_j + 1)
                                            
                                

        # MoverAntes
        # de un camion, adelantar una peticion a una posicion de la lista de viajes
        for cam_i in range(len(self.camiones)):
            camion = self.camiones[cam_i]
            # el primer y el ultimo viaje son centros, no se pueden mover
            # si es la primera peticion con viaje_i == 1 de la lista de viajes, no lo podemos mover más adelante
            for viaje_i in range(2, len(camion.viajes) - 1):
                viaje = camion.viajes[viaje_i]
                if viaje[2] != -1:
                    # es una peticion
                    """
                    # miramos que la poscion anterior no sea un centro
                    
                    esta parte es absolutamente inutil, ya que no varia ni las ganancias ni los costes
                    simplemente se intercambia el orden de las peticiones entre dos viajes a centros, pero la distancia recorrida es la misma
                    
                    if camion.viajes[viaje_i - 1][2] != -1:
                        # para este caso, no variara la distancia recorrida porque partimos y terminamos en el mismo centro pasando por las mismas gasolineras, pero en otro orden,
                        # tampoco variara el numero de viajes
                        yield MoverAntes(cam_i, viaje_i, viaje_i - 1)
                    """
                    if camion.viajes[viaje_i - 1][2] == -1:
                        # si la anterior es centro movemos dos posiciones adelante, sin que haya 3 peticiones seguidas
                        if viaje_i - 2 >= 1:
                            # si el viaje_i - 3 es centro y viaje_i - 1 es centro, entonces viaje_i -2 tiene que ser peticion y podemos moverlo ahi detras
                            if camion.viajes[viaje_i - 3][2] == -1:
                                # comprobamos km max
                                distancia_1_a_centro = distancia((camion.viajes[viaje_i - 2][0], camion.viajes[viaje_i - 2][1]), (camion.viajes[0][0], camion.viajes[0][1]))
                                distancia_nueva_a_2 = distancia((viaje[0], viaje[1]), (camion.viajes[viaje_i + 1][0], camion.viajes[viaje_i + 1][1]))
                                
                                # esta distancia se mantiene, pero iria en sentido contrario, pero el valor es el mismo
                                # distancia_centro_a_nueva = distancia((camion.viajes[0][0], camion.viajes[0][1]), (viaje[0], viaje[1]))
                                
                                distancia_centro_a_2 = distancia((camion.viajes[0][0], camion.viajes[0][1]), (camion.viajes[viaje_i + 1][0], camion.viajes[viaje_i + 1][1]))
                                distancia_1_a_nueva = distancia((camion.viajes[viaje_i - 2][0], camion.viajes[viaje_i - 2][1]), (viaje[0], viaje[1]))
                                
                                distancia_nueva = camion.km_recorridos - distancia_1_a_centro + distancia_1_a_nueva - distancia_nueva_a_2 + distancia_centro_a_2
                                
                                if distancia_nueva <= self.params.max_km:
                                    # en apply_actions miramos si viaje_i + 1 es un centro para eliminarlo
                                    yield MoverAntes(cam_i, viaje, viaje_i, viaje_i - 2)

        # MoverDespues 
        # de un camion, retrasar una peticion a una posicion de la lista de viajes
        for cam_i in range(len(self.camiones)):
            camion = self.camiones[cam_i]
            # el primer y el ultimo viaje son centros, no se pueden mover
            # si es la ultima peticion con viaje_i == len(self.camiones[cam_i].viajes) - 2 de la lista de viajes, lo podemos mover más atras si podemos hacer más viajes, pero no puede estar solo
            for viaje_i in range(1, len(camion.viajes) - 1):
                viaje = camion.viajes[viaje_i]
                if viaje[2] != -1:
                    # es una peticion
                    if camion.viajes[viaje_i + 1][2] == -1:
                        # si la siguiente es centro movemos dos posiciones despues, sin que haya 3 peticiones seguidas
                        if viaje_i + 3 < len(camion.viajes):
                            # si el viaje_i + 3 es centro y viaje_i + 1 es centro, entonces viaje_i + 2 tiene que ser peticion y podemos moverlo ahi delante
                            if camion.viajes[viaje_i + 3][2] == -1:
                                # comprobamos km max
                                distancia_1_a_centro = distancia((camion.viajes[viaje_i + 2][0], camion.viajes[viaje_i + 2][1]), (camion.viajes[0][0], camion.viajes[0][1]))
                                distancia_nueva_a_2 = distancia((viaje[0], viaje[1]), (camion.viajes[viaje_i - 1][0], camion.viajes[viaje_i - 1][1]))
                                
                                # esta distancia se mantiene, pero iria en sentido contrario, pero el valor es el mismo
                                # distancia_centro_a_nueva = distancia((camion.viajes[0][0], camion.viajes[0][1]), (viaje[0], viaje[1]))
                                
                                distancia_centro_a_2 = distancia((camion.viajes[0][0], camion.viajes[0][1]), (camion.viajes[viaje_i - 1][0], camion.viajes[viaje_i - 1][1]))
                                distancia_1_a_nueva = distancia((camion.viajes[viaje_i + 2][0], camion.viajes[viaje_i + 2][1]), (viaje[0], viaje[1]))

                                distancia_nueva = camion.km_recorridos - distancia_1_a_centro + distancia_1_a_nueva - distancia_nueva_a_2 + distancia_centro_a_2
                                
                                if distancia_nueva <= self.params.max_km:
                                    # en apply_actions miramos si viaje_i - 1 es un centro para eliminarlo
                                    yield MoverDespues(cam_i, viaje, viaje_i, viaje_i + 2)
                        else:
                            # es la ultima peticion, miramos si podemos anadir viajes
                            if camion.num_viajes < self.params.max_viajes:
                                # que no sea una unica peticion en el viaje final
                                if camion.viajes[viaje_i - 1][2] != -1:
                                    # si se puede, comprovamos max km
                                    distancia_1_a_nueva = distancia((camion.viajes[viaje_i - 1][0], camion.viajes[viaje_i - 1][1]), (viaje[0], viaje[1]))
                                    distancia_centro_nueva = distancia((camion.viajes[0][0], camion.viajes[0][1]), (viaje[0], viaje[1]))

                                    distancia_1_centro = distancia((camion.viajes[viaje_i - 1][0], camion.viajes[viaje_i - 1][1]), (camion.viajes[0][0], camion.viajes[0][1]))
                                    
                                    # solo hay que sumar una vez la distancia al centro, ya que el camion ya vuelve al centro en su ultimo viaje
                                    distancia_nueva = camion.km_recorridos - distancia_1_a_nueva + distancia_centro_nueva + distancia_1_centro
                                    if distancia_nueva <= self.params.max_km:
                                        # si se puede lo anadimos al final del todo, y en apply_actions forzamos volver al centro
                                        yield MoverDespues(cam_i, viaje, viaje_i, len(camion.viajes))

        # AsignarPeticion
        for pet in self.lista_pet_no_asig:
            for camion in self.camiones:
                # tiene que tener recorridos y viajes disponibles
                assert camion.num_viajes <= self.params.max_viajes and camion.km_recorridos < self.params.max_km
                # el ultimo viaje es un centro
                for viaje in range(len(camion.viajes)):
                    if camion.viajes[viaje][2] == -1:
                        if viaje + 2 < len(camion.viajes):
                            if camion.viajes[viaje + 2][2] == -1:
                                # condicion: si asignamos la peticion, el camion debe poder realizar todos los demás viajes
                                # restamos la distancia original y le sumamos las dos nuevas distancias al km_recorridos del camion
                                distancia_1_a_nueva = distancia((camion.viajes[viaje][0], camion.viajes[viaje][1]), (pet[0], pet[1]))
                                distancia_nueva_a_centro = distancia((pet[0], pet[1]), (camion.viajes[0][0], camion.viajes[0][1]))
                                
                                distancia_1_a_centro = distancia((camion.viajes[viaje][0], camion.viajes[viaje][1]), (camion.viajes[0][0], camion.viajes[0][1])) 
                                
                                distancia_nueva = camion.km_recorridos + distancia_1_a_nueva + distancia_nueva_a_centro - distancia_1_a_centro
                                # si no excede el maximo de km, generamos el operador
                                if distancia_nueva < self.params.max_km:
                                    num_viaje = viaje + 1
                                    yield AsignarPeticion(pet, self.camiones.index(camion), num_viaje)
                       
                        # si estamos en el último viaje, que es un centro, y aun nos puede hacer viajes, miraremos si lo podemos anadir al final
                        elif camion.num_viajes != self.params.max_viajes:
                            # condicion: si asignamos la peticion, el camion debe poder realizar todos los demás viajes
                            distancia_1_a_nueva = distancia((camion.viajes[viaje][0], camion.viajes[viaje][1]), (pet[0], pet[1]))
                            distancia_nueva_a_centro = distancia((pet[0], pet[1]), (camion.viajes[0][0], camion.viajes[0][1]))
                            
                            distancia_1_a_centro = distancia((camion.viajes[viaje][0], camion.viajes[viaje][1]), (camion.viajes[0][0], camion.viajes[0][1]))
                            
                            distancia_nueva = camion.km_recorridos + distancia_1_a_nueva + distancia_nueva_a_centro - distancia_1_a_centro
                            # si no excede el maximo de km, generamos el operador
                            if distancia_nueva < self.params.max_km:
                                num_viaje = len(camion.viajes)
                                yield AsignarPeticion(pet, self.camiones.index(camion), num_viaje)

        #SwapPeticiones

        # para peticiones no asignadas, intercambiamos una peticion no asignada con una asignada en un camion
        for pet in self.lista_pet_no_asig:
            for cam_j, camion_j in enumerate(self.camiones):
                for pos_j in range(1, len(camion_j.viajes)):
                    if camion_j.viajes[pos_j][2] != -1:
                        # condicion: si cambiamos la peticion, el camion debe poder realizar todos los demás viajes
                        distancia_1_a_nueva_j = distancia((camion_j.viajes[pos_j - 1][0], camion_j.viajes[pos_j - 1][1]), (pet[0], pet[1]))
                        distancia_nueva_a_2_j = distancia((pet[0], pet[1]), (camion_j.viajes[pos_j + 1][0], camion_j.viajes[pos_j + 1][1]))
                        
                        distancia_1_a_vieja_j = distancia((camion_j.viajes[pos_j - 1][0], camion_j.viajes[pos_j - 1][1]), (camion_j.viajes[pos_j][0], camion_j.viajes[pos_j][1]))
                        distancia_vieja_a_2_j = distancia((camion_j.viajes[pos_j][0], camion_j.viajes[pos_j][1]), (camion_j.viajes[pos_j + 1][0], camion_j.viajes[pos_j + 1][1]))
                        
                        distancia_nueva_j = camion_j.km_recorridos + distancia_1_a_nueva_j + distancia_nueva_a_2_j - distancia_1_a_vieja_j - distancia_vieja_a_2_j

                        if distancia_nueva_j <= self.params.max_km:
                            # si no excede el maximo de km, generamos el operador
                            yield SwapPeticiones(-1, pos_j, -1, cam_j)

        # para peticiones asignadas en camiones, intercambiar peticiones entre camiones
        # iteramos sobre parejas de camiones, incluido el mismo camion
        for cam_i in range(len(self.camiones)):
            # evitamos repetir swaps ya realizados
            for cam_j in range(cam_i, len(self.camiones)):
                camion_i = self.camiones[cam_i]
                camion_j = self.camiones[cam_j]
                # recogemos el indice de la peticion para cada pareja de camion
                ind_i = [ind for ind, v in enumerate(camion_i.viajes) if v[2] != -1]
                ind_j = [ind for ind, v in enumerate(camion_j.viajes) if v[2] != -1]
                # vamos intercambiando las peticiones entre ambos camiones
                # no incumplirá el max_viajes ya que el numero de viajes no cambiará
                # solo hay que mirar que no sobrepase los km_max tras el swap
                for ii in ind_i:
                    for jj in ind_j:
                        if cam_i == cam_j and ii == jj:
                            # no swap dentro del mismo camion en la misma posicion
                            continue
                        # calculamos peticiones consecutivas desde el ultimo centro
                        pet_i = camion_i.viajes[ii]
                        pet_j = camion_j.viajes[jj]
                        
                        # condicion: si intercambiamos las peticiones, ambos camiones deben poder realizar todos los demás viajes
                        distancia_1_a_nueva_i = distancia((camion_i.viajes[ii-1][0], camion_i.viajes[ii-1][1]), (pet_j[0], pet_j[1]))
                        distancia_nueva_a_2_i = distancia((pet_j[0], pet_j[1]), (camion_i.viajes[ii+1][0], camion_i.viajes[ii+1][1]))
                        distancia_1_a_vieja_i = distancia((camion_i.viajes[ii-1][0], camion_i.viajes[ii-1][1]), (camion_i.viajes[ii][0], camion_i.viajes[ii][1]))
                        distancia_vieja_a_2_i = distancia((camion_i.viajes[ii][0], camion_i.viajes[ii][1]), (camion_i.viajes[ii+1][0], camion_i.viajes[ii+1][1]))
                        distancia_nueva_i = camion_i.km_recorridos + distancia_1_a_nueva_i + distancia_nueva_a_2_i - distancia_1_a_vieja_i - distancia_vieja_a_2_i

                        distancia_1_a_nueva_j = distancia((camion_j.viajes[jj-1][0], camion_j.viajes[jj-1][1]), (pet_i[0], pet_i[1]))
                        distancia_nueva_a_2_j = distancia((pet_i[0], pet_i[1]), (camion_j.viajes[jj+1][0], camion_j.viajes[jj+1][1]))
                        distancia_1_a_vieja_j = distancia((camion_j.viajes[jj-1][0], camion_j.viajes[jj-1][1]), (camion_j.viajes[jj][0], camion_j.viajes[jj][1]))
                        distancia_vieja_a_2_j = distancia((camion_j.viajes[jj][0], camion_j.viajes[jj][1]), (camion_j.viajes[jj+1][0], camion_j.viajes[jj+1][1]))
                        distancia_nueva_j = camion_j.km_recorridos + distancia_1_a_nueva_j + distancia_nueva_a_2_j - distancia_1_a_vieja_j - distancia_vieja_a_2_j

                        if distancia_nueva_i <= self.params.max_km and distancia_nueva_j <= self.params.max_km:
                        # si no excede el maximo de km, generamos el operador
                            yield SwapPeticiones(ii, jj, cam_i, cam_j)

        # Eliminar Peticiones
        # tiene que ser una peticion asignada
        for cam_i, camion in enumerate(self.camiones):
            for pet_i in range(len(camion.viajes)):
                if camion.viajes[pet_i][2] != -1:
                    yield EliminarPeticiones(camion.viajes[pet_i], cam_i)

    def apply_action(self, action: CamionOperators) -> 'Camiones':
        
        camiones_copy = self.copy()

        # MoverPeticion
        if isinstance(action, MoverPeticion):
            pet = action.pet_i
            pos_i = action.pos_i
            pos_j = action.pos_j
            
            if action.cam_i != action.cam_j:
                # para camiones diferentes o peticion no asignada
                if action.cam_i == -1:
                    # peticion no asignada a camion, la anadimos al camion destino
                    dest = camiones_copy.camiones[action.cam_j]

                    # calculamos primero el coste del camion dest
                    coste_cam_ant = camiones_copy.coste_km_1camion(dest)

                    if pos_j < len(dest.viajes):
                        # cuando no se inserta después del último viaje
                        
                        # anadimos al camion destino
                        dest.viajes.insert(pos_j, pet)
                        
                        # recalcular km recorridos por camion destino
                        distancia_1_a_nueva_j = distancia((dest.viajes[pos_j - 1][0], dest.viajes[pos_j - 1][1]), (pet[0], pet[1]))
                        distancia_nueva_a_2_j = distancia((pet[0], pet[1]), (dest.viajes[pos_j + 1][0], dest.viajes[pos_j + 1][1]))

                        distancia_1_a_2 = distancia((dest.viajes[pos_j - 1][0], dest.viajes[pos_j - 1][1]), (dest.viajes[pos_j + 1][0], dest.viajes[pos_j + 1][1]))

                        dest.km_recorridos = dest.km_recorridos + distancia_1_a_nueva_j + distancia_nueva_a_2_j - distancia_1_a_2

                    elif pos_j == len(dest.viajes):
                        # si la posicion donde inserir es despues del ultimo
                        dest.viajes.append(pet)
                        volver_a_centro(dest)
                        
                        # recalcular km recorridos por camion destino
                        distancia_centro_nueva_j = distancia((dest.viajes[0][0], dest.viajes[0][1]), (pet[0], pet[1]))
                        # tiene que ir y volver
                        dest.km_recorridos = dest.km_recorridos + 2 * distancia_centro_nueva_j

                    # actualizamos la lista de peticiones no asignadas
                    camiones_copy.lista_pet_no_asig.remove(pet)

                    # calculamos el nuevo coste por km del camion destino
                    coste_cam_nuevo = camiones_copy.coste_km_1camion(dest)

                    # modificamos los valores de costes y ganancias de la nueva solucion
                    camiones_copy.mod_coste_km(coste_cam_ant, coste_cam_nuevo)
                    camiones_copy.mod_ganancias(pet, 'asignar')
                    camiones_copy.mod_coste_petno(pet, 'asignar')

                    
                elif action.cam_j != -1:
                    # para camiones diferentes
                    org = camiones_copy.camiones[action.cam_i]
                    dest = camiones_copy.camiones[action.cam_j]

                    # antes de mover el viaje, guardamos los costes por km del camion origen y del camion destino
                    cost_org_ant = camiones_copy.coste_km_1camion(org)
                    cost_dest_ant = camiones_copy.coste_km_1camion(dest)

                    # miramos si es una peticion unica en un viaje en el camion origen
                    if org.viajes[pos_i - 1][2] == -1 and org.viajes[pos_i + 1][2] == -1:
                        # si es asi, eliminamos el centro anterior y el viaje de peticion
                        org.viajes.pop(pos_i - 1)
                        # como q hemos eliminado el centro anterior, el indice de la peticion baja en 1
                        org.viajes.pop(pos_i - 1)
                        org.num_viajes -= 1
                    else:
                        # si no es una peticion unica, solo eliminamos el viaje de peticion
                        org.viajes.pop(pos_i)

                    # recalcular km rec por el camion origen
                    distancia_1_elim_org = distancia((org.viajes[pos_i - 1][0], org.viajes[pos_i - 1][1]), (pet[0], pet[1]))
                    distancia_elim_2_org = distancia((pet[0], pet[1]), (org.viajes[pos_i + 1][0], org.viajes[pos_i + 1][1]))

                    distancia_1_2_org = distancia((org.viajes[pos_i - 1][0], org.viajes[pos_i - 1][1]), (org.viajes[pos_i + 1][0], org.viajes[pos_i + 1][1]))

                    org.km_recorridos = org.km_recorridos - distancia_1_elim_org - distancia_elim_2_org + distancia_1_2_org
                    
                    cost_org_desp = camiones_copy.coste_km_1camion(org)
                            
                    if pos_j < len(dest.viajes):
                        # cuando no se inserta después del último viaje

                        # anadimos al camion destino
                        dest.viajes.insert(pos_j, pet)

                        # recalcular km recorridos por camion destino
                        distancia_1_a_nueva_j = distancia((dest.viajes[pos_j - 1][0], dest.viajes[pos_j - 1][1]), (pet[0], pet[1]))
                        distancia_nueva_a_2_j = distancia((pet[0], pet[1]), (dest.viajes[pos_j + 1][0], dest.viajes[pos_j + 1][1]))

                        distancia_1_a_2 = distancia((dest.viajes[pos_j - 1][0], dest.viajes[pos_j - 1][1]), (dest.viajes[pos_j + 1][0], dest.viajes[pos_j + 1][1]))

                        distancia_nueva_j = dest.km_recorridos + distancia_1_a_nueva_j + distancia_nueva_a_2_j - distancia_1_a_2
                        dest.km_recorridos = distancia_nueva_j

                    elif pos_j == len(dest.viajes):
                        # si la posicion donde inserir es despues del ultimo
                        dest.viajes.append(pet)
                        volver_a_centro(dest)
                        
                        # recalcular km recorridos por camion destino
                        distancia_centro_nueva_j = distancia((dest.viajes[0][0], dest.viajes[0][1]), (pet[0], pet[1]))
                        # tiene que ir y volver
                        dest.km_recorridos = dest.km_recorridos + 2 * distancia_centro_nueva_j

                    # calculamos el nuevo coste por km del camion destino
                    cost_dest_desp = camiones_copy.coste_km_1camion(dest)

                    # las ganancias y el coste por peticiones no servidas no cambian al mover una peticion entre camiones
                    # modificamos los valores de costes y ganancias de la nueva solucion
                    camiones_copy.mod_coste_km(cost_org_ant + cost_dest_ant, cost_org_desp + cost_dest_desp)

            else:
                # para camiones iguales
                camion = camiones_copy.camiones[action.cam_i]

                # guardamos el coste por km antes
                coste_cam_ant = camiones_copy.coste_km_1camion(camion)

                # miramos si es una peticion unica en un viaje en el camion origen
                if camion.viajes[pos_i - 1][2] == -1 and camion.viajes[pos_i + 1][2] == -1:
                    # si es asi, eliminamos el centro anterior y el viaje de peticion
                    camion.viajes.pop(pos_i - 1)
                    # como q hemos eliminado el centro anterior, el indice de la peticion baja en 1
                    camion.viajes.pop(pos_i - 1)      
                    camion.num_viajes -= 1
                    # ajustamos la posicion j si es necesario
                    if pos_i < pos_j:
                        pos_j -= 2
                else:
                    # si no es una peticion unica, solo eliminamos el viaje de peticion
                    camion.viajes.pop(pos_i)
                    # ajustamos la posicion j si es necesario
                    if pos_i < pos_j:
                        pos_j -= 1

                # eliminamos la peticion de su posicion original
                camion.viajes.pop(pos_i)

                # dist que lo usaremos despues
                distancia_1_elim = distancia((camion.viajes[pos_i - 1][0], camion.viajes[pos_i - 1][1]), (pet[0], pet[1]))
                distancia_elim_2 = distancia((pet[0], pet[1]), (camion.viajes[pos_i + 1][0], camion.viajes[pos_i + 1][1]))

                distancia_1_2 = distancia((camion.viajes[pos_i - 1][0], camion.viajes[pos_i - 1][1]), (camion.viajes[pos_i + 1][0], camion.viajes[pos_i + 1][1]))


                if pos_j < len(camion.viajes):
                    # cuando no se inserta después del último viaje
                    # insertamos la peticion en la nueva posicion
                    camion.viajes.insert(pos_i, pet)

                    # recalcular km recorridos del camion
                    distancia_3_a_nueva = distancia((camion.viajes[pos_j - 1][0], camion.viajes[pos_j - 1][1]), (pet[0], pet[1]))
                    distancia_nueva_a_4 = distancia((pet[0], pet[1]), (camion.viajes[pos_j + 1][0], camion.viajes[pos_j + 1][1]))

                    distancia_3_4 = distancia((camion.viajes[pos_j - 1][0], camion.viajes[pos_j - 1][1]), (camion.viajes[pos_j + 1][0], camion.viajes[pos_j + 1][1]))

                    camion.km_recorridos = camion.km_recorridos - distancia_1_elim - distancia_elim_2 + distancia_1_2 + distancia_3_a_nueva + distancia_nueva_a_4 - distancia_3_4

                elif pos_j == len(camion.viajes):
                    # si la posicion donde inserir es despues del ultimo
                    camion.viajes.append(pet)
                    volver_a_centro(camion)

                    # recalcular km recorridos del camion
                    distancia_centro_nueva= distancia((camion.viajes[0][0], camion.viajes[0][1]), (pet[0], pet[1]))
                    
                    # tiene que ir y volver, menos las distancias eliminadas y la nueva 
                    camion.km_recorridos = camion.km_recorridos - distancia_1_elim - distancia_elim_2 + distancia_1_2 + 2 * distancia_centro_nueva

            # calculamos el nuevo coste por km del camion
            coste_cam_desp = camiones_copy.coste_km_1camion(camion)

            # mod coste km
            camiones_copy.mod_coste_km(coste_cam_ant, coste_cam_desp)

            # las ganancias y el coste por peticiones no servidas no cambian al mover una peticion entre camiones
            return camiones_copy

        # MoverAntes: adelantar una peticion dentro del mismo camion (no anade viajes pero puede reducirlos)
        if isinstance(action, MoverAntes):
            cam_i = action.cam_i
            pet = action.pet_i
            pos_i = action.pos_i
            pos_j = action.pos_j

            camion = camiones_copy.camiones[cam_i]

            # guardamos coste km antes
            coste_cam_ant = camiones_copy.coste_km_1camion(camion)

            # insertamos la peticion en la nueva posicion
            camion.viajes.insert(pos_j, pet)

            # calc las distancias q usaremos despues
            distancia_1_elim = distancia((camion.viajes[pos_i - 1][0], camion.viajes[pos_i - 1][1]), (pet[0], pet[1]))
            distancia_elim_2 = distancia((pet[0], pet[1]), (camion.viajes[pos_i + 1][0], camion.viajes[pos_i + 1][1]))
            distancia_1_2 = distancia((camion.viajes[pos_i - 1][0], camion.viajes[pos_i - 1][1]), (camion.viajes[pos_i + 1][0], camion.viajes[pos_i + 1][1]))
            
            if camion.viajes[pos_i + 1][2] == -1:
                camion.viajes.pop(pos_i)
                # eliminar el centro siguiente redundante
                camion.viajes.pop(pos_i)
                camion.num_viajes -= 1
                # ajustamos la posicion j si es necesario
                if pos_i < pos_j:
                    pos_j -= 2
            else:
                camion.viajes.pop(pos_i)
                # ajustamos la posicion j si es necesario
                if pos_i < pos_j:
                    pos_j -= 1

            # Insertamos la peticion en la nueva posicion
            camion.viajes.insert(pos_j, pet)
            
            # recalculamos los km_recorridos del camion
            distancia_3_a_nueva = distancia((camion.viajes[pos_j - 1][0], camion.viajes[pos_j - 1][1]), (pet[0], pet[1]))
            distancia_nueva_a_4 = distancia((pet[0], pet[1]), (camion.viajes[pos_j + 1][0], camion.viajes[pos_j + 1][1]))
            distancia_3_4 = distancia((camion.viajes[pos_j - 1][0], camion.viajes[pos_j - 1][1]), (camion.viajes[pos_j + 1][0], camion.viajes[pos_j + 1][1]))
            
            camion.km_recorridos = camion.km_recorridos - distancia_1_elim - distancia_elim_2 + distancia_1_2 + distancia_3_a_nueva + distancia_nueva_a_4 - distancia_3_4

            # calculamos nuevo coste por km
            coste_cam_desp = camiones_copy.coste_km_1camion(camion)

            camiones_copy.mod_coste_km(coste_cam_ant, coste_cam_desp)
            # no cambiamos ganancias ni coste por peticiones no servidas

            return camiones_copy

        # MoverDespues: retrasar una peticion dentro del mismo camion (puede anadir viajes)
        if isinstance(action, MoverDespues):
            cam_i = action.cam_i
            pos_i = action.pos_i
            pet = action.pet_i
            pos_j = action.pos_j

            camion = camiones_copy.camiones[cam_i]

            # guardamos coste km antes
            coste_cam_ant = camiones_copy.coste_km_1camion(camion)

            if camion.viajes[pos_i + 1][2] == -1:
                camion.viajes.pop(pos_i)
                # eliminar el centro siguiente redundante
                camion.viajes.pop(pos_i)
                camion.num_viajes -= 1
                # ajustamos la posicion j si es necesario
                if pos_i < pos_j:
                    pos_j -= 2
            else:
                camion.viajes.pop(pos_i)
                # ajustamos la posicion j si es necesario
                if pos_i < pos_j:
                    pos_j -= 1

            # Insertamos la peticion en la nueva posicion
            camion.viajes.insert(pos_j, pet)

            # calc las distancias q usaremos despues
            distancia_1_elim = distancia((camion.viajes[pos_i - 1][0], camion.viajes[pos_i - 1][1]), (pet[0], pet[1]))
            distancia_elim_2 = distancia((pet[0], pet[1]), (camion.viajes[pos_i + 1][0], camion.viajes[pos_i + 1][1]))
            distancia_1_2 = distancia((camion.viajes[pos_i - 1][0], camion.viajes[pos_i - 1][1]), (camion.viajes[pos_i + 1][0], camion.viajes[pos_i + 1][1]))
            
            distancia

            # calculamos nuevo coste por km
            coste_cam_desp = camiones_copy.coste_km_1camion(camion)

            camiones_copy.mod_coste_km(coste_cam_ant, coste_cam_desp)
            return camiones_copy

        # AsignarPeticion
        if isinstance(action, AsignarPeticion):
            camion = camiones_copy.camiones[action.cam_i]
            pet = action.pet_i
            num_viaje = action.num_viaje

            # antes de asignar la peticion, guardamos el coste por km del camion
            coste_cam_ant = camiones_copy.coste_km_1camion(camion)
            
            if num_viaje < len(camion.viajes):
                # anadir viaje en la posición indicada
                camion.viajes.insert(num_viaje, pet)
            elif num_viaje == len(camion.viajes):
                # si se lo anadimos en la ultima posicion, tiene que volver al centro
                camion.viajes.append(pet)
                camion.num_viajes += 1
                volver_a_centro(camion)

            # recalculamos los km_recorridos del camion
            calcular_distancia_camion(camion)

            # calculamos el nuevo coste por km del camion
            coste_cam_desp = camiones_copy.coste_km_1camion(camion)

            # modificamos las listas de peticiones asignadas y no asignadas
            camiones_copy.lista_pet_no_asig.remove(action.pet_i)

            # modificamos los valores de costes y ganancias de la nueva solucion
            camiones_copy.mod_coste_km(coste_cam_ant, coste_cam_desp)
            camiones_copy.mod_ganancias(action.pet_i, "asignar")
            camiones_copy.mod_coste_petno(action.pet_i, "asignar")

            return camiones_copy
        
        #SwapPeticiones
        if isinstance(action, SwapPeticiones):
            ii = action.pet_i
            jj = action.pet_j
            cam_i = action.cam_i
            cam_j = action.cam_j

            if cam_i != cam_j:
                # si son camiones diferentes
                org = camiones_copy.camiones[cam_i]
                dest = camiones_copy.camiones[cam_j]
        
                # calculamos los costes por km antes del swap
                cost_org_ant = camiones_copy.coste_km_1camion(org)
                cost_dest_ant = camiones_copy.coste_km_1camion(dest)

                # extraemos viajes antes del cambio
                pet_i = org.viajes[ii]
                pet_j = dest.viajes[jj]

                # eliminamos del origen y del destino
                org.viajes.pop(ii)
                dest.viajes.pop(jj)

                # anadimos los viajes intercambiados
                org.viajes.insert(ii, pet_j)
                dest.viajes.insert(jj, pet_i)

                # Recalcular km para ambos camiones
                # como que ahora los centros no interfieren en esta operacion, podemos modificar solo las distancias afectadas por el swap
                # y asi evitamos recalcular toda la distancia del camion
                distancia_1_a_nueva_org = distancia((org.viajes[ii-1][0], org.viajes[ii-1][1]), (pet_j[0], pet_j[1]))
                distancia_nueva_a_2_org = distancia((pet_j[0], pet_j[1]), (org.viajes[ii+1][0], org.viajes[ii+1][1]))
                
                distancia_1_a_vieja_org = distancia((org.viajes[ii-1][0], org.viajes[ii-1][1]), (org.viajes[ii][0], org.viajes[ii][1]))
                distancia_vieja_a_2_org = distancia((org.viajes[ii][0], org.viajes[ii][1]), (org.viajes[ii+1][0], org.viajes[ii+1][1]))
                
                org.dist_nueva(distancia_1_a_nueva_org + distancia_nueva_a_2_org - distancia_1_a_vieja_org - distancia_vieja_a_2_org)

                distancia_1_a_nueva_dest = distancia((dest.viajes[jj-1][0], dest.viajes[jj-1][1]), (pet_i[0], pet_i[1]))
                distancia_nueva_a_2_dest = distancia((pet_i[0], pet_i[1]), (dest.viajes[jj+1][0], dest.viajes[jj+1][1]))
                
                distancia_1_a_vieja_dest = distancia((dest.viajes[jj-1][0], dest.viajes[jj-1][1]), (dest.viajes[jj][0], dest.viajes[jj][1]))
                distancia_vieja_a_2_dest = distancia((dest.viajes[jj][0], dest.viajes[jj][1]), (dest.viajes[jj+1][0], dest.viajes[jj+1][1]))
                
                dest.dist_nueva(distancia_1_a_nueva_dest + distancia_nueva_a_2_dest - distancia_1_a_vieja_dest - distancia_vieja_a_2_dest)
                
                # calculamos los nuevos costes por km de ambos camiones
                cost_org_desp = camiones_copy.coste_km_1camion(org)
                cost_dest_desp = camiones_copy.coste_km_1camion(dest)

                # modificamos los valores de costes y ganancias de la nueva solucion
                camiones_copy.mod_coste_km(cost_org_ant + cost_dest_ant, cost_org_desp + cost_dest_desp)
            
            else:
                # si son el mismo camion
                camion = camiones_copy.camiones[cam_i]

                # antes del swap, guardamos el coste por km del camion
                coste_cam_ant = camiones_copy.coste_km_1camion(camion)

                # extraemos los viajes antes del cambio
                pet_i = camion.viajes[ii]
                pet_j = camion.viajes[jj]

                # realizamos el swap
                camion.viajes[ii] = pet_j
                camion.viajes[jj] = pet_i

                # Recalcular km para el camion
                distancia_1_a_nueva_i = distancia((camion.viajes[ii-1][0], camion.viajes[ii-1][1]), (pet_j[0], pet_j[1]))
                distancia_nueva_a_2_i = distancia((pet_j[0], pet_j[1]), (camion.viajes[ii+1][0], camion.viajes[ii+1][1]))
                
                distancia_1_a_vieja_i = distancia((camion.viajes[ii-1][0], camion.viajes[ii-1][1]), (camion.viajes[ii][0], camion.viajes[ii][1]))
                distancia_vieja_a_2_i = distancia((camion.viajes[ii][0], camion.viajes[ii][1]), (camion.viajes[ii+1][0], camion.viajes[ii+1][1]))
                
                distancia_1_a_nueva_j = distancia((camion.viajes[jj-1][0], camion.viajes[jj-1][1]), (pet_i[0], pet_i[1]))
                distancia_nueva_a_2_j = distancia((pet_i[0], pet_i[1]), (camion.viajes[jj+1][0], camion.viajes[jj+1][1]))
                
                distancia_1_a_vieja_j = distancia((camion.viajes[jj-1][0], camion.viajes[jj-1][1]), (camion.viajes[jj][0], camion.viajes[jj][1]))
                distancia_vieja_a_2_j = distancia((camion.viajes[jj][0], camion.viajes[jj][1]), (camion.viajes[jj+1][0], camion.viajes[jj+1][1]))
                
                nueva_distancia = camion.km_recorridos + distancia_1_a_nueva_i + distancia_nueva_a_2_i - distancia_1_a_vieja_i - distancia_vieja_a_2_i + distancia_1_a_nueva_j + distancia_nueva_a_2_j - distancia_1_a_vieja_j - distancia_vieja_a_2_j
                camion.dist_nueva(nueva_distancia)

                # calculamos el nuevo coste por km del camion
                coste_cam_desp = camiones_copy.coste_km_1camion(camion)

                # modificamos los valores de costes y ganancias de la nueva solucion
                camiones_copy.mod_coste_km(coste_cam_ant, coste_cam_desp)
            
            # las ganancias y el coste por peticiones no servidas no cambian al intercambiar una peticion entre camiones

            return camiones_copy
        
        # EliminarPeticiones
        if isinstance(action, EliminarPeticiones):
            pet = action.pet_i
            camion = camiones_copy.camiones[action.cam_i]

            # antes de eliminar la peticion, guardamos el coste por km del camion
            coste_cam_ant = camiones_copy.coste_km_1camion(camion)

            # eliminamos la peticion del camion
            for viaje in range(len(camion.viajes)):
                if camion.viajes[viaje] == pet:
                    if camion.viajes[viaje -1][2] == - 1 and camion.viajes[viaje +1][2] == -1:
                        #miramos si hay que quitar centros redundantes y recalculamos num_viajes
                        # si la peticion esta entre dos centros, eliminamos tambien uno de los centros para evitar redundancia
                        camion.viajes.remove(camion.viajes[viaje -1])
                        # el indice se reduce en 1 tras eliminar el centro anterior
                        camion.viajes.remove(camion.viajes[viaje -1])
                    else:
                        # si no, simplemente eliminamos la peticion
                        camion.viajes.remove(camion.viajes[viaje])
                    break
            
            # recalculamos los km_recorridos del camion
            calcular_distancia_camion(camion)

            # calculamos el nuevo coste por km del camion
            coste_cam_desp = camiones_copy.coste_km_1camion(camion)
            
            # modificamos la lista de peticiones asignadas y no asignadas
            camiones_copy.lista_pet_no_asig.append(pet)
            
            # modificamos los valores de costes y ganancias de la nueva solucion
            camiones_copy.mod_coste_km(coste_cam_ant, coste_cam_desp)
            camiones_copy.mod_ganancias(pet, "eliminar")
            camiones_copy.mod_coste_petno(pet, "eliminar")

            return camiones_copy

        return camiones_copy
    
    def ganancias_actual(self) -> float:
        return self.ganancias
    
    def coste_km_actual(self) -> float:
        return self.coste_km

    def coste_petno_actual(self) -> float:
        return self.coste_petno
    
    def heuristic(self) -> float:
        return self.ganancias - self.coste_km - self.coste_petno

    # funcion ganancias de la solucion inicial
    # solo se llama una vez, para modificar las ganancias se usa otra funcion de menor coste computacional
    def ganancias_inicial(self) -> float:
        total_ganancias = 0
        for camion in self.camiones:
            for peticion in camion.viajes:
                if peticion[2] == 0:
                    total_ganancias += 1000 * 1.02
                elif peticion[2] > 0:
                    total_ganancias += 1000 * (1 - (2 ** peticion[2]) / 100)
        self.ganancias = total_ganancias
        return self.ganancias

    # modifica las ganancias a partir de las ganancias actuales
    # la unica manera de variar las ganancias es asignando o quitando peticiones
    # por tanto las ganancias solo dependen de las peticiones, no hace nos hace falta saber el camion
    # para saber si se asigna o elimina una peticion pondremos un string operacion
    def mod_ganancias(self, peticion: tuple, operacion: str) -> float:
        if operacion == "asignar":
            if peticion[2] == 0:
                self.ganancias += self.params.valor_deposito * 1.02
            elif peticion[2] > 0:
                self.ganancias += self.params.valor_deposito * (1 - (2 ** peticion[2]) / 100)
        elif operacion == "eliminar":
            if peticion[2] == 0:
                self.ganancias -= self.params.valor_deposito * 1.02
            elif peticion[2] > 0:
                self.ganancias -= self.params.valor_deposito * (1 - (2 ** peticion[2]) / 100)
        return self.ganancias

    # coste por km de la solucion inicial
    def coste_km_inicial(self) -> float:
        total_coste = 0
        for camion in self.camiones:
            total_coste += calcular_distancia_camion(camion) * self.params.coste_km_max
        self.coste_km = total_coste
        return self.coste_km

    # el coste por km se modifica cuando se altera la lista de viajes de un camion, 
    # ya sea anadiendo, eliminando o moviendo peticiones. Solo necesitamos saber el camion modificado
    # necesitamos la distancia anterior y la nueva distancia de este camion
    def coste_km_1camion(self, camion: Camion) -> float:
        return camion.km_recorridos * self.params.coste_km_max

    # restamos el coste anterior de ese camion y sumamos el nuevo coste
    def mod_coste_km(self, coste_cam_ant: float, cost_cam_nue: float) -> float:
        # coste_cam_ant may be the sum of previous affected trucks' costs;
        # subtract the old cost(s) and add the new cost(s)
        self.coste_km = self.coste_km - coste_cam_ant + cost_cam_nue
        return self.coste_km

    # coste de las peticiones no servidas en la solucion inicial
    # definiremos como coste a las perdidas por dejar una peticion sin servir durante un dia más
    # necesitamos saber que peticiones se han asignado y cuales no
    def coste_petno_inicial(self) -> float:
        coste = 0
        # de las que no estan servidas, calculamos el coste
        for peticion in self.lista_pet_no_asig:
            if peticion[2] == 0:
                coste += (self.params.valor_deposito * 1.02) - (self.params.valor_deposito * 0.98)
            elif peticion[2] > 0:
                coste += (self.params.valor_deposito * (1 - (2 ** peticion[2]) / 100)) - (self.params.valor_deposito * (1 - (2 ** (peticion[2]+1)) / 100))
        self.coste_petno = coste
        return self.coste_petno

    # la unica manera de modificar el coste de peticiones no servidas es asignando o eliminando peticiones
    # por tanto solo necesitamos saber la peticion asignada o eliminada
    # si se asigna una peticion, el coste disminuye
    # si se elimina una peticion, el coste aumenta
    def mod_coste_petno(self, peticion: tuple, operacion: str) -> float:
        if operacion == "asignar":
            if peticion[2] == 0:
                self.coste_petno -= (self.params.valor_deposito * 1.02) - (self.params.valor_deposito * 0.98)
            elif peticion[2] > 0:
                self.coste_petno -= (self.params.valor_deposito * (1 - (2 ** peticion[2]) / 100)) - (self.params.valor_deposito * (1 - (2 ** (peticion[2]+1)) / 100))
        elif operacion == "eliminar":
            if peticion[2] == 0:
                self.coste_petno += (self.params.valor_deposito * 1.02) - (self.params.valor_deposito * 0.98)
            elif peticion[2] > 0:
                self.coste_petno += (self.params.valor_deposito * (1 - (2 ** peticion[2]) / 100)) - (self.params.valor_deposito * (1 - (2 ** (peticion[2]+1)) / 100))
        return self.coste_petno


    # y la lista de peticiones no asignadas
    def lista_pet_no_asig_inicial(self) -> List[tuple]:
        lista_no_asig = []
        lista_pet_asig = []
        for camion in self.camiones:
            for peticion in camion.viajes:
                lista_pet_asig.append(peticion)

        for gasolinera in gasolineras.gasolineras:
            for peticion in gasolinera.peticiones:
                if peticion not in lista_pet_asig:
                    lista_no_asig.append((gasolinera.cx, gasolinera.cy, peticion))
        self.lista_pet_no_asig = lista_no_asig
        return self.lista_pet_no_asig
    

####################### Soluciones iniciales
def generar_sol_inicial_vacia(params: ProblemParameters) -> Camiones:
    camiones = Camiones(params, [])
    # solo hace falta calc la lista de pet no asignadas
    camiones.lista_pet_no_asig_inicial()
    # calculamos los valores iniciales
    camiones.coste_km_inicial()
    camiones.ganancias_inicial()
    camiones.coste_petno_inicial()
    return camiones


def generar_sol_inicial(params: ProblemParameters) -> Camiones:
    camiones = Camiones(params, [])
    c = 0
    g = 0
    camion = camiones.camiones[c]

    # hacemos un bucle para cada camion
    while c < len(camiones.camiones):
        x = gasolineras.gasolineras[g].cx
        y = gasolineras.gasolineras[g].cy
        
        # Asignamos las peticiones de la gasolinera g al camion c
        for p in range(len(gasolineras.gasolineras[g].peticiones)):
            
            # si el camion ha llegado al máximo de viajes, no hace falta calcular distancias
            # podemos estar seguros de que si el camion no puede hacer más viajes, ya está en el centro
            if camion.num_viajes == params.max_viajes or camion.km_recorridos == params.max_km:
                # pasamos al siguiente camion
                c += 1
                # comprobamos que no nos salgamos del rango de camiones
                if c >= len(camiones.camiones):
                    break
                camion = camiones.camiones[c]

            # esto servira para ahorrarnos un calculo de distancia para cada camion
            # ya hemos comprobado que un camion puede hacer al menos 2 peticiones o 1 viaje sin problemas
            if camion.num_viajes != 0:
                # distancia acumulada del camion hasta el momento
                distancia_camion = calcular_distancia_camion(camion)
                
                # distancia desde la ultima posicion del camion hasta la gasolinera
                distancia_gasolinera = distancia((camion.viajes[-1][0], camion.viajes[-1][1]), (x, y))
                
                # también calculamos la distancia de la gasolinera hasta el centro de distribucion porque el camion debe poder 
                # volver en cualquier momento sin sobrepasar el máximo de km
                distancia_vuelta = distancia((x, y), (camion.viajes[0][0], camion.viajes[0][1]))

                distancia_total = distancia_camion + distancia_gasolinera + distancia_vuelta
                if distancia_total > params.max_km:
                    # si este camion no puede más, lo enviamos de vuelta al centro
                    # estamos seguros de que tiene distancia suficiente para volver porque sino deberia haberse detenido en la iteracion anterior
                    volver_a_centro(camion)
                    # pasamos al siguiente camion
                    c += 1
                    # comprobamos que no nos salgamos del rango de camiones
                    if c >= len(camiones.camiones):
                        break
                    camion = camiones.camiones[c]

            camiones.camiones[c].viajes.append((x, y, gasolineras.gasolineras[g].peticiones[p]))
            camion.capacidad -= 1

            # miramos que un camion no vaya a una gasolinera con el deposito vacio y que aun pueda hacer más viajes
            # ya habremos comprobado que el camion puede volver al centro sin sobrepasar el máximo de km
            if camion.capacidad == 0:
                volver_a_centro(camion)
        
        # pasamos a la siguiente gasolinera
        g += 1

    # calc la lista de peticiones asignadas y no asignadas
    camiones.lista_pet_no_asig_inicial()
    
    # calculamos los valores iniciales
    camiones.coste_km_inicial()
    camiones.ganancias_inicial()
    camiones.coste_petno_inicial()
    
    return camiones
          

def generar_sol_inicial_greedy(params: ProblemParameters) -> Camiones:
    camiones = Camiones(params, [])
    peticiones = []

    # creamos una lista con todas las peticiones de las gasolineras y su indice de gasolinera
    for g in range(len(gasolineras.gasolineras)):
        for p in range(len(gasolineras.gasolineras[g].peticiones)):
            peticiones.append((gasolineras.gasolineras[g].peticiones[p], g))

    # ordenamos las peticiones de mayor a menor numero de dias de retraso, excepto las de 0 dias, que iran al principio
    # los FALSE se ordenan antes que los TRUE en la funcion sort(), luego la parte de TRUE se ordena de mayor a menor
    peticiones.sort(key=lambda x: (x[0] != 0, -x[0]))

    # asignamos las peticiones a los camiones más cercanos
    for peticion, g in peticiones:
        x = gasolineras.gasolineras[g].cx
        y = gasolineras.gasolineras[g].cy

        # intentamos asignar la peticion al camion más cercano que pueda hacerla
        distancia_minima = float('inf')
        camion_seleccionado = None
        
        # miremos que los camiones tengan viajes disponibles
        # luego buscamos el camion más cercano
        # no podremos ahorrar cálculos de distancia como antes usando la propiedad de que los camiones sin viajes pueden 
        # servir al menos 2 peticiones sin problemas, porque necesitamos buscar el camion más cercano
        for camion in camiones.camiones:
          
            # Las distancias hasta la gasolinera se calculan con el penultimo elemento de la lista de viajes
            # comprobamos si puede hacer más viajes y tiene capacidad
            # Igual que antes, comprobamos que el camion pueda volver al centro en cualquier momento
            if camion.num_viajes < params.max_viajes:
                # if camion has less than 2 recorded positions, use the last position as the departure point
                if len(camion.viajes) >= 2:
                    pos_salida = (camion.viajes[-2][0], camion.viajes[-2][1])
                else:
                    pos_salida = (camion.viajes[-1][0], camion.viajes[-1][1])
                distancia_gasolinera = distancia(pos_salida, (x, y))
                distancia_volver = distancia((x, y), (camion.viajes[0][0], camion.viajes[0][1]))
                distancia_total = calcular_distancia_camion(camion) + distancia_gasolinera + distancia_volver

                # Buscamos el camion más cercano entre los que están disponibles
                if distancia_total <= params.max_km and distancia_gasolinera < distancia_minima:
                    distancia_minima = distancia_gasolinera
                    camion_seleccionado = camion

        # si hemos encontrado un camion adecuado, le asignamos la peticion
        if camion_seleccionado is not None:
            camion_seleccionado.viajes.append((x, y, peticion))
            camion_seleccionado.capacidad -= 1

            # miramos que un camion no vaya a una gasolinera con el deposito vacio y que aun pueda hacer más viajes
            if camion_seleccionado.capacidad == 0:
                volver_a_centro(camion_seleccionado)
    
    # nos aseguramos de que todos los camiones terminen en el centro
    # tendrán distancia suficiente para volver
    for camion in camiones.camiones:
        if camion.viajes[-1][2] != -1:
            volver_a_centro(camion)

    # calc la lista de peticiones asignadas y no asignadas
    camiones.lista_pet_no_asig_inicial()
    
    # calculamos los valores iniciales
    camiones.coste_km_inicial()
    camiones.ganancias_inicial()
    camiones.coste_petno_inicial()

    return camiones

###########################




################################## Funciones auxiliares

def volver_a_centro(camion: Camion) -> None:
    # Anadir un viaje de vuelta al centro de distribucion, las restricciones se comprueban antes de llamar a esta funcion
    centro_origen = camion.viajes[0]
    camion.viajes.append((centro_origen[0], centro_origen[1], -1))
    camion.num_viajes += 1
    camion.capacidad = params.capacidad_maxima

# funcion para calcular la distancia total recorrida por un solo camion
# tmb modifica el atributo km_recorridos del camion
def calcular_distancia_camion(camion: Camion) -> float:
    total_distance = 0
    for i in range(1, len(camion.viajes)):
        total_distance += distancia(camion.viajes[i-1][:2], camion.viajes[i][:2])
    assert total_distance >= 0 and total_distance <= params.max_km
    camion.km_recorridos = total_distance
    return total_distance

# dist L1
def distancia(p1: tuple, p2: tuple) -> float:
    return abs(p2[0] - p1[0]) + abs(p2[1] - p1[1])

def limpiar_centros_redundantes(camion: Camion, params: ProblemParameters) -> None:
    # eliminar centros finales redundantes (si no hay peticiones después del centro anterior)
    while camion.viajes and camion.viajes[-1][2] == -1:
        # buscar penultimo centro
        penult = None
        for x in range(len(camion.viajes)-2, -1, -1):
            if camion.viajes[x][2] == -1:
                penult = x
                break
        # comprobar si hay peticiones entre penult+1 y el penultimo elemento (excluyendo ultimo centro)
        start = penult + 1 if penult is not None else 0
        hay_peticiones = any(v[2] != -1 for v in camion.viajes[start:len(camion.viajes)-1])
        if not hay_peticiones:
            camion.viajes.pop()
        else:
            break

    # Recalcular num_viajes: numero de retornos al centro (excluyendo centro inicial)
    total_centros = sum(1 for v in camion.viajes if v[2] == -1)
    camion.num_viajes = max(0, total_centros - 1)

    # Recalcular capacidad segun peticiones consecutivas desde el ultimo centro
    ult_centro = None
    for id in range(len(camion.viajes)-1, -1, -1):
        if camion.viajes[id][2] == -1:
            ult_centro = id
            break
    consec = 0
    start = ult_centro + 1 if ult_centro is not None else 0
    for v in camion.viajes[start:]:
        if v[2] != -1:
            consec += 1
    camion.capacidad = params.capacidad_maxima - consec
    if camion.capacidad < 0:
        camion.capacidad = 0


#######################################
