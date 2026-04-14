#!/usr/bin/env bash
set -euo pipefail

CODEBASE_CMD="$(command -v codebase)"

WORKSPACE_PATH="${CODEBASE_WORKSPACE:-$(git rev-parse --show-toplevel 2>/dev/null | tr -d '\n')}"
[ -z "$WORKSPACE_PATH" ] && { echo "Nao e um repositorio git." >&2; exit 1; }

PORT="$(python3 -c "
import socket
for p in range(3001, 65536):
    try:
        s = socket.socket(); s.bind(('127.0.0.1', p)); s.close(); print(p); break
    except OSError: pass
")"

echo "autodev-codebase: porta $PORT" >&2

"$CODEBASE_CMD" index --serve --host=127.0.0.1 --port="$PORT" --path="$WORKSPACE_PATH" --log-level=error &

exec "$CODEBASE_CMD" stdio --server-url="http://127.0.0.1:$PORT/mcp" --log-level=error
