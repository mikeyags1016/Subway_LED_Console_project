import yaml
import json

# Function to convert YAML to JSON-compatible dictionary
def yaml_to_dict(input_file):
    with open(input_file, 'r') as file:
        data = yaml.safe_load(file) or {}

    runs = data.get('runs', {})
    stop_lookup = {}

    for run_number, stations in runs.items():
        for station in stations:
            station_index = station['station_index']
            stop_ids = station['stop_id']
            stop_name = station['stop_name']

            for stop_id in stop_ids:
                stop_lookup[stop_id] = {
                    'run': run_number,
                    'index': station_index,
                    'name': stop_name
                }

    return stop_lookup

if __name__ == "__main__":
    input_yaml = "reformatted_led_layout.yaml"
    stop_dict = yaml_to_dict(input_yaml)

    # Example usage
    print("Generated stop lookup dictionary:")
    for stop_id, details in list(stop_dict.items())[:10]:  # Print first 10 entries
        print(f"{stop_id}: {details}")

    output_file = "stop_lookup.json"
    with open(output_file, 'w') as file:
        json.dump(stop_dict, file, indent=4)

    print(f"Stop lookup dictionary saved to {output_file}")