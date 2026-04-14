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
  REPO_ROOT="$(cygpath -w "$REPO_ROOT" 2>/dev/null || echo "$REPO_ROOT")"
else
  OS="linux"
  PYTHON_CMD="python3"
fi

echo "OS detectado : $OS"
echo "REPO_ROOT    : $REPO_ROOT"
echo "Python       : $PYTHON_CMD"
echo ""

# ── Resolver comando do autodev-codebase por plataforma ───────────────────────

AI_BIN="${HOME}/.ai/bin"

if [[ "$OS" == "windows" ]]; then
  PWSH="$(command -v pwsh 2>/dev/null || echo 'C:/Program Files/PowerShell/7/pwsh.exe')"
  AUTODEV_CMD="$PWSH"
  AUTODEV_ARGS="[\"-File\", \"$(cygpath -w "$AI_BIN" 2>/dev/null || echo "$AI_BIN")/autodev-codebase-mcp.ps1\"]"
  AUTODEV_ARGS_TOML="[\"-File\", \"$(cygpath -w "$AI_BIN" 2>/dev/null || echo "$AI_BIN")/autodev-codebase-mcp.ps1\"]"
else
  AUTODEV_CMD="bash"
  AUTODEV_ARGS="[\"${AI_BIN}/autodev-codebase-mcp.sh\"]"
  AUTODEV_ARGS_TOML="[\"${AI_BIN}/autodev-codebase-mcp.sh\"]"
fi

# ── Helpers ───────────────────────────────────────────────────────────────────

CLAUDE_DIR="${HOME}/.claude"
CODEX_DIR="${HOME}/.codex"
mkdir -p "$CLAUDE_DIR" "$AI_BIN"

resolve_template() {
  "$PYTHON_CMD" - "$REPO_ROOT" "$PYTHON_CMD" "$AUTODEV_CMD" "$AUTODEV_ARGS" "$AI_BIN" <<'PYEOF'
import sys
content = sys.stdin.read()
repo_root, python_cmd, autodev_cmd, autodev_args, ai_bin = sys.argv[1:]
content = content.replace("{{REPO_ROOT}}", repo_root)
content = content.replace("{{PYTHON_CMD}}", python_cmd)
content = content.replace("{{AUTODEV_CMD}}", autodev_cmd)
content = content.replace("{{AUTODEV_ARGS}}", autodev_args)
content = content.replace("{{AI_BIN}}", ai_bin)
print(content, end="")
PYEOF
}

# Mescla JSON: adiciona/sobrescreve chaves de topo e faz merge profundo de
# hooks.PreToolUse (deduplicar por matcher) e mcpServers
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

# mcpServers: sobrescreve entrada por entrada
existing.setdefault("mcpServers", {}).update(source.get("mcpServers", {}))

# hooks.PreToolUse: adiciona apenas matchers ausentes
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

print("  atualizado.")
PYEOF
}

# Adiciona ou substitui secao [mcp_servers.autodev-codebase] no config.toml do Codex
merge_codex_toml() {
  local target="$1"
  local autodev_cmd="$2"
  local autodev_args="$3"
  "$PYTHON_CMD" - "$target" "$autodev_cmd" "$autodev_args" <<'PYEOF'
import sys, re

target_path, autodev_cmd, autodev_args = sys.argv[1], sys.argv[2], sys.argv[3]

try:
    with open(target_path, encoding="utf-8") as f:
        content = f.read()
except FileNotFoundError:
    content = ""

new_section = f"""[mcp_servers.autodev-codebase]
command = "{autodev_cmd}"
args = {autodev_args}
startup_timeout_sec = 30
"""

# Remove secao existente (ate o proximo [mcp_servers.* ou EOF)
pattern = r"\[mcp_servers\.autodev-codebase\].*?(?=\[mcp_servers\.|$)"
content = re.sub(pattern, "", content, flags=re.DOTALL).strip()

# Insere antes da primeira secao [mcp_servers.*] ou no inicio
insert_match = re.search(r"\[mcp_servers\.", content)
if insert_match:
    pos = insert_match.start()
    content = content[:pos] + new_section + "\n" + content[pos:]
else:
    content = new_section + ("\n" + content if content else "")

with open(target_path, "w", encoding="utf-8") as f:
    f.write(content.strip() + "\n")

print("  config.toml atualizado.")
PYEOF
}

# ── Claude — CLAUDE.md ────────────────────────────────────────────────────────

echo "==> Configurando Claude..."

CLAUDE_MD="$CLAUDE_DIR/CLAUDE.md"
MINIMAL_CONTENT="$(cat "$REPO_ROOT/CLAUDE.minimal.md")"
CLAUDE_MD_CONTENT="${MINIMAL_CONTENT//\~\/.meus_mcps\/ai-rules/$REPO_ROOT\/ai-rules}"
echo "$CLAUDE_MD_CONTENT" > "$CLAUDE_MD"
echo "  CLAUDE.md -> $CLAUDE_MD"

# ── Claude — settings.json (hooks + mcpServers customizados) ──────────────────

SETTINGS_PATH="$CLAUDE_DIR/settings.json"
SETTINGS_RESOLVED="$(resolve_template < "$REPO_ROOT/ai-rules/claude/claude_settings.json")"
echo -n "  settings.json: "
merge_json "$SETTINGS_PATH" "$SETTINGS_RESOLVED"

# ── Claude — .mcp.json (todos os MCPs incluindo autodev-codebase) ─────────────

MCP_PATH="$CLAUDE_DIR/.mcp.json"
MCP_RESOLVED="$(resolve_template < "$REPO_ROOT/ai-rules/claude/mcp.json")"
echo -n "  .mcp.json: "
merge_json "$MCP_PATH" "$MCP_RESOLVED"

# ── Scripts de MCP (WSL/Linux) ────────────────────────────────────────────────

if [[ "$OS" == "wsl" || "$OS" == "linux" ]]; then
  cp "$REPO_ROOT/scripts/autodev-codebase-mcp.sh" "$AI_BIN/"
  chmod +x "$AI_BIN/autodev-codebase-mcp.sh"
  echo "  autodev-codebase-mcp.sh -> $AI_BIN/"
fi

# ── Codex ─────────────────────────────────────────────────────────────────────

echo ""
echo "==> Configurando Codex..."

if [[ -d "$CODEX_DIR" ]]; then
  # AGENTS.md
  AGENTS_MD="$CODEX_DIR/AGENTS.md"
  AGENTS_CONTENT="$(cat "$REPO_ROOT/AGENTS.minimal.md")"
  AGENTS_MD_CONTENT="${AGENTS_CONTENT//\~\/.meus_mcps\/ai-rules/$REPO_ROOT\/ai-rules}"
  echo "$AGENTS_MD_CONTENT" > "$AGENTS_MD"
  echo "  AGENTS.md -> $AGENTS_MD"

  # config.toml — adicionar/atualizar entrada autodev-codebase
  CODEX_CONFIG="$CODEX_DIR/config.toml"
  if [[ -f "$CODEX_CONFIG" ]]; then
    echo -n "  config.toml: "
    merge_codex_toml "$CODEX_CONFIG" "$AUTODEV_CMD" "$AUTODEV_ARGS_TOML"
  else
    echo "  config.toml nao encontrado em $CODEX_DIR — pulando."
  fi
else
  echo "  ~/.codex nao encontrado — pulando (rode novamente apos instalar o Codex)."
fi

# ── Feito ─────────────────────────────────────────────────────────────────────

echo ""
echo "Bootstrap concluido. Reinicie o Claude Code para carregar os novos hooks e MCPs."
