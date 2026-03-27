#!/usr/bin/env bash
set -euo pipefail

# Brainstorming Visual Companion - Stop Server
# Usage: stop-server.sh <SESSION_DIR>

SESSION_DIR="${1:-}"

if [[ -z "$SESSION_DIR" ]]; then
  echo "Usage: stop-server.sh <SESSION_DIR>" >&2
  exit 1
fi

STATE_DIR="${SESSION_DIR}/state"
INFO_FILE="${STATE_DIR}/server-info"

if [[ ! -f "$INFO_FILE" ]]; then
  echo '{"type":"info","message":"No server-info found — server may already be stopped"}'
  exit 0
fi

# Find the server process by checking who's listening on the port
PORT=$(cat "$INFO_FILE" | grep -o '"port":[0-9]*' | grep -o '[0-9]*')

if [[ -n "$PORT" ]]; then
  # Find PID listening on this port
  SERVER_PID=$(lsof -ti :"$PORT" 2>/dev/null || true)
  if [[ -n "$SERVER_PID" ]]; then
    kill "$SERVER_PID" 2>/dev/null || true
    # Wait for process to exit
    for i in $(seq 1 20); do
      kill -0 "$SERVER_PID" 2>/dev/null || break
      sleep 0.1
    done
  fi
fi

# Clean up state
rm -f "$INFO_FILE"

# If session is in /tmp, clean up entirely
if [[ "$SESSION_DIR" == /tmp/* ]]; then
  rm -rf "$SESSION_DIR"
  echo '{"type":"server-stopped","message":"Server stopped and temp session cleaned up"}'
else
  echo '{"type":"server-stopped","message":"Server stopped. Mockups preserved in '"$SESSION_DIR"'"}'
fi
