#!/usr/bin/env bash
set -euo pipefail

# Brainstorming Visual Companion - Start Server
# Usage: start-server.sh [--project-dir DIR] [--port PORT] [--host HOST] [--url-host HOST] [--foreground]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR=""
PORT=""
HOST=""
URL_HOST=""
FOREGROUND=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --project-dir)
      PROJECT_DIR="$2"
      shift 2
      ;;
    --port)
      PORT="$2"
      shift 2
      ;;
    --host)
      HOST="$2"
      shift 2
      ;;
    --url-host)
      URL_HOST="$2"
      shift 2
      ;;
    --foreground)
      FOREGROUND=true
      shift
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

# Check Node.js
if ! command -v node &>/dev/null; then
  echo '{"type":"error","message":"Node.js is required but not found. Install it from https://nodejs.org"}' >&2
  exit 1
fi

# Create session directory
TIMESTAMP=$(date +%s)
PID_SUFFIX=$$

if [[ -n "$PROJECT_DIR" ]]; then
  SESSION_DIR="${PROJECT_DIR}/.claude/brainstorm/${PID_SUFFIX}-${TIMESTAMP}"
else
  SESSION_DIR="/tmp/brainstorm-${PID_SUFFIX}-${TIMESTAMP}"
fi

mkdir -p "${SESSION_DIR}/content" "${SESSION_DIR}/state"

# Build environment
export BRAINSTORM_DIR="$SESSION_DIR"
[[ -n "$PORT" ]] && export BRAINSTORM_PORT="$PORT"
[[ -n "$HOST" ]] && export BRAINSTORM_HOST="$HOST"
[[ -n "$URL_HOST" ]] && export BRAINSTORM_URL_HOST="$URL_HOST"

# Find owner PID (the agent process)
# Walk up PPID chain to find a long-lived parent
find_owner_pid() {
  local pid=$$
  local parent
  for _ in 1 2 3; do
    parent=$(ps -o ppid= -p "$pid" 2>/dev/null | tr -d ' ')
    [[ -z "$parent" || "$parent" == "1" ]] && break
    pid="$parent"
  done
  echo "$pid"
}

export BRAINSTORM_OWNER_PID="$(find_owner_pid)"

SERVER_SCRIPT="${SCRIPT_DIR}/server.cjs"

if [[ "$FOREGROUND" == true ]]; then
  # Foreground mode: blocks, suitable for environments that reap background processes
  exec node "$SERVER_SCRIPT"
else
  # Background mode: detach and print server info
  nohup node "$SERVER_SCRIPT" > "${SESSION_DIR}/server.log" 2>&1 &
  SERVER_PID=$!

  # Wait for server to start (max 5 seconds)
  for i in $(seq 1 50); do
    if [[ -f "${SESSION_DIR}/state/server-info" ]]; then
      cat "${SESSION_DIR}/state/server-info"
      exit 0
    fi
    sleep 0.1
  done

  # Check if server process is still running
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    echo '{"type":"error","message":"Server failed to start. Check '"${SESSION_DIR}/server.log"'"}' >&2
    [[ -f "${SESSION_DIR}/server.log" ]] && cat "${SESSION_DIR}/server.log" >&2
    exit 1
  fi

  echo '{"type":"error","message":"Server started but no info file found after 5s"}' >&2
  exit 1
fi
