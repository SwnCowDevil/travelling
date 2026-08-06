#!/bin/sh

LOCAL_SCRIPT_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
PROJECT_ROOT=${LOCAL_PROJECT_ROOT:-$(CDPATH= cd -- "$LOCAL_SCRIPT_DIR/.." && pwd)}
BACKEND_DIR="$PROJECT_ROOT/backend"
RUNTIME_DIR=${LOCAL_RUNTIME_DIR:-$PROJECT_ROOT/.local}
UVICORN_BIN=${LOCAL_UVICORN_BIN:-$BACKEND_DIR/.venv/bin/uvicorn}
PS_BIN=${LOCAL_PS_BIN:-ps}
ALEMBIC_BIN="$BACKEND_DIR/.venv/bin/alembic"
PID_FILE="$RUNTIME_DIR/backend.pid"
LOG_FILE="$RUNTIME_DIR/backend.log"
API_URL="http://127.0.0.1:8000"

recorded_pid() {
    test -f "$PID_FILE" || return 1
    pid=$(sed -n '1p' "$PID_FILE")
    case "$pid" in
        ''|*[!0-9]*) return 1 ;;
    esac
    printf '%s\n' "$pid"
}

is_backend_running() {
    pid=$(recorded_pid) || return 1
    kill -0 "$pid" 2>/dev/null || return 1
    command_line=$($PS_BIN -p "$pid" -o command= 2>/dev/null) || return 1
    case "$command_line" in
        *"$UVICORN_BIN"*"app.main:app"*) return 0 ;;
        *) return 1 ;;
    esac
}

remove_stale_pid() {
    if ! is_backend_running; then
        rm -f "$PID_FILE"
    fi
}

show_log_tail() {
    if test -f "$LOG_FILE"; then
        echo "最近日志："
        tail -n 20 "$LOG_FILE"
    fi
}
