#!/bin/bash

set -euo pipefail

rm -rf test/roles/* || true
mkdir -p test/roles

while IFS='' read -r line; do DRIVER_NAMES+=("$line"); done < <(python "tools/extract_plugin_names.py" "pyproject.toml")

cd test/roles
for DRIVER_NAME in "${DRIVER_NAMES[@]}"; do
  molecule init role roles."${DRIVER_NAME}"plugin --driver-name="${DRIVER_NAME}"
  sed \
	-e 's!author:.*!author: molecule-plugins!g' \
	-e 's!company:.*!company: ansible-community!g' \
	-e 's!min_ansible_version:.*!min_ansible_version: "2.1"!g' \
	-e 's!license:.*!license: MIT!g' \
	-i "${DRIVER_NAME}"plugin/meta/main.yml
  # Not sure if the issue is in molecule or ansible-lint or pre-commit ansible-lint hook
  # As a workaround, kill the offending files.
  rm -rf "${DRIVER_NAME}"plugin/tests
done

exit 0
