#!/bin/bash
set -exuo pipefail

mkdir -p dist
for DIR in packages/*; do
    python3 -m build --outdir dist/ $DIR
done
