# scopus-search

Use para trabalho bibliografico em exportacoes Scopus.

- `collection_stats`: validar cobertura e estado do indice.
- `index_csv`: indexar nova exportacao.
- `search`: busca semantica por tema, autor, metodo ou lacuna.
- `list_collections`: listar collections disponiveis quando a collection ainda nao estiver clara.

Fluxo preferencial:

1. se a collection nao estiver informada, rode `list_collections` e pergunte ao usuario qual collection usar; para indexacao, ofereca tambem a opcao de criar uma nova collection
2. cheque `collection_stats(collection="...")`
3. rode `index_csv(collection="...", csv_path="...")` quando houver nova base — passe o CSV original completo, o servidor ja faz chunking interno
4. use `search(collection="...", query="...")` para recuperar artigos relevantes

As ferramentas de indexacao e busca exigem `collection` explicitamente. Nao existe collection padrao nem variavel de ambiente para escolher collection automaticamente.

## index_csv — comportamento interno

O servidor (`server_scopus.py`) ja trata abstracts longos com chunking automatico:
- Textos ate 4000 chars sao indexados como um unico documento.
- Textos maiores sao divididos em chunks de 4000 chars com 200 de sobreposicao; cada chunk recebe ID `<doi>__chunkN`.
- `csv.field_size_limit` esta configurado para suportar campos grandes sem erro.

**Se `index_csv` falhar com erro de contexto/tamanho**, o problema esta no codigo do servidor — leia `server_scopus.py` e corrija la. Nao fatie o CSV manualmente nem chame a ferramenta multiplas vezes.
