# data.py
import requests
import math
import sys
import time

# --- Constants ---
DEFAULT_DEMAND = 10
DEFAULT_SERVICE_TIME = 15 # in minutes
DEFAULT_READY_TIME_STR = "00:00"
DEFAULT_DUE_TIME_STR = "23:59"

DEPOT_ID = 0
VEHICLE_CAPACITY = 100
POPULATION_SIZE = 50
GENERATIONS = 500
MUTATION_RATE = 0.1
CAPACITY_PENALTY = 1000
TIME_WINDOW_PENALTY = 500

# --- Helper function to parse time ---
def parse_hhmm_to_minutes(time_str, default_minutes):
    """
    Parses a 'HH:MM' string into minutes.
    Returns default_minutes if the string is empty.
    """
    if not time_str:
        return default_minutes
        
    try:
        parts = time_str.split(':')
        if len(parts) == 2:
            h = int(parts[0])
            m = int(parts[1])
        elif len(parts) == 1:
            h = int(parts[0])
            m = 0
        else:
            raise ValueError
            
        if not (0 <= h <= 23 and 0 <= m <= 59):
            print(f"  > Invalid time '{time_str}'. Using default.")
            return default_minutes
            
        return (h * 60) + m
        
    except ValueError:
        print(f"  > Invalid time format '{time_str}'. Using default.")
        return default_minutes

# --- METHOD 1: Get data interactively from user ---
def get_interactive_data():
    """
    Interactively prompts the user for coordinates and constraints.
    """
    print("--- 🚚 Vehicle Routing Problem: Data Entry (Manual Coordinates) ---")
    print("How to find coordinates: Go to Google Maps, right-click on a spot,")
    print("and the coordinates (e.g., '22.97, 88.43') will appear. Click to copy.")
    
    customer_locations = {} # For demand, time, etc.
    customer_coordinates = {} # For lat/lng
    
    # 1. Get Depot Coordinates
    depot_coords_str = input(f"\nDepot (ID 0) Coordinates (Lat, Lng): ")
    if not depot_coords_str:
        depot_coords_str = "22.9749, 88.4345" # Default to Kalyani
    
    # OSRM wants 'lng,lat'
    try:
        lat, lng = depot_coords_str.split(',')
        customer_coordinates[DEPOT_ID] = f"{lng.strip()},{lat.strip()}"
    except Exception:
        print("Invalid format. Using default Kalyani coordinates.")
        customer_coordinates[DEPOT_ID] = "88.4345,22.9749"
        
    customer_locations[DEPOT_ID] = ("Depot", 0, 0, 1440, 0) 
    print(f"Depot set at: {customer_coordinates[DEPOT_ID]}")
    
    # 2. Get Customer Data
    try:
        num_customers = int(input("\nHow many customers do you want to plan for (e.g., 3)? "))
        if num_customers <= 0:
            raise ValueError
    except ValueError:
        print("Invalid number. Defaulting to 3 customers.")
        num_customers = 3
        
    customer_ids = list(range(1, num_customers + 1))
    
    default_ready_min = parse_hhmm_to_minutes(DEFAULT_READY_TIME_STR, 0)
    default_due_min = parse_hhmm_to_minutes(DEFAULT_DUE_TIME_STR, 1440)
    
    for i in customer_ids:
        print(f"\n--- Enter details for Customer {i} ---")
        
        coords_str = input(f"  Coordinates for C{i} (Lat, Lng): ")
        try:
            lat, lng = coords_str.split(',')
            customer_coordinates[i] = f"{lng.strip()},{lat.strip()}"
        except Exception:
            print("  Invalid format. Please re-run. Exiting.")
            sys.exit()
        
        demand_str = input(f"  Demand for C{i} (default: {DEFAULT_DEMAND}): ")
        demand = int(demand_str) if demand_str else DEFAULT_DEMAND
        
        ready_str = input(f"  Ready Time [HH:MM] (default: {DEFAULT_READY_TIME_STR}): ")
        ready_time = parse_hhmm_to_minutes(ready_str, default_ready_min)
        
        due_str = input(f"  Due Time [HH:MM] (default: {DEFAULT_DUE_TIME_STR}): ")
        due_time = parse_hhmm_to_minutes(due_str, default_due_min)
        
        service_str = input(f"  Service Time in mins (default: {DEFAULT_SERVICE_TIME}): ")
        service_time = int(service_str) if service_str else DEFAULT_SERVICE_TIME
        
        if ready_time > due_time:
            print(f"  > Warning: Ready Time is after Due Time. Using defaults.")
            ready_time = default_ready_min
            due_time = default_due_min
            
        customer_locations[i] = (f"Customer {i}", demand, ready_time, due_time, service_time)
        
    return customer_locations, customer_ids, customer_coordinates

# --- METHOD 2: Get hard-coded test data ---
def get_hardcoded_data():
    """
    Returns a pre-defined set of 8 customers in Kalyani.
    """
    print("--- 🚚 Vehicle Routing Problem: Using Hard-coded Test Data (8 Customers in Kalyani) ---")
    
    # Coordinates are in OSRM format: "longitude,latitude"
    # Found using Google Maps (Right-click -> Copy coordinates)
    customer_coordinates = {
        0: "88.4345,22.9749", # Depot: Kalyani City
        1: "88.4394,22.9818", # C1: ITI More
        2: "88.4504,22.9859", # C2: Buddha Park
        3: "88.4328,22.9903", # C3: IIIT Kalyani
        4: "88.4526,22.9710", # C4: Kalyani Ghoshpara Station
        5: "88.4589,22.9898", # C5: Kalyani University
        6: "88.4402,22.9698", # C6: JNM Hospital
        7: "88.4468,22.9788", # C7: Kalyani Central Park
        8: "88.4632,22.9822", # C8: Kalyani Main Station
    }
    
    # Times are in minutes from midnight (e.g., 9 AM = 540)
    customer_locations = {
        # ID: ("Name", Demand, Ready Time, Due Time, Service Time)
        0: ("Depot", 0, 0, 1440, 0),
        1: ("C1: ITI More", 15, 540, 720, 10),    # 9:00 AM - 12:00 PM
        2: ("C2: Buddha Park", 20, 540, 1020, 15), # 9:00 AM - 5:00 PM
        3: ("C3: IIIT Kalyani", 10, 600, 840, 10),    # 10:00 AM - 2:00 PM
        4: ("C4: Ghoshpara Stn", 25, 720, 1080, 20), # 12:00 PM - 6:00 PM
        5: ("C5: Kalyani Uni", 15, 540, 720, 10),    # 9:00 AM - 12:00 PM
        6: ("C6: JNM Hospital", 30, 0, 1440, 25),   # All day
        7: ("C7: Central Park", 10, 960, 1140, 10), # 4:00 PM - 7:00 PM
        8: ("C8: Kalyani Main", 20, 780, 960, 15),   # 1:00 PM - 4:00 PM
    }

    # Total Demand = 145. This will require at least 2 trucks (Capacity 100).
    
    customer_ids = list(range(1, 9)) # Customer IDs are 1 through 8
    
    return customer_locations, customer_ids, customer_coordinates


def build_osrm_matrices(coordinates):
    """
    Calls the free OSRM public server to build matrices.
    (This function is unchanged)
    """
    print("\nConnecting to OSRM server to build matrices...")
    
    ids_in_order = list(coordinates.keys())
    coords_string = ";".join(coordinates[i] for i in ids_in_order)
    
    url = f"http://router.project-osrm.org/table/v1/driving/{coords_string}"
    params = {
        'annotations': 'duration,distance'
    }
    
    try:
        response = requests.get(url, params=params).json()
        
        if response['code'] != 'Ok':
            print(f"Error from OSRM: {response['message']}")
            return None, None
            
        if 'distances' not in response or 'durations' not in response:
            print("Error: OSRM returned 'Ok' but did not provide matrices.")
            return None, None
            
        durations = response['durations']
        distances = response['distances']
        
        distance_matrix = {}
        time_matrix = {}
        
        for i, origin_id in enumerate(ids_in_order):
            distance_matrix[origin_id] = {}
            time_matrix[origin_id] = {}
            for j, dest_id in enumerate(ids_in_order):
                
                if distances[i][j] is None or durations[i][j] is None:
                    distance_km = float('inf')
                    time_min = float('inf')
                else:
                    distance_km = distances[i][j] / 1000.0
                    time_min = durations[i][j] / 60.0
                
                distance_matrix[origin_id][dest_id] = distance_km
                time_matrix[origin_id][dest_id] = time_min
                
        print("Successfully built distance and time matrices from OSRM.")
        return distance_matrix, time_matrix

    except requests.exceptions.ConnectionError as e:
        print(f"  Error: Connection failed to OSRM. {e}")
        return None, None
    except Exception as e:
        print(f"An error occurred while calling OSRM: {e}")
        return None, None

# --- Main execution block for data.py ---

# --- CHOOSE YOUR METHOD ---

# METHOD 1: Interactive User Input
# To use, uncomment the line below and comment out METHOD 2
# CUSTOMER_LOCATIONS, CUSTOMER_IDS, CUSTOMER_COORDINATES = get_interactive_data()

# METHOD 2: Hard-coded 8-Customer Test (Kalyani)
# To use, keep this line uncommented. Comment out METHOD 1.
CUSTOMER_LOCATIONS, CUSTOMER_IDS, CUSTOMER_COORDINATES = get_hardcoded_data()
# --- End of choice ---


# This part runs after your choice
print(f"Building route matrices for {len(CUSTOMER_IDS)} customers...")
DISTANCE_MATRIX, TRAVEL_TIME_MATRIX = build_osrm_matrices(CUSTOMER_COORDINATES)

if DISTANCE_MATRIX is None:
    print("CRITICAL ERROR: Could not build matrices. Exiting.")
    sys.exit()

