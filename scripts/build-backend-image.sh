#!/bin/sh

set -eu

project_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)

docker build \
  --file "$project_root/deploy/Dockerfile.backend" \
  --tag travel-api:local \
  "$project_root"
