#!/bin/sh

set -eu

project_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
runtime_source=${TRAVEL_PYTHON_RUNTIME:-/opt/python3.12}
runtime_target="$project_root/.runtime/python3.12"

if [ ! -x "$runtime_source/bin/python3.12" ]; then
  echo "Missing Python 3.12 runtime: $runtime_source" >&2
  exit 1
fi

mkdir -p "$project_root/.runtime"
rm -rf "$runtime_target"
cp -a "$runtime_source" "$runtime_target"

cleanup() {
  rm -rf "$runtime_target"
}
trap cleanup EXIT INT TERM

docker build \
  --file "$project_root/deploy/Dockerfile.backend" \
  --tag travel-api:local \
  "$project_root"
