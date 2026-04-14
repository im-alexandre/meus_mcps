# Claude Code — Regras Autoritativas

Fonte unica de verdade para o Claude Code neste ambiente. Regras de projeto especifico sobrescrevem estas quando houver conflito.

## Contexto global

Este arquivo contem apenas regras invariantes entre projetos. Regras especificas de contexto ficam em arquivos separados e sao carregadas sob demanda — nunca no bootstrap.

Quando `AUTHORITATIVE_RULES_ROOT` ainda nao existir no ambiente local, use o bootstrap publico em `https://github.com/im-alexandre/meus_mcps/blob/main/bootstrap.md` como procedimento de configuracao global.

## Commits

Nunca incluir linha `Co-Authored-By` em mensagens de commit.

## Ordem de ferramentas de busca

O `settings.json` global aplica hooks `PreToolUse` que bloqueiam `Grep` e `Glob` diretamente.

Ao receber esse bloqueio:

1. Use `mcp__autodev-codebase__search_codebase` para buscas semanticas de codigo.
2. Use `mcp__autodev-codebase__outline_codebase` para mapear estrutura de modulos e funcoes.
3. Use `Read` diretamente apenas para arquivos cujo caminho ja e conhecido.
4. Recorra a `Grep` / `Glob` somente quando houver divergencia confirmada entre o indice e o estado real — nesse caso, informe o usuario antes de prosseguir para que ele possa autorizar manualmente.

## DOCX

Qualquer tarefa que leia, revise, valide, comente, cite, formate, renumere ou edite arquivo `.docx` deve ler `AUTHORITATIVE_RULES_ROOT/mcp/docx-manager.md` antes de prosseguir, mesmo que o MCP `docx-manager` ainda nao tenha sido chamado no task.

Se o `docx-manager` nao cobrir o caso, use `python-docx` como fallback. Se `python-docx` nao estiver disponivel, instale-o antes de continuar.

## Regras sob demanda

Carregue os arquivos abaixo somente quando o task exigir — nao antecipadamente:

| Condicao | Arquivo a carregar |
|---|---|
| Handoff formal (planejamento → execucao → revisao) | `AUTHORITATIVE_RULES_ROOT/shared/handoff.md` |
| Delegacao ou uso de subagentes | `AUTHORITATIVE_RULES_ROOT/shared/task-delegation-policy.md` |
| Primeiro uso de qualquer MCP no task | `AUTHORITATIVE_RULES_ROOT/shared/mcp-policy.md` |
| Primeiro uso de um MCP especifico | `AUTHORITATIVE_RULES_ROOT/mcp/<nome>.md` |
| Alteracao global de `AGENTS.md` ou `CLAUDE.md` | `AUTHORITATIVE_RULES_ROOT/shared/global-config-update-policy.md` |
