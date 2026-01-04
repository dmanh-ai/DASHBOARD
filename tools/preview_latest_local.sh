#!/bin/bash
set -euo pipefail

# One-shot local preview:
# - Pull latest market report (outputs/market/reports/BaoCao_*.docx)
# - Convert + parse + update UI GLM data (no git commit/push)
# - Start a local HTTP server and print the dashboard URL

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
WORKSPACE_ROOT="$(cd "$PROJECT_ROOT/.." && pwd)"

PORT="${UI_GLM_PORT:-8010}"

echo "[UI GLM] Updating data (local-only)…"
UI_GLM_NO_GIT=1 WORD_SOURCE_MODE=market "$SCRIPT_DIR/auto_daily_update.sh"

echo "[UI GLM] Starting local server…"
cd "$PROJECT_ROOT"

choose_port() {
  local p="$1"
  for i in {0..20}; do
    local try_port=$((p+i))
    if python3 - <<PY >/dev/null 2>&1
import socket
s=socket.socket()
try:
    s.bind(("127.0.0.1", ${try_port}))
    print("ok")
except OSError:
    raise SystemExit(1)
finally:
    s.close()
PY
    then
      echo "$try_port"
      return 0
    fi
  done
  return 1
}

PORT="$(choose_port "$PORT")"

LOG="/tmp/ui_glm_server_${PORT}.log"
PID="/tmp/ui_glm_server_${PORT}.pid"
nohup python3 -m http.server "$PORT" --bind 127.0.0.1 >"$LOG" 2>&1 &
echo $! >"$PID"

echo "[UI GLM] Server started: pid=$(cat "$PID") log=$LOG"
echo "[UI GLM] Open:"
echo "  http://127.0.0.1:${PORT}/DASHBOARD_V3_PRO.local.html?v=local_20260102"
echo
echo "[UI GLM] Stop server:"
echo "  kill \$(cat \"$PID\")"

