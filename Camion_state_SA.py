from abia_Gasolina import *
from Camion_parameters import ProblemParameters
from Camion_operators import CamionOperators, MoverPeticion, AsignarPeticion, SwapPeticiones, EliminarPeticiones, MoverAntes, MoverDespues

from typing import Generator, List, Optional
import random


params = ProblemParameters()
centros = CentrosDistribucion(params.num_centros, params.multiplicidad, params.seed)
gasolineras = Gasolineras(params.num_gasolineras, params.seed)

class Camion(object):

    def __init__(self, viajes: List[tuple]):
        self.capacidad = params.capacidad_maxima
        self.num_viajes = 0
        self.km_recorridos = 0.0
        self.centro = viajes[0]

        self.viajes = viajes
        # Lista de ubicaciones de gasolineras asignadas y centros de distribucion que debe pasar
        # y un integer que indique num de dias de retraso y también identifica si es centro (valor = -1) o gasolinera (valor > -1).
        
        # Puede haber ubicaciones duplicadas que representen las dos peticiones de la misma gasolinera.
        # Las ubicaciones de centros pueden repetirse si el camion tiene que volver a un centro varias veces.
        
        # Lo hacemos asi para que se pueda permitir el servicio parcial (sirve una sola peticion), el servicio completo (completa las 2 peticiones),
        # distinguir el orden de visitas a gasolineras y centros para poder calcular la distancia recorrida.

        # El primer elemento de la lista de viajes es siempre el centro de distribucion inicial.
        # El ultimo elemento de la lista de viajes es siempre el centro de distribucion final (puede coincidir con el inicial).
    
    # tenemos que definir un copy también para la clase Camion
    def copy(self) -> 'Camion':
            nuevo = Camion(self.viajes.copy())
            nuevo.capacidad = self.capacidad
            nuevo.num_viajes = self.num_viajes
            nuevo.centro = self.centro
            nuevo.km_recorridos = self.km_recorridos
            return nuevo
    
    # funcion para calcular la distancia total recorrida por un solo camion
    # tmb modifica el atributo km_recorridos del camion
    def recalcular_km(self) -> float:
        # recalcula los km recorridos por el camion
        total = 0.0
        for i in range(1, len(self.viajes)):
            p1 = self.viajes[i - 1]
            p2 = self.viajes[i]
            total += distancia((p1[0], p1[1]), (p2[0], p2[1]))
        self.km_recorridos = total
        return total

class Camiones(object):
    def __init__(self, params: ProblemParameters, camiones: List[Camion], lista_pet_no_asig: List[tuple] = [], ganancias: float = 0, coste_km: float = 0, coste_petno: float = 0, pasos: int =0):
        self.params = params
        self.camiones = camiones
        self.lista_pet_no_asig = lista_pet_no_asig
        self.ganancias = ganancias
        self.coste_km = coste_km
        self.coste_petno = coste_petno
        self.pasos = pasos
        # Crear un camion por cada centro de distribucion si la lista de camiones está vacia
        # Si multiplicidad > 1, varios camiones estarán en la misma posicion inicial
        if len(self.camiones) == 0:
            # Crear una instancia separada de Camion por cada multiplicidad.
            for c in range(len(centros.centros)):
                for _ in range(params.multiplicidad):
                    camion = Camion([(centros.centros[c].cx, centros.centros[c].cy, -1)])
                    self.camiones.append(camion)

    def copy(self) -> 'Camiones':
        # Afegim el copy per cada llista de camions
        camiones_copy = [camion.copy() for camion in self.camiones]
        lista_pet_no_asig_copy = [tuple(pet) for pet in self.lista_pet_no_asig]
        return Camiones(self.params, camiones_copy, lista_pet_no_asig_copy, self.ganancias, self.coste_km, self.coste_petno, self.pasos)

    def random_action(self) -> Optional[CamionOperators]:
        # Selecciona al azar un operador y parámetros válidos, devolviendo exactamente una acción
        if not self.camiones:
            return None

        ops = ['MoverPeticion', 'MoverAntes', 'MoverDespues', 'AsignarPeticion', 'SwapPeticiones', 'EliminarPeticiones']
        random.shuffle(ops)

        # Limitar intentos por operador para evitar bucles largos en instancias sin movimientos válidos
        max_por_op = 30

        for op in ops:
            # MoverPeticion: desde no asignadas o desde asignadas a otra posición/camión
            if op == 'MoverPeticion':
                for _ in range(max_por_op):
                    from_unassigned = bool(self.lista_pet_no_asig) and random.random() < 0.5
                    if from_unassigned:
                        pet = random.choice(self.lista_pet_no_asig)
                        cam_j = random.randrange(len(self.camiones))
                        camion_j = self.camiones[cam_j]
                        # escoger un centro destino válido
                        center_indices = [idx for idx, v in enumerate(camion_j.viajes) if v[2] == -1]
                        if not center_indices:
                            continue
                        idx_c = random.choice(center_indices)
                        # dos casos válidos: entre centros o al final si hay viajes disponibles
                        if idx_c + 2 < len(camion_j.viajes) and camion_j.viajes[idx_c + 2][2] == -1:
                            return MoverPeticion(pet, -1, cam_j, -1, idx_c + 1)
                        if idx_c == len(camion_j.viajes) - 1 and camion_j.num_viajes < self.params.max_viajes:
                            return MoverPeticion(pet, -1, cam_j, -1, idx_c + 1)
                        continue
                    # desde asignadas
                    # elegir camión y petición
                    cam_i = random.randrange(len(self.camiones))
                    camion_i = self.camiones[cam_i]
                    pet_indices = [idx for idx, v in enumerate(camion_i.viajes) if v[2] != -1]
                    if not pet_indices:
                        continue
                    pos_i = random.choice(pet_indices)
                    pet = camion_i.viajes[pos_i]
                    # elegir destino
                    cam_j = random.randrange(len(self.camiones))
                    camion_j = self.camiones[cam_j]
                    center_indices = [idx for idx, v in enumerate(camion_j.viajes) if v[2] == -1]
                    if not center_indices:
                        continue
                    idx_c = random.choice(center_indices)
                    if idx_c + 2 < len(camion_j.viajes) and camion_j.viajes[idx_c + 2][2] == -1:
                        return MoverPeticion(pet, cam_i, cam_j, pos_i, idx_c + 1)
                    if idx_c == len(camion_j.viajes) - 1 and camion_j.num_viajes < self.params.max_viajes:
                        return MoverPeticion(pet, cam_i, cam_j, pos_i, idx_c + 1)
                # si no se encontró válido, probar otro operador

            elif op == 'MoverAntes':
                for _ in range(max_por_op):
                    cam_i = random.randrange(len(self.camiones))
                    camion = self.camiones[cam_i]
                    if len(camion.viajes) < 4:
                        continue
                    # candidatos con patrón C P C (mirando hacia atrás) -> mover P detrás del centro anterior
                    candidates = [i for i in range(2, len(camion.viajes) - 1)
                                  if camion.viajes[i][2] != -1 and camion.viajes[i - 1][2] == -1 and camion.viajes[i - 3][2] == -1]
                    if not candidates:
                        continue
                    pos_i = random.choice(candidates)
                    pet = camion.viajes[pos_i]
                    pos_j = pos_i - 2
                    return MoverAntes(cam_i, pet, pos_i, pos_j)

            elif op == 'MoverDespues':
                for _ in range(max_por_op):
                    cam_i = random.randrange(len(self.camiones))
                    camion = self.camiones[cam_i]
                    if len(camion.viajes) < 3:
                        continue
                    i = random.randrange(1, len(camion.viajes) - 1)
                    if camion.viajes[i][2] == -1:
                        continue
                    # caso entre centros: C P C ... C -> mover P delante del siguiente P (i+2)
                    if i + 3 < len(camion.viajes) and camion.viajes[i + 1][2] == -1 and camion.viajes[i + 3][2] == -1:
                        return MoverDespues(cam_i, camion.viajes[i], i, i + 2)
                    # caso final: última petición del viaje y aún puede añadir viaje
                    if camion.viajes[i][2] != -1 and camion.viajes[i + 1][2] == -1 and camion.num_viajes < self.params.max_viajes:
                        if camion.viajes[i - 1][2] != -1:
                            return MoverDespues(cam_i, camion.viajes[i], i, len(camion.viajes))
                
            elif op == 'AsignarPeticion':
                for _ in range(max_por_op):
                    if not self.lista_pet_no_asig:
                        break
                    pet = random.choice(self.lista_pet_no_asig)
                    cam_i = random.randrange(len(self.camiones))
                    camion = self.camiones[cam_i]
                    if camion.num_viajes > self.params.max_viajes or camion.km_recorridos >= self.params.max_km:
                        continue
                    center_indices = [idx for idx, v in enumerate(camion.viajes) if v[2] == -1]
                    if not center_indices:
                        continue
                    idx_c = random.choice(center_indices)
                    if idx_c + 2 < len(camion.viajes) and camion.viajes[idx_c + 2][2] == -1:
                        return AsignarPeticion(pet, cam_i, idx_c + 1)
                    if idx_c == len(camion.viajes) - 1 and camion.num_viajes < self.params.max_viajes:
                        return AsignarPeticion(pet, cam_i, len(camion.viajes))

            elif op == 'SwapPeticiones':
                for _ in range(max_por_op):
                    # 50% no asignada vs asignada, 50% asignada vs asignada
                    if self.lista_pet_no_asig and random.random() < 0.5:
                        pet_no = random.choice(self.lista_pet_no_asig)
                        cam_j = random.randrange(len(self.camiones))
                        camion_j = self.camiones[cam_j]
                        pos_candidates = [idx for idx, v in enumerate(camion_j.viajes) if v[2] != -1]
                        if not pos_candidates:
                            continue
                        pos_j = random.choice(pos_candidates)
                        pet_asig = camion_j.viajes[pos_j]
                        return SwapPeticiones(pet_no, pet_asig, -1, pos_j, -1, cam_j)
                    # asignada vs asignada
                    cam_i = random.randrange(len(self.camiones))
                    cam_j = random.randrange(len(self.camiones))
                    camion_i = self.camiones[cam_i]
                    camion_j = self.camiones[cam_j]
                    pos_i_candidates = [idx for idx, v in enumerate(camion_i.viajes) if v[2] != -1]
                    pos_j_candidates = [idx for idx, v in enumerate(camion_j.viajes) if v[2] != -1]
                    if not pos_i_candidates or not pos_j_candidates:
                        continue
                    pos_i = random.choice(pos_i_candidates)
                    pos_j = random.choice(pos_j_candidates)
                    if cam_i == cam_j and pos_i == pos_j:
                        continue
                    return SwapPeticiones(camion_i.viajes[pos_i], camion_j.viajes[pos_j], pos_i, pos_j, cam_i, cam_j)

            elif op == 'EliminarPeticiones':
                for _ in range(max_por_op):
                    cam_i = random.randrange(len(self.camiones))
                    camion = self.camiones[cam_i]
                    pos_candidates = [idx for idx, v in enumerate(camion.viajes) if v[2] != -1]
                    if not pos_candidates:
                        continue
                    pos_i = random.choice(pos_candidates)
                    return EliminarPeticiones(camion.viajes[pos_i], cam_i)

        return None

    def apply_action(self, action: CamionOperators) -> 'Camiones':
        
        camiones_copy = self.copy()

        # MoverPeticion
        if isinstance(action, MoverPeticion):
            pet = action.pet_i
            cam_i = action.cam_i
            cam_j = action.cam_j
            pos_i = action.pos_i
            pos_j = action.pos_j

            if cam_i == -1:
                # peticion no asignada a camion, la anadimos al camion destino
                dest = camiones_copy.camiones[cam_j]

                if pos_j < len(dest.viajes):
                    # cuando no se inserta después del último viaje
                    
                    # anadimos al camion destino
                    dest.viajes.insert(pos_j, pet)
                    
                elif pos_j == len(dest.viajes):
                    # si la posicion donde inserir es despues del ultimo
                    dest.viajes.append(pet)
                    volver_a_centro(dest)
                    
                # actualizamos la lista de peticiones no asignadas
                camiones_copy.lista_pet_no_asig.remove(pet)

                # modificamos los valores de costes y ganancias de la nueva solucion

                camiones_copy.mod_ganancias(pet, 'asignar')
                camiones_copy.mod_coste_petno(pet, 'asignar')

                dest.recalcular_km()

                if dest.km_recorridos > self.params.max_km:
                    # si el camion resultante excede el maximo de km, forzamos un coste infinito
                    # no hará falta recalcular los km de todos los camiones
                    # de esta manera, la heuristica del sucesor sera -infinito y el hill climbing lo descartara
                    camiones_copy.coste_km = float('inf')
                    return camiones_copy
                
            elif cam_j != cam_i:
                # para camiones diferentes
                org = camiones_copy.camiones[cam_i]
                dest = camiones_copy.camiones[cam_j]

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

                if pos_j < len(dest.viajes):
                    # cuando no se inserta después del último viaje

                    # anadimos al camion destino
                    dest.viajes.insert(pos_j, pet)

                elif pos_j == len(dest.viajes):
                    # si la posicion donde inserir es despues del ultimo
                    dest.viajes.append(pet)
                    volver_a_centro(dest)
                    
                org.recalcular_km()
                dest.recalcular_km()

                if dest.km_recorridos > self.params.max_km or org.km_recorridos > self.params.max_km:
                    # si alguno de los camiones resultantes excede el maximo de km, forzamos un coste infinito
                    # no hará falta recalcular los km de todos los camiones
                    camiones_copy.coste_km = float('inf')
                    return camiones_copy

            else:
                # para camiones iguales
                camion = camiones_copy.camiones[action.cam_i]

                # miramos si es una peticion unica en un viaje en el camion origen
                if camion.viajes[pos_i - 1][2] == -1 and camion.viajes[pos_i + 1][2] == -1:
                    # si es asi, eliminamos el centro redundante y el viaje de peticion
                    camion.viajes.pop(pos_i)
                    # como q hemos eliminado el viaje de peticion, el indice del centro baja en 1
                    camion.viajes.pop(pos_i)
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

                if pos_j < len(camion.viajes):
                    # cuando no se inserta después del último viaje
                    # insertamos la peticion en la nueva posicion
                    camion.viajes.insert(pos_j, pet)

                elif pos_j == len(camion.viajes):
                    # si la posicion donde inserir es despues del ultimo
                    camion.viajes.append(pet)
                    volver_a_centro(camion)

                # recalculamos los km_recorridos del camion
                camion.recalcular_km()

                if camion.km_recorridos > self.params.max_km:
                    # si el camion resultante excede el maximo de km, forzamos un coste infinito
                    # no hará falta recalcular los km de todos los camiones
                    camiones_copy.coste_km = float('inf')
                    return camiones_copy

        # MoverAntes: adelantar una peticion dentro del mismo camion (no anade viajes pero puede reducirlos)
        if isinstance(action, MoverAntes):
            cam_i = action.cam_i
            pet = action.pet_i
            pos_i = action.pos_i
            pos_j = action.pos_j

            camion = camiones_copy.camiones[cam_i]

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
            camion.recalcular_km()

            if camion.km_recorridos > self.params.max_km:
                    # si el camion resultante excede el maximo de km, forzamos un coste infinito
                    # no hará falta recalcular los km de todos los camiones
                    camiones_copy.coste_km = float('inf')
                    return camiones_copy

        # MoverDespues: retrasar una peticion dentro del mismo camion (puede anadir viajes)
        if isinstance(action, MoverDespues):
            cam_i = action.cam_i
            pos_i = action.pos_i
            pet = action.pet_i
            pos_j = action.pos_j

            camion = camiones_copy.camiones[cam_i]

            # miramos si es una peticion unica en un viaje en el camion
            if camion.viajes[pos_i - 1][2] == -1:
                camion.viajes.pop(pos_i)
                # eliminar el centro siguiente redundante
                camion.viajes.pop(pos_i)
                camion.num_viajes -= 1
                # ajustamos la posicion j si es necesario
                if pos_i < pos_j:
                    pos_j -= 2
            else:
                # no hay que eliminar centro
                camion.viajes.pop(pos_i)
                # ajustamos la posicion j si es necesario
                if pos_i < pos_j:
                    pos_j -= 1
            
            if pos_j != len(camion.viajes):
                # no es la ultima peticion
                # Insertamos la peticion en la nueva posicion
                camion.viajes.insert(pos_j, pet)            
            else:
                # es la ultima peticion
                camion.viajes.append(pet)
                volver_a_centro(camion)

            camion.recalcular_km()
            # no cambiamos ganancias ni coste por peticiones no servidas

            if camion.km_recorridos > self.params.max_km:
                    # si el camion resultante excede el maximo de km, forzamos un coste infinito
                    # no hará falta recalcular los km de todos los camiones
                    camiones_copy.coste_km = float('inf')
                    return camiones_copy

        # AsignarPeticion
        if isinstance(action, AsignarPeticion):
            camion = camiones_copy.camiones[action.cam_i]
            pet = action.pet_i
            pos_i = action.pos_i

            if pos_i < len(camion.viajes):
                # anadir viaje en la posición indicada
                camion.viajes.insert(pos_i, pet)

            elif pos_i == len(camion.viajes):
                # si se lo anadimos en la ultima posicion, tiene que volver al centro
                camion.viajes.append(pet)
                camion.num_viajes += 1
                volver_a_centro(camion)

            # modificamos las listas de peticiones asignadas y no asignadas
            camiones_copy.lista_pet_no_asig.remove(action.pet_i)

            # modificamos los valores de costes y ganancias de la nueva solucion
            camiones_copy.mod_ganancias(action.pet_i, "asignar")
            camiones_copy.mod_coste_petno(action.pet_i, "asignar")
            
            camion.recalcular_km()

            if camion.km_recorridos > self.params.max_km:
                    # si el camion resultante excede el maximo de km, forzamos un coste infinito
                    # no hará falta recalcular los km de todos los camiones
                    camiones_copy.coste_km = float('inf')
                    return camiones_copy
        
        #SwapPeticiones
        if isinstance(action, SwapPeticiones):
            pet_i = action.pet_i
            pet_j = action.pet_j
            pos_i = action.pos_i
            pos_j = action.pos_j
            cam_i = action.cam_i
            cam_j = action.cam_j

            if cam_i == -1 and cam_j != -1:
                # Para peticiones no asignadas
                dest = camiones_copy.camiones[cam_j]
                # es una tupla porque es una peticion no asignada
                pet_no = pet_i

                # peticion asignada
                pet_asig = pet_j

                # realizamos el intercambio
                dest.viajes[pos_j] = pet_no

                # actualizar lista de peticiones no asignadas
                camiones_copy.lista_pet_no_asig.remove(pet_no)
                camiones_copy.lista_pet_no_asig.append(pet_asig)

                # update gains and unserved-costs
                camiones_copy.mod_ganancias(pet_asig, "eliminar")
                camiones_copy.mod_coste_petno(pet_asig, "eliminar")

                camiones_copy.mod_ganancias(pet_no, "asignar")
                camiones_copy.mod_coste_petno(pet_no, "asignar")

                # recompute km and cost for the affected camion
                dest.recalcular_km()

                if dest.km_recorridos > self.params.max_km:
                    # si el camion resultante excede el maximo de km, forzamos un coste infinito
                    # no hará falta recalcular los km de todos los camiones
                    camiones_copy.coste_km = float('inf')
                    return camiones_copy


            else:
                # entre dos camiones diferentes o el mismo camion
                if cam_i != cam_j:
                    # si son camiones diferentes
                    org = camiones_copy.camiones[cam_i]
                    dest = camiones_copy.camiones[cam_j]

                    # extraemos viajes antes del cambio
                    pet_i = org.viajes[pos_i]
                    pet_j = dest.viajes[pos_j]

                    # eliminamos del origen y del destino
                    org.viajes.pop(pos_i)
                    dest.viajes.pop(pos_j)

                    # anadimos los viajes intercambiados
                    org.viajes.insert(pos_i, pet_j)
                    dest.viajes.insert(pos_j, pet_i)

                    org.recalcular_km()
                    dest.recalcular_km()

                    if org.km_recorridos > self.params.max_km or dest.km_recorridos > self.params.max_km:
                        # si alguno de los camiones resultantes excede el maximo de km, forzamos un coste infinito
                        # no hará falta recalcular los km de todos los camiones
                        camiones_copy.coste_km = float('inf')
                        return camiones_copy

                else:
                    # si son el mismo camion
                    camion = camiones_copy.camiones[cam_i]

                    # extraemos los viajes antes del cambio
                    pet_i = camion.viajes[pos_i]
                    pet_j = camion.viajes[pos_j]

                    # realizamos el swap
                    camion.viajes[pos_i] = pet_j
                    camion.viajes[pos_j] = pet_i

                    # las ganancias y el coste por peticiones no servidas no cambian al intercambiar una peticion entre camiones
                    camion.recalcular_km()

                    if camion.km_recorridos > self.params.max_km:
                        # si el camion resultante excede el maximo de km, forzamos un coste infinito
                        # no hará falta recalcular los km de todos los camiones
                        camiones_copy.coste_km = float('inf')
                        return camiones_copy

        # EliminarPeticiones
        if isinstance(action, EliminarPeticiones):
            pet = action.pet_i
            cam_i = action.cam_i
            camion = camiones_copy.camiones[cam_i]

            # eliminamos la peticion del camion
            for viaje_i, viaje in enumerate(camion.viajes):
                if viaje == pet:
                    if camion.viajes[viaje_i -1][2] == - 1 and camion.viajes[viaje_i +1][2] == -1:
                        #miramos si hay que quitar centros redundantes y recalculamos num_viajes
                        # si la peticion esta entre dos centros, eliminamos tambien uno de los centros para evitar redundancia
                        camion.viajes.remove(camion.viajes[viaje_i -1])
                        # el indice se reduce en 1 tras eliminar el centro anterior
                        camion.viajes.remove(camion.viajes[viaje_i -1])
                        camion.num_viajes -= 1
                        
                    else:
                        # si no, simplemente eliminamos la peticion
                        camion.viajes.remove(camion.viajes[viaje_i])
                    break

            # modificamos la lista de peticiones asignadas y no asignadas
            camiones_copy.lista_pet_no_asig.append(pet)

            # modificamos los valores de costes y ganancias de la nueva solucion
            camiones_copy.mod_ganancias(pet, "eliminar")
            camiones_copy.mod_coste_petno(pet, "eliminar")

            camion.recalcular_km()
            
            # eliminar viajes no superará el max de km
        
        camiones_copy.coste_km_rec()
        camiones_copy.pasos += 1
        return camiones_copy
    
    def pasos_actual(self) -> int:
        return self.pasos
    
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
                self.ganancias = self.ganancias + self.params.valor_deposito * 1.02
            elif peticion[2] > 0:
                self.ganancias = self.ganancias + self.params.valor_deposito * (1 - (2 ** peticion[2]) / 100)
        elif operacion == "eliminar":
            if peticion[2] == 0:
                self.ganancias = self.ganancias - self.params.valor_deposito * 1.02
            elif peticion[2] > 0:
                self.ganancias = self.ganancias - self.params.valor_deposito * (1 - (2 ** peticion[2]) / 100)
        return self.ganancias

    # coste por km de la solucion inicial
    def coste_km_rec(self) -> float:
        total_coste = 0
        for camion in self.camiones:
            if camion.km_recorridos <= self.params.max_km and camion.num_viajes <= self.params.max_viajes:
                total_coste += camion.km_recorridos * self.params.coste_km
            else:
                total_coste = float('inf')
                break
        self.coste_km = total_coste
        return self.coste_km

    # el coste por km se modifica cuando se altera la lista de viajes de un camion, 
    # ya sea anadiendo, eliminando o moviendo peticiones. Solo necesitamos saber el camion modificado
    # necesitamos la distancia anterior y la nueva distancia de este camion
    def coste_km_1camion(self, camion: Camion) -> float:
        return camion.km_recorridos * self.params.coste_km

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
                self.coste_petno = self.coste_petno - ((self.params.valor_deposito * 1.02) - (self.params.valor_deposito * 0.98))
            elif peticion[2] > 0:
                self.coste_petno = self.coste_petno - ((self.params.valor_deposito * (1 - (2 ** peticion[2]) / 100)) - (self.params.valor_deposito * (1 - (2 ** (peticion[2]+1)) / 100)))
        elif operacion == "eliminar":
            if peticion[2] == 0:
                self.coste_petno = self.coste_petno + ((self.params.valor_deposito * 1.02) - (self.params.valor_deposito * 0.98))
            elif peticion[2] > 0:
                self.coste_petno = self.coste_petno + ((self.params.valor_deposito * (1 - (2 ** peticion[2]) / 100)) - (self.params.valor_deposito * (1 - (2 ** (peticion[2]+1)) / 100)))
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
                if (gasolinera.cx, gasolinera.cy, peticion) not in lista_pet_asig:
                    lista_no_asig.append((gasolinera.cx, gasolinera.cy, peticion))

        self.lista_pet_no_asig = lista_no_asig
        return lista_no_asig
    

####################### Soluciones iniciales
def generar_sol_inicial_vacia(params: ProblemParameters) -> Camiones:
    camiones = Camiones(params, [])
    # solo hace falta calc la lista de pet no asignadas
    camiones.lista_pet_no_asig_inicial()
    # calculamos los valores iniciales
    camiones.coste_km_rec()
    camiones.ganancias_inicial()
    camiones.coste_petno_inicial()
    return camiones


def generar_sol_inicial_aleat(params: ProblemParameters) -> Camiones:
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
                distancia_camion = camion.recalcular_km()
                
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
    camiones.coste_km_rec()
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
                distancia_total = camion.recalcular_km() + distancia_gasolinera + distancia_volver

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
    camiones.coste_km_rec()
    camiones.ganancias_inicial()
    camiones.coste_petno_inicial()

    return camiones

###########################




################################## Funciones auxiliares

def volver_a_centro(camion: Camion) -> None:
    # Anadir un viaje de vuelta al centro de distribucion, las restricciones se comprueban antes de llamar a esta funcion
    camion.viajes.append((camion.centro[0], camion.centro[1], -1))
    camion.num_viajes += 1
    camion.capacidad = params.capacidad_maxima

# dist L1
def distancia(p1: tuple, p2: tuple) -> float:
    return abs(p2[0] - p1[0]) + abs(p2[1] - p1[1])

#######################################
