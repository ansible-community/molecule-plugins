import sys


def print_plugin_names() -> None:
    import toml

    if len(sys.argv) != 2:
        raise SystemExit(f"Usage: {sys.argv[0]} <filename>")

    filename = sys.argv[1]
    with open(filename) as f:
        toml_data = toml.load(f)

    result = toml_data["project"]["entry-points"]["molecule.driver"].keys()
    for i in result:
        print(i)  # noqa: T201


if __name__ == "__main__":
    print_plugin_names()
