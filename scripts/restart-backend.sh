#!/bin/sh

set -eu

project_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
env_file=/etc/travelling/travel-api.env

if [ ! -f "$env_file" ]; then
  echo "Missing production environment file: $env_file" >&2
  exit 1
fi

mkdir -p /opt/travelling/backend/data
chown 10001:10001 /opt/travelling/backend/data
chmod 700 /opt/travelling/backend/data

docker rm -f travel-api >/dev/null 2>&1 || true
docker run -d \
  --name travel-api \
  --env-file "$env_file" \
  --restart unless-stopped \
  -p 127.0.0.1:8000:8000 \
  -v /opt/travelling/backend:/app:ro \
  -v /opt/travelling/backend/data:/app/data:rw \
  travel-api:local >/dev/null

docker exec travel-api alembic upgrade head
docker exec travel-api /opt/python3.12/bin/python3.12 -m app.destinations.seed_command

attempt=0
until curl -fsS http://127.0.0.1:8000/health; do
  attempt=$((attempt + 1))
  if [ "$attempt" -ge 20 ]; then
    echo "travel-api did not become healthy in time" >&2
    exit 1
  fi
  sleep 1
done
