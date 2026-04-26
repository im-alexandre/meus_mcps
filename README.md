# meus_mcps

Colecao de servidores MCP locais voltada a fluxos de pesquisa assistida, com foco atual em:

- geracao local de texto e embeddings;
- indexacao e busca semantica em acervos bibliograficos;
- bootstrap e regras autoritativas para configurar o ambiente.

## Servidores

- `local-llm`: geracao local de texto e embeddings via Ollama
- `scopus-search`: indexacao e busca semantica em exportacoes do Scopus

## Estrutura

- `server_llm.py`: servidor MCP para geracao e embeddings locais
- `server_scopus.py`: servidor MCP para indexacao e busca em CSVs do Scopus
- `bootstrap.md`: ponto de entrada publico para configurar Claude e Codex a partir de uma unica URL
- `AGENTS.minimal.md`: stub minimo para `~/.codex/AGENTS.md`
- `CLAUDE.minimal.md`: stub minimo para `~/.claude/CLAUDE.md`
- `ai-rules/codex/AGENTS.authoritative.md`: regras autoritativas globais do Codex
- `ai-rules/claude/CLAUDE.authoritative.md`: regras autoritativas globais do Claude

## Bootstrap recomendado

Para configurar Codex ou Claude em uma maquina nova, entregue ao agente a URL:

```text
https://github.com/im-alexandre/meus_mcps/blob/main/bootstrap.md
```

O `bootstrap.md` e o procedimento canonico. Ele cobre:

- descoberta do `REPO_ROOT`
- atualizacao de `~/.codex/AGENTS.md`
- atualizacao de `~/.codex/config.toml` para MCPs globais sem `autodev-codebase`
- atualizacao de `~/.claude/CLAUDE.md`
- atualizacao de `~/.claude/settings.json`
- atualizacao de `~/.claude/.mcp.json` ou `~/.claude/mcp.json`, quando aplicavel
- orientacao para configuracao local por repositorio Git quando `autodev-codebase` for usado

## Templates de configuracao

Os templates usados pelo bootstrap sao:

- Codex:
  - `AGENTS.minimal.md`
  - `ai-rules/codex/codex_settings.toml`
- Claude:
  - `CLAUDE.minimal.md`
  - `ai-rules/claude/claude_settings.json`
  - `ai-rules/claude/mcp.json`

Esses arquivos devem ser copiados ou mesclados manualmente pelo agente no ambiente local, substituindo os placeholders pelo estado real da maquina.

## Servicos de suporte

Alguns servicos precisam estar em execucao antes de iniciar os MCPs. Rode-os em segundo plano para nao bloquear o terminal.

### Ollama

Necessario para `local-llm` e `scopus-search`.

**Bash:**

```bash
ollama serve > /dev/null 2>&1 &
```

**PowerShell:**

```powershell
Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
```

### autodev-codebase

Servidor MCP para busca semantica e outline estrutural do codigo-fonte do projeto. Repositorio: https://github.com/anrgct/autodev-codebase

Instale as dependencias uma vez:

```bash
npm install
npm run build
```

A configuracao recomendada e local por repositorio Git:

- Codex: `$repoRoot/.codex/config.toml`
- Claude MCP: `$repoRoot/.mcp.json`
- Claude hooks: `$repoRoot/.claude/settings.json`

## Observacoes

- O diretorio `pdf-indexer-mcp/` esta ignorado no Git para evitar versionar um projeto maior e independente junto com estes servidores.
- O `scopus-search` usa `ChromaDB` e `Ollama`.
