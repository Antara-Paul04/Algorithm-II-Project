# data.py
import requests
import math
import sys
import time

# --- NEW: Constants for our defaults ---
DEFAULT_DEMAND = 10
DEFAULT_SERVICE_TIME = 15 # in minutes
DEFAULT_READY_TIME_STR = "00:00"
DEFAULT_DUE_TIME_STR = "23:59"
# --- End New ---

# --- Constants ---
DEPOT_ID = 0
VEHICLE_CAPACITY = 100
POPULATION_SIZE = 50
GENERATIONS = 500
MUTATION_RATE = 0.1
CAPACITY_PENALTY = 1000
TIME_WINDOW_PENALTY = 500

# --- FIX: THIS IS THE "ID CARD" NOMINATIM REQUIRES ---
NOMINATIM_HEADERS = {'Neeraj': 'VRP-Python-Project (alwaysneerudj@gmail.com)'}

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

# --- The main user input function ---
def get_customer_data_from_user():
    """
    Interactively prompts the user to build the customer data,
    using smart defaults and HH:MM time.
    """
    print("--- 🚚 Vehicle Routing Problem: Data Entry (User-Friendly) ---")
    
    depot_address = "Kalyani, Nadia, West Bengal, India"
    print(f"Depot (ID {DEPOT_ID}) is set to: {depot_address}\n")
    
    customer_locations = {
        DEPOT_ID: (depot_address, 0, 0, 1440, 0) 
    }
    
    try:
        num_customers = int(input("How many customers do you want to plan for (e.g., 3)? "))
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
        
        address = input(f"  Address for C{i} (e.g., 'iti more'): ")
        
        demand_str = input(f"  Demand for C{i} (default: {DEFAULT_DEMAND}): ")
        demand = int(demand_str) if demand_str else DEFAULT_DEMAND
        
        ready_str = input(f"  Ready Time [HH:MM] (default: {DEFAULT_READY_TIME_STR}): ")
        ready_time = parse_hhmm_to_minutes(ready_str, default_ready_min)
        
        due_str = input(f"  Due Time [HH:MM] (default: {DEFAULT_DUE_TIME_STR}): ")
        due_time = parse_hhmm_to_minutes(due_str, default_due_min)
        
        service_str = input(f"  Service Time in mins (default: {DEFAULT_SERVICE_TIME}): ")
        service_time = int(service_str) if service_str else DEFAULT_SERVICE_TIME
        
        if ready_time > due_time:
            print(f"  > Warning: Ready Time ({ready_str}) is after Due Time ({due_str}).")
            print(f"  > Using default window ({DEFAULT_READY_TIME_STR} - {DEFAULT_DUE_TIME_STR}) instead.")
            ready_time = default_ready_min
            due_time = default_due_min
            
        # FIX: Store 5 items
        customer_locations[i] = (address, demand, ready_time, due_time, service_time)
        
    return customer_locations, customer_ids

def geocode_single_address(address, bias_viewbox=None):
    """
    Geocodes a single address, with better error handling
    AND the required User-Agent.
    """
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': address,
        'format': 'json',
        'limit': 5
    }
    
    if bias_viewbox:
        params['viewbox'] = bias_viewbox
        params['bounded'] = 1
        
    try:
        # --- FIX: This line now includes "headers=NOMINATIM_HEADERS" ---
        response = requests.get(url, params=params, headers=NOMINATIM_HEADERS)
        
        if response.status_code != 200:
            print(f"  Error: Nominatim server returned status code {response.status_code}.")
            print(f"  Response: {response.text}")
            return []
            
        response_json = response.json()
        
        time.sleep(1) # Respect Nominatim's 1-sec rate limit
        return response_json
        
    except requests.exceptions.ConnectionError as e:
        print(f"  Error: Connection failed. Are you connected to the internet?")
        print(f"  Details: {e}")
        return []
    except Exception as e:
        print(f"  Error connecting to Nominatim or decoding response: {e}")
        print(f"  Raw server response: {response.text}")
        return []

def get_interactive_coordinates(customer_locations):
    """
    The main interactive logic for geocoding all addresses.
    """
    print("\nStarting interactive geocoding (Address -> Lat, Lng)...")
    coordinates = {}
    
    depot_address = customer_locations[DEPOT_ID][0]
    depot_results = geocode_single_address(depot_address)
    
    if not depot_results:
        print(f"CRITICAL ERROR: Could not find Depot '{depot_address}'. Exiting.")
        sys.exit()
        
    depot_data = depot_results[0]
    depot_lat = float(depot_data['lat'])
    depot_lon = float(depot_data['lon'])
    coordinates[DEPOT_ID] = f"{depot_lon},{depot_lat}"
    print(f"  Depot set at: {depot_data['display_name']} ({depot_lat}, {depot_lon})\n")
    
    margin = 0.25 # Degrees
    viewbox = f"{depot_lon-margin},{depot_lat-margin},{depot_lon+margin},{depot_lat+margin}"
    
    for i, data in customer_locations.items():
        if i == DEPOT_ID:
            continue
            
        address = data[0]
        
        while True:
            print(f"--- Searching for Customer {i}: '{address}' ---")
            
            results = geocode_single_address(address, bias_viewbox=viewbox)
            
            if not results:
                print("  No results found near Kalyani. Searching worldwide...")
                results = geocode_single_address(address)
            
            if not results:
                print(f"  No results found anywhere for '{address}'.")
                address = input("  Please re-enter the address: ")
                continue

            print("  Please choose the correct location:")
            for idx, res in enumerate(results):
                print(f"    [{idx+1}] {res['display_name']}")
            print("    [0] None of these (Re-enter address)")
            
            try:
                choice = int(input(f"  Enter your choice (0-{len(results)}): "))
                
                if choice == 0:
                    address = input("  Please re-enter the address: ")
                    continue
                    
                if 1 <= choice <= len(results):
                    chosen_result = results[choice-1]
                    lat = float(chosen_result['lat'])
                    lon = float(chosen_result['lon'])
                    coordinates[i] = f"{lon},{lat}"
                    print(f"  > Selected: {chosen_result['display_name']}\n")
                    break
                else:
                    print(f"  Invalid choice. Please enter a number 0-{len(results)}.")
                    
            except ValueError:
                print("  Invalid input. Please enter a number.")
                
    return coordinates

def build_osrm_matrices(coordinates):
    """
    Calls the free OSRM public server to build matrices.
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
CUSTOMER_LOCATIONS, CUSTOMER_IDS = get_customer_data_from_user()
coordinates = get_interactive_coordinates(CUSTOMER_LOCATIONS)
DISTANCE_MATRIX, TRAVEL_TIME_MATRIX = build_osrm_matrices(coordinates)

if DISTANCE_MATRIX is None:
    print("CRITICAL ERROR: Could not build matrices. Exiting.")
    sys.exit()