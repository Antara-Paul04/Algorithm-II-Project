# Dynamic VRP Solver with Genetic Algorithm

This Python project solves the Vehicle Routing Problem with Time Windows (VRPTW) using a Genetic Algorithm.

Instead of using static, hard-coded data, this tool is fully interactive. It prompts the user for real-world customer addresses in Kalyani, West Bengal, and uses free, open-source APIs (Nominatim and OSRM) to calculate real road network distances and travel times. The Genetic Algorithm then finds a near-optimal set of routes that respects vehicle capacity and customer time windows.

## Features

- Genetic Algorithm Solver: Uses a GA with tournament selection, order crossover (OX), and swap mutation to find high-quality solutions.
- Real-World Routing: Uses OSRM (Open Source Routing Machine) to calculate actual road distances (km) and travel times (minutes), which is far more accurate than straight-line distance.
- Interactive Geocoding: Uses Nominatim (OpenStreetMap) to convert user-entered addresses (e.g., "ITI More") into precise coordinates.
- Location-Biased Search: Address search is prioritized around the depot ("Kalyani, Nadia") to prevent ambiguous results (e.g., finding "ITI More" in another city).
- User-Friendly Input: Asks for time in HH:MM format (e.g., "09:00") and provides smart defaults to prevent common errors.
- No API Keys Required: Runs on a 100% free and open-source stack with no sign-ups or billing required.

## Requirements

The project has one external dependency: the `requests` library.

Install it with pip:

```
pip install requests
```

## How to Run

1. Make sure you have both `vrp.py` and `data.py` in the same directory.

2. Ensure you have an active internet connection (required for the Nominatim and OSRM APIs).

3. Run the main script from your terminal:

```
python vrp.py
```

4. Follow the prompts:

- Enter the number of customers you want to route.
- For each customer, enter their address (e.g., "Buddha Park").
- Enter their demand, ready time (HH:MM), due time (HH:MM), and service time (in minutes). You can press Enter to accept the defaults.
- The program will show you a list of matching locations. Enter the number for the correct one (e.g., 1).
- Wait for the GA: After all customers are entered, the Genetic Algorithm will start and print its progress to the console.
- View Results: The final, optimized routes will be printed at the end.

## File Structure

`vrp.py` (Main Solver):

Contains the core Genetic Algorithm logic:

- `solve_vrp_ga()` — The main GA loop.
- `decode_and_evaluate()` — The fitness function that simulates routes and calculates cost.
- `initialize_population()`, `select_parents()`, `crossover_ox()`, `mutate_swap()` — The GA operators.

This is the file you run (`python vrp.py`).

`data.py` (Data & API Handler):

Handles all user input (`get_customer_data_from_user`).

Connects to the Nominatim API to convert addresses to coordinates (`get_interactive_coordinates`).

Connects to the OSRM API to build the DISTANCE_MATRIX and TRAVEL_TIME_MATRIX.

Contains all global constants (GENERATIONS, POPULATION_SIZE, VEHICLE_CAPACITY, etc.).

---

If you'd like, I can also:

- Add a `requirements.txt` and a tiny example dataset to make it easy to test offline.
- Create a small usage example with sample addresses and expected output.
- Add a LICENSE file and unit tests for core GA operators.

Tell me which of these you'd like next and I'll proceed.
