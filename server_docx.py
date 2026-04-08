"""MCP Server — Leitura e manipulacao de DOCX (comentarios, citacoes, referencias)."""

import re
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Pt
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
TABLE_CAPTION_RE = re.compile(r'^Tabela\s+\d+\s+[–-]\s+.+')


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


def _set_run_font(run, font_name: str = "Times New Roman", font_size: int = 10, bold: bool | None = None) -> None:
    run.font.name = font_name
    run.font.size = Pt(font_size)
    if bold is not None:
        run.font.bold = bold

    r_pr = run._element.get_or_add_rPr()
    r_fonts = r_pr.rFonts
    if r_fonts is None:
        r_fonts = OxmlElement("w:rFonts")
        r_pr.append(r_fonts)
    for key in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        r_fonts.set(qn(key), font_name)


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


def _get_body_children(doc: Document):
    return list(doc._body._element)


def _paragraph_text_from_element(element) -> str:
    parts = []
    for node in element.iter():
        if getattr(node, "tag", None) == qn("w:t") and node.text:
            parts.append(node.text)
    return "".join(parts).strip()


def _get_table_caption(doc: Document, table) -> str:
    children = _get_body_children(doc)
    table_el = table._element
    child_idx = children.index(table_el)

    for idx in range(child_idx - 1, -1, -1):
        element = children[idx]
        if element.tag == qn("w:p"):
            text = _paragraph_text_from_element(element)
            if text:
                return text
    return ""


def _get_table_caption_paragraph(doc: Document, table):
    children = _get_body_children(doc)
    table_el = table._element
    child_idx = children.index(table_el)

    for idx in range(child_idx - 1, -1, -1):
        element = children[idx]
        if element.tag == qn("w:p"):
            text = _paragraph_text_from_element(element)
            if text:
                for paragraph in doc.paragraphs:
                    if paragraph._element is element:
                        return paragraph
                return None
    return None


def _set_table_caption(doc: Document, table, caption_text: str) -> None:
    existing = _get_table_caption_paragraph(doc, table)
    if existing is not None and TABLE_CAPTION_RE.match(_get_paragraph_full_text(existing).strip()):
        if existing.runs:
            existing.runs[0].text = caption_text
            for run in existing.runs[1:]:
                run.text = ""
        else:
            existing.add_run(caption_text)
        for run in existing.runs:
            _set_run_font(run, font_name="Times New Roman", font_size=10, bold=False)
        return

    p = OxmlElement("w:p")
    r = OxmlElement("w:r")
    t = OxmlElement("w:t")
    t.text = caption_text
    r.append(t)
    p.append(r)
    table._element.addprevious(p)


def _cell_border_sides(cell_el) -> set[str]:
    tc_pr = cell_el.find(qn("w:tcPr"))
    if tc_pr is None:
        return set()
    tc_borders = tc_pr.find(qn("w:tcBorders"))
    if tc_borders is None:
        return set()

    sides = set()
    for side in ("top", "bottom", "left", "right"):
        border = tc_borders.find(qn(f"w:{side}"))
        if border is not None and border.get(qn("w:val")) not in (None, "nil"):
            sides.add(side)
    return sides


def _set_cell_border(cell, **kwargs) -> None:
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_borders = tc_pr.first_child_found_in("w:tcBorders")
    if tc_borders is None:
        tc_borders = OxmlElement("w:tcBorders")
        tc_pr.append(tc_borders)

    for edge in ("top", "bottom", "left", "right"):
        data = kwargs.get(edge)
        if data is None:
            continue
        tag = qn(f"w:{edge}")
        element = tc_borders.find(tag)
        if element is None:
            element = OxmlElement(f"w:{edge}")
            tc_borders.append(element)
        for key, value in data.items():
            element.set(qn(f"w:{key}"), str(value))


def _clear_top_bottom_borders(table) -> None:
    for row in table.rows:
        for cell in row.cells:
            _set_cell_border(
                cell,
                top={"val": "nil"},
                bottom={"val": "nil"},
            )


def _apply_minimal_table_borders(table) -> None:
    if not table.rows:
        return

    _clear_top_bottom_borders(table)

    for cell in table.rows[0].cells:
        _set_cell_border(
            cell,
            top={"val": "single", "sz": "4", "color": "000000"},
            bottom={"val": "single", "sz": "4", "color": "000000"},
        )

    for cell in table.rows[-1].cells:
        _set_cell_border(
            cell,
            bottom={"val": "single", "sz": "4", "color": "000000"},
        )


def _apply_table_font(table, font_name: str = "Times New Roman", font_size: int = 10) -> None:
    for row_idx, row in enumerate(table.rows):
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    _set_run_font(run, font_name=font_name, font_size=font_size, bold=(row_idx == 0))


def _parse_table_numbers(table_numbers: str, total_tables: int) -> list[int]:
    if not table_numbers.strip():
        return list(range(1, total_tables + 1))

    result = []
    for part in table_numbers.split(","):
        value = int(part.strip())
        if value < 1 or value > total_tables:
            raise ValueError(f"Tabela {value} fora do intervalo 1..{total_tables}")
        result.append(value)
    return sorted(set(result))


def _remove_table_row(table, row_index: int) -> None:
    row = table.rows[row_index]
    row._tr.getparent().remove(row._tr)


def _ensure_paragraph_anchor(paragraph):
    if paragraph.runs:
        return paragraph.runs[0]
    return paragraph.add_run("")


def _add_comment_to_table(doc: Document, table, text: str, author: str = "docx-manager") -> bool:
    if not table.rows or not table.rows[0].cells:
        return False
    paragraph = table.rows[0].cells[0].paragraphs[0]
    anchor = _ensure_paragraph_anchor(paragraph)
    doc.add_comment(anchor, text, author=author)
    return True


def _table_report(doc: Document) -> list[dict]:
    report = []
    for idx, table in enumerate(doc.tables, start=1):
        caption = _get_table_caption(doc, table)
        jc = None
        layout = None
        tbl_pr = table._element.find(qn("w:tblPr"))
        if tbl_pr is not None:
            jc_el = tbl_pr.find(qn("w:jc"))
            if jc_el is not None:
                jc = jc_el.get(qn("w:val"))
            layout_el = tbl_pr.find(qn("w:tblLayout"))
            if layout_el is not None:
                layout = layout_el.get(qn("w:type"))

        rows = table._element.findall(qn("w:tr"))
        first_row_cells = rows[0].findall(qn("w:tc")) if rows else []
        last_row_cells = rows[-1].findall(qn("w:tc")) if rows else []
        middle_rows = rows[1:-1] if len(rows) > 2 else []

        issues = []
        if not TABLE_CAPTION_RE.match(caption):
            issues.append('legenda acima ausente ou fora do padrão "Tabela N – ..."')
        if jc != "center":
            issues.append("tabela sem alinhamento explícito centralizado")
        if layout == "fixed":
            issues.append("layout fixo; não está em autoajuste")

        first_ok = bool(first_row_cells) and all(
            {"top", "bottom"}.issubset(_cell_border_sides(cell))
            for cell in first_row_cells
        )
        last_ok = bool(last_row_cells) and all(
            "bottom" in _cell_border_sides(cell)
            for cell in last_row_cells
        )
        if not first_ok:
            issues.append("primeira linha sem bordas superior e inferior em todas as células")
        if not last_ok:
            issues.append("última linha sem borda inferior em todas as células")

        has_internal_borders = False
        for row in middle_rows:
            for cell in row.findall(qn("w:tc")):
                sides = _cell_border_sides(cell)
                if "bottom" in sides:
                    has_internal_borders = True
                    break
            if has_internal_borders:
                break
        if has_internal_borders:
            issues.append("há bordas internas além do padrão mínimo esperado")

        font_issues = []
        for row_idx, row in enumerate(table.rows):
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        if not run.text:
                            continue
                        if run.font.name not in (None, "Times New Roman"):
                            font_issues.append("texto fora de Times New Roman")
                            break
                        if run.font.size is not None and abs(run.font.size.pt - 10) > 0.1:
                            font_issues.append("texto fora do tamanho 10")
                            break
                        if row_idx == 0 and run.font.bold is False:
                            font_issues.append("primeira linha sem negrito completo")
                            break
                    if font_issues:
                        break
                if font_issues:
                    break
            if font_issues:
                break
        issues.extend(font_issues)

        report.append({
            "table_index": idx,
            "status": "ok" if not issues else "erro",
            "issues": issues,
            "summary": "conforme esperado" if not issues else "; ".join(issues),
            "caption": caption,
        })
    return report


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
def validate_tables_format(doc_path: str) -> list[dict]:
    """Valida legenda, alinhamento, bordas e fonte das tabelas do DOCX."""
    doc = Document(doc_path)
    return _table_report(doc)


@mcp.tool()
def report_tables_format(doc_path: str) -> list[str]:
    """Retorna um relatório textual de ok/erro por tabela."""
    doc = Document(doc_path)
    report = _table_report(doc)
    return [
        f"Tabela {item['table_index']}: {item['status']} - {item['summary']}"
        for item in report
    ]


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
    anchor = _ensure_paragraph_anchor(para)
    doc.add_comment(anchor, candidate_text, author="docx-manager")

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
def apply_table_style(
    doc_path: str,
    output_path: str,
    table_numbers: str = "",
    font_name: str = "Times New Roman",
    font_size: int = 10,
    caption_prefix: str = "",
) -> dict:
    """Aplica estilo padrao de tabelas e valida o resultado.

    `table_numbers` deve ser uma string CSV com indices 1-based, ex.: "3,4,8".
    Se vazio, aplica em todas as tabelas.
    """
    doc = Document(doc_path)
    selected = _parse_table_numbers(table_numbers, len(doc.tables))
    before = _table_report(doc)

    for table_number in selected:
        table = doc.tables[table_number - 1]
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = True
        _apply_minimal_table_borders(table)
        _apply_table_font(table, font_name=font_name, font_size=font_size)
        if caption_prefix:
            _set_table_caption(doc, table, f"Tabela {table_number} – {caption_prefix} {table_number}".strip())

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    doc.save(output_path)

    after_doc = Document(output_path)
    after = _table_report(after_doc)

    return {
        "ok": all(item["status"] == "ok" for item in after if item["table_index"] in selected),
        "message": "Estilo de tabela aplicado." if selected else "Nenhuma tabela selecionada.",
        "table_numbers": selected,
        "validation_before": [item for item in before if item["table_index"] in selected],
        "validation_after": [item for item in after if item["table_index"] in selected],
        "output_path": output_path,
    }


@mcp.tool()
def set_table_caption(
    doc_path: str,
    output_path: str,
    table_number: int,
    caption_text: str,
) -> dict:
    """Insere ou corrige a legenda acima de uma tabela específica."""
    doc = Document(doc_path)
    if table_number < 1 or table_number > len(doc.tables):
        return {"ok": False, "message": f"Tabela {table_number} fora do intervalo 1..{len(doc.tables)}"}

    table = doc.tables[table_number - 1]
    _set_table_caption(doc, table, caption_text)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    doc.save(output_path)
    after_doc = Document(output_path)
    report = _table_report(after_doc)
    item = next(x for x in report if x["table_index"] == table_number)
    return {
        "ok": "legenda acima ausente ou fora do padrão \"Tabela N – ...\"" not in item["issues"],
        "table_number": table_number,
        "caption": caption_text,
        "validation_after": item,
        "output_path": output_path,
    }


@mcp.tool()
def validate_tables_with_comments(
    doc_path: str,
    output_path: str,
) -> dict:
    """Valida as tabelas, insere comentario nas que tiverem erro e retorna o relatorio textual."""
    doc = Document(doc_path)
    report = _table_report(doc)
    annotated = []

    for item in report:
        if item["status"] != "erro":
            continue
        table = doc.tables[item["table_index"] - 1]
        comment_text = f"ERRO DE FORMATAÇÃO DA TABELA {item['table_index']}: {item['summary']}"
        if _add_comment_to_table(doc, table, comment_text):
            annotated.append(item["table_index"])

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    doc.save(output_path)

    return {
        "output_path": output_path,
        "annotated_tables": annotated,
        "report": [
            f"Tabela {item['table_index']}: {item['status']} - {item['summary']}"
            for item in report
        ],
    }


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
