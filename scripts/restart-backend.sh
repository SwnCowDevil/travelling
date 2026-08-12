#!/bin/sh

set -eu

project_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
compose_file="$project_root/deploy/docker-compose.backend.yml"
env_file=/etc/travelling/travel-api.env

if [ ! -f "$env_file" ]; then
  echo "Missing production environment file: $env_file" >&2
  exit 1
fi

mkdir -p /opt/travelling/backend/data
chown 10001:10001 /opt/travelling/backend/data
chmod 700 /opt/travelling/backend/data

docker compose -f "$compose_file" up -d --force-recreate
docker compose -f "$compose_file" exec -T travel-api alembic upgrade head

attempt=0
until curl -fsS http://127.0.0.1:8000/health; do
  attempt=$((attempt + 1))
  if [ "$attempt" -ge 20 ]; then
    echo "travel-api did not become healthy in time" >&2
    exit 1
  fi
  sleep 1
done
