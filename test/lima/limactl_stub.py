"""Stub of the limactl command, driven by a JSON state file."""

import json
import os
import sys
from pathlib import Path


def state_dir() -> Path:
    return Path(os.environ["LIMACTL_STATE_DIR"])


def load(state: Path) -> list[str]:
    if state.is_file():
        return json.loads(state.read_text())
    return []


def main() -> int:
    args = sys.argv[1:]
    state = state_dir() / "instances.json"

    with (state_dir() / "calls.jsonl").open("a") as fh:
        fh.write(json.dumps(args) + "\n")

    if not args:
        return 1

    if args[0] == "--version":
        version = os.environ.get("LIMACTL_VERSION", "2.1.4")
        sys.stdout.write(f"limactl version {version}\n")
        return 0

    if args[0] == "list":
        for name in load(state):
            sys.stdout.write(
                json.dumps(
                    {
                        "name": name,
                        "status": "Running",
                        "sshAddress": "127.0.0.1",
                        "sshLocalPort": 60000 + len(name),
                        "IdentityFile": f"/home/tester/.lima/_config/{name}",
                        "config": {"user": {"name": "tester"}},
                    },
                )
                + "\n",
            )
        return 0

    if args[0] == "start":
        name = next(a.split("=", 1)[1] for a in args if a.startswith("--name="))
        names = load(state)
        if name not in names:
            names.append(name)
        state.write_text(json.dumps(names))
        return 0

    if args[0] == "delete":
        names = [n for n in load(state) if n not in args]
        state.write_text(json.dumps(names))
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
