# meus_mcps

Colecao de servidores MCP locais voltada a fluxos de pesquisa assistida, com foco atual em:

- geracao local de texto e embeddings;
- indexacao e busca semantica em acervos bibliograficos;
- bootstrap e regras autoritativas para configurar o ambiente.

## Servidores

- `local-llm`: geracao local de texto e embeddings via Ollama
- `scopus-search`: indexacao e busca semantica em exportacoes do Scopus nos formatos CSV e RIS

## Estrutura

- `server_llm.py`: servidor MCP para geracao e embeddings locais
- `server_scopus.py`: servidor MCP para indexacao e busca em CSVs e RIS do Scopus
- `bootstrap.md`: ponto de entrada publico para configurar Claude e Codex a partir de uma unica URL
- `AGENTS.minimal.md`: stub minimo para `~/.codex/AGENTS.md`
- `CLAUDE.minimal.md`: stub minimo para `~/.claude/CLAUDE.md`
- `ai-rules/codex/AGENTS.authoritative.md`: regras autoritativas globais do Codex
- `ai-rules/claude/CLAUDE.authoritative.md`: regras autoritativas globais do Claude

## Bootstrap recomendado

Para configurar Codex ou Claude em uma maquina nova, entregue ao agente a URL:

```text
https://github.com/im-alexandre/meus_mcps/blob/main/bootstrap.md
```

O `bootstrap.md` e o procedimento canonico. Ele cobre:

- descoberta do `REPO_ROOT`
- atualizacao de `~/.codex/AGENTS.md`
- atualizacao de `~/.codex/config.toml` para MCPs globais sem `autodev-codebase`
- atualizacao de `~/.claude/CLAUDE.md`
- atualizacao de `~/.claude/settings.json`
- atualizacao de `~/.claude/.mcp.json` ou `~/.claude/mcp.json`, quando aplicavel
- orientacao para configuracao local por repositorio Git quando `autodev-codebase` for usado

## Templates de configuracao

Os templates usados pelo bootstrap sao:

- Codex:
  - `AGENTS.minimal.md`
  - `ai-rules/codex/codex_settings.toml`
- Claude:
  - `CLAUDE.minimal.md`
  - `ai-rules/claude/claude_settings.json`
  - `ai-rules/claude/mcp.json`

Esses arquivos devem ser copiados ou mesclados manualmente pelo agente no ambiente local, substituindo os placeholders pelo estado real da maquina.

## Servicos de suporte

Alguns servicos precisam estar em execucao antes de iniciar os MCPs. Rode-os em segundo plano para nao bloquear o terminal.

### Ollama

Necessario para `local-llm` e `scopus-search`.

**Bash:**

```bash
ollama serve > /dev/null 2>&1 &
```

**PowerShell:**

```powershell
Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
```

### autodev-codebase

Servidor MCP para busca semantica e outline estrutural do codigo-fonte do projeto. Repositorio: https://github.com/anrgct/autodev-codebase

Instale as dependencias uma vez:

```bash
npm install
npm run build
```

A configuracao recomendada e local por repositorio Git:

- Codex: `$repoRoot/.codex/config.toml`
- Claude MCP: `$repoRoot/.mcp.json`
- Claude hooks: `$repoRoot/.claude/settings.json`

## MCP `scopus-search`

O servidor `server_scopus.py` cria um indice persistente no ChromaDB para busca semantica em acervos exportados do Scopus. Ele usa o Ollama para gerar embeddings.

### Pre-requisitos

Instale as dependencias Python:

```bash
pip install -r requirements.txt
```

Garanta que o Ollama esteja em execucao no host configurado e que o modelo de embedding esteja disponivel:

```bash
ollama pull embeddinggemma
```

Por padrao, o servidor chama o Ollama em `http://localhost:11434` e usa o modelo `embeddinggemma`. As ferramentas aceitam os parametros opcionais `host`, `port` e `model` quando for necessario sobrescrever esses valores em uma chamada especifica.

### Armazenamento

O indice e persistido no diretorio definido por `CHROMA_DIR`. Se a variavel nao estiver configurada, o padrao e `./chroma_data`.

A collection usada no ChromaDB vem de `CHROMA_COLLECTION`. Se a variavel estiver vazia ou ausente, o padrao e `scopus`.

O host do Ollama vem de `HOST`. Se a variavel estiver vazia ou ausente, o padrao e `http://localhost`.

A porta do Ollama vem de `PORT`. Se a variavel estiver vazia ou ausente, o padrao e `11434`.

O modelo de embedding vem de `MODEL`. Se a variavel estiver vazia ou ausente, o padrao e `embeddinggemma`.

Exemplo:

```powershell
$env:CHROMA_DIR="C:\Users\<usuario>\.codex\mcp\scopus\chroma"
$env:CHROMA_COLLECTION="scopus"
$env:HOST="http://localhost"
$env:PORT="11434"
$env:MODEL="embeddinggemma"
python D:\mcp\server_scopus.py
```

### Ferramentas

- `index_csv(csv_path, host="http://localhost", port=11434, model="embeddinggemma")`: indexa uma exportacao CSV do Scopus. Espera as colunas `Title`, `Abstract`, `Author Keywords`, `Authors`, `Year`, `Source title` e `DOI`.
- `index_ris(ris_path, host="http://localhost", port=11434, model="embeddinggemma")`: indexa um arquivo RIS. Usa campos como titulo, resumo, palavras-chave, autores, ano, periodico/fonte e DOI.
- `search(query, top_k=5, host="http://localhost", port=11434, model="embeddinggemma")`: busca no indice e retorna resultados com score, titulo, autores, ano, DOI, fonte e trecho.
- `collection_stats()`: retorna o nome da collection e a quantidade de itens indexados.

### Comportamento de indexacao

Cada registro precisa ter titulo para ser indexado. O identificador base e o DOI quando disponivel; caso contrario, o servidor usa um identificador baseado na linha. Textos longos sao divididos automaticamente em chunks com sobreposicao, entao nao e necessario fatiar manualmente abstracts extensos antes de chamar `index_csv` ou `index_ris`.

## Observacoes

- O diretorio `pdf-indexer-mcp/` esta ignorado no Git para evitar versionar um projeto maior e independente junto com estes servidores.
- O `scopus-search` usa `ChromaDB`, `Ollama` e `rispy`.
