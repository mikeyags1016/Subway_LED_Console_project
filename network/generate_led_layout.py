import csv
import json
import sqlite3
from collections import defaultdict

# Path to the CSV file
csv_path = "MTA_Subway_Stations_and_Complexes.csv"

# Path to the subway.db database
db_path = "subway.db"

# Define the number of main runs
NUM_MAIN_RUNS = 10

# Function to get all valid stop IDs from the node table
def get_valid_stop_ids(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Query to get all stop IDs from the node table
    cursor.execute("SELECT DISTINCT stop_id FROM node")
    valid_ids = [row[0] for row in cursor.fetchall()]

    conn.close()
    return valid_ids

# Function to group stations by line based on the node table and CSV file
def group_stations_by_line(csv_path, db_path):
    # Get all valid stop IDs from the node table
    valid_stop_ids = get_valid_stop_ids(db_path)

    # Initialize line groups
    line_groups = defaultdict(list)

    with open(csv_path, "r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            gtfs_stop_ids = row["GTFS Stop IDs"].split(";")
            lines = row["Daytime Routes"].split()

            for line in lines:
                for stop_id in gtfs_stop_ids:
                    # Include only valid stop IDs
                    if f"{stop_id}N" in valid_stop_ids and f"{stop_id}S" in valid_stop_ids:
                        line_groups[line].append({"stop_id": stop_id, "nodes": [f"{stop_id}N", f"{stop_id}S"]})

    return line_groups

# Function to divide lines into main runs
def divide_into_main_runs(line_groups, num_runs):
    main_runs = defaultdict(list)
    run_index = 0

    for line, stations in line_groups.items():
        main_runs[f"Run_{run_index % num_runs + 1}"].append({"line": line, "stations": stations})
        run_index += 1

    return main_runs

# Group stations by line using GTFS Stop IDs and include N and S nodes
line_groups = group_stations_by_line(csv_path, db_path)

# Divide lines into main runs
main_runs = divide_into_main_runs(line_groups, NUM_MAIN_RUNS)

# Save the main runs layout to a JSON file
layout_path = "led_layout.json"
with open(layout_path, "w") as json_file:
    json.dump(main_runs, json_file, indent=4)

print(f"LED layout with N and S nodes saved to {layout_path}")