import sqlite3
import json

# Path to the subway.db database
db_path = "subway.db"

# Define the physical LED layout
# Example: {"line": {"branch": [station_id1, station_id2, ...]}}
led_layout = {
    "1": {
        "north": ["101", "102", "103"],
        "south": ["104", "105", "106"]
    },
    "2": {
        "east": ["201", "202", "203"],
        "west": ["204", "205", "206"]
    }
    # Add more lines and branches as needed
}

# Function to map station IDs to LED indices
def map_station_ids_to_leds(db_path, led_layout):
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Query to get station IDs and their details
    cursor.execute("SELECT station_id, line, branch FROM stations")
    stations = cursor.fetchall()

    # Create a mapping of station IDs to LED indices
    station_to_led = {}
    for line, branches in led_layout.items():
        for branch, station_ids in branches.items():
            for index, station_id in enumerate(station_ids):
                station_to_led[station_id] = {
                    "line": line,
                    "branch": branch,
                    "led_index": index
                }

    # Close the database connection
    conn.close()

    return station_to_led

# Generate the mapping
station_to_led_mapping = map_station_ids_to_leds(db_path, led_layout)

# Save the mapping to a JSON file
with open("station_to_led_mapping.json", "w") as json_file:
    json.dump(station_to_led_mapping, json_file, indent=4)

print("Mapping saved to station_to_led_mapping.json")