#!/bin/sh

set -eu

project_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)

grep -F '127.0.0.1:8000:8000' "$project_root/deploy/docker-compose.backend.yml"
grep -F '/opt/travelling/backend:/app:ro' "$project_root/deploy/docker-compose.backend.yml"
grep -F '/opt/travelling/backend/data:/app/data:rw' "$project_root/deploy/docker-compose.backend.yml"
grep -F 'alembic upgrade head' "$project_root/scripts/restart-backend.sh"
grep -F 'curl -fsS http://127.0.0.1:8000/health' "$project_root/scripts/restart-backend.sh"
