class CamionOperators(object):
    pass

class MoverPeticion(CamionOperators):
    def __init__(self, pet_i: tuple, cam_i: int, cam_j: int):
        self.pet_i = pet_i
        self.cam_i = cam_i
        self.cam_j = cam_j

    def __repr__(self) -> str:
        return f"Mover la petición {self.pet_i} del camión {self.cam_i} al camión {self.cam_j}"

class AsignarPeticion(CamionOperators):
    def __init__(self, pet_i: tuple, cam_i: int):
        self.pet_i = pet_i
        self.cam_i = cam_i

    def __repr__(self) -> str:
        return f"Asignar petición {self.pet_i} al camión {self.cam_i}"

class SwapPeticiones(CamionOperators):
    def __init__(self, pet_i: int, pet_j: int, cam_i: int, cam_j: int):
        self.pet_i = pet_i
        self.pet_j = pet_j
        self.cam_i = cam_i
        self.cam_j = cam_j

    def __repr__(self) -> str:
        return f"Intercambiar la petición {self.pet_i} del camión {self.cam_i} por la petición {self.pet_j} del camión {self.cam_j}"

class MoverAntes(CamionOperators):
    def __init__(self, pet_i: tuple, pos_i: int, pos_j: int, cam_i: int):
        self.cam_i = cam_i
        self.pet_i = pet_i
        self.pos_i = pos_i
        self.pos_j = pos_j

    def __repr__(self) -> str:
        return f"Mover la petición {self.pet_i} del camión {self.cam_i} de la posición {self.pos_i} a la posición {self.pos_j}"
        
class MoverDespues(CamionOperators):
    def __init__(self, cam_i: int, pet_i: int, pos_i: int, pos_j: int):
        self.cam_i = cam_i
        self.pet_i = pet_i
        self.pos_i = pos_i
        self.pos_j = pos_j

    def __repr__(self) -> str:
        return f"Mover la petición {self.pet_i} del camión {self.cam_i} de la posición {self.pos_i} a la posición {self.pos_j}"

class EliminarPeticion(CamionOperators):
    def __init__(self, pet_i: tuple, cam_i: int):
        self.pet_i = pet_i
        self.cam_i = cam_i 

    def __repr__(self) -> str:
        return f"Eliminar la petición {self.pet_i} del camión {self.cam_i}"
