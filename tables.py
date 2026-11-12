"""
tables.py — 표·텍스트 결합 RAG의 표 부분

    지금 chunk는 PDF 표를 줄글로 펼쳐 저장해서 행·열 구조가 깨져 있다
    (병합된 칸은 한 번만 나오고, 페이지가 넘어가면 머리줄이 다시 끼어든다).
    여기서는 표를 구조 그대로 따로 뽑아 저장하고, 본문 chunk의 "Table N" 언급과 연결한다.
    검색에서 chunk가 뽑히면 연결된 표를 함께 LLM에 넘긴다.

    추출:  PyMuPDF find_tables()로 페이지마다 표를 찾는다.
           - 표 위의 "Table N 제목" 글을 찾아 번호와 제목을 붙인다
           - 제목 없이 다음 페이지 맨 위에서 열 수가 같은 표가 나오면 앞 표의 이어지는 부분으로 본다
           - 머리줄은 PyMuPDF가 찾은 머리줄 영역, "1) ..." 한 칸짜리 행은 각주
           - 병합된 칸은 그 칸의 상자가 덮는 자리에만 같은 글을 채운다 (가로 병합은 옆, 세로 병합은 아래)
    소속:  표 제목 글이 들어 있는 chunk의 조항(ref)을 표의 소속으로 한다 (Pt, Ch, Sec 단위로 번호가 매겨짐)
    연결:  chunk 본문의 "Table 3", "Sec.1 Table 2", "Ch.3 Sec.1 Table 2" 등을 (Pt, Ch, Sec, 번호)로 풀어 찾는다

실행:  python tables.py          → table_db/tables.json (규정 내용이 들어 있어 git에 올리지 않는다)
"""
import json
import re
import sys
from pathlib import Path

from config import BASE_DIR, COLLECTION, DB_DIR, DOCS_DIR

OUT = BASE_DIR / "table_db" / "tables.json"
CAPTION_RE = re.compile(r"^\s*Table\s+(\d+)\s+(.*)", re.S)
NUMBER_RE = re.compile(r"^-?\d+([.,]\d+)?(\s*\d\))?$")
FOOTNOTE_RE = re.compile(r"^\s*\d\)\s")
REF_RE = re.compile(r"(Pt\.\d+)\s+(Ch\.\d+)\s+(Sec\.\d+)")
MENTION_RE = re.compile(r"(?:(Pt\.\d+)\s+)?(?:(Ch\.\d+)\s+)?(?:(Sec\.\d+)\s+)?Table\s+(\d+)")


def clean(cell):
    return re.sub(r"\s+", " ", (cell or "").replace("\xa0", " ")).strip()


def is_number(text):
    return bool(NUMBER_RE.match(text))


def caption_above(page, bbox):
    """표 바로 위(70pt 이내)의 'Table N 제목' 글"""
    best = None
    for x0, y0, x1, y1, text, *_ in page.get_text("blocks"):
        text = clean(text)
        match = CAPTION_RE.match(text)
        if match and y1 <= bbox[1] + 2 and bbox[1] - y1 < 70:
            if best is None or y1 > best[0]:
                best = (y1, int(match.group(1)), match.group(2)[:200])
    return best[1:] if best else None


def read_table(table):
    """표 하나를 (머리줄, 본문, 각주, 병합으로 채운 칸 수)로 읽는다.

    PyMuPDF는 병합된 칸을 '큰 상자 하나 + 가려진 자리(None)'로 돌려준다.
    큰 상자가 실제로 덮는 자리에만 같은 글을 넣는다: 가로 병합은 옆으로, 세로 병합은 아래로.
    원래 비어 있는 칸('')은 그대로 둔다. 머리줄은 PyMuPDF가 찾은 머리줄 영역의 행."""
    raw = table.extract()
    n_rows, n_cols = len(raw), table.col_count
    # 각 행·열의 대표 범위: 병합되지 않은(가장 작은) 상자 기준
    col_x = [None] * n_cols
    row_y = [None] * n_rows
    for r, row in enumerate(table.rows):
        for c, box in enumerate(row.cells):
            if box is None:
                continue
            if col_x[c] is None or box[2] - box[0] < col_x[c][1] - col_x[c][0]:
                col_x[c] = (box[0], box[2])
            if row_y[r] is None or box[3] - box[1] < row_y[r][1] - row_y[r][0]:
                row_y[r] = (box[1], box[3])
    grid = [[None if v is None else clean(v) for v in row] for row in raw]
    filled = 0
    for r, row in enumerate(table.rows):
        for c, box in enumerate(row.cells):
            if box is None:
                continue
            for r2 in range(r, n_rows):
                for c2 in range(c, n_cols):
                    if grid[r2][c2] is not None or col_x[c2] is None or row_y[r2] is None:
                        continue
                    cx, cy = sum(col_x[c2]) / 2, sum(row_y[r2]) / 2
                    if box[0] <= cx <= box[2] and box[1] <= cy <= box[3]:
                        grid[r2][c2] = grid[r][c]
                        filled += 1
    grid = [[v or "" for v in row] for row in grid]
    header_bottom = table.header.bbox[3] if not table.header.external else None
    header, body, notes = [], [], []
    for r, row in enumerate(grid):
        joined = " ".join(dict.fromkeys(c for c in row if c))      # 가로 병합으로 반복된 글은 한 번만
        if not joined:
            continue
        if header_bottom is not None and row_y[r] and row_y[r][1] <= header_bottom + 1:
            header.append(row)
        elif FOOTNOTE_RE.match(joined) and len(set(c for c in row if c)) == 1:
            notes.append(joined)
        else:
            body.append(row)
    if not header and any(any(is_number(c) for c in row) for row in body):
        # PyMuPDF가 머리줄을 못 찾은 숫자 표: 맨 앞의 숫자 없는 행(최대 2줄)을 머리줄로
        while body and len(header) < 2 and not any(is_number(c) for c in body[0]):
            header.append(body.pop(0))
    return header, body, notes, filled


def header_names(header, width):
    """여러 줄 머리줄을 열 이름 하나씩으로 합친다"""
    names = [""] * width
    for row in header:
        for c in range(width):
            cell = row[c] if c < len(row) else ""
            if cell and cell not in names[c]:
                names[c] = f"{names[c]} / {cell}" if names[c] else cell
    return [n or f"col{c + 1}" for c, n in enumerate(names)]


def realign(rows, old_names, new_names):
    """열 구성이 다른 조각을 합칠 때, 이름이 같은 열끼리 맞춘다"""
    out = []
    for row in rows:
        value = dict(zip(old_names, row))
        out.append([value.get(name, "") for name in new_names])
    return out


def extract_pdf(path):
    import pymupdf
    doc = pymupdf.open(path)
    tables, open_table = [], None
    for index, page in enumerate(doc):
        found = page.find_tables().tables
        for t_index, table in enumerate(found):
            if table.row_count < 1 or table.col_count < 2:
                continue
            header, body, notes, filled = read_table(table)
            names = header_names(header, table.col_count)
            caption = caption_above(page, table.bbox)
            near_top = table.bbox[1] < page.rect.height * 0.25
            same_shape = table.col_count == open_table["width"] if open_table else False
            same_header = bool(header) and open_table and set(names) >= set(open_table["columns"]) - {""}
            if caption is None and open_table and t_index == 0 and near_top and open_table["pages"][-1] == index                     and (same_shape or same_header):           # 앞 페이지 표의 이어지는 부분
                if header and header != open_table["header"] and not same_header:
                    body = header + body                       # 반복된 머리줄이 아니면 본문으로
                body = [r for r in body if r not in open_table["header"]]
                if names != open_table["columns"] and same_header:
                    open_table["body"] = realign(open_table["body"], open_table["columns"], names)
                    open_table["columns"], open_table["width"] = names, table.col_count
                if body and open_table["body"]:                # 페이지 경계에서 잘린 병합 칸(맨 앞 빈 칸)은 앞 행 값으로
                    for c, cell in enumerate(body[0]):
                        if cell == "" and c < len(open_table["body"][-1]) and not is_number(open_table["body"][-1][c]):
                            body[0][c] = open_table["body"][-1][c]
                open_table["body"] += body
                open_table["notes"] += notes
                open_table["filled_cells"] += filled
                open_table["pages"].append(index + 1)
                continue
            open_table = {"file": path.name, "pages": [index + 1], "number": caption[0] if caption else None,
                          "title": caption[1] if caption else "", "width": table.col_count, "columns": names,
                          "header": header, "body": body, "notes": notes, "filled_cells": filled}
            tables.append(open_table)
        if not found or found[-1].bbox[3] < page.rect.height * 0.75:
            open_table = None                                  # 페이지 끝까지 이어진 표만 다음 페이지로 넘어갈 수 있다
    return tables


def merged_columns(table):
    """이름이 같은 이웃 열(가로 병합)을 한 열로 합친다. 값이 다르면 ' / '로 이어 붙인다"""
    groups = []
    for c, name in enumerate(table["columns"]):
        if groups and groups[-1][0] == name:
            groups[-1][1].append(c)
        else:
            groups.append((name, [c]))
    rows = [[" / ".join(dict.fromkeys(row[c] for c in cols if c < len(row) and row[c])) for _, cols in groups]
            for row in table["body"]]
    return [name for name, _ in groups], rows


def to_markdown(table):
    """LLM에 넘길 표. 병합 칸을 모두 채워 행 하나만 봐도 뜻이 통하게 한다"""
    title = f"Table {table['number']} {table['title']}".strip() if table["number"] else "Table (no caption)"
    columns, rows = merged_columns(table)
    lines = [f"{title} ({table['ref'] or table['file']}, PDF p.{'-'.join(map(str, table['pages']))})",
             "| " + " | ".join(columns) + " |", "|" + "---|" * len(columns)]
    lines += ["| " + " | ".join(row) + " |" for row in rows]
    lines += [f"Note {n}" for n in table["notes"]]
    return "\n".join(lines)


def assign_refs(tables):
    """표 제목이 들어 있는 chunk의 조항을 표의 소속으로"""
    import chromadb
    data = chromadb.PersistentClient(path=str(DB_DIR)).get_collection(COLLECTION).get(include=["documents", "metadatas"])
    by_page = {}
    for doc, meta in zip(data["documents"], data["metadatas"]):
        by_page.setdefault((meta["file"], meta["pdf_page"]), []).append((meta["ref"], doc))
    for t in tables:
        chunks = by_page.get((t["file"], t["pages"][0]), [])
        ref = None
        if t["number"]:
            needle = f"Table {t['number']}"
            ref = next((r for r, d in chunks if needle in d), None)
        t["ref"] = ref or (chunks[0][0] if chunks else None)
        m = REF_RE.search(t["ref"] or "")
        t["key"] = f"{m.group(1)} {m.group(2)} {m.group(3)} Table {t['number']}" if (m and t["number"]) else None
        t["markdown"] = to_markdown(t)
    return tables


def build():
    tables = []
    for path in sorted(DOCS_DIR.glob("*.pdf")):
        part = extract_pdf(path)
        print(f"{path.name}: 표 {len(part)}개", flush=True)
        tables += part
    tables = assign_refs(tables)
    for n, t in enumerate(tables):
        t["id"] = f"table-{n}"
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(tables, ensure_ascii=False, indent=1), encoding="utf-8")
    return tables


# ------------------------------------------------------------------ 검색 단계에서 쓰는 부분
class TableIndex(dict):
    """key("Pt.3 Ch.6 Sec.4 Table 1") → 표. by_ref 에는 조항(ref) → 그 조항 안의 표 목록"""
    by_ref = {}


def load():
    tables = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else []
    index = TableIndex()
    index.by_ref = {}
    for t in tables:
        if t["key"]:
            index.setdefault(t["key"], t)          # 같은 번호가 여러 번 잡히면 첫 번째
        if t["ref"] and t["number"]:
            index.by_ref.setdefault(t["ref"], []).append(t)
    return index


def mentioned(chunk_text, chunk_ref):
    """chunk 본문에서 언급한 표의 key 목록. 빠진 Pt/Ch/Sec는 chunk 자신의 조항에서 채운다"""
    own = REF_RE.search(chunk_ref or "")
    if not own:
        return []
    keys = []
    for pt, ch, sec, number in MENTION_RE.findall(chunk_text):
        key = f"{pt or own.group(1)} {ch or own.group(2)} {sec or own.group(3)} Table {number}"
        if key not in keys:
            keys.append(key)
    return keys


def linked_tables(index, chunk_text, chunk_ref):
    """chunk와 연결된 표: (1) 본문이 "Table N"으로 언급한 표, (2) chunk와 같은 조항에 들어 있는 표"""
    found = [index[k] for k in mentioned(chunk_text, chunk_ref) if k in index]
    for t in getattr(index, "by_ref", {}).get(chunk_ref, []):
        if t not in found:
            found.append(t)
    return found


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    result = build()
    captioned = sum(1 for t in result if t["number"])
    multi = sum(1 for t in result if len(t["pages"]) > 1)
    print(f"전체 {len(result)}개, 제목(Table N) 있음 {captioned}개, 여러 페이지에 걸친 표 {multi}개 → {OUT}")
