from aima.search import Problem, hill_climbing, simulated_annealing

from typing import Generator


from abia_Gasolina import Gasolineras, Gasolinera, CentrosDistribucion, Distribucion
from Camion_state_opt import *
from Camion_parameters import ProblemParameters
from Camion_operators import CamionOperators


class CamionesyPeticiones(Problem):
    def __init__(self, initial_state: Camiones):
        super().__init__(initial_state)

    def actions(self, state: Camiones) -> Generator[CamionOperators, None, None]:
        return state.generate_actions()

    def result(self, state: Camiones, action: CamionOperators) -> Camiones:
        return state.apply_action(action)

    def value(self, state: Camiones) -> float:
        return state.heuristic()

    def goal_test(self, state: Camiones) -> bool:
        return False



    




