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
        self.km_recorridos = 0

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

class Camiones(object):
    def __init__(self, params: ProblemParameters, camiones: List[Camion], ganancias: float = 0, coste_km: float = 0, coste_petno: float = 0):
        self.params = params
        self.camiones = camiones
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
        return Camiones(self.params, camiones_copy, self.ganancias, self.coste_km, self.coste_petno)

    def generate_actions(self) -> Generator[CamionOperators, None, None]:
        """
        Generar operadores:
        - MoverPeticion: mover una peticion (cualquier viaje con peticion != -1) de un camion al final de otro camion.
        - AsignarPeticion: asignar peticiones no asignadas a un camion
        """
        # MoverPeticion
        # precaclular los indices de las peticiones por camion
        petitions_per_cam = [ [i for i,v in enumerate(cam.viajes) if v[2] != -1] for cam in self.camiones ]
        for cam_i, indices in enumerate(petitions_per_cam):
            if not indices:
                continue
            for viaje_i in indices:
                for cam_j, camion_j in enumerate(self.camiones):
                    if cam_j == cam_i:
                        continue
                    if camion_j.capacidad <= 0:
                        continue
                    yield MoverPeticion((cam_i, viaje_i), cam_i, cam_j)

        # MoverAntes 
        # Limitamos el avance máximo para reducir branching (optimización)
        MAX_ADVANCE = 10
        for cam_i, camion in enumerate(self.camiones):
            indices = petitions_per_cam[cam_i]
            if not indices:
                continue
            for viaje_i in indices:
                start_pos = max(1, viaje_i - MAX_ADVANCE)
                for pos_obj in range(start_pos, viaje_i):
                    yield MoverAntes(cam_i, viaje_i, viaje_i, pos_obj)

        # MoverDespues 
        for cam_i, camion in enumerate(self.camiones):
            indices = petitions_per_cam[cam_i]
            if not indices:
                continue
            primer_pet_ind = indices[0]
            for viaje_i in indices:
                # si es la primera petición, generamos operador que la manda a la última posición
                if viaje_i == primer_pet_ind:
                    pos_obj = len(camion.viajes) - 1
                    if viaje_i < pos_obj:
                        yield MoverDespues(cam_i, viaje_i, viaje_i, pos_obj)
                else:
                    if viaje_i + 1 < len(camion.viajes):
                        yield MoverDespues(cam_i, viaje_i, viaje_i, viaje_i + 1)

        # AsignarPeticion (optimized: per-truck caching of metrics)
        asignado = set()
        for camion in self.camiones:
            for viaje in camion.viajes:
                if viaje[2] != -1:
                    asignado.add((viaje[0], viaje[1], viaje[2]))

        num_cam = len(self.camiones)
        camion_distancia = [0.0] * num_cam
        camion_last_pos = [None] * num_cam
        camion_ult_centro = [None] * num_cam
        camion_consec = [0] * num_cam
        camion_capacidad = [0] * num_cam
        for i, camion in enumerate(self.camiones):
            camion_distancia[i] = calcular_distancia_camion(camion)
            camion_last_pos[i] = (camion.viajes[-1][0], camion.viajes[-1][1])
            camion_capacidad[i] = camion.capacidad
            ult = None
            for x in range(len(camion.viajes)-1, -1, -1):
                if camion.viajes[x][2] == -1:
                    ult = x
                    break
            camion_ult_centro[i] = ult
            consec = 0
            start_x = ult + 1 if ult is not None else 0
            for x in range(start_x, len(camion.viajes)):
                if camion.viajes[x][2] != -1:
                    consec += 1
            camion_consec[i] = consec

        for gas_i, g in enumerate(gasolineras.gasolineras):
            for pet_i, pet in enumerate(g.peticiones):
                viaje_repr = (g.cx, g.cy, pet)
                if viaje_repr in asignado:
                    continue
                for cam_i in range(num_cam):
                    if camion_capacidad[cam_i] <= 0:
                        continue
                    if camion_consec[cam_i] + 1 > self.params.capacidad_maxima:
                        continue
                    distancia_actual = camion_distancia[cam_i]
                    last_pos = camion_last_pos[cam_i]
                    # inline simple L1 distance calculations to avoid extra function overhead
                    distancia_gasolinera = abs(last_pos[0] - g.cx) + abs(last_pos[1] - g.cy)
                    centro = self.camiones[cam_i].viajes[0]
                    distancia_vuelta = abs(g.cx - centro[0]) + abs(g.cy - centro[1])
                    distancia_total = distancia_actual + distancia_gasolinera + distancia_vuelta
                    if distancia_total > self.params.max_km:
                        continue
                    yield AsignarPeticion((gas_i, pet_i), cam_i)

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
                        #  calculamos peticiones consecutivas desde el último centro
                        def desp_swap(cam, eliminar_ind, añadir_viaje):
                            # construimos una lista de viajes después de eliminar el indice y añadir el viaje
                            viajes = cam.viajes.copy()
                            # eliminamos el indice
                            viajes.pop(eliminar_ind)
                            # añadimos el viaje
                            viajes.append(añadir_viaje)
                            # encontramos el último centro
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
            
            # eliminamos del camión origen
            org.viajes.pop(viaje_i)

            # añadimos al camión destino
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

            # modificamos los valores de costes y ganancias de la nueva solución
            camiones_copy.mod_coste_km(cost_org_ant + cost_dest_ant, cost_org_desp + cost_dest_desp)
            # las ganancias y el coste por peticiones no servidas no cambian al mover una peticion entre camiones
            return camiones_copy

        # MoverAntes: adelantar una petición dentro del mismo camión (no añade viajes)
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

        # MoverDespues: retrasar una petición dentro del mismo camión (no añade viajes)
        if isinstance(action, MoverDespues):
            cam_i = action.cam_i
            pos_i = action.pos_i
            pos_j = action.pos_j

            # validaciones básicas
            if cam_i < 0 or cam_i >= len(camiones_copy.camiones):
                return camiones_copy
            camion = camiones_copy.camiones[cam_i]
            if pos_i < 0 or pos_i >= len(camion.viajes):
                return camiones_copy
            # pos_j should be within [1, len-1]
            if pos_j < 1 or pos_j >= len(camion.viajes):
                return camiones_copy
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

            # antes de asignar la peticion, guardamos el coste por km del camion
            coste_cam_ant = camiones_copy.coste_km_1camion(camion)

            pet = gas.peticiones[pet_i]
            # añadir viaje
            camion.viajes.append((gas.cx, gas.cy, pet))
            limpiar_centros_redundantes(camion, self.params)
            # si la capacidad llega a 0, devolvemos el camión al centro
            if camion.capacidad == 0:
                volver_a_centro(camion)

            # calculamos el nuevo coste por km del camion
            coste_cam_desp = camiones_copy.coste_km_1camion(camion)
            
            # modificamos los valores de costes y ganancias de la nueva solución
            camiones_copy.mod_coste_km(coste_cam_ant, coste_cam_desp)
            camiones_copy.mod_ganancias((gas.cx, gas.cy, pet), "asignar")
            camiones_copy.mod_coste_petno((gas.cx, gas.cy, pet), "asignar")

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

            # si alguna capacidad queda a 0 tras la recalculación, enviarlo al centro
            if org.capacidad == 0:
                volver_a_centro(org)
            if dest.capacidad == 0:
                volver_a_centro(dest)

            # calculamos los nuevos costes por km de ambos camiones
            cost_org_desp = camiones_copy.coste_km_1camion(org)
            cost_dest_desp = camiones_copy.coste_km_1camion(dest)

            # modificamos los valores de costes y ganancias de la nueva solución
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

            # eliminamos la petición del camión
            camion.viajes.pop(viaje_i)
            limpiar_centros_redundantes(camion, self.params)

            # calculamos el nuevo coste por km del camion
            coste_cam_desp = camiones_copy.coste_km_1camion(camion)

            # modificamos los valores de costes y ganancias de la nueva solución
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
        for camion in self.camiones:
            for viaje in camion.viajes:
                if viaje[2] == 0:
                    total_ganancias += 1000 * 1.02
                elif viaje[2] > 0:
                    total_ganancias += 1000 * (1 - (2 ** viaje[2]) / 100)
        self.ganancias = total_ganancias
        return total_ganancias

    # modifica las ganancias a partir de las ganancias actuales
    # la única manera de variar las ganancias es asignando o quitando peticiones
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
        return total_coste

    # el coste por km se modifica cuando se altera la lista de viajes de un camion, 
    # ya sea añadiendo, eliminando o moviendo peticiones. Solo necesitamos saber el camion modificado
    # necesitamos la distancia anterior y la nueva distancia de este camion
    def coste_km_1camion(self, camion: Camion) -> float:
        return calcular_distancia_camion(camion) * self.params.coste_km_max

    # restamos el coste anterior de ese camion y sumamos el nuevo coste
    def mod_coste_km(self, coste_cam_ant: float, cost_cam_nue: float) -> float:
        # coste_cam_ant may be the sum of previous affected trucks' costs;
        # subtract the old cost(s) and add the new cost(s)
        self.coste_km = self.coste_km - coste_cam_ant + cost_cam_nue
        return self.coste_km

    # coste de las peticiones no servidas en la solucion inicial
    # definiremos como coste a las perdidas por dejar una peticion sin servir durante un día más
    def coste_petno_inicial(self) -> float:
        total_coste = 0
        for camion in self.camiones:
            for viaje in camion.viajes:
                if viaje[2] == 0:
                    total_coste += ((self.params.valor_deposito * 1.02) - (self.params.valor_deposito * 0.98))
                elif viaje[2] > 0:
                    total_coste += (self.params.valor_deposito * (1 - (2 ** viaje[2]) / 100)) - (self.params.valor_deposito * (1 - (2 ** (viaje[2]+1)) / 100))
        self.coste_petno = total_coste
        return total_coste

    # la única manera de modificar el coste de peticiones no servidas es asignando o eliminando peticiones
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

####################### Soluciones iniciales
def generar_sol_inicial_vacio(params: ProblemParameters) -> Camiones:
    camiones = Camiones(params, [])
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
            if camion.num_viajes == params.max_viajes:
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
                
                # distancia desde la última posicion del camion hasta la gasolinera
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

            # miramos que un camion no vaya a una gasolinera con el deposito vacío y que aún pueda hacer más viajes
            # ya habremos comprobado que el camion puede volver al centro sin sobrepasar el máximo de km
            if camion.capacidad == 0:
                volver_a_centro(camion)
        
        # pasamos a la siguiente gasolinera
        g += 1
    
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

    # ordenamos las peticiones de mayor a menor número de días de retraso, excepto las de 0 días, que iran al principio
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
          
            # Las distancias hasta la gasolinera se calculan con el penúltimo elemento de la lista de viajes
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

            # miramos que un camion no vaya a una gasolinera con el deposito vacío y que aún pueda hacer más viajes
            if camion_seleccionado.capacidad == 0:
                volver_a_centro(camion_seleccionado)
    
    # nos aseguramos de que todos los camiones terminen en el centro
    # tendrán distancia suficiente para volver
    for camion in camiones.camiones:
        if camion.viajes[-1][2] != -1:
            volver_a_centro(camion)
    
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
def calcular_distancia_camion(camion: Camion) -> float:
    total_distance = 0
    for i in range(1, len(camion.viajes)):
        total_distance += distancia(camion.viajes[i-1][:2], camion.viajes[i][:2])
    return total_distance

# dist L1
def distancia(p1: tuple, p2: tuple) -> float:
    return abs(p2[0] - p1[0]) + abs(p2[1] - p1[1])

def limpiar_centros_redundantes(camion: Camion, params: ProblemParameters) -> None:
    # eliminar centros finales redundantes (si no hay peticiones después del centro anterior)
    while camion.viajes and camion.viajes[-1][2] == -1:
        # buscar penúltimo centro
        penult = None
        for x in range(len(camion.viajes)-2, -1, -1):
            if camion.viajes[x][2] == -1:
                penult = x
                break
        # comprobar si hay peticiones entre penult+1 y el penúltimo elemento (excluyendo último centro)
        start = penult + 1 if penult is not None else 0
        hay_peticiones = any(v[2] != -1 for v in camion.viajes[start:len(camion.viajes)-1])
        if not hay_peticiones:
            camion.viajes.pop()
        else:
            break

    # Recalcular num_viajes: número de retornos al centro (excluyendo centro inicial)
    total_centros = sum(1 for v in camion.viajes if v[2] == -1)
    camion.num_viajes = max(0, total_centros - 1)

    # Recalcular capacidad según peticiones consecutivas desde el último centro
    last_center = None
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
