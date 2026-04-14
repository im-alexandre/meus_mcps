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

## MCPs externos

Os MCPs abaixo nao devem ser copiados de dumps locais. Eles devem ser instalados a partir dos repositorios oficiais.

- `autodev-codebase`: `https://github.com/anrgct/autodev-codebase`
- `pdf-indexer`: `https://github.com/lizTheDeveloper/pdf-indexer-mcp`

Comandos textuais obrigatorios para a IA seguir durante a instalacao:

- `Leia o README de https://github.com/anrgct/autodev-codebase e siga as orientacoes de instalacao.`
- `Leia o README de https://github.com/lizTheDeveloper/pdf-indexer-mcp e siga as orientacoes de instalacao.`

## Atualizacoes futuras

Quando o usuario pedir atualizacao global, leia `ai-rules/shared/global-config-update-policy.md` e siga esse fluxo.
