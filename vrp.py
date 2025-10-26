import random
import math
import time

# --- 1. PROBLEM DATA & CONSTANTS ---

# Customer Data Format: (ID): (x, y, demand, ready_time, due_time, service_time)
# Time is measured in minutes from the start of the day (0 min).
# Distance unit is generic (e.g., kilometers).
# Ready/Due times are for customer service start.
CUSTOMER_LOCATIONS = {
    0: (0, 0, 0, 0, 1440, 0),      # Depot (ID 0)
    1: (10, 20, 30, 60, 180, 10),  # Customer 1: (10, 20), Demand: 30, TW: 1hr-3hr, Service: 10min
    2: (50, 40, 45, 120, 240, 15), # Customer 2
    3: (80, 10, 15, 0, 100, 5),    # Customer 3
    4: (30, 70, 20, 180, 300, 10), # Customer 4
    5: (60, 90, 10, 240, 360, 5),  # Customer 5
    6: (5, 50, 15, 60, 150, 8),    # Customer 6
    7: (90, 50, 35, 200, 400, 12), # Customer 7
    8: (40, 10, 25, 30, 210, 10),  # Customer 8
}

DEPOT_ID = 0
VEHICLE_CAPACITY = 100 # Max load in units (kg, boxes, etc.)
VEHICLE_SPEED_KM_PER_MIN = 0.6  # Example: 36 km/h (0.6 km/min)

# GA Parameters
POPULATION_SIZE = 50
GENERATIONS = 500
MUTATION_RATE = 0.1
CUSTOMER_IDS = list(CUSTOMER_LOCATIONS.keys())[1:] # [1, 2, 3, 4, 5, 6, 7, 8]

# Penalty Multipliers (HIGH penalties enforce constraints)
CAPACITY_PENALTY = 1000  # Cost per unit of capacity excess
TIME_WINDOW_PENALTY = 500  # Cost per minute of tardiness

# --- 2. HELPER FUNCTIONS ---

def euclidean_distance(id1, id2):
    """Calculates the Euclidean distance between two customer locations."""
    x1, y1, *_ = CUSTOMER_LOCATIONS[id1]
    x2, y2, *_ = CUSTOMER_LOCATIONS[id2]
    return math.sqrt((x1 - x2)**2 + (y1 - y2)**2)

def calculate_travel_time(distance):
    """Converts distance to travel time in minutes."""
    return distance / VEHICLE_SPEED_KM_PER_MIN

def build_route_matrix():
    """Pre-calculates all distances between all stops."""
    matrix = {}
    ids = list(CUSTOMER_LOCATIONS.keys())
    for i in ids:
        matrix[i] = {j: euclidean_distance(i, j) for j in ids}
    return matrix

DISTANCE_MATRIX = build_route_matrix()

# --- 3. CORE FITNESS FUNCTION ---

def decode_and_evaluate(chromosome, distance_matrix):
    """
    Decodes a customer permutation (chromosome) into a set of feasible routes,
    calculates fitness based on distance and applies penalties for constraints.

    The decoding uses a greedy approach: start a new route whenever capacity is exceeded.
    Returns: (total_cost, total_distance, routes_list)
    """
    routes = []
    current_route = []
    current_load = 0
    current_time = 0  # Time at the depot (start of the route)
    total_distance = 0
    total_penalty = 0

    # Start the first route
    current_start_node = DEPOT_ID
    
    for customer_id in chromosome:
        _, _, demand, ready_time, due_time, service_time = CUSTOMER_LOCATIONS[customer_id]
        
        # 1. Check Capacity Constraint
        if current_load + demand > VEHICLE_CAPACITY:
            # Capacity exceeded, finish the current route and start a new one.
            
            # Distance from last stop to depot
            dist_to_depot = distance_matrix[current_start_node][DEPOT_ID]
            total_distance += dist_to_depot
            
            # Route closing penalty check (return time must be acceptable, though often relaxed)
            # Not explicitly checked here, as TW constraints focus on customer visits.

            routes.append(current_route)
            
            # Reset for new route
            current_route = []
            current_load = 0
            current_time = 0
            current_start_node = DEPOT_ID

        # --- If capacity is OK, add the customer to the current route ---
        
        # Distance from previous node to current customer
        dist_to_customer = distance_matrix[current_start_node][customer_id]
        travel_time = calculate_travel_time(dist_to_customer)
        total_distance += dist_to_customer

        # 2. Time Window Constraint Check
        arrival_time = current_time + travel_time
        
        wait_time = max(0, ready_time - arrival_time)
        service_start_time = arrival_time + wait_time
        
        # Calculate tardiness (if arrival is after due_time)
        tardiness = max(0, service_start_time - due_time)
        total_penalty += tardiness * TIME_WINDOW_PENALTY
        
        # Update current time to time after service completion
        current_time = service_start_time + service_time
        
        # Update route state
        current_route.append(customer_id)
        current_load += demand
        current_start_node = customer_id
    
    # After processing all customers, close the final route
    if current_route:
        dist_to_depot = distance_matrix[current_start_node][DEPOT_ID]
        total_distance += dist_to_depot
        routes.append(current_route)

    # Note: We don't need a separate penalty for capacity violation in this approach,
    # because the routing mechanism *prevents* single routes from exceeding capacity.
    # We only penalize time violations.

    total_cost = total_distance + total_penalty
    
    # Fitness is the reciprocal of the total cost (minimization problem)
    fitness = 1 / total_cost if total_cost > 0 else 0
    
    return fitness, total_distance, total_penalty, routes

# --- 4. GENETIC ALGORITHM OPERATORS ---

def initialize_population(size, customer_ids):
    """Creates a randomly shuffled initial population."""
    population = []
    for _ in range(size):
        individual = customer_ids[:]
        random.shuffle(individual)
        population.append(individual)
    return population

def select_parents(population, fitnesses, k=3):
    """Tournament Selection: Selects the fittest individual from k random individuals."""
    parents = []
    pop_fit = list(zip(population, fitnesses))

    for _ in range(2): # Select two parents
        tournament = random.sample(pop_fit, k)
        # Sort by fitness (higher is better) and pick the best one
        best_parent, _ = max(tournament, key=lambda x: x[1])
        parents.append(best_parent)
    return parents[0], parents[1]

def crossover_ox(parent1, parent2):
    """Order Crossover (OX) for permutation encoding."""
    size = len(parent1)
    # 1. Select a random segment
    start, end = sorted(random.sample(range(size), 2))

    # 2. Child 1: Copy segment from parent 1
    child1 = [None] * size
    child1[start:end+1] = parent1[start:end+1]

    # 3. Fill remaining genes from parent 2, maintaining order
    p2_sequence = [gene for gene in parent2 if gene not in child1]
    
    p2_idx = 0
    for i in range(size):
        if child1[i] is None:
            child1[i] = p2_sequence[p2_idx]
            p2_idx += 1
    
    # For simplicity, only return one child
    return child1

def mutate_swap(individual, mutation_rate):
    """Simple Swap Mutation: Swaps two random customers."""
    if random.random() < mutation_rate:
        size = len(individual)
        # Choose two distinct positions
        idx1, idx2 = random.sample(range(size), 2)
        individual[idx1], individual[idx2] = individual[idx2], individual[idx1]
    return individual

# --- 5. MAIN VRP SOLVER ---

def solve_vrp_ga(generations, population_size, customer_ids, mutation_rate, distance_matrix):
    """Executes the Genetic Algorithm to solve the VRP-TW."""
    
    # 1. Initialization
    population = initialize_population(population_size, customer_ids)
    
    best_chromosome = None
    best_fitness = -1
    best_routes = []
    best_distance = float('inf')
    
    print(f"Starting GA with {len(customer_ids)} customers over {generations} generations...")

    for generation in range(generations):
        
        # 2. Evaluation
        results = [decode_and_evaluate(chrom, distance_matrix) for chrom in population]
        fitnesses = [r[0] for r in results]
        
        # Find current best solution
        current_best_index = fitnesses.index(max(fitnesses))
        current_best_fitness, current_best_distance, current_best_penalty, current_best_routes = results[current_best_index]

        # 3. Update Global Best
        if current_best_fitness > best_fitness:
            best_fitness = current_best_fitness
            best_chromosome = population[current_best_index][:]
            best_distance = current_best_distance
            best_routes = current_best_routes
            
            print(f"Gen {generation}: New Best Cost: {1/best_fitness:.2f} (Dist: {best_distance:.2f}, Penalty: {current_best_penalty:.0f}) | Routes: {len(best_routes)}")

        # 4. Generate New Population
        new_population = []
        # Elitism: keep the best solution from the current generation
        new_population.append(population[current_best_index][:])

        while len(new_population) < population_size:
            # Selection
            p1, p2 = select_parents(population, fitnesses)
            
            # Crossover
            offspring = crossover_ox(p1, p2)
            
            # Mutation
            offspring = mutate_swap(offspring, mutation_rate)
            
            new_population.append(offspring)
            
        population = new_population

    print("\n--- GA FINISHED ---")
    return best_chromosome, best_distance, best_routes, best_fitness

# --- 6. EXECUTION ---

if __name__ == "__main__":
    start_time = time.time()
    
    final_chromosome, final_distance, final_routes, final_fitness = solve_vrp_ga(
        GENERATIONS, POPULATION_SIZE, CUSTOMER_IDS, MUTATION_RATE, DISTANCE_MATRIX
    )
    
    total_cost = 1 / final_fitness if final_fitness > 0 else float('inf')
    
    print(f"\nOptimization Time: {time.time() - start_time:.2f} seconds")
    print("\n--- BEST SOLUTION FOUND ---")
    print(f"Total Cost (Distance + Penalty): {total_cost:.2f}")
    print(f"Total Travel Distance: {final_distance:.2f} (Units)")
    print(f"Number of Vehicles Used: {len(final_routes)}")
    print("-" * 30)

    for i, route in enumerate(final_routes):
        # Calculate time metrics for the final printout
        current_time = 0
        current_start_node = DEPOT_ID
        route_details = f"Route {i+1}: Depot (Time 00:00)"

        for customer_id in route:
            _, _, _, ready_time, due_time, service_time = CUSTOMER_LOCATIONS[customer_id]
            
            # Travel time calculation
            dist = DISTANCE_MATRIX[current_start_node][customer_id]
            travel_time = calculate_travel_time(dist)
            
            arrival_time = current_time + travel_time
            wait_time = max(0, ready_time - arrival_time)
            service_start_time = arrival_time + wait_time
            service_end_time = service_start_time + service_time
            
            # Convert minutes to H:MM format for display
            def to_h_mm(minutes):
                h = int(minutes // 60)
                m = int(minutes % 60)
                return f"{h:02d}:{m:02d}"
                
            start_h_mm = to_h_mm(service_start_time)
            end_h_mm = to_h_mm(service_end_time)
            tw_h_mm = f"[{to_h_mm(ready_time)} - {to_h_mm(due_time)}]"

            route_details += f" -> C{customer_id} (Arrive: {to_h_mm(arrival_time)}, Service: {start_h_mm} - {end_h_mm}, TW: {tw_h_mm})"
            
            current_time = service_end_time
            current_start_node = customer_id
        
        # Return to Depot
        dist_to_depot = DISTANCE_MATRIX[current_start_node][DEPOT_ID]
        travel_time_to_depot = calculate_travel_time(dist_to_depot)
        return_time = current_time + travel_time_to_depot
        
        route_details += f" -> Depot (Return: {to_h_mm(return_time)})"
        
        print(route_details)
        print(f"  Customers: {route}")
    print("-" * 30)
