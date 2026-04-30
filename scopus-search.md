# scopus-search

Use para trabalho bibliografico em exportacoes Scopus.

- `collection_stats`: validar cobertura e estado do indice.
- `index_csv`: indexar nova exportacao.
- `search`: busca semantica por tema, autor, metodo ou lacuna.

Fluxo preferencial:

1. cheque `collection_stats`
2. rode `index_csv` quando houver nova base — passe o CSV original completo, o servidor ja faz chunking interno
3. use `search` para recuperar artigos relevantes

## index_csv — comportamento interno

O servidor (`server_scopus.py`) ja trata abstracts longos com chunking automatico:
- Textos ate 4000 chars sao indexados como um unico documento.
- Textos maiores sao divididos em chunks de 4000 chars com 200 de sobreposicao; cada chunk recebe ID `<doi>__chunkN`.
- `csv.field_size_limit` esta configurado para suportar campos grandes sem erro.

**Se `index_csv` falhar com erro de contexto/tamanho**, o problema esta no codigo do servidor — leia `server_scopus.py` e corrija la. Nao fatie o CSV manualmente nem chame a ferramenta multiplas vezes.
