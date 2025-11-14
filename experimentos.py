import timeit
from aima.search import hill_climbing, simulated_annealing
from CamionesyPeticiones_problem import CamionesyPeticiones
from Camion_parameters import ProblemParameters
from Camion_operators import *
from Camion_state import *

# hemos modificado hill_climbing para imprimir los valores finales
"""
	def hill_climbing(problem):
    current = Node(problem.initial)
    while True:
        neighbors = current.expand(problem)
        if not neighbors:
            break
        neighbor = argmax_random_tie(neighbors, key=lambda node: problem.value(node.state))
        if problem.value(neighbor.state) <= problem.value(current.state):
            break
        current = neighbor
    print("ganancias brutas finales")
    print(current.state.ganancias_actual())
    print("coste_km finales")
    print(current.state.coste_km_actual())
    print("coste pet no serv finales")
    print(current.state.coste_petno_actual())
    print("pasos")
    print(current.state.pasos_actual())
    print("heuristic")
    print(current.state.heuristic())
    print("num peticiones servidas")
    print(current.state.num_pet_servidas())
    return current.state
	"""

if __name__ == '__main__':
	# parametros por defecto
	# ponemos prints en medio para saber en que paso estamos
	params = ProblemParameters()

	# asegurar reproducibilidad: seed del random global (aima puede usar random)
	random.seed(params.seed)

	# con la solucion inicial que consideramos adecuada
	print('Generando solucion inicial aleatoria...')
	initial_state = generar_sol_inicial_aleat(params)
	print('Solucion inicial generada.')
	print(f"Ganancias iniciales: {initial_state.ganancias_actual()}")
	print(f'Coste_km inicial: {initial_state.coste_km_actual()}')
	print(f'Coste peticiones no servidas inicial: {initial_state.coste_petno_actual()}')
	print(f'Pasos iniciales: {initial_state.pasos}')
	print(f"Heuristica inicial: {initial_state.heuristic()}")
	print('Ejecutando Hill Climbing...')
	hc_1 = hill_climbing(CamionesyPeticiones(initial_state))
	print('Hill Climbing ejecutado.')
	print(hc_1.heuristic())
    # tiempo en segundos
	hc_1_t = timeit.timeit(lambda: hill_climbing(CamionesyPeticiones(initial_state)), number=10)
	print('Tiempo de ejecucion Hill Climbing:')
	print(hc_1_t/10)
	

    # con la solucion inicial vacía
	print('Generando solucion inicial vacía...')
	initial_state = generar_sol_inicial_vacia(params)
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
	hc_1_t = timeit.timeit(lambda: hill_climbing(CamionesyPeticiones(initial_state)), number=10)
	print('Tiempo de ejecucion Hill Climbing:')
	print(hc_1_t/10)
	
    # con la solucion inicial greedy
	print('Generando solucion inicial greedy...')
	initial_state = generar_sol_inicial_greedy(params)
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
	hc_1_t = timeit.timeit(lambda: hill_climbing(CamionesyPeticiones(initial_state)), number=10)
	print('Tiempo de ejecucion Hill Climbing:')
	print(hc_1_t/10)