# docx-manager

Use para leitura e edicao dirigida de arquivos `.docx`.

- Se o `docx-manager` nao possuir recursos para concluir a tarefa pedida, use `python-docx` no ambiente como fallback.
- Se `python-docx` nao estiver disponivel, instale-o no ambiente global antes de prosseguir.
- Antes de editar, prefira localizar o trecho com ferramentas dirigidas, como `list_comments`, `list_equations`, `validate_*` e consultas focadas equivalentes.
- Nunca use `list_paragraphs` para despejar o documento inteiro apenas para procurar um trecho, exceto em documentos muito pequenos ou quando o usuario pedir explicitamente.
- Se a localizacao textual ainda for necessaria e o MCP nao oferecer busca, altere o `docx-manager` para suportar busca/recorte ou use um fallback local estreito que retorne apenas a janela relevante.
- Use `list_comments` como ponto de entrada operacional para comentarios, instrucoes e pendencias bibliograficas.
- Use `insert_candidate_comment` para sugestoes de citacao ainda nao validadas.
- Use `insert_citation` apenas quando a referencia ja estiver validada.
- Ao chamar `insert_candidate_comment` ou `insert_citation`, sempre passe `author` com o nome do agente chamador (`"claude"`, `"codex"`, etc.).
- Para equacoes e tabelas, prefira validar antes de corrigir.
- Para legenda e fonte de tabelas/figuras, use `set_table_caption`, `set_figure_caption`, `set_table_source` e `set_figure_source`.
- Quando o usuario pedir para listar comentarios de um `.docx`, a resposta deve incluir:
  - comentarios de topo;
  - comentarios filhos/respostas encadeadas;
  - indicacao explicita se houve reacao/resposta ao comentario.
- Para esse fluxo operacional, trate `houve reacao` como `resolvido`, mesmo que o campo nativo `resolved` do documento permaneça `false`.

Fluxos comuns:

- comentarios e citacoes: `list_comments` -> `insert_candidate_comment` ou `insert_citation`
- equacoes: `list_equations` -> `validate_equation_references` -> `renumber_equations` se necessario
- tabelas e figuras: `report_tables_format` ou `validate_tables_format` -> `apply_table_style`, `set_table_caption`, `set_figure_caption`, `set_table_source` ou `set_figure_source`
