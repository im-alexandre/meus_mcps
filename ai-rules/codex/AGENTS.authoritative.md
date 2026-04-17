# Codex Global Rules

Estas regras sao a fonte autoritativa para o Codex. Quando houver conflito, o arquivo mais especifico do projeto prevalece.

## Contexto global

Mantenha o contexto de inicializacao enxuto. Carregue apenas regras globais invariantes neste arquivo e leia regras complementares somente quando o task exigir.

Quando `AUTHORITATIVE_RULES_ROOT` ainda nao existir no ambiente local, use o bootstrap publico em `https://github.com/im-alexandre/meus_mcps/blob/main/bootstrap.md` como procedimento de configuracao global.

## Preferencias de apresentacao

Para respostas em terminal, especialmente no `codex-cli` em PowerShell/Windows Terminal:

1. ao apresentar tabelas para este usuario, prefira tabelas Unicode com box-drawing, e nao tabelas Markdown cruas
2. se a tabela ficar larga demais, quebre em multiplas tabelas menores ou use formato vertical alinhado
3. para formulas, expressoes e simbolos matematicos, prefira Unicode legivel em terminal quando o layout permanecer estavel, por exemplo `∫`, `∞`, `√`, `π`, `Σ`, `→`, `−`, `²`
4. emoji estao autorizados quando melhorarem legibilidade, sinalizacao visual ou escaneabilidade no terminal
5. use ASCII linear apenas como fallback quando houver risco real de quebra de alinhamento, incompatibilidade de fonte ou pedido explicito do usuario

## Commits

Nunca incluir linha `Co-Authored-By` em mensagens de commit.

## Ordem de ferramentas de busca

Para exploracao de codigo e estrutura de projeto:

1. Se o repositório Git tiver um MCP de codigo configurado localmente, use-o primeiro.
2. Se nao houver MCP de codigo local no projeto, use as ferramentas nativas de shell e leitura direta com parcimonia.
3. Leia arquivos diretamente apenas quando o caminho ja estiver conhecido por contexto explicito do usuario, pela estrutura do repositorio ou por descoberta previa.
4. Leia diretorios diretamente apenas quando isso for a forma mais curta e objetiva de confirmar o estado real do workspace.

## Configuracao local por repositorio Git

`autodev-codebase` nao deve ficar no `~/.codex/config.toml` global.

Quando o projeto atual for um repositório Git e usar `autodev-codebase`, configure-o em `$repoRoot/.codex/config.toml`.

## DOCX

Qualquer tarefa que leia, revise, valide, comente, cite, formate, renumere ou edite arquivo `.docx` deve ler `AUTHORITATIVE_RULES_ROOT/mcp/docx-manager.md` antes de prosseguir, mesmo que o MCP `docx-manager` ainda nao tenha sido chamado neste task.

Se o `docx-manager` nao cobrir o caso, use `python-docx` como fallback. Se `python-docx` nao estiver disponivel, instale-o antes de continuar.

Ao trabalhar com `.docx`, nao leia o documento inteiro apenas para localizar um trecho. Prefira comentarios, validacoes e buscas dirigidas; se faltar busca no MCP, ajuste o `docx-manager` ou use um fallback local que retorne apenas o recorte necessario.

## Refatoracao e extracao de codigo

Ao mover ou extrair simbolos (funcoes, classes, constantes) para outros modulos, execute obrigatoriamente uma etapa de verificacao pos-extracao: para cada simbolo declarado como "movido", confirme que nao existe mais definicao no arquivo original. Sem essa verificacao, o arquivo fonte pode reter a definicao original enquanto o novo modulo tambem a define, causando shadowing silencioso ou residuos que quebram a refatoracao.

## Regras sob demanda

- Se houver handoff formal de planejamento, execucao ou revisao, leia `AUTHORITATIVE_RULES_ROOT/shared/handoff.md`.
- Se o task usar delegacao ou subagentes, leia `AUTHORITATIVE_RULES_ROOT/shared/task-delegation-policy.md`.
- Antes do primeiro uso de qualquer MCP no task, leia `AUTHORITATIVE_RULES_ROOT/shared/mcp-policy.md`.
- Antes do primeiro uso de um MCP especifico, leia `AUTHORITATIVE_RULES_ROOT/mcp/<nome>.md`.
- Se o usuario pedir alteracao global de `AGENTS.md` ou `CLAUDE.md`, leia `AUTHORITATIVE_RULES_ROOT/shared/global-config-update-policy.md`.
