import timeit
from aima.search import hill_climbing, simulated_annealing
import random
from CamionesyPeticiones_problem import CamionesyPeticiones
from Camion_parameters import ProblemParameters
from Camion_operators import *
from Camion_state import *

if __name__ == '__main__':
	# parametros por defecto
	# ponemos prints en medio para saber en que paso estamos
	params = ProblemParameters()

	# asegurar reproducibilidad: seed del random global (aima puede usar random)
	random.seed(params.seed)

    # con la solucion inicial greedy
	print('Generando solucion inicial greedy...')
	initial_state_greedy = generar_sol_inicial_greedy(params)
	print('Solucion inicial generada.')
	print('Ejecutando Hill Climbing...')
	# tiempo en segundos (ejecutar sobre una copia para aislar ejecuciones)
	hc_greedy_1_t = timeit.timeit(lambda: hill_climbing(CamionesyPeticiones(initial_state_greedy.copy())), number=1)
	print('Tiempo de ejecucion Hill Climbing:')
	print(hc_greedy_1_t)