import yaml
from collections import defaultdict

# Path to the YAML file
yaml_path = "led_layout.yaml"

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

# Function to convert YAML to C++ unordered_map
def yaml_to_cpp_map(yaml_path):
    with open(yaml_path, "r") as yaml_file:
        yaml_data = yaml.load(yaml_file, Loader=CustomLoader)

    cpp_map = []
    led_index = 0

    for run, items in yaml_data["runs"].get("dictitems", {}).items():
        run_number = int(run.split(" ")[1])  # Convert "Run X" to integer X
        for item in items:
            if isinstance(item, dict):
                # Check if it's a direct station
                if "stop_id" in item:
                    stop_id = item["stop_id"]
                    cpp_map.append(f'{{"{stop_id}", {{{run_number}, 0, {led_index}}}}}')
                    led_index += 1
                # Check if it's a branch
                else:
                    branch_name, branch_stations = next(iter(item.items()))
                    branch_number = int(branch_name.split(" ")[1]) if branch_name.startswith("Branch") else 0
                    for station in branch_stations:
                        stop_id = station["stop_id"]
                        cpp_map.append(f'{{"{stop_id}", {{{run_number}, {branch_number}, {led_index}}}}}')
                        led_index += 1

    cpp_code = "#include <unordered_map>\n#include <string>\n\nstruct StopInfo {\n    int run;\n    int branch;\n    int led_index;\n};\n\nstd::unordered_map<std::string, StopInfo> lookup_map = {\n"
    cpp_code += ",\n".join(cpp_map)
    cpp_code += "\n};"

    return cpp_code

# Generate the C++ unordered_map
cpp_code = yaml_to_cpp_map(yaml_path)

# Write the C++ code to a file
output_path = "lookup_map.cpp"
with open(output_path, "w") as cpp_file:
    cpp_file.write(cpp_code)

print(f"C++ unordered_map written to {output_path}")