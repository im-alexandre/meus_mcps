# Politica Geral de MCPs

- Use MCP especializado antes de shell, busca textual bruta ou leitura direta, quando houver MCP adequado.
- Para exploracao de codigo, priorize `autodev-codebase`.
- Para regras operacionais detalhadas, leia o arquivo em `ai-rules/mcp/<nome>.md` antes do primeiro uso do MCP no task atual.
- Se o estado real divergir do indice do MCP de codigo, reindexe antes de continuar.
- `codex_settings.toml` registra a configuracao de MCPs customizados do Codex. `claude_settings.json` registra MCPs customizados do Claude e tambem hooks e permissoes — serve de fonte de verdade para o que deve estar em `~/.claude/settings.json`.
- `autodev-codebase` e `pdf-indexer` devem ser instalados a partir dos respectivos repositorios oficiais e README.

## Falhas por limite de tamanho

Quando uma ferramenta MCP falhar com erro de limite de contexto/tamanho de input:

1. **Leia o codigo-fonte do MCP imediatamente** — identifique onde o limite e atingido.
2. **Corrija o codigo do MCP** para tratar o caso internamente (chunking, truncamento controlado, batching, etc.).
3. **Nunca contorne o limite fazendo multiplas chamadas externas** (ex: fatiar o CSV manualmente e chamar a ferramenta 124 vezes). Isso desperdiça quota de API do usuario de forma catastrofica.
4. A regra e: consertar a ferramenta, nao abusar dela.
