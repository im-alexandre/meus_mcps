# Bootstrap

URL publica recomendada para bootstrap manual-assistido:

- https://github.com/im-alexandre/meus_mcps/blob/main/bootstrap.md

Use este documento quando o ambiente global do Codex ou do Claude ainda nao estiver configurado. O objetivo e permitir que um agente configure os arquivos locais corretos apenas lendo esta pagina.

## Resultado esperado

Ao final do bootstrap, o ambiente deve ter:

- `~/.codex/AGENTS.md` apontando para o `AUTHORITATIVE_RULES_ROOT` real
- `~/.codex/config.toml` com os MCPs do Codex configurados
- `~/.claude/CLAUDE.md` apontando para o `AUTHORITATIVE_RULES_ROOT` real
- `~/.claude/settings.json` configurado a partir do template do repositório
- `~/.claude/.mcp.json` configurado a partir do template do repositório, quando aplicavel

## Fluxo unico

### 1. Garantir um clone local do repositorio

Se o repositorio ainda nao existir localmente, clone:

```bash
git clone https://github.com/im-alexandre/meus_mcps.git
```

Se ele ja existir, identifique o diretorio raiz real do clone. Esse diretorio sera o `REPO_ROOT`.

### 2. Definir `AUTHORITATIVE_RULES_ROOT`

Use:

```text
AUTHORITATIVE_RULES_ROOT = <REPO_ROOT>/ai-rules
```

Exemplos:

- Windows: `D:/mcp/ai-rules`
- WSL/Linux: `/mnt/d/mcp/ai-rules` ou `/home/<usuario>/meus_mcps/ai-rules`

### 3. Atualizar os stubs minimos

Copie os arquivos abaixo do repositório para os caminhos globais e substitua o valor padrao de `AUTHORITATIVE_RULES_ROOT` pelo path real do clone:

- `AGENTS.minimal.md` -> `~/.codex/AGENTS.md`
- `CLAUDE.minimal.md` -> `~/.claude/CLAUDE.md`

Os arquivos globais devem continuar curtos. Nao mova regras longas para eles.

## Passos do Codex

### 4. Configurar `~/.codex/config.toml`

Use `ai-rules/codex/codex_settings.toml` como template de referencia.

Substitua manualmente os placeholders abaixo:

- `{{REPO_ROOT}}`: diretorio raiz real do clone
- `{{PYTHON_CMD}}`: binario Python que deve executar os servidores MCP
- `{{AUTODEV_CMD}}`: comando usado para iniciar o `autodev-codebase`
- `{{AUTODEV_ARGS}}`: lista TOML de argumentos do `autodev-codebase`
- `{{CHROMA_DIR}}`: diretorio local onde o `scopus-search` armazenara o ChromaDB

Secoes obrigatorias do Codex:

- `[mcp_servers.autodev-codebase]`
- `[mcp_servers.local-llm]`
- `[mcp_servers.scopus-search]`
- `[mcp_servers.docx-manager]`

Secoes opcionais do Codex:

- blocos `[mcp_servers.<nome>.tools.<tool>]` com `approval_mode`
- `[mcp_servers.scopus-search.env]` se voce quiser explicitar `CHROMA_DIR`

Se `~/.codex/config.toml` ja existir, faca merge preservando configuracoes nao relacionadas a estes MCPs.

## Passos do Claude CLI

### 5. Configurar `~/.claude/settings.json`

Use `ai-rules/claude/claude_settings.json` como fonte de verdade.

Substitua manualmente:

- `{{REPO_ROOT}}` pelo diretorio raiz real do clone

> **Nota**: `claude_settings.json` contem apenas hooks (`PreToolUse`). Nao ha `mcpServers` neste arquivo — todos os MCPs ficam em `mcp.json` (passo 6).

Se `~/.claude/settings.json` ja existir:

- preserve chaves nao relacionadas
- faca merge de `hooks.PreToolUse` sem duplicar `matcher`

### 6. Configurar `~/.claude/.mcp.json`

Use `ai-rules/claude/mcp.json` como template (o nome do arquivo de destino tem ponto: `.mcp.json`).

Substitua manualmente:

- `{{REPO_ROOT}}`
- `{{PYTHON_CMD}}`

> **Nota**: o servidor `autodev-codebase` ja usa `pwsh` com o script `scripts/autodev-codebase-current-git-mcp.ps1` — nao ha placeholders `{{AUTODEV_CMD}}` ou `{{AUTODEV_ARGS}}` no template.

Se `~/.claude/.mcp.json` ja existir, faca merge preservando entradas nao relacionadas.

### 7. Claude Desktop

Qualquer configuracao especifica do Claude Desktop e opcional e nao faz parte do bootstrap obrigatorio do CLI.

## Como resolver placeholders

Defaults razoaveis quando o agente nao tiver outra informacao melhor:

- Windows:
  - `{{PYTHON_CMD}} = python`
  - `{{AUTODEV_CMD}} = pwsh`
  - `{{AUTODEV_ARGS}} = ["-File", "C:/Users/<usuario>/.ai/bin/autodev-codebase-mcp.ps1"]`
- WSL/Linux:
  - `{{PYTHON_CMD}} = python3`
  - `{{AUTODEV_CMD}} = bash`
  - `{{AUTODEV_ARGS}} = ["~/.ai/bin/autodev-codebase-mcp.sh"]`
- `{{CHROMA_DIR}}`:
  - Windows: `C:/Users/<usuario>/.codex/mcp/scopus/chroma`
  - WSL/Linux: `~/.codex/mcp/scopus/chroma`

Se o agente conhecer paths melhores do ambiente atual, deve usar o estado real da maquina.

## Validacao final

### Codex

Confirme:

- `~/.codex/AGENTS.md` existe
- `~/.codex/AGENTS.md` aponta para `<REPO_ROOT>/ai-rules`
- `~/.codex/config.toml` contem as secoes MCP obrigatorias

### Claude

Confirme:

- `~/.claude/CLAUDE.md` existe
- `~/.claude/CLAUDE.md` aponta para `<REPO_ROOT>/ai-rules`
- `~/.claude/settings.json` e JSON valido
- `~/.claude/.mcp.json` e JSON valido, se o arquivo existir

### Sanidade do repositório

Confirme tambem:

- `REPO_ROOT/ai-rules/codex/AGENTS.authoritative.md` existe
- `REPO_ROOT/ai-rules/claude/CLAUDE.authoritative.md` existe
- os caminhos de `server_llm.py`, `server_scopus.py` e `server_docx.py` usados nas configs existem de fato

## MCPs externos

Os MCPs abaixo nao devem ser copiados de dumps locais. Instale a partir dos repositorios oficiais:

- `autodev-codebase`: https://github.com/anrgct/autodev-codebase
- `pdf-indexer`: https://github.com/lizTheDeveloper/pdf-indexer-mcp

Comandos textuais obrigatorios para a IA seguir durante a instalacao:

- `Leia o README de https://github.com/anrgct/autodev-codebase e siga as orientacoes de instalacao.`
- `Leia o README de https://github.com/lizTheDeveloper/pdf-indexer-mcp e siga as orientacoes de instalacao.`

## Atualizacoes futuras

Quando o usuario pedir alteracao global de bootstrap, `AGENTS.md` ou `CLAUDE.md`, leia `ai-rules/shared/global-config-update-policy.md` antes de modificar os arquivos.
