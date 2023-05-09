import sys
import toml

if len(sys.argv) != 2:
    print("Usage: python toml_to_json.py <filename>")
    sys.exit(1)

filename = sys.argv[1]
with open(filename, "r") as f:
    toml_data = toml.load(f)

result = toml_data["project"]["entry-points"]["molecule.driver"].keys()
for i in result:
    print(i)
