"""MCP Server — LLM local via Ollama."""

from mcp.server.fastmcp import FastMCP
import ollama

mcp = FastMCP("local-llm")

_gpu = ollama.Client(host="http://localhost:11434")  # GPU — geração LLM
_cpu = ollama.Client(host="http://localhost:11435")  # CPU — embeddings


@mcp.tool()
def generate(prompt: str, model: str = "qwen3:1.7b") -> str:
    """Gera texto usando modelo local via Ollama (GPU)."""
    return _gpu.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )["message"]["content"]


@mcp.tool()
def embed(text: str) -> list[float]:
    """Gera embedding usando nomic-embed-text (CPU)."""
    return _cpu.embeddings(
        model="embeddinggemma",
        prompt=text,
    )["embedding"]


if __name__ == "__main__":
    mcp.run()

