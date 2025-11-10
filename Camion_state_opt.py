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
        
        # Lo hacemos así para que se pueda permitir el servicio parcial (sirve una sola peticion), el servicio completo (completa las 2 peticiones),
        # distinguir el orden de visitas a gasolineras y centros para poder calcular la distancia recorrida.

        # El primer elemento de la lista de viajes es siempre el centro de distribucion inicial.
    
    # tenemos que definir un copy también para la clase Camion
    def copy(self) -> 'Camion':
            nuevo = Camion(self.viajes.copy())
            nuevo.capacidad = self.capacidad
            nuevo.num_viajes = self.num_viajes
            nuevo.km_recorridos = self.km_recorridos
            return nuevo
    
    def dist_actual(self) -> float:
        return self.km_recorridos
    
    def dist_nueva(self, distancia: float) -> float:
        self.km_recorridos = distancia
        return self.km_recorridos

class Camiones(object):
    def __init__(self, params: ProblemParameters, camiones: List[Camion], lista_pet_asig: List[tuple] = [], lista_pet_no_asig: List[tuple] = [], ganancias: float = 0, coste_km: float = 0, coste_petno: float = 0):
        self.params = params
        self.camiones = camiones
        self.lista_pet_asig = lista_pet_asig
        self.lista_pet_no_asig = lista_pet_no_asig
        self.ganancias = ganancias
        self.coste_km = coste_km
        self.coste_petno = coste_petno
        # Crear un camion por cada centro de distribucion si la lista de camiones está vacía
        # Si multiplicidad > 1, varios camiones estarán en la misma posicion inicial
        if len(self.camiones) == 0:
            for c in range(len(centros.centros)):
                camion = Camion([(centros.centros[c].cx, centros.centros[c].cy, -1)])
                for _ in range(params.multiplicidad):
                    self.camiones.append(camion)

    def copy(self) -> 'Camiones':
        # Afegim el copy per cada llista de camions
        camiones_copy = [camion.copy() for camion in self.camiones]
        lista_pet_asig_copy = [tuple(pet) for pet in self.lista_pet_asig]
        lista_pet_no_asig_copy = [tuple(pet) for pet in self.lista_pet_no_asig]
        return Camiones(self.params, camiones_copy, lista_pet_asig_copy, lista_pet_no_asig_copy, self.ganancias, self.coste_km, self.coste_petno)

    def generate_actions(self) -> Generator[CamionOperators, None, None]:
        """
        Generar operadores:
        - MoverPeticion: mover una peticion (cualquier viaje con peticion != -1) de un camion al final de otro camion.
        - AsignarPeticion: asignar peticiones no asignadas a un camion
        """
        # MoverPeticion
        # precaclular los indices de las peticiones por camion
        pet_por_cam = []
        for x in range(len(self.camiones)):
            cam = self.camiones[x]
            indices = []
            for ind in range(len(cam.viajes)):
                if cam.viajes[ind][2] != -1:
                    indices.append(ind)
            pet_por_cam.append(indices)

        for cam_i in range(len(pet_por_cam)):
            indices = pet_por_cam[cam_i]
            if len(indices) == 0:
                continue
            org = self.camiones[cam_i]
            for indice_pos in range(len(indices)):
                viaje_i = indices[indice_pos]
                for cam_j in range(len(self.camiones)):
                    if cam_j == cam_i:
                        continue
                    dest = self.camiones[cam_j]
                    if dest.capacidad <= 0:
                        continue
                    temp_org = Camion(org.viajes.copy())
                    temp_dest = Camion(dest.viajes.copy())
                    if viaje_i < 0 or viaje_i >= len(temp_org.viajes):
                        continue
                    trip = temp_org.viajes.pop(viaje_i)
                    temp_dest.viajes.append(trip)
                    limpiar_centros_redundantes(temp_org, self.params)
                    limpiar_centros_redundantes(temp_dest, self.params)
                    try:
                        assert temp_dest.capacidad >= 0
                        km_org = calcular_distancia_camion(temp_org)
                        km_dest = calcular_distancia_camion(temp_dest)
                        assert km_org <= self.params.max_km
                        assert km_dest <= self.params.max_km
                        assert temp_org.num_viajes <= self.params.max_viajes
                        assert temp_dest.num_viajes <= self.params.max_viajes
                        num_peticiones_org = 0
                        for vv in temp_org.viajes:
                            if vv[2] != -1:
                                num_peticiones_org += 1
                        assert not (temp_org.num_viajes == 1 and num_peticiones_org == 0)
                    except AssertionError:
                        continue
                    yield MoverPeticion((cam_i, viaje_i), cam_i, cam_j)

        # MoverAntes 
        for cam_i in range(len(self.camiones)):
            camion = self.camiones[cam_i]
            for viaje_i in range(len(camion.viajes)):
                viaje = camion.viajes[viaje_i]
                if viaje[2] == -1:
                    continue
                for pos_obj in range(1, viaje_i):
                    temp = Camion(camion.viajes.copy())
                    mov = temp.viajes.pop(viaje_i)
                    temp.viajes.insert(pos_obj, mov)
                    limpiar_centros_redundantes(temp, self.params)
                    # comprobar restricciones
                    try:
                        # km límite
                        km_nuevo = calcular_distancia_camion(temp)
                        assert km_nuevo <= self.params.max_km
                        # cisterna: max consecutivas entre centros 
                        consec = 0
                        max_consec = 0
                        for v in temp.viajes:
                            if v[2] == -1:
                                if consec > max_consec:
                                    max_consec = consec
                                consec = 0
                            else:
                                consec += 1
                        if consec > max_consec:
                            max_consec = consec
                        assert max_consec <= self.params.capacidad_maxima
                    except AssertionError:
                        continue
                    yield MoverAntes(cam_i, viaje_i, viaje_i, pos_obj)
        
        # MoverDespues 
        for cam_i, camion in enumerate(self.camiones):
            indices = petitions_per_cam[cam_i]
            if not indices:
                continue
            primer_pet_ind = indices[0]
            for viaje_i in indices:
                # si es la primera peticion, generamos operador que la manda a la ultima posicion
                if viaje_i == primer_pet_ind:
                    pos_obj = len(camion.viajes) - 1
                    if viaje_i < pos_obj:
                        yield MoverDespues(cam_i, viaje_i, viaje_i, pos_obj)
                else:
                    if viaje_i + 1 < len(camion.viajes):
                        yield MoverDespues(cam_i, viaje_i, viaje_i, viaje_i + 1)
        
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
                        # si estamos en el último viaje, que es un centro, y aun nos puede hacer viajes, miraremos si lo podemos añadir al final
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
        # iteramos sobre distintas parejas de camiones
        for cam_i in range(len(self.camiones)):
            for cam_j in range(cam_i + 1, len(self.camiones)):
                camion_i = self.camiones[cam_i]
                camion_j = self.camiones[cam_j]
                # recogemos el índice de la peticion para cada camion
                ind_i = [ind for ind, v in enumerate(camion_i.viajes) if v[2] != -1]
                ind_j = [ind for ind, v in enumerate(camion_j.viajes) if v[2] != -1]
                for ii in ind_i:
                    for jj in ind_j:
                        # aseguramos las restricciones de la cisterna después del swap
                        #  calculamos peticiones consecutivas desde el ultimo centro
                        def desp_swap(cam, eliminar_ind, añadir_viaje):
                            # construimos una lista de viajes después de eliminar el indice y añadir el viaje
                            viajes = cam.viajes.copy()
                            # eliminamos el indice
                            viajes.pop(eliminar_ind)
                            # añadimos el viaje
                            viajes.append(añadir_viaje)
                            # encontramos el ultimo centro
                            ult_centro = None
                            for x in range(len(viajes)-1, -1, -1):
                                if viajes[x][2] == -1:
                                    ult_centro = x
                                    break
                            consec = 0
                            start_x = ult_centro + 1 if ult_centro is not None else 0
                            for x in range(start_x, len(viajes)):
                                if viajes[x][2] != -1:
                                    consec += 1
                            return consec

                        trip_i = camion_i.viajes[ii]
                        trip_j = camion_j.viajes[jj]
                        # miramos la capacidad de la cisterna de ambos camiones después del swap 
                        consec_i = desp_swap(camion_i, ii, trip_j)
                        consec_j = desp_swap(camion_j, jj, trip_i)
                        if consec_i > self.params.capacidad_maxima or consec_j > self.params.capacidad_maxima:
                            continue
                        yield SwapPeticiones(ii, jj, cam_i, cam_j)

        # Eliminar Peticiones
        for cam_i, indices in enumerate(petitions_per_cam):
            for viaje_i in indices:
                yield EliminarPeticiones((cam_i, viaje_i), cam_i)

    def apply_action(self, action: CamionOperators) -> 'Camiones':
        """
        Aplicar el operador dado:
         - MoverPeticion((cam_i, viaje_i), cam_i, cam_j)
         - AsignarPeticion((gas_i, pet_i), cam_i)
         - SwapPeticion()
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
            
            # antes de mover el viaje, guardamos los costes por km del camion origen y del camion destino
            cost_org_ant = camiones_copy.coste_km_1camion(org)
            cost_dest_ant = camiones_copy.coste_km_1camion(dest)
            
            # eliminamos del camion origen
            org.viajes.pop(viaje_i)

            # añadimos al camion destino
            dest.viajes.append(trip)
            # Recalcular estado para ambos camiones
            limpiar_centros_redundantes(org, self.params)
            limpiar_centros_redundantes(dest, self.params)
            # si la capacidad llega a cero, vuelve al centro
            if dest.capacidad == 0:
                volver_a_centro(dest)
            #limpiar centros rebundantes y recacular num_viajes/capacidad 
            limpiar_centros_redundantes(org, self.params)

            # calculamos los nuevos costes por km de ambos camiones
            cost_org_desp = camiones_copy.coste_km_1camion(org)
            cost_dest_desp = camiones_copy.coste_km_1camion(dest)

            # modificamos los valores de costes y ganancias de la nueva solucion
            camiones_copy.mod_coste_km(cost_org_ant + cost_dest_ant, cost_org_desp + cost_dest_desp)
            # las ganancias y el coste por peticiones no servidas no cambian al mover una peticion entre camiones
            return camiones_copy

        # MoverAntes: adelantar una peticion dentro del mismo camion (no añade viajes)
        if isinstance(action, MoverAntes):
            cam_i = action.cam_i
            pos_i = action.pos_i
            pos_j = action.pos_j

            # validaciones básicas
            if cam_i < 0 or cam_i >= len(camiones_copy.camiones):
                return camiones_copy
            camion = camiones_copy.camiones[cam_i]
            if pos_i < 0 or pos_i >= len(camion.viajes):
                return camiones_copy
            if pos_j < 1 or pos_j >= pos_i:
                # target must be earlier than pos_i and not be before the initial center
                return camiones_copy
            if camion.viajes[pos_i][2] == -1:
                return camiones_copy

            # guardamos coste km antes
            coste_cam_ant = camiones_copy.coste_km_1camion(camion)

            trip = camion.viajes.pop(pos_i)
            camion.viajes.insert(pos_j, trip)

            # Recalcular num_viajes y capacidad; no forzamos volver_a_centro aunque capacidad llegue a 0
            limpiar_centros_redundantes(camion, self.params)

            # calculamos nuevo coste por km
            coste_cam_desp = camiones_copy.coste_km_1camion(camion)

            camiones_copy.mod_coste_km(coste_cam_ant, coste_cam_desp)
            # no cambiamos ganancias ni coste por peticiones no servidas
            return camiones_copy

        # MoverDespues: retrasar una peticion dentro del mismo camion (no añade viajes)
        if isinstance(action, MoverDespues):
            cam_i = action.cam_i
            pos_i = action.pos_i
            pos_j = action.pos_j

            camion = camiones_copy.camiones[cam_i]
            
            if camion.viajes[pos_i][2] == -1:
                return camiones_copy

            # guardamos coste km antes
            coste_cam_ant = camiones_copy.coste_km_1camion(camion)

            trip = camion.viajes.pop(pos_i)
            # adjust insertion index if popping earlier element shifts indices
            insert_at = pos_j if pos_j <= pos_i else pos_j
            # if we popped an earlier index, and pos_j > pos_i, the target index decreases by 1
            if pos_j > pos_i:
                insert_at = pos_j - 1
            camion.viajes.insert(insert_at, trip)

            # Recalcular num_viajes y capacidad; do not force volver_a_centro
            limpiar_centros_redundantes(camion, self.params)

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
                # añadir viaje en la posición indicada
                camion.viajes.insert(num_viaje, pet)
            elif num_viaje == len(camion.viajes):
                # si se lo añadimos en la ultima posicion, tiene que volver al centro
                camion.viajes.append(pet)
                camion.num_viajes += 1
                volver_a_centro(camion)

            # recalculamos los km_recorridos del camion
            calcular_distancia_camion(camion)
            
            # calculamos el nuevo coste por km del camion
            coste_cam_desp = camiones_copy.coste_km_1camion(camion)

            # modificamos las listas de peticiones asignadas y no asignadas
            camiones_copy.lista_pet_asig.append(action.pet_i)
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
            org = camiones_copy.camiones[cam_i]
            dest = camiones_copy.camiones[cam_j]

            # validamos indices
            if ii < 0 or ii >= len(org.viajes):
                return camiones_copy
            if jj < 0 or jj >= len(dest.viajes):
                return camiones_copy
            if org.viajes[ii][2] == -1 or dest.viajes[jj][2] == -1:
                return camiones_copy
            
            # calculamos los costes por km antes del swap
            cost_org_ant = camiones_copy.coste_km_1camion(org)
            cost_dest_ant = camiones_copy.coste_km_1camion(dest)

            # extraemos viajes antes del cambio
            trip_i = org.viajes[ii]
            trip_j = dest.viajes[jj]

            # eliminamos del origen y del destino
            org.viajes.pop(ii)
            dest.viajes.pop(jj)

            # añadimos los viajes intercambiados
            org.viajes.append(trip_j)
            dest.viajes.append(trip_i)

            # Recalcular estado de ambos camiones (num_viajes y capacidad)
            limpiar_centros_redundantes(org, self.params)
            limpiar_centros_redundantes(dest, self.params)

            # si alguna capacidad queda a 0 tras la recalculacion, enviarlo al centro
            if org.capacidad == 0:
                volver_a_centro(org)
            if dest.capacidad == 0:
                volver_a_centro(dest)

            # calculamos los nuevos costes por km de ambos camiones
            cost_org_desp = camiones_copy.coste_km_1camion(org)
            cost_dest_desp = camiones_copy.coste_km_1camion(dest)

            # modificamos los valores de costes y ganancias de la nueva solucion
            camiones_copy.mod_coste_km(cost_org_ant + cost_dest_ant, cost_org_desp + cost_dest_desp)
            # las ganancias y el coste por peticiones no servidas no cambian al intercambiar una peticion entre camiones

            return camiones_copy
        
        # EliminarPeticiones
        if isinstance(action, EliminarPeticiones):
            cam_i, viaje_i = action.pet_i
            camion = camiones_copy.camiones[action.cam_i]

            # validamos índices
            if viaje_i < 0 or viaje_i >= len(camion.viajes):
                return camiones_copy
            trip = camion.viajes[viaje_i]
            if trip[2] == -1:
                return camiones_copy

            # antes de eliminar la peticion, guardamos el coste por km del camion
            coste_cam_ant = camiones_copy.coste_km_1camion(camion)

            # eliminamos la peticion del camion
            camion.viajes.pop(viaje_i)
            limpiar_centros_redundantes(camion, self.params)

            # calculamos el nuevo coste por km del camion
            coste_cam_desp = camiones_copy.coste_km_1camion(camion)
            
            # modificamos la lista de peticiones asignadas y no asignadas
            camiones_copy.lista_pet_asig.remove(trip)
            camiones_copy.lista_pet_no_asig.append(trip)
            # modificamos los valores de costes y ganancias de la nueva solucion
            camiones_copy.mod_coste_km(coste_cam_ant, coste_cam_desp)
            camiones_copy.mod_ganancias(trip, "eliminar")
            camiones_copy.mod_coste_petno(trip, "eliminar")

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
        for peticion in self.lista_pet_asig:
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
    # ya sea añadiendo, eliminando o moviendo peticiones. Solo necesitamos saber el camion modificado
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
    # definiremos como coste a las perdidas por dejar una peticion sin servir durante un día más
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


    # tambien necesitamos la lista de peticiones inicialmente asignadas
    def lista_pet_asig_inicial(self) -> List[tuple]:
        lista_asig = []
        for camion in self.camiones:
            for viaje in camion.viajes:
                if viaje[2] != -1:
                    lista_asig.append((viaje))
        self.lista_pet_asig = lista_asig
        return self.lista_pet_asig

    # y la lista de peticiones no asignadas
    def lista_pet_no_asig_inicial(self) -> List[tuple]:
        lista_no_asig = []
        for gasolinera in gasolineras.gasolineras:
            for peticion in gasolinera.peticiones:
                if peticion not in self.lista_pet_asig:
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
                    # estamos seguros de que tiene distancia suficiente para volver porque sino debería haberse detenido en la iteracion anterior
                    volver_a_centro(camion)
                    # pasamos al siguiente camion
                    c += 1
                    # comprobamos que no nos salgamos del rango de camiones
                    if c >= len(camiones.camiones):
                        break
                    camion = camiones.camiones[c]

            camiones.camiones[c].viajes.append((x, y, gasolineras.gasolineras[g].peticiones[p]))
            camion.capacidad -= 1

            # miramos que un camion no vaya a una gasolinera con el deposito vacío y que aun pueda hacer más viajes
            # ya habremos comprobado que el camion puede volver al centro sin sobrepasar el máximo de km
            if camion.capacidad == 0:
                volver_a_centro(camion)
        
        # pasamos a la siguiente gasolinera
        g += 1

    # calc la lista de peticiones asignadas y no asignadas
    camiones.lista_pet_asig_inicial()
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

    # ordenamos las peticiones de mayor a menor numero de días de retraso, excepto las de 0 días, que iran al principio
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

            # miramos que un camion no vaya a una gasolinera con el deposito vacío y que aun pueda hacer más viajes
            if camion_seleccionado.capacidad == 0:
                volver_a_centro(camion_seleccionado)
    
    # nos aseguramos de que todos los camiones terminen en el centro
    # tendrán distancia suficiente para volver
    for camion in camiones.camiones:
        if camion.viajes[-1][2] != -1:
            volver_a_centro(camion)

    # calc la lista de peticiones asignadas y no asignadas
    camiones.lista_pet_asig_inicial()
    camiones.lista_pet_no_asig_inicial()
    
    # calculamos los valores iniciales
    camiones.coste_km_inicial()
    camiones.ganancias_inicial()
    camiones.coste_petno_inicial()

    return camiones

###########################




################################## Funciones auxiliares

def volver_a_centro(camion: Camion) -> None:
    # Añadir un viaje de vuelta al centro de distribucion, las restricciones se comprueban antes de llamar a esta funcion
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
