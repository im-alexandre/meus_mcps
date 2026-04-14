# Claude Global Bootstrap Stub

`BOOTSTRAP_STUB_V1`

`AUTHORITATIVE_RULES_ROOT = ~/.meus_mcps/ai-rules`

Este arquivo deve permanecer curto. Ele existe apenas para bootstrap e redirecionamento.

1. Leia imediatamente `AUTHORITATIVE_RULES_ROOT/claude/CLAUDE.authoritative.md`.
2. Se `AUTHORITATIVE_RULES_ROOT` nao existir, leia o `bootstrap.md` do repositorio publico `https://github.com/im-alexandre/meus_mcps` e execute a secao `Bootstrap de configuracoes`.
3. O bootstrap e feito via `setup.sh` na raiz do repositorio. Ele detecta o OS automaticamente (Windows/WSL/Linux), resolve `REPO_ROOT`, sobrescreve este arquivo com o path real e mescla hooks e MCPs em `~/.claude/settings.json`.
