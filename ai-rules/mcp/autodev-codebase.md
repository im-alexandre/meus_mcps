# autodev-codebase

Use este MCP como primeiro passo para exploracao do repositorio quando disponivel no projeto.

## Ferramentas disponíveis

- `search_codebase` — busca semantica por vetor. Recebe uma pergunta em linguagem natural e retorna snippets relevantes com score de similaridade.
- `outline_codebase` — extrai estrutura de codigo (funcoes, classes, metodos) via Tree-sitter. Suporta `summarize: true` (resumos IA, cacheados) e `title: true` (so sumario do arquivo, sem listar definicoes).

## Estrategia de uso

### Para responder perguntas sobre o codigo

1. Comece sempre com `search_codebase` — 2 a 3 queries bem formuladas cobrem a maioria dos casos.
2. Use `outline_codebase` apenas nos arquivos especificos retornados pelo search, quando precisar entender a estrutura ao redor (ex: outras funcoes no mesmo arquivo).
3. **Nunca** faca `outline_codebase` com path generico (`"*"` ou `"**/*.py"`) como primeiro passo — isso desperdiça tokens sem ganho de qualidade.

### Para prover contexto em edicoes

1. `search_codebase` para localizar o codigo a editar e seus callers.
2. `outline_codebase(arquivo, summarize=true)` no arquivo especifico — gera resumos de todas as funcoes. Na primeira execucao usa LLM; nas seguintes e cache (>90% hit rate, custo ~zero).
3. `search_codebase` para encontrar dependencias e evitar regressoes.

### Tabela de decisao

| Situacao | Ferramenta |
|---|---|
| Pergunta de negocio / fluxo / comportamento | `search_codebase` (2-3 queries) |
| Localizar funcao ou simbolo especifico | `search_codebase` com query direta |
| Entender estrutura de arquivo antes de editar | `outline_codebase(arquivo, summarize=true)` |
| Visao geral rapida de um arquivo | `outline_codebase(arquivo, title=true)` |
| Encontrar callers / dependencias | `search_codebase("quem chama / usa X")` |
| Estrutura do projeto pela primeira vez | `outline_codebase("*")` — so neste caso |

## Parametros uteis do search_codebase

- `limit` — reduza para 5-10 quando a query for precisa; o padrao (20) traz mais ruido.
- `filters.pathFilters` — restrinja a busca a subdiretorios ou extensoes relevantes (ex: `["**/*.py"]`, `["mcda_hibrido/**"]`).
- `filters.minScore` — use 0.6+ para resultados de alta confianca; 0.4 para exploração mais ampla.

## Regras

- Prefira `search_codebase` como ponto de entrada — e mais eficiente em tokens e chamadas do que `outline` generico.
- Use `outline` com path especifico, nunca como mapa geral do projeto.
- `outline + summarize` faz sentido para edicoes (contexto estrutural do arquivo); para perguntas, o search ja e suficiente.
- Se os resultados do search forem ambiguos ou fragmentados, faca nova query mais especifica antes de recorrer ao outline.
- Recorra a `Grep`, `Glob` ou leitura direta apenas quando houver divergencia confirmada entre o indice e o estado real do repositorio. Se houver divergencia, reindexe antes de continuar.

## Instalacao

- Leia o README em `https://github.com/anrgct/autodev-codebase`
- Siga as instrucoes oficiais do repositorio
- Configure o MCP em `$repoRoot/.mcp.json` (nao no global `~/.claude/mcp.json`)
