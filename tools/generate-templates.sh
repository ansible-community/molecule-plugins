#!/bin/bash

set -euo pipefail

rm -rf test/roles/* || true
mkdir -p test/roles

while IFS='' read -r line; do DRIVER_NAMES+=("$line"); done < <(python "tools/toml_to_json.py" "pyproject.toml" | jq -rc '.project."entry-points"."molecule.driver" | keys[]')

cd test/roles
for DRIVER_NAME in "${DRIVER_NAMES[@]}"; do
  molecule init role roles."${DRIVER_NAME}"plugin --driver-name="${DRIVER_NAME}"
done

exit 0
