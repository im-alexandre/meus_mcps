#!/usr/bin/env bash
set -euo pipefail

CODEBASE_CMD="$(command -v codebase)"

resolve_existing_path() {
  local candidate="$1"
  [ -z "$candidate" ] && return 1
  if [ -d "$candidate" ] || [ -f "$candidate" ]; then
    python3 -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "$candidate"
    return 0
  fi
  return 1
}

resolve_codex_workspace_from_thread() {
  [ -z "${CODEX_THREAD_ID:-}" ] && return 1

  local sessions_root="$HOME/.codex/sessions"
  [ -d "$sessions_root" ] || return 1

  python3 - "$sessions_root" "$CODEX_THREAD_ID" <<'PY'
import json
import os
import sys

sessions_root, thread_id = sys.argv[1], sys.argv[2]
matches = []
for root, _, files in os.walk(sessions_root):
    for name in files:
        if name.endswith(".jsonl"):
            path = os.path.join(root, name)
            try:
                stat = os.stat(path)
            except OSError:
                continue
            matches.append((stat.st_mtime, path))

for _, path in sorted(matches, reverse=True):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            lines = fh.readlines()
    except OSError:
        continue

    if not any(thread_id in line for line in lines):
        continue

    cwd = None
    for line in lines:
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if entry.get("type") == "turn_context":
            payload = entry.get("payload") or {}
            if payload.get("cwd"):
                cwd = payload["cwd"]

    if cwd:
        print(os.path.realpath(cwd))
        sys.exit(0)

sys.exit(1)
PY
}

resolve_workspace_path() {
  local candidate=""

  for candidate in "${CODEBASE_WORKSPACE:-}" "${CLAUDE_PROJECT_DIR:-}"; do
    if resolved="$(resolve_existing_path "$candidate" 2>/dev/null)"; then
      printf '%s\n' "$resolved"
      return 0
    fi
  done

  if resolved="$(resolve_codex_workspace_from_thread 2>/dev/null)"; then
    printf '%s\n' "$resolved"
    return 0
  fi

  if git_root="$(git rev-parse --show-toplevel 2>/dev/null | tr -d '\n')" && [ -n "$git_root" ]; then
    if resolved="$(resolve_existing_path "$git_root" 2>/dev/null)"; then
      printf '%s\n' "$resolved"
      return 0
    fi
  fi

  return 1
}

WORKSPACE_PATH="$(resolve_workspace_path || true)"
[ -z "$WORKSPACE_PATH" ] && { echo "Nao foi possivel resolver o workspace do autodev-codebase." >&2; exit 1; }

LOG_ROOT="${TMPDIR:-/tmp}/autodev-codebase"
mkdir -p "$LOG_ROOT"
WORKSPACE_SLUG="$(python3 -c 'import hashlib, sys; print(hashlib.sha1(sys.argv[1].encode()).hexdigest()[:24])' "$WORKSPACE_PATH")"
STDOUT_LOG="$LOG_ROOT/$WORKSPACE_SLUG.stdout.log"
STDERR_LOG="$LOG_ROOT/$WORKSPACE_SLUG.stderr.log"

wait_for_codebase_http() {
  local host="$1"
  local port="$2"
  python3 - "$host" "$port" <<'PY'
import socket
import sys
import time

host = sys.argv[1]
port = int(sys.argv[2])

for _ in range(60):
    sock = socket.socket()
    sock.settimeout(0.5)
    try:
        sock.connect((host, port))
        sock.close()
        sys.exit(0)
    except OSError:
        sock.close()
        time.sleep(0.5)

print(f"autodev-codebase HTTP nao ficou pronto em {host}:{port}.", file=sys.stderr)
sys.exit(1)
PY
}

PORT="$(python3 -c "
import socket
for p in range(3001, 65536):
    try:
        s = socket.socket(); s.bind(('127.0.0.1', p)); s.close(); print(p); break
    except OSError: pass
")"

echo "autodev-codebase: porta $PORT" >&2

nohup "$CODEBASE_CMD" index --serve --watch --host=127.0.0.1 --port="$PORT" --path="$WORKSPACE_PATH" --log-level=error >"$STDOUT_LOG" 2>"$STDERR_LOG" </dev/null &

wait_for_codebase_http 127.0.0.1 "$PORT"

exec "$CODEBASE_CMD" stdio --server-url="http://127.0.0.1:$PORT/mcp" --log-level=error
