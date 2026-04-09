# Politica de atualizacao da configuracao global

Quando o usuario pedir para alterar a configuracao global:

1. mantenha `~/.codex/AGENTS.md` e `~/.claude/CLAUDE.md` o mais concisos possivel
2. se a mudanca pedida for pequena, ajuste diretamente o arquivo global minimo correspondente
3. se a mudanca pedida for grande, atualize `AGENTS.authoritative.md` ou `CLAUDE.authoritative.md`
4. se a mudanca ainda ficar longa demais para o arquivo autoritativo, crie um arquivo separado em `AUTHORITATIVE_RULES_ROOT` e adicione uma referencia explicita no autoritativo correspondente
5. nunca mova conteudo extenso para os arquivos globais minimos apenas por conveniencia
