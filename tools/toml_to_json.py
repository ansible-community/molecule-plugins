import sys
import toml
import json

if len(sys.argv) != 2:
    print("Usage: python toml_to_json.py <filename>")
    sys.exit(1)

filename = sys.argv[1]
with open(filename, "r") as f:
    toml_data = toml.load(f)

json_data = json.dumps(toml_data)
print(json_data)
