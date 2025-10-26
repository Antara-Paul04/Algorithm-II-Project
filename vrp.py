import random
import time
from data import *

def calculate_travel_time(distance):
    return distance / VEHICLE_SPEED_KM_PER_MIN

def decode_and_evaluate(chromosome, distance_matrix):
    routes = []
    current_route = []
    current_load = 0
    current_time = 0
    total_distance = 0
    total_penalty = 0
    current_start_node = DEPOT_ID
    
    for customer_id in chromosome:
        _, _, demand, ready_time, due_time, service_time = CUSTOMER_LOCATIONS[customer_id]
        if current_load + demand > VEHICLE_CAPACITY:
            dist_to_depot = distance_matrix[current_start_node][DEPOT_ID]
            total_distance += dist_to_depot
            routes.append(current_route)
            current_route = []
            current_load = 0
            current_time = 0
            current_start_node = DEPOT_ID
        
        dist_to_customer = distance_matrix[current_start_node][customer_id]
        travel_time = calculate_travel_time(dist_to_customer)
        total_distance += dist_to_customer
        arrival_time = current_time + travel_time
        wait_time = max(0, ready_time - arrival_time)
        service_start_time = arrival_time + wait_time
        tardiness = max(0, service_start_time - due_time)
        total_penalty += tardiness * TIME_WINDOW_PENALTY
        current_time = service_start_time + service_time
        current_route.append(customer_id)
        current_load += demand
        current_start_node = customer_id
    
    if current_route:
        dist_to_depot = distance_matrix[current_start_node][DEPOT_ID]
        total_distance += dist_to_depot
        routes.append(current_route)

    total_cost = total_distance + total_penalty
    fitness = 1 / total_cost if total_cost > 0 else 0
    return fitness, total_distance, total_penalty, routes

def initialize_population(size, customer_ids):
    population = []
    for _ in range(size):
        individual = customer_ids[:]
        random.shuffle(individual)
        population.append(individual)
    return population

def select_parents(population, fitnesses, k=3):
    parents = []
    pop_fit = list(zip(population, fitnesses))
    for _ in range(2):
        tournament = random.sample(pop_fit, k)
        best_parent, _ = max(tournament, key=lambda x: x[1])
        parents.append(best_parent)
    return parents[0], parents[1]

def crossover_ox(parent1, parent2):
    size = len(parent1)
    start, end = sorted(random.sample(range(size), 2))
    child1 = [None] * size
    child1[start:end+1] = parent1[start:end+1]
    p2_sequence = [gene for gene in parent2 if gene not in child1]
    p2_idx = 0
    for i in range(size):
        if child1[i] is None:
            child1[i] = p2_sequence[p2_idx]
            p2_idx += 1
    return child1

def mutate_swap(individual, mutation_rate):
    if random.random() < mutation_rate:
        size = len(individual)
        idx1, idx2 = random.sample(range(size), 2)
        individual[idx1], individual[idx2] = individual[idx2], individual[idx1]
    return individual

def solve_vrp_ga(generations, population_size, customer_ids, mutation_rate, distance_matrix):
    population = initialize_population(population_size, customer_ids)
    best_chromosome = None
    best_fitness = -1
    best_routes = []
    best_distance = float('inf')
    print(f"Starting GA with {len(customer_ids)} customers over {generations} generations...")
    for generation in range(generations):
        results = [decode_and_evaluate(chrom, distance_matrix) for chrom in population]
        fitnesses = [r[0] for r in results]
        current_best_index = fitnesses.index(max(fitnesses))
        current_best_fitness, current_best_distance, current_best_penalty, current_best_routes = results[current_best_index]
        if current_best_fitness > best_fitness:
            best_fitness = current_best_fitness
            best_chromosome = population[current_best_index][:]
            best_distance = current_best_distance
            best_routes = current_best_routes
            print(f"Gen {generation}: New Best Cost: {1/best_fitness:.2f} (Dist: {best_distance:.2f}, Penalty: {current_best_penalty:.0f}) | Routes: {len(best_routes)}")
        new_population = []
        new_population.append(population[current_best_index][:])
        while len(new_population) < population_size:
            p1, p2 = select_parents(population, fitnesses)
            offspring = crossover_ox(p1, p2)
            offspring = mutate_swap(offspring, mutation_rate)
            new_population.append(offspring)
        population = new_population
    print("\n--- GA FINISHED ---")
    return best_chromosome, best_distance, best_routes, best_fitness

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
        current_time = 0
        current_start_node = DEPOT_ID
        route_details = f"Route {i+1}: Depot (Time 00:00)"
        for customer_id in route:
            _, _, _, ready_time, due_time, service_time = CUSTOMER_LOCATIONS[customer_id]
            dist = DISTANCE_MATRIX[current_start_node][customer_id]
            travel_time = calculate_travel_time(dist)
            arrival_time = current_time + travel_time
            wait_time = max(0, ready_time - arrival_time)
            service_start_time = arrival_time + wait_time
            service_end_time = service_start_time + service_time
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
        dist_to_depot = DISTANCE_MATRIX[current_start_node][DEPOT_ID]
        travel_time_to_depot = calculate_travel_time(dist_to_depot)
        return_time = current_time + travel_time_to_depot
        route_details += f" -> Depot (Return: {to_h_mm(return_time)})"
        print(route_details)
        print(f"  Customers: {route}")
    print("-" * 30)
