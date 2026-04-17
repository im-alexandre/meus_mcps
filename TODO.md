#https://github.com/anrgct/autodev-codebase TODO — Capacidades pendentes no docx-manager

Specs derivadas das capacidades descritas no README e do estado atual de `server_docx.py`.

---

## 1. Executar instruções arbitrárias de comentários

**Status**
Implementado.

**Estado atual**

- `list_comments(doc_path)` lista todos os comentários em árvore, com `replies`, `paragraph_index` e `paragraph_text` quando o vínculo com o documento pode ser resolvido.
- Reações 👍 são tratadas como `resolved=True` na leitura dos comentários.
- `reply_comment(doc_path, comment_id, reply_text, output_path="")` insere respostas em thread OOXML.

---

## 2. Inserir texto gerado no documento e marcá-lo com comentário

**Contexto**
O fluxo descreve: geração ou edição de texto diretamente no documento, seguida de um comentário marcando o trecho gerado com justificativa. Hoje `insert_citation` apenas appenda um run ao final do parágrafo e não deixa nenhuma marcação de autoria.

**Spec**

Criar tool `replace_paragraph_text(doc_path: str, output_path: str, paragraph_index: int, new_text: str, comment: str) -> str`:
- Substitui o conteúdo textual do parágrafo `paragraph_index` por `new_text`, preservando o estilo do primeiro run existente (fonte, tamanho, negrito via `_set_run_font`)
- Usa `_replace_in_word_text_nodes` como ponto de partida, mas deve suportar substituição completa (não apenas transformação)
- Após a substituição, insere um comentário `comment` no parágrafo via `doc.add_comment` (mesmo padrão de `insert_candidate_comment`), author `"docx-manager"`
- Salva em `output_path`
- Retorna string de confirmação com `paragraph_index` e `output_path`

---

## 3. Detectar validação "OK" e finalizar alteração pendente

**Contexto**
O fluxo define que o pesquisador valida respondendo o comentário com `"OK"`. Hoje não existe nenhuma tool que leia respostas de comentários (threads) nem que aja sobre elas.

**Spec**

Criar tool `find_approved_comments(doc_path: str) -> list[dict]`:
- Lê `word/comments.xml` via ZipFile (padrão de `_get_comments`)
- Verifica também `word/commentsExtended.xml` (se existir) para localizar respostas em thread
- Considera "aprovado" qualquer comentário cuja resposta contenha `"ok"` (case-insensitive, strip)
- Retorna lista com `comment_id`, `original_text`, `paragraph_index`, `reply_text`

> **Nota de investigação necessária:** o formato de threads de comentários no OOXML usa `<w15:commentEx>` com `paraIdParent`. Verificar se `python-docx` expõe isso ou se é necessário acesso direto ao XML via ZipFile/lxml.

---

## 4. Salvar in-place (output_path opcional)

**Contexto**
Todas as tools que escrevem no documento (`insert_candidate_comment`, `insert_citation`, `apply_table_style`, `set_table_caption`, `validate_tables_with_comments`, `renumber_equations`) exigem `output_path` obrigatório. O comportamento esperado é salvar no mesmo arquivo por padrão.

**Spec**

Para cada tool de escrita acima:
- Tornar `output_path` opcional (default `""`)
- Se `output_path` for vazio ou igual a `doc_path`, salvar in-place: `doc.save(doc_path)`
- Se `output_path` for diferente, comportamento atual (salva em caminho novo)
- Ajustar docstring de cada tool para refletir o novo default

---

## 5. Renumerar tabelas

**Contexto**
O README menciona que o `docx-manager` renumera tabelas e equações. `renumber_equations` já existe. Não há equivalente para tabelas.

**Spec**

Criar tool `renumber_tables(doc_path: str, output_path: str, start_number: int = 1) -> dict`:
- Percorre `doc.tables` em ordem de aparição
- Para cada tabela, localiza a legenda via `_get_table_caption_paragraph`
- Se a legenda bater com `TABLE_CAPTION_RE`, substitui o número (`Tabela N`) pelo novo número sequencial a partir de `start_number`
- Usa `_replace_in_word_text_nodes` para atualizar o texto da legenda
- Atualiza também referências textuais do tipo `"Tabela N"` nos parágrafos do documento (novo regex análogo a `SINGLE_EQ_REF_RE`)
- Valida antes e depois com `_table_report`
- Retorna `ok`, `mapping`, `validation_before`, `validation_after`, `output_path`

---

## 6. Inserir citação no formato ABNT

**Contexto**
O README especifica inserção de citação inline e referência ao final em formato ABNT. A tool `insert_citation` atual apenas concatena as strings fornecidas sem nenhuma validação ou formatação de padrão ABNT.

**Spec**

Atualizar `insert_citation` (ou criar `insert_abnt_citation`) para:
- Validar que `citation` segue o padrão ABNT de citação no texto: `(SOBRENOME, ano)` ou `(SOBRENOME et al., ano)` — regex de validação
- Validar que `reference` segue estrutura mínima ABNT para referência bibliográfica (SOBRENOME, Nome. *Título*. ...)
- Se inválido, retornar erro descritivo sem modificar o documento
- Inserir a referência no final sem duplicar: verificar se já existe linha idêntica antes de adicionar
- Manter assinatura compatível com a tool atual (`doc_path`, `output_path`, `paragraph_index`, `citation`, `reference`)
