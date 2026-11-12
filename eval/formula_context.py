"""
eval/formula_context.py — 계산 비교 실험에서 LLM에게 줄 규정 발췌문 묶음

    공식 6개를 계산하는 데 필요한 chunk(공식 조항, 기호 정의, 계수 표, 강재 등급 표)를 DB에서 그대로 꺼낸다.
    파이썬 엔진(조건 C)이 공식 6개를 모두 가진 것과 맞추려고, LLM 조건에도 6개 공식의 발췌문을 모두 준다.
    (검색 오류의 영향은 빼고, "계산을 누가 하느냐"의 차이만 보려는 것)

    plain   : DB에 저장된 그대로. PDF의 공식이 이미지라 식이 빠져 있다 ("given by:" 다음이 바로 "where:")
    formula : 위 chunk 끝에 PDF 이미지에서 옮긴 식을 텍스트로 붙인 것. 표는 그대로(줄글로 펼쳐진 상태)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# 순서대로: 단위·기호, 강재 등급, k, fr, Cw, 선체 단면계수, 관성모멘트, 최소 두께, 판, 보강재
CHUNK_IDS = ["chunk-1076", "chunk-1079", "chunk-1147", "chunk-1149", "chunk-1286", "chunk-1294",
             "chunk-1377", "chunk-1379", "chunk-1416", "chunk-1417", "chunk-1420", "chunk-1421",
             "chunk-1429", "chunk-1431", "chunk-1432"]

# chunk → PDF 이미지에서 옮긴 식 (formulas/hull.py, 검증표와 같은 내용)
FORMULA_TEXT = {
    "chunk-1294": ["Cw = 0.0856 L  for L < 90",
                   "Cw = 10.75 - ((300 - L) / 100)^1.5  for 90 <= L <= 300",
                   "Cw = 10.75  for 300 < L <= 350",
                   "Cw = 10.75 - ((L - 350) / 150)^1.5  for 350 < L <= 500"],
    "chunk-1377": ["Z_R-gr = k ((1 + fr) / 2) Cw0 L^2 B (CB + 0.7) 10^-6"],
    "chunk-1379": ["I_yR-gr = 3 fr Cw L^3 B (CB + 0.7) 10^-8"],
    "chunk-1416": ["t = a + b L2 sqrt(k)"],
    "chunk-1420": ["alpha_p = 1.2 - b / (2.1 a)   (not to be taken greater than 1.0)"],
    "chunk-1421": ["t = 0.0158 alpha_p b sqrt(|P| / (Ca ReH))",
                   "Ca = beta_a - alpha_a |sigma_hg| / ReH   (not to be taken greater than Ca-max)"],
    "chunk-1431": ["Z = fu |P| s l_bdg^2 / (fbdg Cs ReH)",
                   "Table 3, stiffeners with one or both ends fixed: tension + pressure on stiffener side, or compression + "
                   "pressure on plate side: Cs = beta_s - alpha_s |sigma_hg| / ReH, not greater than Cs-max",
                   "Table 3, stiffeners with one or both ends fixed: tension + pressure on plate side, or compression + "
                   "pressure on stiffener side: Cs = fm (beta_s - alpha_s |sigma_hg| / ReH), not greater than Cs-max",
                   "Table 3, stiffeners with simply supported ends: tension + pressure on plate side, or compression + "
                   "pressure on stiffener side: Cs = beta_s - alpha_s |sigma_hg| / ReH, not greater than Cs-max",
                   "Table 3, stiffeners with simply supported ends: tension + pressure on stiffener side, or compression + "
                   "pressure on plate side: Cs = Cs-max"],
}


def load(kind="plain"):
    """발췌문 묶음을 하나의 글로. kind: plain | formula"""
    import chromadb
    from config import COLLECTION, DB_DIR
    data = chromadb.PersistentClient(path=str(DB_DIR)).get_collection(COLLECTION).get(ids=CHUNK_IDS, include=["documents"])
    text = dict(zip(data["ids"], data["documents"]))
    parts = []
    for n, cid in enumerate(CHUNK_IDS, start=1):
        body = text[cid]
        if kind == "formula" and cid in FORMULA_TEXT:
            body += "\n[Formulas on this page, transcribed from the PDF image]\n" + "\n".join(FORMULA_TEXT[cid])
        parts.append(f"[{n}] {body}")
    return "\n\n".join(parts)


if __name__ == "__main__":
    for kind in ("plain", "formula"):
        print(kind, len(load(kind)), "chars")
