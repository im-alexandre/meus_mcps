#!/usr/bin/env bash
# setup.sh — Bootstrap de configuracoes Claude e Codex
# Funciona em: Windows (Git Bash), WSL e Linux nativo
# Uso: bash setup.sh
set -euo pipefail

# ── Detectar OS e resolver REPO_ROOT ──────────────────────────────────────────

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT_SRC="$REPO_ROOT"   # preserva path Unix antes do cygpath (Windows)

if grep -qi microsoft /proc/version 2>/dev/null; then
  OS="wsl"
  PYTHON_CMD="python3"
elif [[ "${OS:-}" == "Windows_NT" ]]; then
  OS="windows"
  PYTHON_CMD="python"
  REPO_ROOT="$(cygpath -m "$REPO_ROOT" 2>/dev/null || echo "$REPO_ROOT")"
  REPO_ROOT_WSL="$("$PYTHON_CMD" -c "
import sys
p = sys.argv[1].replace('\\\\', '/')
drive, rest = p[0].lower(), p[2:]
print(f'/mnt/{drive}{rest}')
" "$REPO_ROOT")"
else
  OS="linux"
  PYTHON_CMD="python3"
fi

REPO_ROOT_WSL="${REPO_ROOT_WSL:-}"   # vazio para wsl/linux
AI_BIN="${HOME}/.ai/bin"
CLAUDE_DIR="${HOME}/.claude"
CODEX_DIR="${HOME}/.codex"

mkdir -p "$CLAUDE_DIR" "$AI_BIN"

echo "OS detectado : $OS"
echo "REPO_ROOT    : $REPO_ROOT"
echo "Python       : $PYTHON_CMD"
echo ""

# ── WSL isolation check ───────────────────────────────────────────────────────

if [[ "$OS" == "wsl" ]]; then
  WSL_CONF="/etc/wsl.conf"
  if ! grep -qE "appendWindowsPath\s*=\s*false" "$WSL_CONF" 2>/dev/null; then
    echo "AVISO: WSL esta compartilhando o PATH do Windows."
    echo "  Isso pode fazer 'claude' resolver para claude.exe do Windows."
    echo ""
    echo "  Para isolar, execute:"
    echo "    echo '[interop]' | sudo tee -a /etc/wsl.conf"
    echo "    echo 'appendWindowsPath = false' | sudo tee -a /etc/wsl.conf"
    echo "  Depois reinicie a distro: wsl --shutdown  (no PowerShell do Windows)"
    echo ""
    echo "  Instale o Claude CLI nativo no WSL:"
    echo "    npm install -g @anthropic-ai/claude-code"
    echo ""
    read -rp "  Continuar o setup sem isolar? [s/N] " REPLY
    [[ "$REPLY" =~ ^[Ss]$ ]] || exit 0
  else
    echo "WSL isolation: OK (appendWindowsPath=false detectado)"
    echo ""
  fi
fi

# ── Helpers ───────────────────────────────────────────────────────────────────

resolve_template() {
  local template_file="$1"
  "$PYTHON_CMD" - "$template_file" "$REPO_ROOT" "$PYTHON_CMD" "$AI_BIN" "$REPO_ROOT_WSL" <<'PYEOF'
import sys, re, subprocess

template_file, repo_root, python_cmd, ai_bin, repo_root_wsl = sys.argv[1:]

if not repo_root_wsl:
    m = re.match(r'([A-Za-z]):[/\\](.*)', repo_root.replace('\\', '/'))
    if m:
        repo_root_wsl = f'/mnt/{m.group(1).lower()}/{m.group(2)}'.rstrip('/')

python_cmd_wsl = 'python3'
if re.match(r'^[A-Za-z]:', repo_root):
    try:
        result = subprocess.run(
            ['wsl', 'bash', '-lc', 'which python3 2>/dev/null || echo /usr/bin/python3'],
            capture_output=True, text=True, timeout=10
        )
        path = result.stdout.strip().split('\n')[0]
        if path.startswith('/'):
            python_cmd_wsl = path
    except Exception:
        pass

with open(template_file, encoding='utf-8') as f:
    content = f.read()
content = content.replace('{{REPO_ROOT}}', repo_root)
content = content.replace('{{PYTHON_CMD}}', python_cmd)
content = content.replace('{{AI_BIN}}', ai_bin)
content = content.replace('{{REPO_ROOT_WSL}}', repo_root_wsl)
content = content.replace('{{PYTHON_CMD_WSL}}', python_cmd_wsl)
print(content, end='')
PYEOF
}

merge_json() {
  local target="$1"
  local source_content="$2"
  local tmp_src
  tmp_src="$(mktemp)"
  printf '%s' "$source_content" > "$tmp_src"
  local target_py="$target"
  local tmp_src_py="$tmp_src"
  if [[ "${OS:-}" == "windows" ]]; then
    target_py="$(cygpath -m "$target" 2>/dev/null || echo "$target")"
    tmp_src_py="$(cygpath -m "$tmp_src" 2>/dev/null || echo "$tmp_src")"
  fi
  "$PYTHON_CMD" - "$target_py" "$tmp_src_py" <<'PYEOF'
import json, sys

target_path, source_path = sys.argv[1], sys.argv[2]

with open(source_path, encoding='utf-8') as f:
    source = json.load(f)

try:
    with open(target_path, encoding='utf-8') as f:
        existing = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    existing = {}

existing.setdefault('mcpServers', {}).update(source.get('mcpServers', {}))

src_hooks = source.get('hooks', {}).get('PreToolUse', [])
if src_hooks:
    existing.setdefault('hooks', {}).setdefault('PreToolUse', [])
    existing_matchers = {h.get('matcher') for h in existing['hooks']['PreToolUse']}
    for hook in src_hooks:
        if hook.get('matcher') not in existing_matchers:
            existing['hooks']['PreToolUse'].append(hook)

with open(target_path, 'w', encoding='utf-8') as f:
    json.dump(existing, f, indent=2, ensure_ascii=False)
    f.write('\n')

print('  atualizado.')
PYEOF
  rm -f "$tmp_src"
}

# ── Claude — CLAUDE.md ────────────────────────────────────────────────────────

echo "==> Configurando Claude..."

CLAUDE_MD="$CLAUDE_DIR/CLAUDE.md"
MINIMAL_CONTENT="$(cat "$REPO_ROOT/CLAUDE.minimal.md")"
CLAUDE_MD_CONTENT="${MINIMAL_CONTENT//\~\/.meus_mcps\/ai-rules/$REPO_ROOT\/ai-rules}"
echo "$CLAUDE_MD_CONTENT" > "$CLAUDE_MD"
echo "  CLAUDE.md -> $CLAUDE_MD"

# ── Claude — settings.json global ─────────────────────────────────────────────

SETTINGS_PATH="$CLAUDE_DIR/settings.json"
SETTINGS_RESOLVED="$(resolve_template "$REPO_ROOT/ai-rules/claude/claude_settings.json")"
echo -n "  settings.json: "
merge_json "$SETTINGS_PATH" "$SETTINGS_RESOLVED"

# ── Claude — ~/.claude/.mcp.json (mcpServers globais) ─────────────────────────

MCP_PATH="$CLAUDE_DIR/.mcp.json"
MCP_RESOLVED="$(resolve_template "$REPO_ROOT/ai-rules/claude/mcp.json")"
echo -n "  .mcp.json: "
merge_json "$MCP_PATH" "$MCP_RESOLVED"

# ── Codex ─────────────────────────────────────────────────────────────────────

echo ""
echo "==> Configurando Codex..."

if [[ -d "$CODEX_DIR" ]]; then
  AGENTS_MD="$CODEX_DIR/AGENTS.md"
  AGENTS_CONTENT="$(cat "$REPO_ROOT/AGENTS.minimal.md")"
  AGENTS_MD_CONTENT="${AGENTS_CONTENT//\~\/.meus_mcps\/ai-rules/$REPO_ROOT\/ai-rules}"
  echo "$AGENTS_MD_CONTENT" > "$AGENTS_MD"
  echo "  AGENTS.md -> $AGENTS_MD"

  echo "  autodev-codebase nao e configurado globalmente no Codex."
  echo "  Para repositorios Git, use wrappers locais que materializam \$repoRoot/.codex/config.toml, \$repoRoot/.mcp.json e \$repoRoot/.claude/settings.json."
else
  echo "  ~/.codex nao encontrado — pulando (rode novamente apos instalar o Codex)."
fi

# ── Claude Desktop (GUI → MCPs via WSL + launcher) ───────────────────────────

if [[ "$OS" == "windows" ]]; then
  echo ""
  echo "==> Configurando Claude Desktop (GUI)..."

  CLAUDE_DESKTOP_DIR="$(cygpath -u "${APPDATA:-}")/Claude"
  mkdir -p "$CLAUDE_DESKTOP_DIR"
  DESKTOP_CONFIG="$CLAUDE_DESKTOP_DIR/claude_desktop_config.json"
  DESKTOP_MCP_RESOLVED="$(resolve_template "$REPO_ROOT/ai-rules/claude/claude_desktop_wsl_mcp.json")"
  echo -n "  claude_desktop_config.json: "
  merge_json "$DESKTOP_CONFIG" "$DESKTOP_MCP_RESOLVED"

  LAUNCHER_SRC="$REPO_ROOT_SRC/scripts/launch-claude-wsl.ps1"
  LAUNCHER_DST="$(cygpath -u "${LOCALAPPDATA:-}")/Programs/launch-claude-wsl.ps1"
  mkdir -p "$(dirname "$LAUNCHER_DST")"
  cp "$LAUNCHER_SRC" "$LAUNCHER_DST"
  echo "  launcher: $LAUNCHER_DST"
  echo ""
  echo "  Para abrir o Claude Desktop com backend WSL, use:"
  echo "    powershell -ExecutionPolicy Bypass -File \"$(cygpath -w "$LAUNCHER_DST")\""
  echo ""
  echo "  Ou crie um atalho no Desktop apontando para esse comando."
  echo ""
  read -rp "  Registrar launcher na inicializacao do Windows? [s/N] " STARTUP_REPLY
  if [[ "$STARTUP_REPLY" =~ ^[Ss]$ ]]; then
    REG_CMD="powershell -WindowStyle Hidden -ExecutionPolicy Bypass -File \"$(cygpath -w "$LAUNCHER_DST")\""
    reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" \
      /v "ClaudeWSLLauncher" /t REG_SZ /d "$REG_CMD" /f 2>/dev/null && \
      echo "  startup: registrado em HKCU\\...\\Run" || \
      echo "  AVISO: nao foi possivel registrar no startup (rode como admin se necessario)"
  fi
fi

echo ""
echo "Bootstrap concluido. Reinicie o Claude Code para carregar os MCPs globais. Para autodev-codebase, use a configuracao local por repositorio Git."
