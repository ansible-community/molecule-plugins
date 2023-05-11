#!/bin/bash

set -euo pipefail

rm -rf test/roles/* || true
mkdir -p test/roles

while IFS='' read -r line; do DRIVER_NAMES+=("$line"); done < <(python "tools/extract_plugin_names.py" "pyproject.toml")

cd test/roles
for DRIVER_NAME in "${DRIVER_NAMES[@]}"; do
  molecule init role roles."${DRIVER_NAME}"plugin --driver-name="${DRIVER_NAME}"
done

exit 0
