"""
verify/build_sheet.py — 공식 검증표 만들기

    formulas/hull.py 에 옮긴 공식을 규정 PDF 원문과 눈으로 대조하기 위한 HTML을 만든다.

    공식마다 한 화면에 나란히 보여 준다:
      - 규정 PDF 원문 페이지 (이미지)
      - 코드에 옮긴 수식 (읽기 쉽게 수식 표기로)
      - 코드에 넣은 표 값과, PDF 표를 자동 추출해 대조한 결과
      - 예제 계산 단계와 실제 파이썬 코드
      - 확인 항목 체크박스와 메모 (브라우저에만 저장, "결과 복사"로 내보내기)

    PDF 페이지 이미지는 라이선스상 재배포하면 안 되므로 verify/pages/ 에만 두고 git에 올리지 않는다.

실행:  python verify/build_sheet.py   →  verify/verification.html 을 브라우저로 연다
"""
import html
import inspect
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
from config import DOCS_DIR  # noqa: E402
from formulas import calculate, hull  # noqa: E402
from formulas.core import fmt  # noqa: E402

PDF = DOCS_DIR / "DNV Rule SHIP Part 3 Hull - 2026_S.pdf"
PAGES = HERE / "pages"
OUT = HERE / "verification.html"
DPI = 130


# ------------------------------------------------------------------ PDF 표 자동 대조
def number(cell):
    """표 칸의 숫자. 각주 표시(예: '6)')와 줄바꿈은 지운다. '0.66/0.68 1)' 같은 칸은 튜플로"""
    text = (cell or "").replace("\xa0", " ").replace("\n", " ")
    text = re.sub(r"\b\d\)", "", text).strip()
    if "/" in text:
        parts = text.split("/")
        if all(re.fullmatch(r"-?\d+(\.\d+)?", p.strip()) for p in parts):
            return tuple(float(p) for p in parts)
    return float(text) if re.fullmatch(r"-?\d+(\.\d+)?", text) else None


def pdf_rows(doc, pieces):
    """(쪽, 표 번호, 숫자 열들) 조각을 이어 붙여 숫자 행 목록을 만든다.
    병합된 칸은 빈칸으로 나오므로 같은 열의 위 값으로 채운다"""
    rows = []
    for page, index, cols in pieces:
        table = doc[page - 1].find_tables().tables[index]
        last = [None] * len(cols)
        for raw in table.extract():
            values = [number(raw[c]) for c in cols]
            texts = [(raw[c] or "").strip() for c in cols]
            row_text = " ".join((c or "").strip() for c in raw).strip()
            if all(v is None for v in values):
                if any(texts) or not row_text or re.match(r"\d\)", row_text):
                    continue                              # 머리줄, 빈 줄, 표 아래 각주
                # 숫자 칸이 전부 병합된 행(예: Peak bulkheads)은 아래에서 위 값으로 채운다
            filled = [v if v is not None else last[i] for i, v in enumerate(values)]
            if any(v is None for v in filled):
                continue
            last = filled
            rows.append(filled)
    return rows


def same(a, b):
    if isinstance(a, tuple) or isinstance(b, tuple):
        return isinstance(a, tuple) and isinstance(b, tuple) and len(a) == len(b) and all(abs(x - y) < 1e-9 for x, y in zip(a, b))
    return a is not None and b is not None and abs(a - b) < 1e-9


TABLES = {
    "material_factor": [{
        "title": "Table 2 Material factor k", "pages": [(86, 1, [0, 1]), (87, 0, [0, 1])],
        "columns": ["R_eH", "k"],
        "labels": ["235", "315", "355", "390", "460"],
        "code": [[235, 1.00], [315, 0.78], [355, 0.72], [390, (0.66, 0.68)], [460, 0.62]],
        "code_note": "코드: k_from_reh() 안의 보간 표. 390은 피로 평가 시 0.66, 아니면 0.68",
    }],
    "min_plate_thickness": [{
        "title": "Table 1 Minimum net thickness for plating", "pages": [(315, 0, [3, 4])],
        "columns": ["a", "b"],
        "labels": [v[2] for v in hull.MIN_T_TABLE.values()],
        "code": [[v[0], v[1]] for v in hull.MIN_T_TABLE.values()],
        "code_note": "코드: MIN_T_TABLE",
    }],
    "plate_lateral_pressure": [{
        "title": "Table 1 Plating, definition of beta_a, alpha_a and C_a-max", "pages": [(319, 0, [3, 4, 5])],
        "columns": ["beta_a", "alpha_a", "C_a-max"],
        "labels": list(hull.PLATE_MEMBERS.values()),
        "code": [list(v) for v in hull.PLATE_TABLE.values()],
        "code_note": "코드: PLATE_TABLE",
    }],
    "stiffener_section_modulus": [{
        "title": "Table 4 Stiffeners, definition of beta_s, alpha_s and C_s-max",
        "pages": [(329, 1, [2, 3, 4]), (330, 0, [3, 4, 5])],
        "columns": ["beta_s", "alpha_s", "C_s-max"],
        "labels": list(hull.STIFF_MEMBERS.values()),
        "code": [list(v) for v in hull.STIFF_TABLE.values()],
        "code_note": "코드: STIFF_TABLE",
    }, {
        "title": "Table 5 Stiffeners, definition of f_bdg and f_m (행: f_bdg, f_m AC-I, f_m AC-II/III)",
        "pages": [(330, 1, [2, 3, 4])],
        "columns": ["fixed, horizontal", "fixed, lower end of vertical", "one fixed + one simple"],
        "labels": ["f_bdg", "f_m (AC-I)", "f_m (AC-II, AC-III)"],
        "code": [[v[i] for v in list(hull.END_TABLE.values())[:3]] for i in range(3)],
        "code_note": "코드: END_TABLE (simply supported 열은 f_bdg 8.00, f_m 없음: 눈으로 확인)",
    }],
}


def table_check(doc, spec):
    try:
        pdf = pdf_rows(doc, spec["pages"])
    except Exception as error:                          # 표 인식 실패
        pdf, spec = [], {**spec, "error": f"{type(error).__name__}: {error}"}
    rows, ok = [], len(pdf) == len(spec["code"])
    for i, code in enumerate(spec["code"]):
        got = pdf[i] if i < len(pdf) else None
        match = got is not None and all(same(c, g) for c, g in zip(code, got))
        ok = ok and match
        rows.append({"label": spec["labels"][i], "code": code, "pdf": got, "match": match})
    return {"title": spec["title"], "columns": spec["columns"], "rows": rows, "ok": ok,
            "count": (len(pdf), len(spec["code"])), "note": spec["code_note"], "error": spec.get("error")}


# ------------------------------------------------------------------ 공식별 내용
SECTIONS = [
    {
        "id": "material_factor", "pages": [86, 87],
        "latex": [r"k = \text{Table 2},\quad \text{intermediate } R_{eH}\text{: linear interpolation}"],
        "example": ("material_factor", {"reh": 335}),
        "hand": "335는 315와 355 사이: 0.78 + (0.72 - 0.78) x 20/40 = 0.75",
        "checks": ["표 값 5개 (235, 315, 355, 390, 460)", "390의 0.66/0.68 구분 조건 (각주 1)", "중간 값은 선형 보간",
                   "적용 범위 235~460 N/mm2 (460 초과는 case-by-case, 2.1.5)"],
    },
    {
        "id": "min_plate_thickness", "pages": [315, 28],
        "latex": [r"t = a + b\,L_2\sqrt{k}\quad[\text{mm, net}]", r"L_2 = \min(L,\ 300)"],
        "example": ("min_plate_thickness", {"location": "shell_bottom", "length": 200, "reh": 355}),
        "hand": "4.5 + 0.035 x 200 x sqrt(0.72) = 4.5 + 5.9397 = 10.44 mm",
        "checks": ["식 구조: a + b L2 sqrt(k)", "L2 정의: L, 단 300 m 초과 안 함 (Ch.1 Sec.4 Table 2)",
                   "Table 1의 위치별 a, b 16행", "병합 칸(a = 4.0, 4.5, 5.0) 적용 범위", "알루미늄은 k = 1 (코드 미반영, 강재만 다룸)"],
    },
    {
        "id": "plate_lateral_pressure", "pages": [318, 319],
        "latex": [r"t = 0.0158\,\alpha_p\,b\sqrt{\dfrac{|P|}{C_a R_{eH}}}\quad[\text{mm, net}]",
                  r"\alpha_p = 1.2 - \dfrac{b}{2.1\,a}\ \le 1.0",
                  r"C_a = \beta_a - \alpha_a\dfrac{|\sigma_{hg}|}{R_{eH}}\ \le C_{a\text{-}max}"],
        "example": ("plate_lateral_pressure", {"pressure": 100, "panel_length": 2400, "panel_breadth": 800, "reh": 235}),
        "hand": "alpha_p = min(1.2 - 800/5040, 1) = 1.0, C_a = min(0.90, 0.80) = 0.80, t = 0.0158 x 800 x sqrt(100/188) = 9.219 mm",
        "checks": ["상수 0.0158", "제곱근 안: |P| / (C_a R_eH)", "alpha_p = 1.2 - b/(2.1a), 상한 1.0",
                   "C_a 식과 상한 C_a-max", "Table 1의 15행 (beta_a, alpha_a, C_a-max)", "단위: P kN/m2, a·b mm, R_eH N/mm2"],
    },
    {
        "id": "stiffener_section_modulus", "pages": [329, 330, 32],
        "latex": [r"Z = \dfrac{f_u\,|P|\,s\,\ell_{bdg}^2}{f_{bdg}\,C_s\,R_{eH}}\quad[\text{cm}^3,\text{ net}]",
                  r"f_u = 1.00\ (\text{flat, T}),\ 1.03\ (\text{bulb}),\ 1.15\ (\text{L})"],
        "cs_logic": [
            ["한 끝 이상 고정", "인장 (+)", "보강재 쪽", "beta_s - alpha_s |sigma_hg| / R_eH (상한 C_s-max)"],
            ["한 끝 이상 고정", "압축 (-)", "판 쪽", "beta_s - alpha_s |sigma_hg| / R_eH (상한 C_s-max)"],
            ["한 끝 이상 고정", "인장 (+)", "판 쪽", "f_m (beta_s - alpha_s |sigma_hg| / R_eH) (상한 C_s-max)"],
            ["한 끝 이상 고정", "압축 (-)", "보강재 쪽", "f_m (beta_s - alpha_s |sigma_hg| / R_eH) (상한 C_s-max)"],
            ["양 끝 단순 지지", "인장 (+)", "판 쪽", "beta_s - alpha_s |sigma_hg| / R_eH (상한 C_s-max)"],
            ["양 끝 단순 지지", "압축 (-)", "보강재 쪽", "beta_s - alpha_s |sigma_hg| / R_eH (상한 C_s-max)"],
            ["양 끝 단순 지지", "인장 (+)", "보강재 쪽", "C_s-max"],
            ["양 끝 단순 지지", "압축 (-)", "판 쪽", "C_s-max"],
        ],
        "example": ("stiffener_section_modulus", {"pressure": 100, "spacing": 800, "span": 3.0, "reh": 355}),
        "hand": "고정 끝, 인장(0), 판 쪽 압력: C_s = min(2.0 x 0.95, 0.85) = 0.85, Z = 100 x 800 x 9 / (12 x 0.85 x 355) = 198.8 cm3",
        "checks": ["식 구조: f_u |P| s l^2 / (f_bdg C_s R_eH)", "f_u 세 값", "Table 3의 C_s 8가지 경우 (위 표와 PDF 대조)",
                   "Table 4의 8행", "Table 5의 f_bdg, f_m (단순 지지 열 포함)", "단위: s mm, l_bdg m (Ch.1 Sec.4 Table 5)"],
    },
    {
        "id": "hull_girder_min_modulus", "pages": [285, 209, 202, 203],
        "latex": [r"Z_{R\text{-}gr} = k\left(\dfrac{1+f_r}{2}\right)C_{w0}\,L^2B\,(C_B+0.7)\,10^{-6}\quad[\text{m}^3,\text{ gross}]",
                  r"C_{w0} = C_w\ (L>90),\qquad 5.7 + 0.0222L\ (L\le 90)",
                  r"C_w = \begin{cases}0.0856L & L<90\\ 10.75-\left(\frac{300-L}{100}\right)^{1.5} & 90\le L\le300\\ 10.75 & 300<L\le350\\ 10.75-\left(\frac{L-350}{150}\right)^{1.5} & 350<L\le500\end{cases}",
                  r"f_r = 1.0\,(R0),\ 0.9\,(R1),\ 0.8\,(R2),\ 0.7\,(R3),\ 0.6\,(R4),\ 0.5\,(RE)"],
        "example": ("hull_girder_min_modulus", {"length": 200, "breadth": 32, "block_coefficient": 0.8, "reh": 235}),
        "hand": "C_w = 10.75 - 1 = 9.75, Z = 1 x 1 x 9.75 x 40000 x 32 x 1.5 x 10^-6 = 18.72 m3",
        "checks": ["식 구조와 10^-6", "(1 + f_r)/2 항", "C_w0의 L 90 m 기준 분기", "C_w 네 구간 (Ch.4 Sec.4)",
                   "f_r 여섯 값 (Ch.4 Sec.3, 다음 쪽까지)", "k는 갑판·선저 부재 재료 기준 ([1.1.2])"],
    },
    {
        "id": "hull_girder_min_inertia", "pages": [285, 209, 202],
        "latex": [r"I_{yR\text{-}gr} = 3\,f_r\,C_w\,L^3B\,(C_B+0.7)\,10^{-8}\quad[\text{m}^4,\text{ gross}]"],
        "example": ("hull_girder_min_inertia", {"length": 200, "breadth": 32, "block_coefficient": 0.8}),
        "hand": "3 x 1 x 9.75 x 8,000,000 x 32 x 1.5 x 10^-8 = 112.3 m4",
        "checks": ["식 구조와 10^-8, 계수 3", "C_w0가 아니라 C_w 사용", "f_r이 (1+f_r)/2가 아니라 그대로 곱해짐",
                   "적용 범위: 자항선, L > 90 m ([1.5.1])"],
    },
]


# ------------------------------------------------------------------ HTML
def esc(value):
    return html.escape(str(value))


def show(value):
    if value is None:
        return "-"
    if isinstance(value, tuple):
        return "/".join(fmt(v) for v in value)
    return fmt(value)


def render_table_check(check):
    head = "".join(f"<th>{esc(c)} 코드</th><th>{esc(c)} PDF</th>" for c in check["columns"])
    body = []
    for row in check["rows"]:
        cells = "".join(f"<td>{show(c)}</td><td>{show(row['pdf'][i] if row['pdf'] else None)}</td>"
                        for i, c in enumerate(row["code"]))
        mark = '<td class="ok">일치</td>' if row["match"] else '<td class="bad">불일치</td>'
        body.append(f"<tr><td class='label'>{esc(row['label'])}</td>{cells}{mark}</tr>")
    status = ("자동 대조 일치" if check["ok"] else "자동 대조 불일치 또는 인식 실패: 눈으로 확인 필요")
    extra = f"<p class='bad'>{esc(check['error'])}</p>" if check["error"] else ""
    return (f"<h4>{esc(check['title'])}</h4><p class='{'ok' if check['ok'] else 'bad'}'>{status} "
            f"(PDF {check['count'][0]}행 / 코드 {check['count'][1]}행)</p>{extra}<p class='muted'>{esc(check['note'])}</p>"
            f"<div class='scroll'><table><tr><th>행</th>{head}<th>결과</th></tr>{''.join(body)}</table></div>")


def render_section(section, checks):
    formula = hull.FORMULAS[section["id"]]
    result = calculate(section["example"][0], **section["example"][1])
    pages = "".join(f"<figure><img src='pages/p3_{p}.png' alt='Pt.3 PDF page {p}' loading='lazy'>"
                    f"<figcaption>PDF {p}쪽</figcaption></figure>" for p in section["pages"])
    latex = "".join(f"<div class='math'>$${line}$$</div>" for line in section["latex"])
    cs = ""
    if "cs_logic" in section:
        rows = "".join("<tr>" + "".join(f"<td>{esc(c)}</td>" for c in r) + "</tr>" for r in section["cs_logic"])
        cs = ("<h4>Table 3 C_s 경우 나누기 (코드 구현 그대로)</h4><div class='scroll'><table>"
              "<tr><th>끝단</th><th>선체 응력</th><th>압력 쪽</th><th>C_s</th></tr>" + rows + "</table></div>")
    tables = "".join(render_table_check(c) for c in checks)
    steps = "".join(f"<tr><td>{esc(s.symbol)}</td><td>{esc(s.expression)}</td><td>{esc(s.substituted)}</td>"
                    f"<td><b>{fmt(s.value)}</b> {esc(s.unit if s.unit != '-' else '')}</td></tr>" for s in result.steps)
    inputs = ", ".join(f"{k} = {v}" for k, v in section["example"][1].items())
    code = esc(inspect.getsource(formula.run))
    items = "".join(f"<label class='check'><input type='checkbox' data-key='{section['id']}:{i}'> {esc(text)}</label>"
                    for i, text in enumerate(section["checks"]))
    return f"""
<section id="{section['id']}" data-title="{esc(formula.title)}">
  <h2>{esc(formula.title)} <span class="ref">{esc(formula.ref)}</span></h2>
  <div class="grid">
    <div class="pdf">{pages}</div>
    <div class="side">
      <h3>코드에 옮긴 수식</h3>{latex}{cs}
      <h3>코드의 표 값과 PDF 표 자동 대조</h3>{tables or "<p class='muted'>표 없음</p>"}
      <h3>예제 계산</h3>
      <p class="muted">입력: {esc(inputs)}</p>
      <div class="scroll"><table><tr><th>단계</th><th>식</th><th>대입</th><th>값</th></tr>{steps}</table></div>
      <p>손계산: {esc(section['hand'])}</p>
      <details><summary>파이썬 코드 보기</summary><pre>{code}</pre></details>
      <h3>확인 항목</h3>
      <div class="checks">{items}</div>
      <label class="memo">메모 (틀린 곳, 의문점)<textarea data-key="{section['id']}:memo" rows="3"></textarea></label>
    </div>
  </div>
</section>"""


PAGE = """<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>DNV 공식 검증표</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9/katex.min.css">
<script defer src="https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9/katex.min.js"></script>
<script defer src="https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9/contrib/auto-render.min.js"
  onload="renderMathInElement(document.body)"></script>
<style>
:root { --bg:#f7f7f5; --card:#fff; --ink:#1d1d1f; --muted:#6b6b70; --line:#dedee3; --ok:#1f7a3f; --bad:#b3261e; --accent:#0b5cad; }
@media (prefers-color-scheme: dark) { :root { --bg:#151517; --card:#1f1f22; --ink:#ececf0; --muted:#a0a0a8; --line:#34343a; --ok:#5cc985; --bad:#ff8a80; --accent:#7fb4ff; } }
* { box-sizing:border-box; }
body { margin:0; background:var(--bg); color:var(--ink); font:15px/1.55 system-ui, -apple-system, "Malgun Gothic", sans-serif; }
header { position:sticky; top:0; z-index:5; background:var(--card); border-bottom:1px solid var(--line); padding:12px 20px; display:flex; flex-wrap:wrap; gap:12px; align-items:center; }
header h1 { font-size:18px; margin:0 12px 0 0; }
header nav a { color:var(--accent); margin-right:10px; text-decoration:none; font-size:14px; }
header .right { margin-left:auto; display:flex; gap:10px; align-items:center; }
button { background:var(--accent); color:#fff; border:0; border-radius:6px; padding:7px 12px; cursor:pointer; font:inherit; }
main { max-width:1500px; margin:0 auto; padding:16px 20px 60px; }
.intro { background:var(--card); border:1px solid var(--line); border-radius:10px; padding:14px 18px; }
section { background:var(--card); border:1px solid var(--line); border-radius:10px; padding:16px 18px; margin-top:18px; }
h2 { margin:0 0 10px; font-size:20px; } h3 { margin:18px 0 8px; font-size:16px; } h4 { margin:12px 0 4px; font-size:14px; }
.ref { font-size:13px; color:var(--muted); font-weight:normal; margin-left:8px; }
.grid { display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1fr); gap:20px; }
@media (max-width: 1000px) { .grid { grid-template-columns:1fr; } }
.pdf { max-height:85vh; overflow:auto; border:1px solid var(--line); border-radius:8px; padding:8px; background:#fff; }
.pdf img { width:100%; display:block; } .pdf figcaption { color:#555; font-size:12px; text-align:center; margin:4px 0 14px; }
.math { overflow-x:auto; }
.scroll { overflow-x:auto; }
table { border-collapse:collapse; width:100%; font-size:13px; }
th, td { border:1px solid var(--line); padding:4px 6px; text-align:left; vertical-align:top; }
th { background:color-mix(in srgb, var(--line) 40%, transparent); }
td.label { max-width:320px; }
td.ok, td.bad { white-space:nowrap; } section { scroll-margin-top:110px; }
.ok { color:var(--ok); font-weight:600; } .bad { color:var(--bad); font-weight:600; } .muted { color:var(--muted); font-size:13px; }
pre { background:color-mix(in srgb, var(--line) 30%, transparent); padding:10px; border-radius:6px; overflow:auto; font-size:12px; max-height:420px; }
.check { display:block; padding:3px 0; } .check input { margin-right:6px; }
.memo { display:block; margin-top:8px; font-size:13px; color:var(--muted); }
textarea { width:100%; margin-top:4px; font:inherit; color:var(--ink); background:var(--bg); border:1px solid var(--line); border-radius:6px; padding:6px; }
</style></head><body>
<header><h1>DNV 공식 검증표</h1><nav>__NAV__</nav>
<div class="right"><span id="progress"></span><button id="copy">결과 복사</button></div></header>
<main>
<div class="intro">
<p><b>무엇을 확인하나:</b> 왼쪽 규정 원문과 오른쪽 코드 내용이 같은지 공식마다 확인 항목을 체크한다. 틀린 곳은 메모에 적는다.</p>
<p><b>자동 대조:</b> 표 값은 PDF 표를 프로그램으로 추출해 코드 값과 비교했다. 일치해도 표 인식 자체가 틀릴 수 있으니 원문과 한 번 더 본다. 수식(이미지)은 자동 대조가 안 되므로 눈으로만 확인한다.</p>
<p class="muted">체크와 메모는 이 브라우저에만 저장된다. 다 보면 "결과 복사"를 눌러 붙여 넣는다. 원본: __SOURCE__, 생성: python verify/build_sheet.py</p>
</div>
__SECTIONS__
</main>
<script>
const KEY = "dnv-verify-v1";
let saved = {};
try { saved = JSON.parse(localStorage.getItem(KEY) || "{}"); } catch (e) {}
const inputs = [...document.querySelectorAll("[data-key]")];
inputs.forEach(el => {
  const v = saved[el.dataset.key];
  if (el.type === "checkbox") el.checked = !!v; else if (v) el.value = v;
  el.addEventListener("input", () => {
    saved[el.dataset.key] = el.type === "checkbox" ? el.checked : el.value;
    try { localStorage.setItem(KEY, JSON.stringify(saved)); } catch (e) {}
    progress();
  });
});
function progress() {
  const boxes = inputs.filter(el => el.type === "checkbox");
  document.getElementById("progress").textContent = `확인 ${boxes.filter(b => b.checked).length} / ${boxes.length}`;
}
progress();
document.getElementById("copy").addEventListener("click", async () => {
  const lines = ["공식 검증 결과"];
  document.querySelectorAll("section").forEach(sec => {
    lines.push("", `[${sec.dataset.title}]`);
    sec.querySelectorAll(".check").forEach(label => {
      const box = label.querySelector("input");
      lines.push(`${box.checked ? "확인" : "미확인"}: ${label.textContent.trim()}`);
    });
    const memo = sec.querySelector("textarea").value.trim();
    if (memo) lines.push(`메모: ${memo}`);
  });
  const text = lines.join("\\n");
  try { await navigator.clipboard.writeText(text); alert("복사했습니다. 대화창에 붙여 넣으세요."); }
  catch (e) { prompt("복사가 막혀 있으면 아래 내용을 직접 복사하세요", text); }
});
</script></body></html>"""


def main():
    import pymupdf
    doc = pymupdf.open(PDF)
    PAGES.mkdir(exist_ok=True)
    for page in sorted({p for s in SECTIONS for p in s["pages"]}):
        target = PAGES / f"p3_{page}.png"
        if not target.exists():
            doc[page - 1].get_pixmap(dpi=DPI).save(target)
    checks = {fid: [table_check(doc, spec) for spec in specs] for fid, specs in TABLES.items()}
    sections = "".join(render_section(s, checks.get(s["id"], [])) for s in SECTIONS)
    nav = "".join(f"<a href='#{s['id']}'>{esc(hull.FORMULAS[s['id']].title)}</a>" for s in SECTIONS)
    page = (PAGE.replace("__NAV__", nav).replace("__SECTIONS__", sections)
            .replace("__SOURCE__", esc(PDF.name)))
    OUT.write_text(page, encoding="utf-8")
    summary = {fid: [c["ok"] for c in cs] for fid, cs in checks.items()}
    print("표 자동 대조:", json.dumps(summary, ensure_ascii=False))
    print(f"저장: {OUT}")


if __name__ == "__main__":
    main()
