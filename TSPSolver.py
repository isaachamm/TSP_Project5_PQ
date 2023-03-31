#!/usr/bin/python3
import math

# from which_pyqt import PYQT_VER
# if PYQT_VER == 'PYQT5':
from PyQt5.QtCore import QLineF, QPointF
# elif PYQT_VER == 'PYQT4':
# 	from PyQt4.QtCore import QLineF, QPointF
# elif PYQT_VER == 'PYQT6':
# 	from PyQt6.QtCore import QLineF, QPointF
# else:
# 	raise Exception('Unsupported Version of PyQt: {}'.format(PYQT_VER))


import time
import numpy as np
from TSPClasses import *
import heapq
import itertools


class TSPSolver:
    def __init__(self, gui_view):
        self._scenario = None

    def setupWithScenario(self, scenario):
        self._scenario = scenario

    ''' <summary>
		This is the entry point for the default solver
		which just finds a valid random tour.  Note this could be used to find your
		initial BSSF.
		</summary>
		<returns>results dictionary for GUI that contains three ints: cost of solution,
		time spent to find solution, number of permutations tried during search, the
		solution found, and three null values for fields not used for this
		algorithm</returns>
	'''

    def defaultRandomTour(self, time_allowance=60.0):
        results = {}
        cities = self._scenario.getCities()
        ncities = len(cities)
        foundTour = False
        count = 0
        bssf = None
        start_time = time.time()
        while not foundTour and time.time() - start_time < time_allowance:
            # create a random permutation
            perm = np.random.permutation(ncities)
            route = []
            # Now build the route using the random permutation
            for i in range(ncities):
                route.append(cities[perm[i]])
            bssf = TSPSolution(route)
            count += 1
            if bssf.cost < np.inf:
                # Found a valid route
                foundTour = True
        end_time = time.time()
        results['cost'] = bssf.cost if foundTour else math.inf
        results['time'] = end_time - start_time
        results['count'] = count
        results['soln'] = bssf
        results['max'] = None
        results['total'] = None
        results['pruned'] = None
        return results

    ''' <summary>
		This is the entry point for the greedy solver, which you must implement for
		the group project (but it is probably a good idea to just do it for the branch-and
		bound project as a way to get your feet wet).  Note this could be used to find your
		initial BSSF.
		</summary>
		<returns>results dictionary for GUI that contains three ints: cost of best solution,
		time spent to find best solution, total number of solutions found, the best
		solution found, and three null values for fields not used for this
		algorithm</returns>
	'''

    def greedy(self, time_allowance=60.0):

        # use seed 232 on hard(deterministic) to debug for multiple routes
        # Check seed 532 on hard(determinsitic) to debug for missing a city? (J)

        results = {}
        cities = self._scenario.getCities()
        ncities = len(cities)
        foundTour = False
        count = 0
        bssf = math.inf
        visited = {}

        start_time = time.time()

        route = []

        # This variable changes our start city until the algorithm finds a route -- different start cities give
        #   different routes, so this helps us find a route if our initial attempt doesn't work
        city_counter = 0
        start_city = cities[city_counter]
        city_counter += 1
        curr_city = start_city
        route.append(curr_city)

        while not foundTour and time.time() - start_time < time_allowance:
            minimum_cost = math.inf
            minimum_city = None

            for i in range(ncities):

                if cities[i] == curr_city or cities[i] in route:
                    continue
                distance = curr_city.costTo(cities[i])
                if distance < minimum_cost:
                    minimum_cost = distance
                    minimum_city = cities[i]

            if minimum_city is None:
                bssf = TSPSolution(route)
                count += 1
                if bssf.cost < math.inf:
                    # Found a valid route
                    foundTour = True
                    break
                else:
                    start_city = cities[city_counter]
                    city_counter += 1
                    if city_counter >= ncities - 1:
                        break
                    curr_city = start_city
                    route.clear()
                    route.append(curr_city)
                    continue

            curr_city = minimum_city
            route.append(curr_city)

        end_time = time.time()
        results['cost'] = bssf.cost if foundTour else math.inf
        results['time'] = end_time - start_time
        results['count'] = count
        results['soln'] = bssf
        results['max'] = None
        results['total'] = None
        results['pruned'] = None
        return results

    ''' <summary>
		This is the entry point for the branch-and-bound algorithm that you will implement
		</summary>
		<returns>results dictionary for GUI that contains three ints: cost of best solution,
		time spent to find best solution, total number solutions found during search (does
		not include the initial BSSF), the best solution found, and three more ints:
		max queue size, total number of states created, and number of pruned states.</returns>
	'''

    def branchAndBound(self, time_allowance=60.0):

        results = {}
        cities = self._scenario.getCities()
        ncities = len(cities)
        foundTour = False
        bssf_updated_count = 0
        max_states_held = 0
        total_states_made = 0
        states_pruned = 0

        # Get our initial BSSF from greedy, or if that doesn't work, do random
        bssf = TSPSolver.greedy(self)["soln"]
        if bssf.cost == math.inf:
            bssf = TSPSolver.defaultRandomTour(self)["soln"]

        start_time = time.time()

        # This is our set of possible problems to approach
        state_subproblems = {}
        # This assigns id's to every state matrix that we create

        initial_subproblem = Matrix(ncities)
        initial_subproblem.state_id = total_states_made

        # This nested for loop creates our initial matrix with the graph's values
        for i in range(ncities):
            for j in range(ncities):
                if i == j:
                    initial_subproblem.matrix[i][j] = math.inf
                    continue
                initial_subproblem.matrix[i][j] = cities[i].costTo(cities[j])

        # Add our initial subproblem to the queue
        state_subproblems[total_states_made] = initial_subproblem
        total_states_made += 1

        initial_subproblem.reduce_matrix()

        while state_subproblems and time.time() - start_time < time_allowance:

            # Update our max states held, if necessary
            if len(state_subproblems) > max_states_held:
                max_states_held = len(state_subproblems)

            # Find the minimum cost matrix in the queue
            # TODO: come up with a more sophisticated way to choose the next state to expand
            minimum_sp_id = -1
            minimum_matrix_cost = math.inf
            for sp in state_subproblems.values():
                if sp.cost_of_matrix < minimum_matrix_cost:
                    minimum_matrix_cost = sp.cost_of_matrix
                    minimum_sp_id = sp.state_id

            matrix_to_expand = state_subproblems[minimum_sp_id]

            # Expanding
            for i in range(ncities):

                # This checks to see if our matrix is state 1 – in which case, we need to check all paths (x and y)
                if not matrix_to_expand.cities_visited:

                    for j in range(ncities):

                        if i == j:
                            continue

                        new_matrix = Matrix(ncities)
                        new_matrix.reset_matrix(matrix_to_expand)
                        new_matrix.set_id(total_states_made)
                        total_states_made += 1

                        new_matrix.cities_visited.append(i)
                        new_matrix.cities_visited.append(j)

                        # Set columns and rows to inf
                        for k in range(ncities):
                            new_matrix.matrix[i][k] = math.inf
                            new_matrix.matrix[k][j] = math.inf

                        # Set back-pointer to inf
                        new_matrix.matrix[j][i] = math.inf

                        new_matrix.reduce_matrix()

                        if new_matrix.cost_of_matrix < bssf.cost:
                            state_subproblems[new_matrix.state_id] = new_matrix






            route = []

        end_time = time.time()
        results['cost'] = bssf.cost if foundTour else math.inf
        results['time'] = end_time - start_time
        results['count'] = bssf_updated_count
        results['soln'] = bssf
        results['max'] = max_states_held
        results['total'] = None
        results['pruned'] = None
        return results

    ''' <summary>
		This is the entry point for the algorithm you'll write for your group project.
		</summary>
		<returns>results dictionary for GUI that contains three ints: cost of best solution,
		time spent to find best solution, total number of solutions found during search, the
		best solution found.  You may use the other three field however you like.
		algorithm</returns>
	'''

    def fancy(self, time_allowance=60.0):
        pass
