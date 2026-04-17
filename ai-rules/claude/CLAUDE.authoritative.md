# Claude Code - Regras Autoritativas

Fonte unica de verdade para o Claude Code neste ambiente. Regras de projeto especifico sobrescrevem estas quando houver conflito.

## Contexto global

Este arquivo contem apenas regras invariantes entre projetos. Regras especificas de contexto ficam em arquivos separados e sao carregadas sob demanda - nunca no bootstrap.

Quando `AUTHORITATIVE_RULES_ROOT` ainda nao existir no ambiente local, use o bootstrap publico em `https://github.com/im-alexandre/meus_mcps/blob/main/bootstrap.md` como procedimento de configuracao global.

## Preferencias de apresentacao

Para respostas em terminal, especialmente no PowerShell/Windows Terminal deste usuario:

1. ao apresentar tabelas, prefira tabelas Unicode com box-drawing, e nao tabelas Markdown cruas
2. se a tabela ficar larga demais, quebre em multiplas tabelas menores ou use formato vertical alinhado
3. para formulas, expressoes e simbolos matematicos, prefira Unicode legivel em terminal quando o layout permanecer estavel, por exemplo `∫`, `∞`, `√`, `π`, `Σ`, `→`, `−`, `²`
4. emoji estao autorizados quando melhorarem legibilidade, sinalizacao visual ou escaneabilidade no terminal
5. use ASCII linear apenas como fallback quando houver risco real de quebra de alinhamento, incompatibilidade de fonte ou pedido explicito do usuario

## Commits

Nunca incluir linha `Co-Authored-By` em mensagens de commit.

## Ordem de ferramentas de busca

Para exploracao de codigo:

1. Se o repositório Git tiver um MCP de codigo configurado localmente, use-o primeiro.
2. Se nao houver MCP de codigo local no projeto, use `Grep`, `Glob` e `Read` normalmente.
3. Prefira `Read` para arquivos cujo caminho ja seja conhecido.
4. Recorra a `Grep` e `Glob` para descobrir estrutura e referencias quando isso for mais direto do que leitura manual.

## Configuracao local por repositorio Git

`autodev-codebase` nao deve ficar no `~/.claude/.mcp.json` ou `~/.claude/mcp.json` globais.

Quando o projeto atual for um repositório Git e usar `autodev-codebase`:

1. Configure o MCP em `$repoRoot/.mcp.json`.
2. Configure os bloqueios em `$repoRoot/.claude/settings.json` para forcar o uso de `autodev-codebase` antes de `Grep` e `Glob`.

## DOCX

Qualquer tarefa que leia, revise, valide, comente, cite, formate, renumere ou edite arquivo `.docx` deve ler `AUTHORITATIVE_RULES_ROOT/mcp/docx-manager.md` antes de prosseguir, mesmo que o MCP `docx-manager` ainda nao tenha sido chamado no task.

Se o `docx-manager` nao cobrir o caso, use `python-docx` como fallback. Se `python-docx` nao estiver disponivel, instale-o antes de continuar.

Ao trabalhar com `.docx`, nao leia o documento inteiro apenas para localizar um trecho. Prefira comentarios, validacoes e buscas dirigidas; se faltar busca no MCP, ajuste o `docx-manager` ou use um fallback local que retorne apenas o recorte necessario.

## Refatoracao e extracao de codigo

Ao mover ou extrair simbolos (funcoes, classes, constantes) para outros modulos, execute obrigatoriamente uma etapa de verificacao pos-extracao: para cada simbolo declarado como "movido", confirme que nao existe mais definicao no arquivo original. Sem essa verificacao, o arquivo fonte pode reter a definicao original enquanto o novo modulo tambem a define, causando shadowing silencioso ou residuos que quebram a refatoracao.

## Regras sob demanda

Carregue os arquivos abaixo somente quando o task exigir - nao antecipadamente:

| Condicao | Arquivo a carregar |
|---|---|
| Handoff formal (planejamento -> execucao -> revisao) | `AUTHORITATIVE_RULES_ROOT/shared/handoff.md` |
| Delegacao ou uso de subagentes | `AUTHORITATIVE_RULES_ROOT/shared/task-delegation-policy.md` |
| Primeiro uso de qualquer MCP no task | `AUTHORITATIVE_RULES_ROOT/shared/mcp-policy.md` |
| Primeiro uso de um MCP especifico | `AUTHORITATIVE_RULES_ROOT/mcp/<nome>.md` |
| Alteracao global de `AGENTS.md` ou `CLAUDE.md` | `AUTHORITATIVE_RULES_ROOT/shared/global-config-update-policy.md` |
