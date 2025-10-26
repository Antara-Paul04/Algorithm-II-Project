import math

CUSTOMER_LOCATIONS = {
    0: (0, 0, 0, 0, 1440, 0),
    1: (10, 20, 30, 60, 180, 10),
    2: (50, 40, 45, 120, 240, 15),
    3: (80, 10, 15, 0, 100, 5),
    4: (30, 70, 20, 180, 300, 10),
    5: (60, 90, 10, 240, 360, 5),
    6: (5, 50, 15, 60, 150, 8),
    7: (90, 50, 35, 200, 400, 12),
    8: (40, 10, 25, 30, 210, 10),
}

DEPOT_ID = 0
VEHICLE_CAPACITY = 100
VEHICLE_SPEED_KM_PER_MIN = 0.6
POPULATION_SIZE = 50
GENERATIONS = 500
MUTATION_RATE = 0.1
CUSTOMER_IDS = list(CUSTOMER_LOCATIONS.keys())[1:]
CAPACITY_PENALTY = 1000
TIME_WINDOW_PENALTY = 500

def euclidean_distance(id1, id2):
    x1, y1, *_ = CUSTOMER_LOCATIONS[id1]
    x2, y2, *_ = CUSTOMER_LOCATIONS[id2]
    return math.sqrt((x1 - x2)**2 + (y1 - y2)**2)

def build_route_matrix():
    matrix = {}
    ids = list(CUSTOMER_LOCATIONS.keys())
    for i in ids:
        matrix[i] = {j: euclidean_distance(i, j) for j in ids}
    return matrix

DISTANCE_MATRIX = build_route_matrix()
