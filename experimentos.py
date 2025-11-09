import timeit
from aima.search import hill_climbing, simulated_annealing
from CamionesyPeticiones_problem import CamionesyPeticiones
from Camion_parameters import ProblemParameters
from Camion_operators import *
from Camion_state import *

if __name__ == '__main__':
	# parametros por defecto
	params = ProblemParameters()
	initial_state = generar_sol_inicial(params)
	n = hill_climbing(CamionesyPeticiones(initial_state))
	print(n)
	print(n.heuristic())



	# Suposant que la funció mesurar s'astar_search
	# i volem fer una e x e c u c i :
	time = timeit.timeit(lambda: hill_climbing(CamionesyPeticiones(initial_state)), number=1)
	print(time) # Retorna temps en segons