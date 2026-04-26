"""MCP Server — geração via Codex e embeddings locais via Ollama."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import ollama
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("local-llm")

DEFAULT_CODEX_MODEL = os.environ.get("CODEX_MODEL", "gpt-5.4")
CODEX_SANDBOX = os.environ.get("CODEX_SANDBOX", "read-only")
CODEX_TIMEOUT_SEC = int(os.environ.get("CODEX_TIMEOUT_SEC", "120"))
CODEX_WORKDIR = Path(
    os.environ.get("CODEX_WORKDIR", Path(tempfile.gettempdir()) / "codex-mcp")
)

_cpu = ollama.Client(host="http://localhost:11435")  # CPU — embeddings


def _resolve_codex_bin() -> str:
    configured = os.environ.get("CODEX_BIN")
    if configured:
        return configured

    found = shutil.which("codex")
    if found:
        return found

    if sys.platform == "win32":
        fallback = Path.home() / "AppData" / "Roaming" / "npm" / "codex.cmd"
        if fallback.exists():
            return str(fallback)

    return "codex"


def _run_codex(prompt: str, model: str) -> str:
    if not prompt.strip():
        return ""

    CODEX_WORKDIR.mkdir(parents=True, exist_ok=True)
    codex_bin = _resolve_codex_bin()

    fd, output_name = tempfile.mkstemp(
        prefix="codex-mcp-",
        suffix=".txt",
        dir=CODEX_WORKDIR,
    )
    os.close(fd)
    output_path = Path(output_name)

    cmd = [
        codex_bin,
        "exec",
        "--ephemeral",
        "--ignore-user-config",
        "--sandbox",
        CODEX_SANDBOX,
        "--skip-git-repo-check",
        "-C",
        str(CODEX_WORKDIR),
        "-m",
        model,
        "-o",
        str(output_path),
        prompt,
    ]

    try:
        completed = subprocess.run(
            cmd,
            capture_output=True,
            check=False,
            stdin=subprocess.DEVNULL,
            text=True,
            timeout=CODEX_TIMEOUT_SEC,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(f"Comando nao encontrado: {codex_bin}") from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"Timeout ao executar {codex_bin} ({CODEX_TIMEOUT_SEC}s).") from exc

    try:
        content = output_path.read_text(encoding="utf-8").strip()
    finally:
        output_path.unlink(missing_ok=True)

    if completed.returncode != 0:
        details = completed.stderr.strip() or completed.stdout.strip() or "sem detalhes"
        raise RuntimeError(f"{codex_bin} exec falhou: {details}")

    if not content:
        details = completed.stderr.strip() or completed.stdout.strip() or "resposta vazia"
        raise RuntimeError(f"{codex_bin} exec nao retornou conteudo: {details}")

    return content


@mcp.tool()
def generate(prompt: str, model: str = DEFAULT_CODEX_MODEL) -> str:
    """Gera texto usando o Codex autenticado no terminal."""
    return _run_codex(prompt=prompt, model=model)


@mcp.tool()
def embed(text: str) -> list[float]:
    """Gera embedding local via Ollama; Codex nao expõe embeddings."""
    return _cpu.embeddings(
        model="embeddinggemma",
        prompt=text,
    )["embedding"]


if __name__ == "__main__":
    mcp.run()
