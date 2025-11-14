from aima.search import Problem
from typing import Generator

# Usamos el estado específico para SA que ofrece random_action()
from Camion_state import Camiones
from Camion_operators import CamionOperators

class CamionesyPeticionesSA(Problem):
    def __init__(self, initial_state: Camiones):
        super().__init__(initial_state)

    def actions(self, state: Camiones) -> Generator[CamionOperators, None, None]:
        """
        Para SA devolvemos un único operador escogido al azar con parámetros al azar,
        en lugar de enumerar todas las acciones posibles.
        """
        action = state.random_action()
        if action is None:
            return iter(())
        # Devolvemos un generador con un solo elemento
        return iter((action,))

    def result(self, state: Camiones, action: CamionOperators) -> Camiones:
        return state.apply_action(action)

    def value(self, state: Camiones) -> float:
        return state.heuristic()

    def goal_test(self, state: Camiones) -> bool:
        return False
