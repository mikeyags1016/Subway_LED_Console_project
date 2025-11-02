import sqlite3
import matplotlib.pyplot as plt
import yaml
from collections import defaultdict

# Path to the database and YAML file
db_path = "subway.db"
yaml_path = "led_layout.yaml"

# Define colors for each run
run_colors = {
    "Run 1": "red",
    "Run 2": "green",
    "Run 3": "blue",
    "Run 4": "orange",
    "Run 5": "yellow",
    "Run 6": "darkgoldenrod",
    "Run 7": "brown",
    "Run 8": "silver",
    "Run 9": "magenta",
    "Run 10": "royalblue"
}

# Custom YAML loader to handle defaultdict
class DefaultDictLoader(yaml.SafeLoader):
    def construct_python_object_apply(self, node, deep=False):
        if node.tag == 'tag:yaml.org,2002:python/object/apply:collections.defaultdict':
            mapping = self.construct_mapping(node, deep=deep)
            return defaultdict(mapping.pop('default_factory', None), mapping)
        return super().construct_python_object_apply(node, deep=deep)

# Custom YAML loader to handle Python-specific tags
def remove_python_tags(loader, node):
    if isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node)
    elif isinstance(node, yaml.MappingNode):
        return loader.construct_mapping(node)
    elif isinstance(node, yaml.ScalarNode):
        return loader.construct_scalar(node)
    return None

DefaultDictLoader.add_constructor('tag:yaml.org,2002:python/name:builtins.list', remove_python_tags)
DefaultDictLoader.add_constructor('tag:yaml.org,2002:python/object/apply:collections.defaultdict', DefaultDictLoader.construct_python_object_apply)

# Convert defaultdict to a regular dictionary during YAML loading
def convert_defaultdict_to_dict(data):
    if isinstance(data, defaultdict):
        return {key: convert_defaultdict_to_dict(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_defaultdict_to_dict(item) for item in data]
    elif isinstance(data, dict):
        return {key: convert_defaultdict_to_dict(value) for key, value in data.items()}
    return data

# Normalize stop_id values for matching
def normalize_stop_id(stop_id):
    return stop_id.strip().upper() if isinstance(stop_id, str) else stop_id

# Function to get station data with coordinates and run assignments from YAML
def get_station_data_from_yaml(yaml_path, db_path):
    with open(yaml_path, "r") as yaml_file:
        # Fix YAML loading to extract `dictitems` from defaultdict
        yaml_data = yaml.load(yaml_file, Loader=DefaultDictLoader)
        if "dictitems" in yaml_data.get("runs", {}):
            yaml_data["runs"] = yaml_data["runs"]["dictitems"]  # Extract `dictitems` if present
        yaml_data = convert_defaultdict_to_dict(yaml_data)  # Convert defaultdict to regular dict

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Query to get all stop IDs, stop names, and coordinates
    cursor.execute("SELECT stop_id, stop_name, stop_lat, stop_lon FROM node")
    nodes = cursor.fetchall()

    conn.close()

    # Assign stations to runs based on the YAML data
    station_data = []
    run_mappings = yaml_data.get("runs", {})

    # Debugging: Print unmatched runs and station data
    unmatched_runs = set()

    # Debugging: Print the structure of run_mappings
    print("Run mappings structure:", {run: stations[:5] for run, stations in run_mappings.items() if isinstance(stations, list)})

    for stop_id, stop_name, stop_lat, stop_lon in nodes:
        normalized_stop_id = normalize_stop_id(stop_id)
        assigned_run = None
        for run, stations in run_mappings.items():
            if isinstance(stations, list) and any(isinstance(station, dict) and normalize_stop_id(station.get("stop_id")) == normalized_stop_id for station in stations):
                assigned_run = run
                break

        station_data.append({
            "stop_id": stop_id,
            "stop_name": stop_name,
            "latitude": stop_lat,
            "longitude": stop_lon,
            "run": assigned_run
        })

    print("Unmatched stop IDs:", unmatched_runs)
    print("Station data:", station_data[:10])  # Print first 10 stations for debugging

    return station_data

# Function to plot the network and save as an image
def plot_network(station_data, run_colors, output_path="network_plot.png"):
    plt.figure(figsize=(12, 8))

    for station in station_data:
        color = run_colors.get(station["run"], "black")  # Default to black for unmapped stations
        plt.scatter(station["longitude"], station["latitude"], color=color, label=station["run"], s=10)

    # Add labels and title
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.title("Subway Network by Run")
    plt.legend(handles=[plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=color, markersize=10, label=run) for run, color in run_colors.items()], loc="upper right")
    plt.grid(True)

    # Save the plot as an image
    plt.savefig(output_path)
    print(f"Network plot saved as {output_path}")

# Get station data from YAML
station_data = get_station_data_from_yaml(yaml_path, db_path)

# Plot the network and save as an image
plot_network(station_data, run_colors)