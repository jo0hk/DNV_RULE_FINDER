"""
eval/formula_context.py — 계산 비교 실험에서 LLM에게 줄 규정 발췌문 묶음

    공식 6개를 계산하는 데 필요한 chunk(공식 조항, 기호 정의, 계수 표, 강재 등급 표)를 DB에서 그대로 꺼낸다.
    파이썬 엔진(조건 C)이 공식 6개를 모두 가진 것과 맞추려고, LLM 조건에도 6개 공식의 발췌문을 모두 준다.
    (검색 오류의 영향은 빼고, "계산을 누가 하느냐"의 차이만 보려는 것)

    plain   : DB에 저장된 그대로. PDF의 공식이 이미지라 식이 빠져 있다 ("given by:" 다음이 바로 "where:")
    formula : 위 chunk 끝에 PDF 이미지에서 옮긴 식을 텍스트로 붙인 것. 표는 그대로(줄글로 펼쳐진 상태)
    tables  : formula + 발췌문이 언급한 표를 구조화된 표로 붙인 것 (표·텍스트 결합 RAG)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# 순서대로: 단위·기호, 강재 등급, k, fr, Cw, 선체 단면계수, 관성모멘트, 최소 두께, 판, 보강재
CHUNK_IDS = ["chunk-1076", "chunk-1079", "chunk-1147", "chunk-1149", "chunk-1286", "chunk-1294",
             "chunk-1377", "chunk-1379", "chunk-1416", "chunk-1417", "chunk-1420", "chunk-1421",
             "chunk-1429", "chunk-1431", "chunk-1432"]

# chunk → PDF 이미지에서 옮긴 식 (formulas/hull.py, 검증표와 같은 내용)
# 표기: 아래첨자는 밑줄(L_2 = L 아래첨자 2), 곱셈은 * 로 명시한다.
#       (1차 실험에서 "L2"를 L의 제곱으로 읽는 오류가 나와서 고친 표기. 1차 결과는 results/archive/)
FORMULA_TEXT = {
    "chunk-1294": ["C_w = 0.0856 * L  for L < 90",
                   "C_w = 10.75 - ((300 - L) / 100)^1.5  for 90 <= L <= 300",
                   "C_w = 10.75  for 300 < L <= 350",
                   "C_w = 10.75 - ((L - 350) / 150)^1.5  for 350 < L <= 500"],
    "chunk-1377": ["Z_R-gr = k * ((1 + f_r) / 2) * C_w0 * L^2 * B * (C_B + 0.7) * 10^-6"],
    "chunk-1379": ["I_yR-gr = 3 * f_r * C_w * L^3 * B * (C_B + 0.7) * 10^-8"],
    "chunk-1416": ["t = a + b * L_2 * sqrt(k)"],
    "chunk-1420": ["alpha_p = 1.2 - b / (2.1 * a)   (not to be taken greater than 1.0)"],
    "chunk-1421": ["t = 0.0158 * alpha_p * b * sqrt(|P| / (C_a * R_eH))",
                   "C_a = beta_a - alpha_a * |sigma_hg| / R_eH   (not to be taken greater than C_a-max)"],
    "chunk-1431": ["Z = f_u * |P| * s * l_bdg^2 / (f_bdg * C_s * R_eH)",
                   "Table 3, stiffeners with one or both ends fixed: tension + pressure on stiffener side, or compression + "
                   "pressure on plate side: C_s = beta_s - alpha_s * |sigma_hg| / R_eH, not greater than C_s-max",
                   "Table 3, stiffeners with one or both ends fixed: tension + pressure on plate side, or compression + "
                   "pressure on stiffener side: C_s = f_m * (beta_s - alpha_s * |sigma_hg| / R_eH), not greater than C_s-max",
                   "Table 3, stiffeners with simply supported ends: tension + pressure on plate side, or compression + "
                   "pressure on stiffener side: C_s = beta_s - alpha_s * |sigma_hg| / R_eH, not greater than C_s-max",
                   "Table 3, stiffeners with simply supported ends: tension + pressure on stiffener side, or compression + "
                   "pressure on plate side: C_s = C_s-max"],
}


def load(kind="plain"):
    """발췌문 묶음을 하나의 글로. kind: plain | formula | tables

    tables: formula에 더해, 발췌문이 언급한 표(Table N)를 구조화된 표(tables.py)로 뒤에 붙인다.
            병합 칸이 모두 채워져 있어 행 하나만 봐도 뜻이 통한다 (표·텍스트 결합 RAG)."""
    import chromadb
    from config import COLLECTION, DB_DIR
    data = chromadb.PersistentClient(path=str(DB_DIR)).get_collection(COLLECTION).get(ids=CHUNK_IDS, include=["documents", "metadatas"])
    text = dict(zip(data["ids"], data["documents"]))
    refs = {cid: meta["ref"] for cid, meta in zip(data["ids"], data["metadatas"])}
    parts = []
    for n, cid in enumerate(CHUNK_IDS, start=1):
        body = text[cid]
        if kind in ("formula", "tables") and cid in FORMULA_TEXT:
            body += "\n[Formulas on this page, transcribed from the PDF image]\n" + "\n".join(FORMULA_TEXT[cid])
        parts.append(f"[{n}] {body}")
    if kind == "tables":
        import tables
        index, seen, blocks = tables.load(), set(), []
        for cid in CHUNK_IDS:
            for t in tables.linked_tables(index, text[cid], refs[cid]):
                if t["id"] not in seen:
                    seen.add(t["id"])
                    blocks.append(t["markdown"])
        parts.append("[Structured tables referenced by the excerpts above (merged cells filled in)]\n\n" + "\n\n".join(blocks))
    return "\n\n".join(parts)


if __name__ == "__main__":
    for kind in ("plain", "formula", "tables"):
        print(kind, len(load(kind)), "chars")
