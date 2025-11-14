import timeit
from aima.search import hill_climbing, simulated_annealing, exp_schedule
from CamionesyPeticiones_problem import CamionesyPeticiones
from CamionesyPeticiones_problem_SA import CamionesyPeticionesSA
from Camion_parameters import ProblemParameters
from Camion_operators import *
from Camion_state_SA import *

# tambien hemos modificado simulated_annealing para imprimir los valores finales

"""
def simulated_annealing(problem, schedule=exp_schedule()):
    current = Node(problem.initial)
    for t in range(sys.maxsize):
        T = schedule(t)
        if T == 0:
            print("pasos")
            print(current.state.pasos_actual())
            print("heuristic")
            print(current.state.heuristic())
            print("num peticiones servidas")
            print(current.state.num_pet_servidas())
            print("ganancias brutas finales")
            print(current.state.ganancias_actual())
            print("coste_km finales")
            print(current.state.coste_km_actual())
            print("coste pet no serv finales")
            print(current.state.coste_petno_actual())
            return current.state
        neighbors = current.expand(problem)
        if not neighbors:
            print("pasos")
            print(current.state.pasos_actual())
            print("heuristic")
            print(current.state.heuristic())
            print("pasos")
            print(current.state.pasos_actual())
            print("heuristic")
            print(current.state.heuristic())
            print("num peticiones servidas")
            print(current.state.num_pet_servidas())
            print("ganancias brutas finales")
            print(current.state.ganancias_actual())
            print("coste_km finales")
            print(current.state.coste_km_actual())
            print("coste pet no serv finales")
            print(current.state.coste_petno_actual())
            return current.state
        next_choice = random.choice(neighbors)
        delta_e = problem.value(next_choice.state) - problem.value(current.state)
        if delta_e > 0 or probability(np.exp(delta_e / T)):
            current = next_choice
    
"""

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
    schedule = exp_schedule(k=20, lam=0.025, limit=10000)
    # sa_state = simulated_annealing(problem, schedule)
    # print('Simulated Annealing ejecutado.')
    # print(f'Heuristica SA: {sa_state.heuristic()}')
    sa_t = timeit.timeit(lambda: simulated_annealing(problem, schedule), number=10)
    print('Tiempo de ejecucion Simulated Annealing:')
    print(sa_t/10)


if __name__ == '__main__':
    # parametros por defecto
    params = ProblemParameters()

    # definir seed para reproducibilidad
    random.seed(params.seed)
    
    """
    # Aleatoria
    print('Generando solucion inicial aleatoria...')
    initial_state = generar_sol_inicial_aleat(params)
    run_experiments_for_initial('Inicial Aleatoria', initial_state)
    """

    # Vacía
    print('\nGenerando solucion inicial vacía...')
    initial_state = generar_sol_inicial_vacia(params)
    run_experiments_for_initial('Inicial Vacía', initial_state)

    """
    # Greedy
    print('\nGenerando solucion inicial greedy...')
    initial_state = generar_sol_inicial_greedy(params)
    run_experiments_for_initial('Inicial Greedy', initial_state)
    """