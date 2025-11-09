import timeit
from aima.search import hill_climbing, simulated_annealing
from CamionesyPeticiones_problem import CamionesyPeticiones
from Camion_parameters import ProblemParameters
from Camion_operators import *
from Camion_state_opt import *

if __name__ == '__main__':
	# parametros por defecto
	# ponemos prints en medio para saber en que paso estamos
	params = ProblemParameters()
	# con la solucion inicial que consideramos adecuada
	print('Generando solucion inicial...')
	initial_state = generar_sol_inicial(params)
	print('Solucion inicial generada.')
	print(f"Ganancias iniciales: {initial_state.ganancias_actual()}")
	print(f'Coste_km inicial: {initial_state.coste_km_actual()}')
	print(f'Coste peticiones no servidas inicial: {initial_state.coste_petno_actual()}')
	print(f"Heuristica inicial: {initial_state.heuristic()}")
	print('Ejecutando Hill Climbing...')
	hc_1 = hill_climbing(CamionesyPeticiones(initial_state))
	print('Hill Climbing ejecutado.')
	print(hc_1.heuristic())
    # tiempo en segundos
	hc_1_t = timeit.timeit(lambda: hill_climbing(CamionesyPeticiones(initial_state)), number=1)
	print('Tiempo de ejecucion Hill Climbing:')
	print(hc_1_t)