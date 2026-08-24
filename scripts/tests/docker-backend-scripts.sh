#!/bin/sh

set -eu

project_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)

grep -F '127.0.0.1:8000:8000' "$project_root/deploy/docker-compose.backend.yml"
grep -F '/opt/travelling/backend:/app:ro' "$project_root/deploy/docker-compose.backend.yml"
grep -F '/opt/travelling/backend/data:/app/data:rw' "$project_root/deploy/docker-compose.backend.yml"
grep -F 'registry.cn-hangzhou.aliyuncs.com/alinux/alinux3:latest' "$project_root/deploy/Dockerfile.backend"
grep -F 'COPY .runtime/python3.12 /opt/python3.12' "$project_root/deploy/Dockerfile.backend"
grep -F 'https://mirrors.aliyun.com/pypi/simple/' "$project_root/deploy/Dockerfile.backend"
grep -F 'python3.12 -m pip install' "$project_root/deploy/Dockerfile.backend"
grep -F 'runtime_source=${TRAVEL_PYTHON_RUNTIME:-/opt/python3.12}' "$project_root/scripts/build-backend-image.sh"
grep -F 'alembic upgrade head' "$project_root/scripts/restart-backend.sh"
grep -F 'python3.12 -m app.destinations.seed_command' "$project_root/scripts/restart-backend.sh"
grep -F 'curl -fsS http://127.0.0.1:8000/health' "$project_root/scripts/restart-backend.sh"
