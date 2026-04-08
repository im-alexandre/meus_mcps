# meus_mcps

Coleção de servidores MCP locais para uso em fluxos de pesquisa, escrita acadêmica e automação documental.

## Servidores

- `local-llm`: geração local de texto e embeddings via Ollama
- `scopus-search`: indexação e busca semântica em exportações do Scopus
- `docx-manager`: leitura e edição dirigida de arquivos `.docx`

## Estrutura

- `server_llm.py`: servidor MCP para geração e embeddings locais
- `server_scopus.py`: servidor MCP para indexação e busca em CSVs do Scopus
- `server_docx.py`: servidor MCP para leitura, comentários, citações e equações em `.docx`

## Contexto do Workflow

Estes MCPs nasceram de um fluxo local-first para escrita acadêmica assistida, com foco em controle humano e rastreabilidade das evidências. A ideia central é separar claramente:

- busca e recuperação de fontes
- validação manual no documento
- inserção final de citações e referências

Fluxo consolidado:

```text
DOCX -> comentários "citar"
     -> leitura dos parágrafos marcados
     -> busca por candidatos em Scopus local, PDFs indexados e internet
     -> comentário com evidência e justificativa
     -> validação manual
     -> inserção final de citação e referência
```

Arquitetura prática:

- `local-llm` apoia geração local e embeddings auxiliares via Ollama
- `scopus-search` cobre indexação e busca semântica em CSVs exportados do Scopus
- `docx-manager` faz leitura e edição dirigida de `.docx`, inclusive validação de referências textuais a equações
- `pdf-indexer` entra como servidor complementar para ingestão e busca semântica em PDFs técnicos

Decisões de implementação que vieram desse workflow:

- priorizar ferramentas locais, com pouca dependência de serviços externos
- manter busca semântica separada da decisão bibliográfica final
- usar comentários no Word como ponto de validação humana
- validar referências textuais sempre que houver manipulação de equações no `.docx`

## Instalação

Pré-requisitos:

- Python 3.11+
- Ollama instalado e em execução
- modelos locais necessários já baixados, especialmente `nomic-embed-text`

Instale as dependências:

```powershell
python -m pip install -r requirements.txt
```

### Codex

Adicione os servidores ao arquivo `~/.codex/config.toml`:

```toml
[mcp_servers.local-llm]
command = "python"
args = ["D:/mcp/server_llm.py"]

[mcp_servers.scopus-search]
command = "python"
args = ["D:/mcp/server_scopus.py"]

[mcp_servers.docx-manager]
command = "python"
args = ["D:/mcp/server_docx.py"]
```

Se quiser usar também o `pdf-indexer`, adicione:

```toml
[mcp_servers.pdf-indexer]
command = "python"
args = ["D:/mcp/pdf-indexer-mcp/semantic_chunked_pdf_rag.py"]
```

### Claude

Adicione os servidores ao arquivo `~/.claude/mcp.json`:

```json
{
  "mcpServers": {
    "local-llm":      { "command": "python", "args": ["D:/mcp/server_llm.py"] },
    "scopus-search":  { "command": "python", "args": ["D:/mcp/server_scopus.py"] },
    "docx-manager":   { "command": "python", "args": ["D:/mcp/server_docx.py"] }
  }
}
```

Se quiser usar também o `pdf-indexer`, acrescente:

```json
{
  "mcpServers": {
    "pdf-indexer": { "command": "python", "args": ["D:/mcp/pdf-indexer-mcp/semantic_chunked_pdf_rag.py"] }
  }
}
```

## Observações

- O diretório `pdf-indexer-mcp/` está ignorado no Git para evitar versionar um projeto maior e independente junto com estes servidores.
- O `scopus-search` usa `ChromaDB` e `Ollama`.
- O `docx-manager` depende de `python-docx` e faz linearização de equações para validação textual.
