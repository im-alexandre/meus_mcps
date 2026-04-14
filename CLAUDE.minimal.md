# Claude Global Bootstrap Stub

`BOOTSTRAP_STUB_V1`

`AUTHORITATIVE_RULES_ROOT = ~/.meus_mcps/ai-rules`

Este arquivo deve permanecer curto. Ele existe apenas para bootstrap e redirecionamento.

1. Leia imediatamente `AUTHORITATIVE_RULES_ROOT/claude/CLAUDE.authoritative.md`.
2. Se `AUTHORITATIVE_RULES_ROOT` nao existir, leia o `bootstrap.md` do repositorio publico `https://github.com/im-alexandre/meus_mcps` e execute a secao `Bootstrap de configuracoes`.
3. O bootstrap deve:
   - Sobrescrever `~/.claude/CLAUDE.md` com este arquivo `.minimal` e atualizar `AUTHORITATIVE_RULES_ROOT` para o path real do clone.
   - Copiar `ai-rules/claude/claude_settings.json` mesclando com `~/.claude/settings.json` (preservar chaves existentes, adicionar `hooks` e `mcpServers`).
   - Preparar `~/.codex/AGENTS.md` com o `.minimal` correspondente.
