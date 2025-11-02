import sqlite3
import yaml
from collections import defaultdict

# Path to the database and output YAML file
db_path = "subway.db"
yaml_output_path = "led_layout.yaml"

# Define the runs and their corresponding lines
runs = {
    "Run 1": ["1", "3"],
    "Run 2": ["4", "5", "6"],
    "Run 3": ["A", "C"],
    "Run 4": ["B", "D"],
    "Run 5": ["W", "N", "Q"],
    "Run 6": ["M", "F", "R"],
    "Run 7": ["J", "Z"],
    "Run 8": ["L"],
    "Run 9": ["7"],
    "Run 10": ["SIR"]
}

# Function to group stations by runs
def group_stations_by_runs(db_path, runs):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Query to get all stop IDs and stop names
    cursor.execute("SELECT stop_id, stop_name FROM node")
    nodes = cursor.fetchall()

    # Initialize run groups and unmapped stations
    run_groups = defaultdict(list)
    unmapped_stations = []

    for stop_id, stop_name in nodes:
        # Check which run the stop_id belongs to based on its line prefix
        assigned = False
        for run, lines in runs.items():
            if any(stop_id.startswith(line) for line in lines):
                run_groups[run].append({"stop_id": stop_id, "stop_name": stop_name})
                assigned = True
                break

        if not assigned:
            unmapped_stations.append({"stop_id": stop_id, "stop_name": stop_name})

    conn.close()
    return run_groups, unmapped_stations

# Group stations by runs
run_groups, unmapped_stations = group_stations_by_runs(db_path, runs)

# Prepare the output data
output_data = {"runs": run_groups, "unmapped": unmapped_stations}

# Write the output to a YAML file
with open(yaml_output_path, "w") as yaml_file:
    yaml.dump(output_data, yaml_file, default_flow_style=False)

print(f"LED layout saved to {yaml_output_path}")