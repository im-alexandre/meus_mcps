# Bootstrap

## Bootstrap de configuracoes

Use estas instrucoes quando a maquina ainda nao tiver o repositorio clonado e o usuario pedir para instalar a configuracao global a partir do repositorio publico.

### Metodo automatico (recomendado)

1. Clone o repositorio:
   - **Windows**: clone em `D:/mcp` (ou qualquer diretorio, o script detecta automaticamente)
   - **WSL**: o repo Windows ja fica acessivel em `/mnt/d/mcp` — nao e necessario clonar novamente
   - **Linux nativo**: clone em `~/meus_mcps` ou qualquer diretorio

2. Execute o script de bootstrap:
   ```bash
   bash setup.sh
   ```
   O script detecta o OS (Windows/WSL/Linux), resolve `REPO_ROOT`, escreve `~/.claude/CLAUDE.md`,
   mescla hooks e MCPs em `~/.claude/settings.json` e configura `~/.codex/AGENTS.md` se o Codex estiver instalado.

3. Reinicie o Claude Code para carregar os novos hooks e MCPs.

### Metodo manual (fallback)

Se o script nao puder ser executado:

1. Copie `CLAUDE.minimal.md` para `~/.claude/CLAUDE.md` e substitua `AUTHORITATIVE_RULES_ROOT` pelo path real do repositorio.
2. Mescle `ai-rules/claude/claude_settings.json` em `~/.claude/settings.json`, substituindo `{{REPO_ROOT}}` pelo path real.
3. Copie `AGENTS.minimal.md` para `~/.codex/AGENTS.md` com o mesmo ajuste de path.

## Scripts de MCP por plataforma

| Script | Plataforma | Localização apos bootstrap |
|---|---|---|
| `scripts/autodev-codebase-mcp.ps1` | Windows | `C:/Users/<user>/.ai/bin/` (instalado manualmente) |
| `scripts/autodev-codebase-mcp.sh` | WSL / Linux | `~/.ai/bin/` (instalado pelo `setup.sh`) |

O `setup.sh` copia automaticamente o `.sh` para `~/.ai/bin/` em ambientes WSL e Linux.

## Isolamento WSL (Claude CLI nativo no WSL)

Por padrao, o WSL herda o PATH do Windows (`appendWindowsPath=true`). Sem isolamento,
`claude` no terminal WSL resolve para `claude.exe` do Windows.

1. Configurar `/etc/wsl.conf` na distro:
   ```bash
   echo '[interop]' | sudo tee -a /etc/wsl.conf
   echo 'appendWindowsPath = false' | sudo tee -a /etc/wsl.conf
   ```
2. Reiniciar a distro (PowerShell do Windows):
   ```powershell
   wsl --shutdown
   ```
3. Instalar o Claude CLI no WSL:
   ```bash
   npm install -g @anthropic-ai/claude-code
   ```
4. Rodar `bash setup.sh` dentro do WSL para configurar `~/.claude/` com paths Linux.

Apos isso, `which claude` no WSL deve retornar `/usr/local/bin/claude` (nao `/mnt/c/...`).

## Claude Desktop: abrir com backend WSL (launcher)

O `setup.sh` (executado no Windows) gera `launch-claude-wsl.ps1` e o instala em
`%LOCALAPPDATA%\Programs\`. Esse launcher:

1. Abre um terminal WSL com `claude` rodando (o CLI WSL vira o worker da sessao).
2. Abre o Claude Desktop app.

**Como usar:**
```powershell
powershell -ExecutionPolicy Bypass -File "$env:LOCALAPPDATA\Programs\launch-claude-wsl.ps1"
```

**Criar atalho no Desktop (uma vez, no PowerShell):**
```powershell
$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut("$env:USERPROFILE\Desktop\Claude (WSL).lnk")
$sc.TargetPath = "powershell.exe"
$sc.Arguments = "-ExecutionPolicy Bypass -WindowStyle Hidden -File `"$env:LOCALAPPDATA\Programs\launch-claude-wsl.ps1`""
$sc.IconLocation = "$env:LOCALAPPDATA\Programs\Claude\Claude.exe"
$sc.Save()
```

**Inicializacao automatica com Windows:** o `setup.sh` oferece registrar o launcher em
`HKCU\Software\Microsoft\Windows\CurrentVersion\Run` — o WSL claude inicia junto com
o login do Windows.

## Claude Desktop: MCPs via WSL (sessao sem worker local)

Quando o desktop inicia uma sessao sem um worker WSL rodando, os MCPs sao spawned
a partir de `%APPDATA%\Claude\claude_desktop_config.json`. O `setup.sh` (Windows)
configura esse arquivo com `wsl` como comando para cada servidor:

```json
{ "mcpServers": { "local-llm": { "command": "wsl", "args": ["python3", "/mnt/d/mcp/server_llm.py"] } } }
```

Pre-requisito: rodar `bash setup.sh` dentro do WSL primeiro (instala `~/.ai/bin/autodev-codebase-mcp.sh`).

## MCPs externos

Os MCPs abaixo nao devem ser copiados de dumps locais. Eles devem ser instalados a partir dos repositorios oficiais.

- `autodev-codebase`: `https://github.com/anrgct/autodev-codebase`
- `pdf-indexer`: `https://github.com/lizTheDeveloper/pdf-indexer-mcp`

Comandos textuais obrigatorios para a IA seguir durante a instalacao:

- `Leia o README de https://github.com/anrgct/autodev-codebase e siga as orientacoes de instalacao.`
- `Leia o README de https://github.com/lizTheDeveloper/pdf-indexer-mcp e siga as orientacoes de instalacao.`

## Atualizacoes futuras

Quando o usuario pedir atualizacao global, leia `ai-rules/shared/global-config-update-policy.md` e siga esse fluxo.
