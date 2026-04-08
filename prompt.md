# 📚 Workflow — Dissertação com RAG Local + MCP + Codex (versão corrigida)

## 🎯 Objetivo

Automatizar:

- sugestão de referências por parágrafo
- validação manual via comentários no Word
- inserção final de citações e referências

Stack:

- local-first
- controlado (sem alucinação)

---

# 🧠 Arquitetura geral

```text
DOCX → comentários "citar"
     → Codex lê parágrafos marcados
     → busca candidatos (CSV → PDF → internet)
     → insere comentário com evidência
     → validação manual (OK)
     → inserção automática de citação + referência
```

---

# 🔧 1. Modelo local exposto via MCP

## Ferramentas

- Ollama
  [https://ollama.com](https://ollama.com)

- MCP Python SDK
  [https://github.com/modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk)

---

## Instalação

```bash
pip install mcp ollama
```

---

## Servidor MCP (exemplo)

```python
from mcp.server.fastmcp import FastMCP
import ollama

mcp = FastMCP("local-llm")

@mcp.tool()
def generate(prompt: str) -> str:
    return ollama.chat(
        model="qwen2.5-coder",
        messages=[{"role": "user", "content": prompt}]
    )["message"]["content"]

if __name__ == "__main__":
    mcp.run()
```

---

## Configuração no Codex

```toml
[mcp_servers.local]
command = "python"
args = ["server.py"]
```

---

# 📊 2. Indexação do CSV (Scopus)

## Ferramentas

- nomic-embed-text
- Chroma

---

## Pipeline

```text
scopus.csv
→ (title + abstract + keywords)
→ embedding local
→ Chroma
```

---

## Exemplo

```python
import ollama
import chromadb

client = chromadb.Client()
collection = client.create_collection("scopus")

def embed(text):
    return ollama.embeddings(
        model="nomic-embed-text",
        prompt=text
    )["embedding"]
```

---

# 📄 3. PDF Indexer via MCP

## Ferramenta

- pdf-indexer-mcp
  [https://github.com/lizTheDeveloper/pdf-indexer-mcp](https://github.com/lizTheDeveloper/pdf-indexer-mcp)

---

## Instalação

```bash
git clone https://github.com/lizTheDeveloper/pdf-indexer-mcp
cd pdf-indexer-mcp
pip install -r requirements.txt
```

---

## Correções aplicadas (Windows + Ollama)

O projeto original foi feito para macOS (Apple Silicon + MLX). Para funcionar no Windows com Ollama, foram necessárias as seguintes alterações:

### 1. Embedding generator reescrito

`embeddings/generator.py` — substituída a implementação MLX por Ollama + nomic-embed-text:

```python
import ollama

def generate_embeddings(self, texts):
    all_embeddings = []
    for text in texts:
        resp = ollama.embeddings(model="nomic-embed-text", prompt=text)
        all_embeddings.append(resp["embedding"])
    return np.array(all_embeddings, dtype=np.float32)
```

### 2. Relative imports corrigidos

5 arquivos usavam `from ..utils.logger import ...` (relative imports), mas o entry point `semantic_chunked_pdf_rag.py` adiciona o package root ao `sys.path` e usa absolute imports. Corrigidos para manter consistência:

- `embeddings/generator.py`
- `embeddings/faiss_index.py`
- `pdf_processing/extractor.py`
- `chunking/s2_chunking.py`
- `database/operations.py`

### 3. requirements.txt atualizado

Removidas dependências Apple-only (`mlx`, `mlx-embeddings`). Adicionado `ollama`:

```text
fastmcp==2.13.0.2
httpx==0.28.1
PyMuPDF>=1.26.0
faiss-cpu==1.12.0
numpy>=2.0.0
SQLAlchemy>=2.0.0
scikit-learn>=1.5.0
ollama>=0.4.0
sentence-transformers>=5.1.0
```

---

## Config Codex

```toml
[mcp_servers.pdf]
command = "python"
args = ["pdf-indexer-mcp/semantic_chunked_pdf_rag.py"]
```

---

# 🔄 4. Workflow de busca por parágrafo

## Entrada

Parágrafos com comentário:

```text
citar
```

---

## Ordem de busca

### 1️⃣ CSV (Chroma)

- busca semântica
- top_k = 3–5

---

### 2️⃣ PDF local (MCP)

- retorna:
  - trecho
  - página
  - seção

---

### 3️⃣ Internet (fallback MCP)

- busca papers
- baixa PDF
- reindexa automaticamente

---

# ✍️ 5. Inserção de comentários no DOCX

## Ferramenta

- python-docx
  [https://python-docx.readthedocs.io](https://python-docx.readthedocs.io)

---

## Exemplo de inserção

```python
from docx import Document

doc = Document("dissertacao.docx")

p = doc.paragraphs[0]

doc.add_comment(
    p.runs,
    text="""CANDIDATO:
Olivares et al. (2024)
Seção 3.2, p.8
Score: 0.91
Motivo: previsão hierárquica"""
)

doc.save("out.docx")
```

---

# 👨‍⚖️ 6. Validação manual

Você responde no comentário:

```text
OK
```

ou

```text
REJEITAR
```

---

# 🔁 7. Inserção final

## Se OK

Substituir no parágrafo:

```text
(OLIVARES et al., 2024)
```

---

## Atualizar referências

Adicionar ao final:

```text
OLIVARES, K. G. et al. Hierarchical Forecasting... 2024.
```

---

# 📌 8. Pipeline completo

```text
1. Abrir DOCX
2. Ler comentários
3. Filtrar comentários "citar"
4. Para cada parágrafo:
   → buscar CSV (Chroma)
   → buscar PDF (MCP)
   → fallback internet
   → inserir comentário com candidato
5. Usuário revisa (OK)
6. Reprocessar DOCX
7. Inserir citação final
8. Atualizar referências
```

---

# 🧠 Regras práticas

- threshold:
  - ≥ 0.85 → forte
  - 0.70–0.84 → revisar

- sempre incluir:
  - página
  - seção
  - trecho

---

# 🚀 Resultado final

- sugestões automáticas por parágrafo
- navegação direta no trecho do paper
- validação manual simples
- documento final limpo
- zero Zotero 😄
