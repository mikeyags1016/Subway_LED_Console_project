import yaml
import sqlite3
import matplotlib.pyplot as plt
import random

def load_yaml(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file) or {}

def get_coordinates(db_path, stop_ids):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    coordinates = {}
    for stop_id in stop_ids:
        cursor.execute("SELECT stop_lat, stop_lon FROM node WHERE stop_id = ?", (stop_id,))
        result = cursor.fetchone()
        if result:
            coordinates[stop_id] = result

    conn.close()
    return coordinates

def visualize_runs(yaml_data, db_path):
    runs = yaml_data.get('runs', {})
    stop_ids = {stop['stop_id'] for run in runs.values() for stop in run}
    coordinates = get_coordinates(db_path, stop_ids)

    plt.figure(figsize=(10, 8))
    colors = {}

    for run_name, stops in runs.items():
        if run_name not in colors:
            colors[run_name] = "#" + ''.join(random.choices('0123456789ABCDEF', k=6))

        run_coords = [coordinates[stop['stop_id']] for stop in stops if stop['stop_id'] in coordinates]
        if run_coords:
            lats, lons = zip(*run_coords)
            plt.scatter(lons, lats, label=run_name, color=colors[run_name], alpha=0.7)

    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.title("Subway Runs Visualization")
    plt.legend()
    plt.savefig("subway_runs_visualization.png")
    print("Visualization saved as 'subway_runs_visualization.png'")

if __name__ == "__main__":
    yaml_file = "led_layout_with_branches_as_runs.yaml"
    db_path = "subway.db"

    yaml_data = load_yaml(yaml_file)
    visualize_runs(yaml_data, db_path)
    
Runs:
    0:
        Stations:
            0:
                stop_id: 
                    - 101N
                    - 101S
                stop_name: Van Cortlandt Park-242 St (1)