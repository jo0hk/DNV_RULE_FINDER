import re
import pymupdf
from config import COLLECTION, DB_DIR, DOCS_DIR, EMBED_MODEL

TARGET_CHARS = 1000 
MAX_CHARS = 1800 
HEADING_SIZE = 12.5 

FOOTER_RE = re.compile(r"DNV-RU-SHIP Pt\.(\d+) Ch\.(\d+)\. Edition (\w+ \d{4})")
PAGE_RE = re.compile(r"^Page (\d+)$", re.M)
LABEL_RE = re.compile(r"Part \d+ Chapter \d+ (Section|Appendix|Contents|Changes)\s*(\w*)")
COVER_RE = re.compile(r"Part (\d+) (.+?)\nChapter (\d+) (.+?)\n\s*The content", re.S)


def clean(text):
    """PDF 특수 공백을 일반 공백으로 바꾸고 양끝을 정리"""
    return text.replace("\xa0", " ").strip()



#페이지 읽기
def read_page(page):
    """
    한 페이지에서 본문 블록(문단)들을 순서대로 꺼낸다.
    반환값: [{"text": 문단 글자, "size": 글자 크기, "bold": 굵은 글씨 여부}, ...]
    """
    portrait = page.rect.height > page.rect.width
    blocks = []

    for block in page.get_text("dict", flags=pymupdf.TEXTFLAGS_TEXT)["blocks"]:
        lines = []
        for line in block.get("lines", []):
            if line["dir"] != (1.0, 0.0):
                continue 
            if portrait and line["bbox"][1] > 733:
                continue  
            text = clean("".join(span["text"] for span in line["spans"]))
            if text:
                lines.append((text, line["spans"][0]))
        if not lines:
            continue

        text = ""
        for line_text, _ in lines:
            if not text or text.endswith("-"):
                text += line_text          
            elif line_text.startswith("— "):
                text += "\n" + line_text    
            else:
                text += " " + line_text
        first_span = lines[0][1]
        blocks.append({
            "text": text,
            "size": first_span["size"],
            "bold": "Bold" in first_span["font"],
        })
    return blocks


#PDF 하나를 조항 단위 chunk로 자르기
def chunk_pdf(pdf_path):
    """PDF 파일 하나를 읽어서 chunk 목록을 돌려준다. chunk = {"text": ..., "meta": {...}}"""
    chunks = []
    titles = {}             
    where = None             
    sec_title = h1 = h2 = ""  
    buf, buf_meta = [], None 

    def flush():
        """buf에 모아둔 문단들을 chunk 하나로 저장"""
        nonlocal buf, buf_meta
        body = "\n".join(buf).strip()
        if len(body) >= 30:
            part, chapter, sec = buf_meta["where"]
            part_title, chapter_title = titles.get((part, chapter), ("", ""))
            heading = buf_meta["h2"] or buf_meta["h1"]
            number = heading.split(" ")[0] if heading[:1].isdigit() else ""
            ref = f"DNV-RU-SHIP Pt.{part} Ch.{chapter} {sec}" + (f" [{number}]" if number else "")
            path = " > ".join(t for t in [chapter_title, buf_meta["sec_title"],
                                          buf_meta["h1"], buf_meta["h2"]] if t)
            chunks.append({

                "text": f"{ref} | {path}\n{body}",
                "meta": {
                    "ref": ref, "path": path, "part_title": part_title,
                    "edition": buf_meta["edition"], "page": buf_meta["page"],
                    "pdf_page": buf_meta["pdf_page"], "file": pdf_path.name,
                },
            })
        buf, buf_meta = [], None

    doc = pymupdf.open(pdf_path)
    for page_index, page in enumerate(doc):
        page_text = page.get_text().replace("\xa0", " ")
        footer = FOOTER_RE.search(page_text)

        if not footer:  
            cover = COVER_RE.search(page_text)
            if cover:
                part, part_title, chapter, chapter_title = cover.groups()
                titles[(part, chapter)] = (clean(part_title), " ".join(chapter_title.split()))
            flush()
            where = None
            continue

        part, chapter, edition = footer.groups()
        label = LABEL_RE.search(page_text)
        if label and label.group(1) in ("Contents", "Changes"):
            flush()  
            where = None
            continue
        if label:
            sec = ("Sec." if label.group(1) == "Section" else "App.") + label.group(2)
        elif where and where[:2] == (part, chapter):
            sec = where[2] 
        else:
            continue

        if (part, chapter, sec) != where:
            flush()
            where, sec_title, h1, h2 = (part, chapter, sec), "", "", ""

        printed = PAGE_RE.search(page_text)
        page_no = int(printed.group(1)) if printed else page_index + 1

        for block in read_page(page):
            text = block["text"]

            if block["size"] >= HEADING_SIZE:     
                if re.match(r"(SECTION|APPENDIX) ", text):
                    flush()
                    sec_title, h1, h2 = text, "", ""  
                elif re.match(r"\d+\.\d+", text):
                    flush()
                    h2 = text                        
                elif re.match(r"\d+ ", text):
                    flush()
                    h1, h2 = text, ""                
                continue                             

            new_clause = block["bold"] and re.match(r"\d+\.\d+\.\d+", text)
            length = sum(len(t) for t in buf)
            if buf and ((new_clause and length >= TARGET_CHARS) or length + len(text) > MAX_CHARS):
                flush()
            if buf_meta is None:
                buf_meta = {"where": where, "sec_title": sec_title, "h1": h1, "h2": h2,
                            "edition": edition, "page": page_no, "pdf_page": page_index + 1}
            buf.append(text)

    flush()
    return chunks


#임베딩, DB 저장
def main():
    pdf_files = sorted(DOCS_DIR.glob("*.pdf"))
    if not pdf_files:
        raise SystemExit(f"PDF를 찾지 못했습니다: {DOCS_DIR}\n(.env의 DOCS_DIR 경로를 확인하세요)")

    chunks = []
    for pdf_path in pdf_files:
        print(f"읽는 중: {pdf_path.name}")
        new_chunks = chunk_pdf(pdf_path)
        print(f"       → chunk {len(new_chunks)}개")
        chunks += new_chunks
    texts = [c["text"] for c in chunks]

    print(f"임베딩 계산 중 (모델: {EMBED_MODEL}, chunk {len(texts)}개) - 몇 분 걸립니다")
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(EMBED_MODEL)
    vectors = model.encode(texts, batch_size=32, normalize_embeddings=True, show_progress_bar=True)

    print(f"DB 저장 중: {DB_DIR}")
    import chromadb
    client = chromadb.PersistentClient(path=str(DB_DIR))
    try:
        client.delete_collection(COLLECTION)
    except Exception:
        pass
    collection = client.create_collection(COLLECTION)
    for start in range(0, len(chunks), 1000):
        batch = chunks[start:start + 1000]
        collection.add(
            ids=[f"chunk-{start + i}" for i in range(len(batch))],
            documents=[c["text"] for c in batch],
            metadatas=[c["meta"] for c in batch],
            embeddings=vectors[start:start + 1000].tolist(),
        )
    print(f"완료! chunk {collection.count()}개가 저장되었습니다.")


if __name__ == "__main__":
    main()
