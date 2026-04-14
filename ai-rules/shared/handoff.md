# Handoff Entre Codex e Claude

O handoff coberto aqui e entre etapas completas de `planejamento -> execucao -> revisao`.

- O handoff e baseado em artefatos explicitos, nao em um modelo chamar subagentes do outro.
- Planos devem ser decision-complete.
- Revisoes devem avaliar aderencia ao plano, aos testes e aos criterios de aceite.
- Nao deixe decisoes abertas quando elas forem necessarias para execucao ou revisao.

## Local canônico dos artefatos

- Se o diretorio atual estiver dentro de um repositorio Git, use `<repo_root>/.ai/handoff/`.
- Se o diretorio atual nao estiver dentro de um repositorio Git, use `~/.ai/shared/`.
- Para cada task com handoff formal, crie um subdiretorio `<YYYYMMDD-HHMMSS>-<slug>/`.
- Grave os artefatos como `plan.md`, `execution.md` e `review.md` dentro desse subdiretorio.
- Quando o handoff estiver dentro de um repositorio Git, trate esses artefatos como locais de trabalho e nao os versione por padrao.

Template minimo de `plan.md`:

- objetivo e resultado esperado
- escopo e fora de escopo
- premissas e decisoes travadas
- passos executaveis em ordem
- arquivos, interfaces ou artefatos afetados
- testes e criterios de aceite
- riscos, pendencias e pontos que exigem confirmacao humana

Template minimo de `review.md`:

- artefato revisado
- findings principais
- divergencias em relacao ao plano
- lacunas de teste ou validacao
- conclusao objetiva
