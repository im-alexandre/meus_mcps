#!/usr/bin/env bash
# autodev-codebase-mcp.sh — Equivalente WSL/Linux do autodev-codebase-mcp.ps1
# Gerencia instancias HTTP do autodev-codebase por workspace, compartilhando
# o servidor entre sessoes (mesmo comportamento do .ps1).
set -euo pipefail

HOST="127.0.0.1"
QDRANT_URL="http://localhost:6333/collections"
BASE_DIR="${HOME}/.ai/shared/autodev-codebase"
LOG_DIR="${BASE_DIR}/logs"
STATE_DIR="${BASE_DIR}/servers"

mkdir -p "$LOG_DIR" "$STATE_DIR"

CODEBASE_CMD="$(command -v codebase 2>/dev/null || true)"
if [[ -z "$CODEBASE_CMD" ]]; then
  echo "Erro: 'codebase' nao encontrado no PATH. Instale autodev-codebase via npm." >&2
  exit 1
fi

# ── Resolver workspace ────────────────────────────────────────────────────────

resolve_workspace_path() {
  if [[ -n "${CODEBASE_WORKSPACE:-}" ]]; then
    if [[ -d "$CODEBASE_WORKSPACE" ]]; then
      echo "$CODEBASE_WORKSPACE"
      return
    else
      echo "CODEBASE_WORKSPACE aponta para path invalido: $CODEBASE_WORKSPACE" >&2
      exit 1
    fi
  fi

  if [[ -n "${CLAUDE_PROJECT_DIR:-}" ]]; then
    if [[ -d "$CLAUDE_PROJECT_DIR" ]]; then
      echo "$CLAUDE_PROJECT_DIR"
      return
    else
      echo "CLAUDE_PROJECT_DIR aponta para path invalido: $CLAUDE_PROJECT_DIR" >&2
      exit 1
    fi
  fi

  local current
  current="$(pwd)"
  while true; do
    if [[ -d "${current}/.git" || -f "${current}/AGENTS.md" ]]; then
      echo "$current"
      return
    fi
    local parent
    parent="$(dirname "$current")"
    if [[ "$parent" == "$current" ]]; then
      echo "" ; return
    fi
    current="$parent"
  done
}

# ── Qdrant ────────────────────────────────────────────────────────────────────

test_qdrant() {
  curl -sf --max-time 2 "$QDRANT_URL" > /dev/null 2>&1
}

ensure_qdrant() {
  test_qdrant && return

  local container_id
  container_id="$(docker ps -aq --filter "name=^qdrant$" 2>/dev/null || true)"
  if [[ -n "$container_id" ]]; then
    docker start qdrant > /dev/null
  else
    docker run -d -p 6333:6333 -p 6334:6334 --name qdrant qdrant/qdrant > /dev/null
  fi

  local attempt=0
  while (( attempt < 20 )); do
    sleep 0.5
    test_qdrant && return
    (( attempt++ )) || true
  done

  echo "Qdrant nao respondeu em localhost:6333 apos inicializacao." >&2
  exit 1
}

# ── Porta livre ───────────────────────────────────────────────────────────────

get_free_port() {
  python3 -c "
import socket
s = socket.socket()
s.bind(('', 0))
print(s.getsockname()[1])
s.close()
"
}

# ── Aguardar servidor HTTP ────────────────────────────────────────────────────

wait_for_http_server() {
  local url="$1"
  local pid="$2"
  local attempt=0
  while (( attempt < 40 )); do
    if ! kill -0 "$pid" 2>/dev/null; then
      echo "Servidor autodev-codebase encerrou antes de aceitar conexoes." >&2
      exit 1
    fi
    if curl -sf --max-time 1 "$url" > /dev/null 2>&1; then
      return
    fi
    sleep 0.5
    (( attempt++ )) || true
  done
  echo "Servidor autodev-codebase nao respondeu no tempo esperado." >&2
  exit 1
}

# ── Chave de workspace (SHA-256 do path normalizado) ─────────────────────────

get_workspace_key() {
  local path
  path="$(python3 -c "import os,sys; print(os.path.realpath(sys.argv[1]).lower())" "$1")"
  echo -n "$path" | sha256sum | awk '{print $1}'
}

get_state_file_path() {
  local key
  key="$(get_workspace_key "$1")"
  echo "${STATE_DIR}/${key}.json"
}

get_lock_path() {
  echo "$(get_state_file_path "$1").lock"
}

# ── Estado do servidor (JSON) ─────────────────────────────────────────────────

read_server_state() {
  local state_file="$1"
  [[ -f "$state_file" ]] && cat "$state_file" || echo ""
}

write_server_state() {
  local state_file="$1"
  local workspace="$2" port="$3" pid="$4" server_url="$5" started_at="$6"
  local stdout_log="$7" stderr_log="$8"
  python3 -c "
import json, sys
d = {
  'workspacePath': sys.argv[1],
  'host': '$HOST',
  'port': int(sys.argv[2]),
  'serverUrl': sys.argv[3],
  'pid': int(sys.argv[4]),
  'startedAt': sys.argv[5],
  'lastSeenAt': sys.argv[5],
  'stdoutLog': sys.argv[6],
  'stderrLog': sys.argv[7],
}
print(json.dumps(d, indent=2))
" "$workspace" "$port" "$server_url" "$pid" "$started_at" "$stdout_log" "$stderr_log" > "$state_file"
}

# ── Lock de workspace (mkdir atomico) ────────────────────────────────────────

acquire_workspace_lock() {
  local lock_path="$1"
  local attempt=0
  while (( attempt < 120 )); do
    mkdir "$lock_path" 2>/dev/null && return
    sleep 0.25
    (( attempt++ )) || true
  done
  echo "Nao foi possivel adquirir o lock do workspace." >&2
  exit 1
}

release_workspace_lock() {
  rm -rf "$1"
}

# ── Verificar processo e saude do servidor ────────────────────────────────────

test_process_alive() {
  kill -0 "$1" 2>/dev/null
}

test_server_health() {
  local url="http://${HOST}:${1}/health"
  curl -sf --max-time 1 "$url" > /dev/null 2>&1
}

# ── Iniciar servidor ──────────────────────────────────────────────────────────

start_workspace_server() {
  local workspace="$1"
  local port
  port="$(get_free_port)"
  local server_url="http://${HOST}:${port}/mcp"
  local timestamp
  timestamp="$(date +%Y%m%d-%H%M%S)"
  local key
  key="$(get_workspace_key "$workspace")"
  local stdout_log="${LOG_DIR}/autodev-codebase-${key}-${timestamp}.stdout.log"
  local stderr_log="${LOG_DIR}/autodev-codebase-${key}-${timestamp}.stderr.log"

  "$CODEBASE_CMD" index --serve \
    --host="$HOST" \
    --port="$port" \
    --path="$workspace" \
    --log-level=error \
    > "$stdout_log" 2> "$stderr_log" &
  local server_pid=$!

  wait_for_http_server "$server_url" "$server_pid"

  local started_at
  started_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  write_server_state \
    "$(get_state_file_path "$workspace")" \
    "$workspace" "$port" "$server_pid" "$server_url" \
    "$started_at" "$stdout_log" "$stderr_log"
}

# ── Obter ou iniciar estado do servidor ───────────────────────────────────────

get_or_start_server() {
  local workspace="$1"
  local state_file
  state_file="$(get_state_file_path "$workspace")"
  local lock_path
  lock_path="$(get_lock_path "$workspace")"

  acquire_workspace_lock "$lock_path"
  trap "release_workspace_lock '$lock_path'" EXIT

  local state
  state="$(read_server_state "$state_file")"

  if [[ -n "$state" ]]; then
    local existing_pid existing_port
    existing_pid="$(echo "$state" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('pid',0))")"
    existing_port="$(echo "$state" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('port',0))")"

    if (( existing_pid > 0 && existing_port > 0 )) && \
       test_process_alive "$existing_pid" && \
       test_server_health "$existing_port"; then
      release_workspace_lock "$lock_path"
      trap - EXIT
      echo "$state"
      return
    fi
  fi

  start_workspace_server "$workspace"
  release_workspace_lock "$lock_path"
  trap - EXIT
  read_server_state "$state_file"
}

# ── Main ──────────────────────────────────────────────────────────────────────

WORKSPACE_PATH="$(resolve_workspace_path)"
if [[ -z "$WORKSPACE_PATH" ]]; then
  echo "Nao foi possivel determinar o workspace. Defina CODEBASE_WORKSPACE ou execute dentro de um repositorio git." >&2
  exit 1
fi

ensure_qdrant

SERVER_STATE="$(get_or_start_server "$WORKSPACE_PATH")"
SERVER_URL="$(echo "$SERVER_STATE" | python3 -c "import json,sys; print(json.load(sys.stdin)['serverUrl'])")"

if [[ -z "$SERVER_URL" ]]; then
  echo "Nao foi possivel inicializar o servidor HTTP do autodev-codebase." >&2
  exit 1
fi

exec "$CODEBASE_CMD" stdio --server-url="$SERVER_URL" --log-level=error
