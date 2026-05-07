#!/bin/bash
# Kanban Worker 启动脚本 — 在 PC 的 WSL 中运行
#
# 用法:
#   ./start_worker.sh              # 正常启动（后台运行）
#   ./start_worker.sh --foreground # 前台运行（调试用）
#   ./start_worker.sh --dry-run    # 只看不干
#   ./start_worker.sh stop         # 停止

SERVER="10.0.0.109"
PORT="9119"
ASSIGNEE="pc-eng"
INTERVAL=120
WORKER_SCRIPT="$(dirname "$0")/kanban_worker.py"
PID_FILE="/tmp/kanban-worker.pid"
LOG_FILE="/tmp/kanban-worker.log"

# 确保 Python3 可用
if ! command -v python3 &>/dev/null; then
    echo "❌ python3 not found. Install Python 3.10+ first."
    exit 1
fi

# 确保 Claude Code 可用
if ! command -v claude &>/dev/null; then
    echo "❌ claude CLI not found. Install Claude Code first."
    exit 1
fi

# 测试连接
echo "🔍 Testing connection to Kanban at $SERVER:$PORT..."
if ! curl -sf "http://$SERVER:$PORT/api/plugins/kanban/board" -o /dev/null; then
    echo "❌ Cannot reach Kanban at $SERVER:$PORT"
    echo "   Make sure the Hermes gateway is running on the server."
    exit 1
fi
echo "✅ Connected!"

case "${1:-}" in
    stop)
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if kill -0 "$PID" 2>/dev/null; then
                kill "$PID"
                rm -f "$PID_FILE"
                echo "🛑 Worker stopped (PID $PID)"
            else
                rm -f "$PID_FILE"
                echo "Worker was not running"
            fi
        else
            echo "Worker was not running"
        fi
        ;;
    --foreground)
        echo "🚀 Starting worker in foreground (Ctrl+C to stop)..."
        python3 "$WORKER_SCRIPT" --server "$SERVER" --port "$PORT" \
            --assignee "$ASSIGNEE" --poll-interval "$INTERVAL" \
            --workspace "$HOME/projects" \
            "${@:2}"
        ;;
    *)
        echo "🚀 Starting worker in background..."
        nohup python3 "$WORKER_SCRIPT" --server "$SERVER" --port "$PORT" \
            --assignee "$ASSIGNEE" --poll-interval "$INTERVAL" \
            --workspace "$HOME/projects" \
            "${@:1}" > "$LOG_FILE" 2>&1 &
        echo $! > "$PID_FILE"
        echo "✅ Worker started (PID $!)"
        echo "   Log: $LOG_FILE"
        echo "   Stop: $0 stop"
        ;;
esac
