# Politica de atualizacao da configuracao global

Quando o usuario pedir para alterar a configuracao global:

1. mantenha `~/.codex/AGENTS.md` e `~/.claude/CLAUDE.md` o mais concisos possivel
2. se a mudanca pedida for pequena, ajuste diretamente o arquivo global minimo correspondente
3. se a mudanca pedida for grande, atualize `AGENTS.authoritative.md` ou `CLAUDE.authoritative.md`
4. se a mudanca ainda ficar longa demais para o arquivo autoritativo, crie um arquivo separado em `AUTHORITATIVE_RULES_ROOT` e adicione uma referencia explicita no autoritativo correspondente
5. atualize `~/.codex/AGENTS.md`
6. atualize `~/.claude/CLAUDE.md`
7. atualize `AGENTS.minimal.md` e `CLAUDE.minimal.md` no repo clonado
8. atualize os arquivos afetados em `AUTHORITATIVE_RULES_ROOT`
9. se o bootstrap publico mudar, atualize tambem `bootstrap.md` para manter o fluxo por documentacao consistente
10. execute `git add`, `git commit` e `git push` no repo clonado
11. se o primeiro `git push` falhar por permissao, instrua o usuario a configurar acesso de escrita e autenticacao GitHub antes de tentar novamente

Nunca mova conteudo extenso para os arquivos globais minimos apenas por conveniencia.
