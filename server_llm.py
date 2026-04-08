"""MCP Server — LLM local via Ollama."""

from mcp.server.fastmcp import FastMCP
import ollama

mcp = FastMCP("local-llm")


@mcp.tool()
def generate(prompt: str, model: str = "qwen2.5-coder:3b") -> str:
    """Gera texto usando modelo local via Ollama."""
    return ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )["message"]["content"]


@mcp.tool()
def embed(text: str) -> list[float]:
    """Gera embedding usando nomic-embed-text."""
    return ollama.embeddings(
        model="nomic-embed-text",
        prompt=text,
    )["embedding"]


if __name__ == "__main__":
    mcp.run()

