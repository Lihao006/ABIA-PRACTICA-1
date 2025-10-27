from abia_Gasolina import Gasolineras, Gasolinera, CentrosDistribucion, Distribucion
from Camion_parameters import ProblemParameters

class Camion(object):

    def __init__(self, params: ProblemParameters, centros: CentrosDistribucion, gasolineras: Gasolineras):
        self.params = params
        self.ubicacion = (centros.centros[0].cx, centros.centros[0].cy)
        self.capacidad = 2
        self.num_viajes = 0
        self.km_recorridos = 0
        self.asignaciones = []  # Lista de ubicaciones de gasolineras asignadas en el viaje actual. 
        # Puede haber ubicaciones duplicadas que representen las dos peticiones de la misma gasolinera.
        # Lo hacemos así porque puede existir el caso en que el camión llegue a alguna gasolinera con dos peticiones
        # pendientes pero solo le queda capacidad para llenar un solo depósito.

    


    def generar_sol_inicial(self):
        

