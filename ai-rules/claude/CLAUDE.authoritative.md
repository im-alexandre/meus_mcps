# Claude Global Rules

Estas regras sao a fonte autoritativa para o Claude. Trate `AGENTS.md` do projeto como instrucao valida e complementar. Quando houver conflito, o arquivo mais especifico do projeto prevalece.

## Commits

Nunca incluir linha `Co-Authored-By` em mensagens de commit.

## Handoff

Leia `AUTHORITATIVE_RULES_ROOT/shared/handoff.md` e siga esse protocolo para artefatos de planejamento, execucao e revisao entre Codex e Claude.

## Planejamento e delegacao

Leia `AUTHORITATIVE_RULES_ROOT/shared/task-delegation-policy.md`.

## Atualizacao global sincronizada

Quando o usuario pedir para atualizar `AGENTS.md` ou `CLAUDE.md` global:

1. atualize `~/.codex/AGENTS.md`
2. atualize `~/.claude/CLAUDE.md`
3. atualize `AGENTS.minimal.md` e `CLAUDE.minimal.md` no repo clonado
4. atualize os arquivos afetados em `AUTHORITATIVE_RULES_ROOT`
5. execute `git add`, `git commit` e `git push` no repo clonado
6. se o primeiro `git push` falhar por permissao, instrua o usuario a configurar acesso de escrita e autenticacao GitHub

Leia tambem `AUTHORITATIVE_RULES_ROOT/shared/global-config-update-policy.md`.

## Exploracao do repositorio

Leia `AUTHORITATIVE_RULES_ROOT/shared/mcp-policy.md`.

Prioridade de MCPs:

- `autodev-codebase`: obrigatorio como primeiro passo em exploracao de codigo
- `local-llm`: auxiliar local para geracao leve e embeddings
- `scopus-search`: bibliografia semantica em CSV Scopus
- `docx-manager`: leitura e edicao dirigida de DOCX
- `pdf-indexer`: instalacao e uso via repositorio oficial

Antes do primeiro uso de um MCP neste task, leia o arquivo correspondente em `AUTHORITATIVE_RULES_ROOT/mcp/`.

Ao manipular qualquer arquivo `.docx`, leia sempre `AUTHORITATIVE_RULES_ROOT/mcp/docx-manager.md` antes de prosseguir, mesmo que o MCP `docx-manager` ainda nao tenha sido chamado neste task.
