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

# Define shapes for branches
branch_shapes = {
    1: "x",  # Circle
    2: "s",  # Square
    3: "^",  # Triangle
    4: "D",  # Diamond
    5: "*"   # Star
}

# Custom YAML loader to handle defaultdict and Python-specific tags
class CustomLoader(yaml.SafeLoader):
    def construct_python_object_apply(self, node):
        if isinstance(node, yaml.MappingNode):
            return defaultdict(list, self.construct_mapping(node, deep=True))
        raise yaml.constructor.ConstructorError(
            None, None, "expected a mapping node, but found %s" % node.id, node.start_mark
        )

    def construct_builtin_list(self, node):
        if isinstance(node, yaml.SequenceNode):
            return list(self.construct_sequence(node, deep=True))
        elif isinstance(node, yaml.ScalarNode):
            return [self.construct_scalar(node)]  # Wrap scalar in a list
        raise yaml.constructor.ConstructorError(
            None, None, "expected a sequence or scalar node, but found %s" % node.id, node.start_mark
        )

CustomLoader.add_constructor(
    'tag:yaml.org,2002:python/object/apply:collections.defaultdict',
    CustomLoader.construct_python_object_apply
)
CustomLoader.add_constructor(
    'tag:yaml.org,2002:python/name:builtins.list',
    CustomLoader.construct_builtin_list
)

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

# Function to get station data with coordinates, run, and branch assignments from YAML
def get_station_data_from_yaml(yaml_path, db_path):
    with open(yaml_path, "r") as yaml_file:
        yaml_data = yaml.load(yaml_file, Loader=CustomLoader)
        yaml_data = convert_defaultdict_to_dict(yaml_data)  # Convert defaultdict to regular dict

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Query to get all stop IDs, stop names, and coordinates
    cursor.execute("SELECT stop_id, stop_name, stop_lat, stop_lon FROM node")
    nodes = cursor.fetchall()

    conn.close()

    # Assign stations to runs and branches based on the YAML data
    station_data = []
    run_mappings = yaml_data.get("runs", {}).get("dictitems", {})

    for stop_id, stop_name, stop_lat, stop_lon in nodes:
        normalized_stop_id = normalize_stop_id(stop_id)

        assigned_run = None
        assigned_branch = None

        for run, items in run_mappings.items():
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict):
                        # Check if it's a direct station
                        if normalize_stop_id(item.get("stop_id")) == normalized_stop_id:
                            assigned_run = run
                            break
                        # Check if it's a branch
                        branch_name, branch_stations = next(iter(item.items()))
                        if branch_name.startswith("Branch") and isinstance(branch_stations, list):
                            for station in branch_stations:
                                if isinstance(station, dict) and normalize_stop_id(station.get("stop_id")) == normalized_stop_id:
                                    assigned_run = run
                                    assigned_branch = int(branch_name.split(" ")[1])  # Extract branch number
                                    break
                            if assigned_branch is not None:
                                break
                if assigned_run:
                    break

        station_data.append({
            "stop_id": stop_id,
            "stop_name": stop_name,
            "latitude": stop_lat,
            "longitude": stop_lon,
            "run": assigned_run,
            "branch": assigned_branch
        })

    return station_data

# Function to display the total number of stations in each run
def display_station_counts(station_data):
    run_counts = {}

    for station in station_data:
        run = station["run"]
        if run:
            run_counts[run] = run_counts.get(run, 0) + 1

    print("\nTotal number of stations in each run:")
    for run, count in run_counts.items():
        print(f"{run}: {count / 2} stations")

# Function to plot the network and save as an image
def plot_network(station_data, run_colors, branch_shapes, output_path="network_plot.png"):
    plt.figure(figsize=(12, 8))

    for station in station_data:
        color = run_colors.get(station["run"], "black")  # Default to black for unmapped stations
        shape = branch_shapes.get(station["branch"], "o")  # Default to 'x' for unmapped branches

        plt.scatter(station["longitude"], station["latitude"], color=color, marker=shape, label=f"{station['run']} - Branch {station['branch']}", s=10)

    # Add labels and title
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.title("Subway Network by Run and Branch")
    plt.legend(handles=[
        plt.Line2D([0], [0], marker=shape, color='w', markerfacecolor=color, markersize=10, label=f"{run} - Branch {branch}")
        for run, color in run_colors.items() for branch, shape in branch_shapes.items()
    ], loc="upper right", fontsize="small")
    plt.grid(True)

    # Save the plot as an image
    plt.savefig(output_path)
    print(f"Network plot saved as {output_path}")

# Get station data from YAML
station_data = get_station_data_from_yaml(yaml_path, db_path)

# Display the total number of stations in each run
display_station_counts(station_data)

# Plot the network and save as an image
plot_network(station_data, run_colors, branch_shapes)