import timeit
from Camion_state_opt import *
from aima.search import hill_climbing, simulated_annealing
from CamionesyPeticiones_problem import CamionesyPeticiones
from Camion_parameters import ProblemParameters
from Camion_operators import *

if __name__ == '__main__':
	# parametros por defecto
	params = ProblemParameters()
	print('Generando solucion inicial...')
	initial_state = generar_sol_inicial(params)
	print('Solucion inicial generada.')
	print('Ejecutando Hill Climbing...')
	hc_1 = hill_climbing(CamionesyPeticiones(initial_state))
	print('Hill Climbing ejecutado.')
	print(hc_1)
	print(hc_1.heuristic())
    # tiempo en segundos
	hc_1_t = timeit.timeit(lambda: hill_climbing(CamionesyPeticiones(initial_state)), number=1)
	print(hc_1_t)