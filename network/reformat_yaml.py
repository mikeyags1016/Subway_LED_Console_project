import yaml
from collections import defaultdict

def load_yaml(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file) or {}

def group_and_reformat_runs(input_file, output_file):
    data = load_yaml(input_file)
    runs = data.get('runs', {})
    new_runs = {}

    for run_index, (run_name, stops) in enumerate(runs.items()):
        # Group stations by stop_name within the same run
        grouped_stops = defaultdict(list)

        for stop in stops:
            stop_name = stop['stop_name']
            grouped_stops[stop_name].append(stop['stop_id'])

        # Reverse the order of stations and reassign indices
        new_run = []
        for station_index, (stop_name, stop_ids) in enumerate(reversed(list(grouped_stops.items()))):
            new_run.append({
                'station_index': station_index,
                'stop_id': stop_ids,
                'stop_name': stop_name
            })

        new_runs[run_index] = new_run  # Use integer keys for runs instead of "Run X" strings

    with open(output_file, 'w') as file:
        yaml.dump({'runs': new_runs}, file, default_flow_style=False)

if __name__ == "__main__":
    input_yaml = "led_layout_with_branches_as_runs.yaml"
    output_yaml = "reformatted_led_layout.yaml"
    group_and_reformat_runs(input_yaml, output_yaml)
    print(f"Reformatted YAML saved to {output_yaml}")