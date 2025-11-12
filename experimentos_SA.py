import timeit
from aima.search import hill_climbing, simulated_annealing, exp_schedule
from CamionesyPeticiones_problem import CamionesyPeticiones
from CamionesyPeticiones_problem_SA import CamionesyPeticionesSA
from Camion_parameters import ProblemParameters
from Camion_operators import *
from Camion_state_SA import *


def run_experiments_for_initial(name: str, initial_state):
    print(f'\n===== {name} =====')
    print('Solucion inicial generada.')
    print(f"Ganancias iniciales: {initial_state.ganancias_actual()}")
    print(f'Coste_km inicial: {initial_state.coste_km_actual()}')
    print(f'Coste peticiones no servidas inicial: {initial_state.coste_petno_actual()}')
    print(f'Pasos iniciales: {initial_state.pasos}')
    print(f"Heuristica inicial: {initial_state.heuristic()}")

    # Para SA usamos el problema que genera un solo sucesor aleatorio
    problem = CamionesyPeticionesSA(initial_state)
    # Simulated Annealing
    print('Ejecutando Simulated Annealing...')
    schedule = exp_schedule(k=20, lam=0.005, limit=1000)
    sa_state = simulated_annealing(problem, schedule)
    print('Simulated Annealing ejecutado.')
    print(f'Heuristica SA: {sa_state.heuristic()}')
    sa_t = timeit.timeit(lambda: simulated_annealing(problem, schedule), number=1)
    print('Tiempo de ejecucion Simulated Annealing:')
    print(sa_t)


if __name__ == '__main__':
    # parametros por defecto
    params = ProblemParameters()

    # Aleatoria
    print('Generando solucion inicial aleatoria...')
    initial_state = generar_sol_inicial_aleat(params)
    run_experiments_for_initial('Inicial Aleatoria', initial_state)

    # Vacía
    print('\nGenerando solucion inicial vacía...')
    initial_state = generar_sol_inicial_vacia(params)
    run_experiments_for_initial('Inicial Vacía', initial_state)

    # Greedy
    print('\nGenerando solucion inicial greedy...')
    initial_state = generar_sol_inicial_greedy(params)
    run_experiments_for_initial('Inicial Greedy', initial_state)