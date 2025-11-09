import random
from typing import List

DISTRIBUCION_PETICIONES = [0.05, 0.65, 0.25, 0.05]
DISTRIBUCION_DIAS = [0.60, 0.20, 0.15, 0.05]


class Gasolinera(object):
    """
    Estructura de datos de una gasolinera
    """

    def __init__(self, cx: int, cy: int, peticiones: List[int]):
        """
        Constructora
        :param cx: coordenada X
        :param cy: coordenada Y
        :param peticiones: ArrayList de Integers con los días pendientes de la peticion (0= hoy)
        """
        self.cx = cx
        self.cy = cy
        self.peticiones = peticiones


class Gasolineras(object):
    """
    Lista de gasolineras
    """

    def __init__(self, num_gasolineras: int, seed: int):
        """
        Genera un número de centros con una semilla aleatoria
        :param num_gasolineras: Número de gasolineras
        :param seed: Semilla para el generador de números aleatorios
        """
        self.my_random = random.Random(seed)
        self.gasolineras = []
        for _ in range(num_gasolineras):
            gasolinera = Gasolinera(self.my_random.randint(0, 99),
                                    self.my_random.randint(0, 99),
                                    self.genera_peticiones())
            self.gasolineras.append(gasolinera)

    def genera_peticiones(self) -> List[int]:
        """
        Generamos un número de peticiones entre 0 y 3 con distribución sesgada
        Generamos el día que lleva la peticion pendiente con otra distribución
        sesgada
        :return: Lista de peticiones
        """
        pet = []
        dice = self.my_random.random()
        if dice < DISTRIBUCION_PETICIONES[0]:
            num_peticiones = 0
        elif dice < (DISTRIBUCION_PETICIONES[0] + DISTRIBUCION_PETICIONES[1]):
            num_peticiones = 1
        else:
            num_peticiones = 2

        for _ in range(num_peticiones):
            dice = self.my_random.random()
            if dice < DISTRIBUCION_DIAS[0]:
                num_dias = 0
            elif dice < (DISTRIBUCION_DIAS[0] + DISTRIBUCION_DIAS[1]):
                num_dias = 1
            elif dice < (DISTRIBUCION_DIAS[0] + DISTRIBUCION_DIAS[1] + DISTRIBUCION_DIAS[2]):
                num_dias = 2
            else:
                num_dias = 3
            pet.append(num_dias)
        return pet


class Distribucion(object):
    """
    Centro de Distribución
    """

    def __init__(self, cx: int, cy: int):
        """
        Constructora
        :param cx: coordenada X
        :param cy: coordenada Y
        """
        self.cx = cx
        self.cy = cy



class CentrosDistribucion(object):
    """
    Lista con los centros de distribución
    """

    def __init__(self, num_centros: int, multiplicidad: int, seed: int):
        """
        Genera un número de centros con una semilla aleatoria
        Si multiplicidad es diferente de 1 genera varios centros
        en la misma posicion para simular tener más de un camion
        en un centro
        :param num_centros: Número de centros
        :param multiplicidad: Multiplicidad en la misma posicion
        :param seed: Semilla para el generador de números aleatorios
        """
        self.centros = []
        self.my_random = random.Random(seed + 1)
        for _ in range(num_centros):
            centro = Distribucion(self.my_random.randint(0, 99),
                                  self.my_random.randint(0, 99))
            for _ in range(multiplicidad):
                self.centros.append(centro)




if __name__ == "__main__":
    """
    Código para probar las clases
    No tiene utilidad para la práctica
    """
    s = Gasolineras(100, 1234)
    c = CentrosDistribucion(10, 1, 1234)
    histograma = [0, 0, 0, 0]

    for i in range(len(s.gasolineras)):
        print(f"Gasolinera {i}: {s.gasolineras[i].cx} {s.gasolineras[i].cy}")
        j = 0
        if not s.gasolineras[i].peticiones:
            print("-> Sin peticiones <-")
        for peticion in s.gasolineras[i].peticiones:
            print(f"Peticion {j}: Días {peticion}")
            j += 1
            histograma[peticion] += 1

    print()
    for i in range(4):
        print(f"{histograma[i]} de {i} días")
    print()
    for i in range(len(c.centros)):
        print(f"Centro {i}: {c.centros[i].cx} {c.centros[i].cy}")

#comentario comentario 
