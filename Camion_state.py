from abia_Gasolina import Gasolineras, Gasolinera, CentrosDistribucion, Distribucion
from Camion_parameters import ProblemParameters
from Camion_operators import CamionOperators

class Camion(object):

    def __init__(self, centros: CentrosDistribucion, gasolineras: Gasolineras):
        self.ubicacion = (centros.centros[0].cx, centros.centros[0].cy)
        self.capacidad = 2
        self.num_viajes = 0
        self.km_recorridos = 0
        self.asignaciones = []  # Lista de ubicaciones de gasolineras asignadas en el viaje actual + int que indique num de dias de retraso. 
        # Puede haber ubicaciones duplicadas que representen las dos peticiones de la misma gasolinera.
        # Lo hacemos así porque puede existir el caso en que el camión llegue a alguna gasolinera con dos peticiones
        # pendientes pero solo le queda capacidad para llenar un solo depósito.

class Camiones(object):
    def __init__(self, params: ProblemParameters, centros: CentrosDistribucion, gasolineras: Gasolineras):
        self.params = params
        self.centros = centros
        self.gasolineras = gasolineras
        self.camiones = []
        # Crear un camión por cada centro de distribución
        # Si multiplicidad > 1, varios camiones estarán en la misma posición inicial
        for _ in range(len(centros.centros)):
            camion = Camion(centros, gasolineras)
            self.camiones.append(camion)

        
        
    
    def generate_actions(self):
        pass

    def apply_action(self, action: CamionOperators) -> Camiones:
        pass
    
    def heuristic(self):
        pass


def generar_sol_inicial(params: ProblemParameters) -> Camiones:
    
