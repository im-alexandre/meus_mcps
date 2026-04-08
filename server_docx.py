"""MCP Server — Leitura e manipulacao de DOCX (comentarios, citacoes, referencias)."""

import re
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from lxml import etree
from mcp.server.fastmcp import FastMCP
import datetime

mcp = FastMCP("docx-manager")

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
MATHLIKE_RE = re.compile(r"[=+\-*/≤≥≠∀ΣΦϕΘρΔεηαβγμ∣\[\]{}()]|max|min|VaR|CVaR|MAE|MAPE|RMSE|MASE")
EQUATION_END_RE = re.compile(r"\((\d+)\)\s*$")
EQUATION_LABEL_RE = re.compile(r"^\s*\((\d+)\)\s*$")
SINGLE_EQ_REF_RE = re.compile(r"\b(?:Equação|eq\.)\s*\((\d+)\)", re.IGNORECASE)
RANGE_EQ_REF_RE = re.compile(r"\b(?:Equações|eqs\.)\s*\((\d+)\)\s*(?:a|até)\s*\((\d+)\)", re.IGNORECASE)
PAIR_EQ_REF_RE = re.compile(r"\b(?:Equações|eqs\.)\s*\((\d+)\)\s*e\s*\((\d+)\)", re.IGNORECASE)


# ── Helpers ──────────────────────────────────────────────────────────────────


def _get_comments(doc_path: str) -> list[dict]:
    """Extrai comentarios do DOCX via XML."""
    from zipfile import ZipFile
    import xml.etree.ElementTree as ET

    comments = []
    with ZipFile(doc_path, "r") as z:
        if "word/comments.xml" not in z.namelist():
            return comments
        tree = ET.parse(z.open("word/comments.xml"))
        ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        for c in tree.findall(".//w:comment", ns):
            text_parts = [t.text or "" for t in c.findall(".//w:t", ns)]
            comments.append({
                "id": c.get(f'{{{ns["w"]}}}id'),
                "author": c.get(f'{{{ns["w"]}}}author', ""),
                "text": "".join(text_parts).strip(),
            })
    return comments


def _get_paragraph_text(para) -> str:
    return "".join(run.text for run in para.runs if run.text)


def _get_paragraph_full_text(para) -> str:
    parts = []
    for node in para._element.iter():
        if isinstance(node.tag, str) and node.tag.endswith("}t") and node.text:
            parts.append(node.text)
    return "".join(parts)


def _word_text_nodes(para):
    return [node for node in para._element.iter() if getattr(node, "tag", None) == qn("w:t")]


def _replace_in_word_text_nodes(para, transform) -> bool:
    nodes = _word_text_nodes(para)
    if not nodes:
        return False

    original = "".join(node.text or "" for node in nodes)
    updated = transform(original)
    if updated == original:
        return False

    nodes[0].text = updated
    for node in nodes[1:]:
        node.text = ""
    return True


def _looks_like_equation_text(text: str) -> bool:
    if not text:
        return False
    return bool(MATHLIKE_RE.search(text))


def _extract_equations(doc: Document) -> list[dict]:
    equations = []
    for idx, para in enumerate(doc.paragraphs):
        full_text = _get_paragraph_full_text(para).strip()
        plain_text = _get_paragraph_text(para).strip()
        match = EQUATION_END_RE.search(full_text)
        if not match:
            continue

        eq_number = int(match.group(1))
        eq_text = EQUATION_END_RE.sub("", full_text).strip()
        if not eq_text or not (_looks_like_equation_text(eq_text) or EQUATION_LABEL_RE.fullmatch(plain_text)):
            continue

        equations.append({
            "equation_number": eq_number,
            "paragraph_index": idx,
            "equation_text": eq_text,
            "label_text": plain_text,
        })
    return equations


def _extract_equation_refs(text: str) -> list[dict]:
    refs = []

    for match in RANGE_EQ_REF_RE.finditer(text):
        start = int(match.group(1))
        end = int(match.group(2))
        refs.append({
            "kind": "range",
            "raw": match.group(0),
            "numbers": list(range(start, end + 1)) if start <= end else [],
            "start": start,
            "end": end,
        })

    for match in PAIR_EQ_REF_RE.finditer(text):
        refs.append({
            "kind": "pair",
            "raw": match.group(0),
            "numbers": [int(match.group(1)), int(match.group(2))],
        })

    for match in SINGLE_EQ_REF_RE.finditer(text):
        refs.append({
            "kind": "single",
            "raw": match.group(0),
            "numbers": [int(match.group(1))],
        })

    return refs


def _validate_equation_state(doc: Document) -> dict:
    equations = _extract_equations(doc)
    numbers = [item["equation_number"] for item in equations]
    unique_numbers = sorted(set(numbers))
    duplicates = sorted(n for n in unique_numbers if numbers.count(n) > 1)

    expected_sequence = []
    missing_numbers = []
    if unique_numbers:
        expected_sequence = list(range(min(unique_numbers), max(unique_numbers) + 1))
        missing_numbers = [n for n in expected_sequence if n not in unique_numbers]

    reference_items = []
    invalid_references = []
    invalid_ranges = []

    for idx, para in enumerate(doc.paragraphs):
        text = _get_paragraph_full_text(para)
        for ref in _extract_equation_refs(text):
            entry = {
                "paragraph_index": idx,
                "raw": ref["raw"],
                "kind": ref["kind"],
                "numbers": ref["numbers"],
            }
            reference_items.append(entry)

            if ref["kind"] == "range" and ref["start"] > ref["end"]:
                invalid_ranges.append(entry | {"start": ref["start"], "end": ref["end"]})

            for n in ref["numbers"]:
                if n not in unique_numbers:
                    invalid_references.append(entry | {"missing_equation_number": n})

    return {
        "equation_count": len(equations),
        "equations": equations,
        "numbers_in_order": numbers,
        "duplicates": duplicates,
        "missing_numbers_in_sequence": missing_numbers,
        "references": reference_items,
        "invalid_references": invalid_references,
        "invalid_ranges": invalid_ranges,
        "is_valid": not duplicates and not invalid_references and not invalid_ranges,
    }


def _renumber_reference_text(text: str, mapping: dict[int, int]) -> str:
    def replace_range(match):
        start = int(match.group(1))
        end = int(match.group(2))
        if start not in mapping or end not in mapping:
            return match.group(0)
        connector = "até" if "até" in match.group(0).lower() else "a"
        prefix = "eqs." if match.group(0).lower().startswith("eqs.") else "Equações"
        return f"{prefix} ({mapping[start]}) {connector} ({mapping[end]})"

    def replace_pair(match):
        left = int(match.group(1))
        right = int(match.group(2))
        if left not in mapping or right not in mapping:
            return match.group(0)
        prefix = "eqs." if match.group(0).lower().startswith("eqs.") else "Equações"
        return f"{prefix} ({mapping[left]}) e ({mapping[right]})"

    def replace_single(match):
        value = int(match.group(1))
        if value not in mapping:
            return match.group(0)
        prefix = "eq." if match.group(0).lower().startswith("eq.") else "Equação"
        return f"{prefix} ({mapping[value]})"

    updated = RANGE_EQ_REF_RE.sub(replace_range, text)
    updated = PAIR_EQ_REF_RE.sub(replace_pair, updated)
    updated = SINGLE_EQ_REF_RE.sub(replace_single, updated)
    return updated


# ── Tools ────────────────────────────────────────────────────────────────────


@mcp.tool()
def list_paragraphs(doc_path: str) -> list[dict]:
    """Lista paragrafos do DOCX com indice e texto."""
    doc = Document(doc_path)
    return [
        {"index": i, "text": _get_paragraph_text(p)[:200]}
        for i, p in enumerate(doc.paragraphs)
        if _get_paragraph_text(p).strip()
    ]


@mcp.tool()
def list_comments(doc_path: str) -> list[dict]:
    """Lista todos os comentarios do DOCX."""
    return _get_comments(doc_path)


@mcp.tool()
def list_equations(doc_path: str) -> list[dict]:
    """Lista as equacoes encontradas no DOCX com numero, paragrafo e texto linearizado."""
    doc = Document(doc_path)
    return _extract_equations(doc)


@mcp.tool()
def validate_equation_references(doc_path: str) -> dict:
    """Valida a numeracao das equacoes e as referencias textuais do documento."""
    doc = Document(doc_path)
    return _validate_equation_state(doc)


@mcp.tool()
def find_citar_paragraphs(doc_path: str) -> list[dict]:
    """Encontra paragrafos que possuem comentario 'citar'. Retorna indice + texto do paragrafo."""
    doc = Document(doc_path)
    comments = _get_comments(doc_path)
    citar_ids = {c["id"] for c in comments if c["text"].strip().lower() == "citar"}

    if not citar_ids:
        return [{"info": "Nenhum comentario 'citar' encontrado."}]

    # Mapear commentRangeStart no XML do documento
    body = doc.element.body
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    results = []

    for para_idx, para in enumerate(doc.paragraphs):
        para_xml = para._element
        starts = para_xml.findall(".//w:commentRangeStart", ns)
        for s in starts:
            cid = s.get(f'{{{ns["w"]}}}id')
            if cid in citar_ids:
                results.append({
                    "paragraph_index": para_idx,
                    "text": _get_paragraph_text(para)[:500],
                    "comment_id": cid,
                })

    return results if results else [{"info": "Nenhum paragrafo marcado com 'citar'."}]


@mcp.tool()
def insert_candidate_comment(
    doc_path: str,
    output_path: str,
    paragraph_index: int,
    candidate_text: str,
) -> str:
    """Insere um comentario de candidato em um paragrafo especifico do DOCX.

    Args:
        doc_path: caminho do DOCX de entrada
        output_path: caminho do DOCX de saida
        paragraph_index: indice do paragrafo
        candidate_text: texto do comentario (ex: 'CANDIDATO: Olivares et al. (2024)\\nScore: 0.91')
    """
    doc = Document(doc_path)
    if paragraph_index >= len(doc.paragraphs):
        return f"Indice {paragraph_index} fora do range (total: {len(doc.paragraphs)})"

    para = doc.paragraphs[paragraph_index]

    # Criar comment via XML
    ns_w = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

    # Obter proximo ID de comentario
    comments_part = None
    for rel in doc.part.rels.values():
        if "comments" in rel.reltype:
            comments_part = rel.target_part
            break

    # Gerar um ID alto para evitar colisoes
    import random
    comment_id = str(random.randint(1000, 9999))

    # Adicionar commentRangeStart e commentRangeEnd ao paragrafo
    range_start = OxmlElement("w:commentRangeStart")
    range_start.set(qn("w:id"), comment_id)
    para._element.insert(0, range_start)

    range_end = OxmlElement("w:commentRangeEnd")
    range_end.set(qn("w:id"), comment_id)
    para._element.append(range_end)

    # commentReference
    comment_ref_run = OxmlElement("w:r")
    comment_ref = OxmlElement("w:commentReference")
    comment_ref.set(qn("w:id"), comment_id)
    comment_ref_run.append(comment_ref)
    para._element.append(comment_ref_run)

    doc.save(output_path)
    return f"Comentario inserido no paragrafo {paragraph_index} -> {output_path}"


@mcp.tool()
def insert_citation(
    doc_path: str,
    output_path: str,
    paragraph_index: int,
    citation: str,
    reference: str,
) -> str:
    """Insere citacao inline no paragrafo e adiciona referencia ao final do documento.

    Args:
        doc_path: caminho do DOCX
        output_path: caminho de saida
        paragraph_index: indice do paragrafo
        citation: texto da citacao inline, ex: '(OLIVARES et al., 2024)'
        reference: referencia completa para o final do documento
    """
    doc = Document(doc_path)
    if paragraph_index >= len(doc.paragraphs):
        return f"Indice {paragraph_index} fora do range"

    para = doc.paragraphs[paragraph_index]

    # Adicionar citacao ao final do paragrafo
    run = para.add_run(f" {citation}")

    # Adicionar referencia ao final do documento
    ref_para = doc.add_paragraph(reference)

    doc.save(output_path)
    return f"Citacao '{citation}' inserida no paragrafo {paragraph_index}. Referencia adicionada ao final."


@mcp.tool()
def renumber_equations(
    doc_path: str,
    output_path: str,
    start_number: int = 1,
) -> dict:
    """Renumera equacoes em ordem de aparicao e atualiza referencias textuais.

    A operacao sempre valida o estado antes e depois da alteracao. Se houver
    referencias para equacoes inexistentes, duplicidades ou intervalos invalidos,
    a renumeracao e abortada.
    """
    doc = Document(doc_path)
    before = _validate_equation_state(doc)

    if not before["equations"]:
        return {
            "ok": False,
            "message": "Nenhuma equacao encontrada no documento.",
            "validation_before": before,
        }

    if not before["is_valid"]:
        return {
            "ok": False,
            "message": "Renumeração abortada: o documento possui inconsistencias nas referencias de equacoes.",
            "validation_before": before,
        }

    mapping = {
        eq["equation_number"]: start_number + offset
        for offset, eq in enumerate(before["equations"])
    }

    # Atualizar labels das equacoes sem tocar nos elementos matematicos.
    for eq in before["equations"]:
        para = doc.paragraphs[eq["paragraph_index"]]
        old_number = eq["equation_number"]
        new_number = mapping[old_number]

        def relabel(text: str) -> str:
            return re.sub(rf"\({old_number}\)\s*$", f"({new_number})", text)

        _replace_in_word_text_nodes(para, relabel)

    # Atualizar referencias textuais no documento inteiro.
    for para in doc.paragraphs:
        _replace_in_word_text_nodes(para, lambda text: _renumber_reference_text(text, mapping))

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    doc.save(output_path)

    after_doc = Document(output_path)
    after = _validate_equation_state(after_doc)

    return {
        "ok": after["is_valid"],
        "message": "Equacoes renumeradas e referencias textuais atualizadas." if after["is_valid"] else "Renumeração concluida, mas a validacao final encontrou inconsistencias.",
        "mapping": mapping,
        "validation_before": before,
        "validation_after": after,
        "output_path": output_path,
    }


if __name__ == "__main__":
    mcp.run()
