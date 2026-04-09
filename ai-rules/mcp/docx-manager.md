# docx-manager

Use para leitura e edicao dirigida de arquivos `.docx`.

- Antes de editar, localize o trecho com `list_paragraphs` ou liste comentarios existentes.
- Use `find_citar_paragraphs` para pendencias bibliograficas.
- Use `insert_candidate_comment` para sugestoes de citacao ainda nao validadas.
- Use `insert_citation` apenas quando a referencia ja estiver validada.
- Ao chamar `insert_candidate_comment` ou `insert_citation`, sempre passe `author` com o nome do agente chamador (`"claude"`, `"codex"`, etc.).
- Para equacoes e tabelas, prefira validar antes de corrigir.

Fluxos comuns:

- comentarios e citacoes: `list_comments` -> `find_citar_paragraphs` -> `insert_candidate_comment` ou `insert_citation`
- equacoes: `list_equations` -> `validate_equation_references` -> `renumber_equations` se necessario
- tabelas: `report_tables_format` ou `validate_tables_format` -> `apply_table_style` ou `set_table_caption`
