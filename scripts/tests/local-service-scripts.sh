#!/bin/sh
set -eu

TEST_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/travel-local-test.XXXXXX")
trap 'test -n "${FAKE_PID:-}" && kill "$FAKE_PID" 2>/dev/null || true; rm -rf "$TEST_ROOT"' EXIT

export LOCAL_PROJECT_ROOT="$TEST_ROOT/project"
export LOCAL_RUNTIME_DIR="$TEST_ROOT/runtime"
export LOCAL_UVICORN_BIN="$TEST_ROOT/fake-uvicorn"
export LOCAL_PS_BIN="$TEST_ROOT/fake-ps"
mkdir -p "$LOCAL_PROJECT_ROOT" "$LOCAL_RUNTIME_DIR"

printf '%s\n' '#!/bin/sh' "trap 'exit 0' TERM" 'while :; do sleep 1; done' > "$LOCAL_UVICORN_BIN"
chmod +x "$LOCAL_UVICORN_BIN"
printf '%s\n' '#!/bin/sh' "echo '$LOCAL_UVICORN_BIN app.main:app'" > "$LOCAL_PS_BIN"
chmod +x "$LOCAL_PS_BIN"

# shellcheck source=../local-service-lib.sh
. "$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)/local-service-lib.sh"

"$LOCAL_UVICORN_BIN" app.main:app &
FAKE_PID=$!
printf '%s\n' "$FAKE_PID" > "$PID_FILE"
sleep 0.1
is_backend_running || { echo "expected recorded backend process to be running" >&2; exit 1; }

printf '%s\n' "999999" > "$PID_FILE"
is_backend_running && { echo "stale PID must not be running" >&2; exit 1; }
remove_stale_pid
test ! -f "$PID_FILE" || { echo "stale PID file was not removed" >&2; exit 1; }

kill "$FAKE_PID"
wait "$FAKE_PID" 2>/dev/null || true
FAKE_PID=
remove_stale_pid
echo "local service library tests passed"
