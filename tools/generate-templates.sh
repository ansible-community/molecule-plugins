#!/bin/bash

set -euo pipefail

rm -rf test/roles/* || true
mkdir -p test/roles
cd test/roles

DRIVER_NAMES=(azure docker gce vagrant podman ec2)

for DRIVER_NAME in "${DRIVER_NAMES[@]}"; do
  molecule init role roles."${DRIVER_NAME}"plugin --driver-name="${DRIVER_NAME}"
done

exit 0
