# Docker Mounted Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deploy the FastAPI backend as a Docker container with host-mounted source, SQLite data, and production environment configuration.

**Architecture:** A reusable Python 3.12 image owns dependencies. Compose bind-mounts application code and data, while Caddy remains the only public HTTPS entry point. Operational scripts separate dependency rebuilds from regular restarts.

**Tech Stack:** Docker Engine, Docker Compose v2, Python 3.12, FastAPI, Alembic, Caddy.

## Global Constraints

- Publish only `127.0.0.1:8000:8000`; Caddy serves public HTTPS.
- Use one Uvicorn worker because SQLite is file-backed.
- Never package real `.env` files or `backend/data` into an image.
- Rebuild only after `backend/pyproject.toml` dependency changes.

---

### Task 1: Add a reusable dependency image and compose definition

**Files:**
- Create: `deploy/Dockerfile.backend`
- Create: `deploy/docker-compose.backend.yml`
- Create: `.dockerignore`

**Interfaces:**
- Produces a `travel-api:local` image and `travel-api` service.
- Consumes `/etc/travelling/travel-api.env` and `/opt/travelling/backend` on the server.

- [ ] **Step 1: Add the Dockerfile**

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY backend/pyproject.toml /tmp/pyproject.toml
RUN pip install --no-cache-dir /tmp/pyproject.toml
USER 10001:10001
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```

- [ ] **Step 2: Add Compose mounts and local-only port binding**

```yaml
services:
  travel-api:
    image: travel-api:local
    env_file: /etc/travelling/travel-api.env
    volumes:
      - /opt/travelling/backend:/app:ro
      - /opt/travelling/backend/data:/app/data:rw
    ports:
      - "127.0.0.1:8000:8000"
```

- [ ] **Step 3: Verify Compose syntax**

Run: `docker compose -f deploy/docker-compose.backend.yml config`
Expected: exit code 0 with `127.0.0.1:8000:8000` and both mounts.

### Task 2: Add explicit rebuild and restart operations

**Files:**
- Create: `scripts/build-backend-image.sh`
- Create: `scripts/restart-backend.sh`
- Test: `scripts/tests/docker-backend-scripts.sh`

**Interfaces:**
- `build-backend-image.sh` builds `travel-api:local` from the repository root.
- `restart-backend.sh` performs migration then restarts and checks health.

- [ ] **Step 1: Write shell assertions for local-only binding, persistent data mount, and health check command**

```sh
grep -F '127.0.0.1:8000:8000' deploy/docker-compose.backend.yml
grep -F '/opt/travelling/backend/data:/app/data:rw' deploy/docker-compose.backend.yml
grep -F 'curl -fsS http://127.0.0.1:8000/health' scripts/restart-backend.sh
```

- [ ] **Step 2: Run the script before implementation**

Run: `sh scripts/tests/docker-backend-scripts.sh`
Expected: FAIL because the files do not exist.

- [ ] **Step 3: Implement scripts with `set -eu` and no destructive cleanup**

```sh
docker compose -f "$compose_file" up -d --force-recreate
docker compose -f "$compose_file" exec -T travel-api alembic upgrade head
curl -fsS http://127.0.0.1:8000/health
```

- [ ] **Step 4: Re-run static verification**

Run: `sh scripts/tests/docker-backend-scripts.sh`
Expected: PASS.

### Task 3: Document server installation and production cutover

**Files:**
- Modify: `docs/deployment/server-setup.md`

- [ ] **Step 1: Document Docker Engine installation on Alibaba Cloud Linux and directory layout**
- [ ] **Step 2: Document initial build, restart workflow, and dependency-change rebuild workflow**
- [ ] **Step 3: Document Caddy reverse proxy and final health checks**

### Task 4: Deploy and verify on ECS

**Files:**
- Server-only: `/opt/travelling`, `/etc/travelling/travel-api.env`, `/etc/caddy/Caddyfile`

- [ ] **Step 1: Install Docker Engine and Compose v2 from the official Docker repository**
- [ ] **Step 2: Copy the verified backend deployment package to `/opt/travelling`**
- [ ] **Step 3: Create the production environment file with owner-only permissions**
- [ ] **Step 4: Build once and start with `restart-backend.sh`**
- [ ] **Step 5: Configure Caddy for `api.sunks.cc` and verify local plus HTTPS health endpoints**
