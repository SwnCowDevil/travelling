#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
. "$SCRIPT_DIR/local-service-lib.sh"

mkdir -p "$RUNTIME_DIR"
if is_backend_running; then
    echo "本地后端已经运行：$API_URL"
    echo "PID：$(recorded_pid)"
    exit 0
fi
remove_stale_pid

if port_in_use; then
    echo "无法启动：端口 8000 已被其他进程占用。" >&2
    echo "请先关闭占用该端口的旧服务，再重新运行本脚本。" >&2
    exit 1
fi

if test ! -x "$UVICORN_BIN" || test ! -x "$ALEMBIC_BIN"; then
    echo "缺少后端虚拟环境，请先在 backend 目录创建 .venv 并安装依赖。" >&2
    exit 1
fi
if test ! -f "$BACKEND_DIR/.env"; then
    echo "缺少 backend/.env，请从 backend/.env.example 复制并填写本地配置。" >&2
    exit 1
fi

echo "正在升级本地数据库..."
(cd "$BACKEND_DIR" && "$ALEMBIC_BIN" upgrade head)

echo "正在生成离线足迹地图包..."
(cd "$BACKEND_DIR" && "$BACKEND_DIR/.venv/bin/python" -m scripts.build_map_pack)

echo "正在启动 FastAPI..."
ORIGINAL_DIR=$(pwd)
cd "$BACKEND_DIR"
TRAVEL_ENABLE_DEV_AUTH=true nohup "$UVICORN_BIN" app.main:app --host 127.0.0.1 --port 8000 --workers 1 > "$LOG_FILE" 2>&1 &
server_pid=$!
cd "$ORIGINAL_DIR"
printf '%s\n' "$server_pid" > "$PID_FILE"

# Give the operating system time to replace the launcher with Uvicorn before
# validating its command line. Without this grace period, a fast first check
# can mistake a newly spawned process for a stale PID.
sleep 0.2
attempt=0
while test "$attempt" -lt 30; do
    if is_backend_running && curl -fsS "$API_URL/health" >/dev/null 2>&1; then
        echo "本地后端启动成功：$API_URL"
        echo "小程序 API：$API_URL"
        echo "日志：$LOG_FILE"
        exit 0
    fi
    if test "$attempt" -ge 4 && ! is_backend_running; then
        break
    fi
    attempt=$((attempt + 1))
    sleep 0.5
done

echo "本地后端启动失败。" >&2
if is_backend_running; then
    kill "$(recorded_pid)" 2>/dev/null || true
fi
rm -f "$PID_FILE"
show_log_tail
exit 1
