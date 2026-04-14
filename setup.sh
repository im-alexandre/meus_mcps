#!/usr/bin/env bash
# setup.sh — Bootstrap de configuracoes Claude e Codex
# Funciona em: Windows (Git Bash), WSL e Linux nativo
# Uso: bash setup.sh
set -euo pipefail

# ── Detectar OS e resolver REPO_ROOT ──────────────────────────────────────────

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if grep -qi microsoft /proc/version 2>/dev/null; then
  OS="wsl"
  PYTHON_CMD="python3"
elif [[ "${OS:-}" == "Windows_NT" ]]; then
  OS="windows"
  PYTHON_CMD="python"
  # Converter path POSIX para Windows se necessario (Git Bash)
  REPO_ROOT="$(cygpath -w "$REPO_ROOT" 2>/dev/null || echo "$REPO_ROOT")"
else
  OS="linux"
  PYTHON_CMD="python3"
fi

echo "OS detectado : $OS"
echo "REPO_ROOT    : $REPO_ROOT"
echo "Python       : $PYTHON_CMD"
echo ""

# ── Helpers ───────────────────────────────────────────────────────────────────

CLAUDE_DIR="${HOME}/.claude"
CODEX_DIR="${HOME}/.codex"
mkdir -p "$CLAUDE_DIR"

# Substitui {{REPO_ROOT}} e {{PYTHON_CMD}} em uma string
resolve_template() {
  local content="$1"
  content="${content//\{\{REPO_ROOT\}\}/$REPO_ROOT}"
  content="${content//\{\{PYTHON_CMD\}\}/$PYTHON_CMD}"
  echo "$content"
}

# Mescla JSON: adiciona chaves de $2 que nao existem em $1 (shallow para keys de topo)
# Para hooks e mcpServers faz merge profundo via Python
merge_json() {
  local target="$1"
  local source_content="$2"
  "$PYTHON_CMD" - "$target" <<PYEOF
import json, sys

target_path = sys.argv[1]
source = json.loads("""$source_content""")

try:
    with open(target_path) as f:
        existing = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    existing = {}

# Mesclar mcpServers
existing.setdefault("mcpServers", {}).update(source.get("mcpServers", {}))

# Mesclar hooks.PreToolUse (deduplicar por matcher)
src_hooks = source.get("hooks", {}).get("PreToolUse", [])
if src_hooks:
    existing.setdefault("hooks", {}).setdefault("PreToolUse", [])
    existing_matchers = {h.get("matcher") for h in existing["hooks"]["PreToolUse"]}
    for hook in src_hooks:
        if hook.get("matcher") not in existing_matchers:
            existing["hooks"]["PreToolUse"].append(hook)

with open(target_path, "w") as f:
    json.dump(existing, f, indent=2, ensure_ascii=False)
    f.write("\n")

print("  settings.json atualizado.")
PYEOF
}

# ── Claude ────────────────────────────────────────────────────────────────────

echo "==> Configurando Claude..."

# 1. CLAUDE.md global
CLAUDE_MD="$CLAUDE_DIR/CLAUDE.md"
MINIMAL_TEMPLATE="$(cat "$REPO_ROOT/CLAUDE.minimal.md")"
CLAUDE_MD_CONTENT="${MINIMAL_TEMPLATE/\~\/.meus_mcps\/ai-rules/$REPO_ROOT\/ai-rules}"
echo "$CLAUDE_MD_CONTENT" > "$CLAUDE_MD"
echo "  CLAUDE.md escrito em $CLAUDE_MD"

# 2. settings.json — mesclar hooks e mcpServers
SETTINGS_PATH="$CLAUDE_DIR/settings.json"
SETTINGS_TEMPLATE="$(cat "$REPO_ROOT/ai-rules/claude/claude_settings.json")"
SETTINGS_RESOLVED="$(resolve_template "$SETTINGS_TEMPLATE")"
merge_json "$SETTINGS_PATH" "$SETTINGS_RESOLVED"

# ── Codex ─────────────────────────────────────────────────────────────────────

echo ""
echo "==> Configurando Codex..."

if [[ -d "$CODEX_DIR" ]]; then
  AGENTS_MD="$CODEX_DIR/AGENTS.md"
  AGENTS_TEMPLATE="$(cat "$REPO_ROOT/AGENTS.minimal.md")"
  AGENTS_MD_CONTENT="${AGENTS_TEMPLATE/\~\/.meus_mcps\/ai-rules/$REPO_ROOT\/ai-rules}"
  echo "$AGENTS_MD_CONTENT" > "$AGENTS_MD"
  echo "  AGENTS.md escrito em $AGENTS_MD"
else
  echo "  ~/.codex nao encontrado — pulando Codex (rode novamente depois de instalar o Codex)."
fi

# ── Scripts de MCP (WSL/Linux) ────────────────────────────────────────────────

if [[ "$OS" == "wsl" || "$OS" == "linux" ]]; then
  echo ""
  echo "==> Instalando scripts de MCP para $OS..."
  AI_BIN="${HOME}/.ai/bin"
  mkdir -p "$AI_BIN"
  cp "$REPO_ROOT/scripts/autodev-codebase-mcp.sh" "$AI_BIN/"
  chmod +x "$AI_BIN/autodev-codebase-mcp.sh"
  echo "  autodev-codebase-mcp.sh instalado em $AI_BIN/"
  echo ""
  echo "  Adicione ao ~/.claude/.mcp.json (ou ~/.claude/mcp.json) a entrada:"
  echo '  "autodev-codebase": {'
  echo '    "command": "bash",'
  echo "    \"args\": [\"$AI_BIN/autodev-codebase-mcp.sh\"],"
  echo '    "env": { "CODEBASE_WORKSPACE": "${CLAUDE_PROJECT_DIR}" }'
  echo '  }'
fi

# ── Feito ─────────────────────────────────────────────────────────────────────

echo ""
echo "Bootstrap concluido."
echo "Reinicie o Claude Code para carregar os novos hooks e MCPs."
