# meus_mcps

Coleção de servidores MCP locais voltada a pesquisadores que precisam combinar programação e escrita acadêmica no mesmo fluxo de trabalho. O projeto nasceu para apoiar uma pesquisa quantitativa que usava notebooks Python — havia uma lacuna entre o código que gerava os resultados e o texto científico que precisava descrevê-los, interpretá-los e citá-los corretamente. Estes servidores preenchem essa lacuna: permitem que um assistente de IA leia, edite e organize documentos Word, busque referências bibliográficas, interprete código e gere texto diretamente no contexto da pesquisa, sem sair do ambiente de escrita.

O conjunto está amplamente testado com Python e há indícios de bom funcionamento com a linguagem R — o fluxo não depende da linguagem de análise, mas sim da capacidade de conectar os resultados computacionais ao documento acadêmico.

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
- validação pelo pesquisador no próprio documento
- inserção final de citações e referências em formato ABNT

### Fluxo consolidado

```text
DOCX -> comentários com instruções em linguagem natural
     -> leitura do trecho e execução do comando indicado
     -> geração ou edição de texto diretamente no documento
     -> comentário marcando o trecho gerado, com justificativa
     -> pesquisador valida respondendo o comentário com "OK"
     -> busca por candidatos em Scopus local, PDFs indexados e internet
     -> inserção final de citação (inline) e referência (ABNT) no documento
```

O ponto central do fluxo é o comentário no Word: qualquer instrução deixada pelo pesquisador — não só "citar", mas também "reescrever", "resumir", "traduzir" — é lida, executada e devolvida como novo comentário para revisão. A validação humana é explícita: o pesquisador lê o resultado e responde com "OK" para confirmar.

### Arquitetura prática

- `local-llm` apoia geração local de texto e embeddings via Ollama (os embeddings são representações numéricas do significado dos textos, usadas para encontrar conteúdo por similaridade semântica)
- `scopus-search` cobre indexação e busca semântica em CSVs exportados do Scopus
- `docx-manager` lê e edita `.docx` — insere e formata texto, tabelas, equações e citações, valida referências cruzadas, renumera elementos e aplica estilos
- `pdf-indexer` complementa com ingestão e busca semântica em PDFs técnicos

### Decisões de implementação

O maior ganho deste fluxo está na junção de dois mundos: o comportamento **não-determinístico** da IA generativa — que interpreta instruções em linguagem natural, adapta o texto ao contexto e sugere conteúdo — com o comportamento **determinístico** das ferramentas programáticas — que inserem citações no formato correto, renumeram equações, validam referências e calculam similaridade via embeddings. Cada um faz o que faz melhor, e o pesquisador decide o que fica.

Outras escolhas que sustentam esse equilíbrio:

- priorizar ferramentas locais, com pouca dependência de serviços externos
- manter busca semântica separada da decisão bibliográfica final
- usar comentários no Word como canal de instrução e validação humana

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
    "local-llm": { "command": "python", "args": ["D:/mcp/server_llm.py"] },
    "scopus-search": {
      "command": "python",
      "args": ["D:/mcp/server_scopus.py"]
    },
    "docx-manager": { "command": "python", "args": ["D:/mcp/server_docx.py"] }
  }
}
```

Se quiser usar também o `pdf-indexer`, acrescente:

```json
{
  "mcpServers": {
    "pdf-indexer": {
      "command": "python",
      "args": ["D:/mcp/pdf-indexer-mcp/semantic_chunked_pdf_rag.py"]
    }
  }
}
```

## Serviços de suporte

Alguns serviços precisam estar em execução antes de iniciar os MCPs. Rode-os em segundo plano (detached) para não bloquear o terminal.

### Ollama

Necessário para `local-llm` e `scopus-search`. Expõe os modelos locais via API REST.

**Bash:**
```bash
ollama serve > /dev/null 2>&1 &
```

**PowerShell:**
```powershell
Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
```

### autodev-codebase

Servidor MCP para busca semântica e outline estrutural do código-fonte do projeto. Repositório: https://github.com/anrgct/autodev-codebase

Instale as dependências uma vez:

```bash
npm install
npm run build
```

Depois inicie em segundo plano:

**Bash:**
```bash
node /caminho/para/autodev-codebase/dist/index.js > /dev/null 2>&1 &
```

**PowerShell:**
```powershell
Start-Process -FilePath "node" -ArgumentList "C:\caminho\para\autodev-codebase\dist\index.js" -WindowStyle Hidden
```

Adicione o servidor ao seu cliente MCP apontando para o mesmo `dist/index.js`.

---

## Observações

- O diretório `pdf-indexer-mcp/` está ignorado no Git para evitar versionar um projeto maior e independente junto com estes servidores.
- O `scopus-search` usa `ChromaDB` e `Ollama`.
- O `docx-manager` depende de `python-docx` e faz linearização de equações para validação textual.
