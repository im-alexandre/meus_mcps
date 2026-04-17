# Bootstrap

URL publica recomendada para bootstrap manual-assistido:

- https://github.com/im-alexandre/meus_mcps/blob/main/bootstrap.md

Use este documento quando o ambiente global do Codex ou do Claude ainda nao estiver configurado. O objetivo e permitir que um agente configure os arquivos locais corretos apenas lendo esta pagina.

## Resultado esperado

Ao final do bootstrap, o ambiente deve ter:

- `~/.codex/AGENTS.md` apontando para o `AUTHORITATIVE_RULES_ROOT` real
- `~/.codex/config.toml` com os MCPs globais do projeto, sem `autodev-codebase`
- `~/.claude/CLAUDE.md` apontando para o `AUTHORITATIVE_RULES_ROOT` real
- `~/.claude/settings.json` configurado a partir do template global do repositório
- `~/.claude/.mcp.json` ou `~/.claude/mcp.json` configurado a partir do template global do repositório, quando aplicavel

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
- `{{CHROMA_DIR}}`: diretorio local onde o `scopus-search` armazenara o ChromaDB

Secoes obrigatorias do Codex neste arquivo global:

- `[mcp_servers.local-llm]`
- `[mcp_servers.scopus-search]`
- `[mcp_servers.docx-manager]`

Se `~/.codex/config.toml` ja existir, faca merge preservando configuracoes nao relacionadas.

> **Importante**: `autodev-codebase` nao deve ficar no config global do Codex. Quando necessario, ele deve ser configurado localmente em `$repoRoot/.codex/config.toml`.

## Passos do Claude CLI

### 5. Configurar `~/.claude/settings.json`

Use `ai-rules/claude/claude_settings.json` como fonte de verdade global.

Se `~/.claude/settings.json` ja existir:

- preserve chaves nao relacionadas
- faca merge sem duplicar entradas ja presentes

### 6. Configurar `~/.claude/.mcp.json` ou `~/.claude/mcp.json`

Use `ai-rules/claude/mcp.json` como template global.

Substitua manualmente:

- `{{REPO_ROOT}}`
- `{{PYTHON_CMD}}`

Se o arquivo global ja existir, faca merge preservando entradas nao relacionadas.

> **Importante**: `autodev-codebase` nao deve ficar no arquivo global do Claude. Quando necessario, ele deve ser configurado localmente em `$repoRoot/.mcp.json`.

## Configuracao local por repositorio Git

Quando o projeto atual for um repositorio Git e usar `autodev-codebase`, a configuracao deve ser criada no proprio repositorio:

- Codex: `$repoRoot/.codex/config.toml`
- Claude MCP: `$repoRoot/.mcp.json`
- Claude hooks: `$repoRoot/.claude/settings.json`

Se voce usa wrappers locais no PowerShell para `codex` e `claude`, esses arquivos podem ser materializados automaticamente ao entrar no repositorio e iniciar o cliente.

## Claude Desktop

Qualquer configuracao especifica do Claude Desktop e opcional e nao faz parte do bootstrap obrigatorio do CLI.

## Como resolver placeholders

Defaults razoaveis quando o agente nao tiver outra informacao melhor:

- Windows:
  - `{{PYTHON_CMD}} = python`
- WSL/Linux:
  - `{{PYTHON_CMD}} = python3`
- `{{CHROMA_DIR}}`:
  - Windows: `C:/Users/<usuario>/.codex/mcp/scopus/chroma`
  - WSL/Linux: `~/.codex/mcp/scopus/chroma`

Se o agente conhecer paths melhores do ambiente atual, deve usar o estado real da maquina.

## Validacao final

### Codex

Confirme:

- `~/.codex/AGENTS.md` existe
- `~/.codex/AGENTS.md` aponta para `<REPO_ROOT>/ai-rules`
- `~/.codex/config.toml` contem as secoes MCP globais esperadas

### Claude

Confirme:

- `~/.claude/CLAUDE.md` existe
- `~/.claude/CLAUDE.md` aponta para `<REPO_ROOT>/ai-rules`
- `~/.claude/settings.json` e JSON valido
- `~/.claude/.mcp.json` ou `~/.claude/mcp.json` e JSON valido, se o arquivo existir

### Repositorios Git com autodev-codebase

Quando o usuario estiver em um repositorio Git e quiser `autodev-codebase`, confirme tambem:

- `$repoRoot/.codex/config.toml` existe
- `$repoRoot/.mcp.json` existe
- `$repoRoot/.claude/settings.json` existe

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
