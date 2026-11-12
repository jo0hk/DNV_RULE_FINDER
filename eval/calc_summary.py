"""
eval/calc_summary.py — 계산 비교 실험(A, B, B2, C) 결과를 표 하나와 그래프 두 장으로 정리

    입력: eval/results/calc_<조건>.json  (calc_experiment.py 결과)
    출력: eval/results/calc_summary.md, calc_accuracy.svg, calc_by_difficulty.svg

실행:  python eval/calc_summary.py
"""
import json
from pathlib import Path

RESULTS = Path(__file__).resolve().parent / "results"
ORDER = ["A", "B", "B2", "C"]
NAMES = {"A": "A  LLM, chunk as stored", "B": "B  LLM, formula text added",
         "B2": "B2 LLM writes Python", "C": "C  LLM picks, engine calculates"}
LEVELS = ["easy", "medium", "hard", "refuse"]

# 색: 기준 팔레트(밝은 화면) 범주형 1~4번을 고정 순서로 사용
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
SERIES = {"A": "#2a78d6", "B": "#eb6834", "B2": "#1baf7a", "C": "#eda100"}
FONT = "font-family='system-ui, -apple-system, Segoe UI, Malgun Gothic, sans-serif'"


def load():
    data = {}
    for c in ORDER:
        path = RESULTS / f"calc_{c}.json"
        if path.exists():
            data[c] = json.loads(path.read_text(encoding="utf-8"))["summary"]
    return data


def accuracy_svg(data):
    """조건별 전체 정확도: 가로 막대 하나씩 (계열 하나라 범례 없이 제목이 이름 역할)"""
    width, left, right, row, top = 760, 250, 110, 46, 66
    height = top + row * len(data) + 40
    plot = width - left - right
    out = [f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {width} {height}' width='{width}' height='{height}' {FONT}>",
           f"<rect width='100%' height='100%' fill='{SURFACE}'/>",
           f"<text x='16' y='28' font-size='16' font-weight='600' fill='{INK}'>Calculation accuracy by method (28 questions x 3 runs)</text>"]
    for tick in range(0, 101, 25):
        x = left + plot * tick / 100
        out.append(f"<line x1='{x}' y1='{top - 8}' x2='{x}' y2='{height - 34}' stroke='{GRID}' stroke-width='1'/>")
        out.append(f"<text x='{x}' y='{height - 16}' font-size='12' fill='{INK2}' text-anchor='middle'>{tick}%</text>")
    for i, c in enumerate(data):
        s = data[c]
        y = top + i * row
        w = max(plot * s["accuracy"] / 100, 2)
        lo, hi = left + plot * s["accuracy_min"] / 100, left + plot * s["accuracy_max"] / 100
        out.append(f"<text x='{left - 12}' y='{y + 19}' font-size='13' fill='{INK}' text-anchor='end'>{NAMES[c]}</text>")
        out.append(f"<path d='M{left},{y + 6} h{w - 4} a4,4 0 0 1 4,4 v12 a4,4 0 0 1 -4,4 h-{w - 4} z' fill='{SERIES['A']}'>"
                   f"<title>{NAMES[c]}: {s['accuracy']:.1f}% (runs {s['accuracy_min']:.0f}-{s['accuracy_max']:.0f}%)</title></path>")
        if hi > lo:
            out.append(f"<line x1='{lo}' y1='{y + 16}' x2='{hi}' y2='{y + 16}' stroke='{INK}' stroke-width='2'/>")
        label_x = max(left + w, hi) + 10                            # 범위 선과 겹치지 않게
        out.append(f"<text x='{label_x}' y='{y + 20}' font-size='13' fill='{INK}'>{s['accuracy']:.1f}%</text>")
    out.append(f"<text x='16' y='46' font-size='11' fill='{INK2}'>Bar: mean of 3 runs. Black line: lowest to highest run.</text>")
    out.append("</svg>")
    return "\n".join(out)


def difficulty_svg(data):
    """난이도별 정확도: 난이도 묶음마다 조건 4개 막대 (범례 + 표로 숫자 제공)"""
    width, height, left, top, bottom = 760, 360, 56, 70, 50
    plot_w, plot_h = width - left - 20, height - top - bottom
    group = plot_w / len(LEVELS)
    bar, gap = 26, 2
    conds = list(data)
    out = [f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {width} {height}' width='{width}' height='{height}' {FONT}>",
           f"<rect width='100%' height='100%' fill='{SURFACE}'/>",
           f"<text x='16' y='28' font-size='16' font-weight='600' fill='{INK}'>Accuracy by question difficulty</text>"]
    for i, c in enumerate(conds):                                  # 범례 (한 줄, 그래프 위)
        x = 16 + i * 180
        out.append(f"<rect x='{x}' y='42' width='12' height='12' rx='3' fill='{SERIES[c]}'/>")
        out.append(f"<text x='{x + 18}' y='52' font-size='12' fill='{INK}'>{NAMES[c]}</text>")
    for tick in range(0, 101, 25):
        y = top + plot_h * (1 - tick / 100)
        out.append(f"<line x1='{left}' y1='{y}' x2='{width - 20}' y2='{y}' stroke='{GRID}' stroke-width='1'/>")
        out.append(f"<text x='{left - 8}' y='{y + 4}' font-size='12' fill='{INK2}' text-anchor='end'>{tick}%</text>")
    for g, level in enumerate(LEVELS):
        start = left + g * group + (group - len(conds) * (bar + gap)) / 2
        for i, c in enumerate(conds):
            value = data[c][level]
            h = max(plot_h * value / 100, 2)
            x, y = start + i * (bar + gap), top + plot_h - h
            out.append(f"<path d='M{x},{top + plot_h} v-{h - 4} a4,4 0 0 1 4,-4 h{bar - 8} a4,4 0 0 1 4,4 v{h - 4} z' fill='{SERIES[c]}'>"
                       f"<title>{NAMES[c]}, {level}: {value:.1f}%</title></path>")
        out.append(f"<text x='{left + g * group + group / 2}' y='{top + plot_h + 22}' font-size='13' fill='{INK}' text-anchor='middle'>{level}</text>")
    out.append("</svg>")
    return "\n".join(out)


def main():
    data = load()
    if not data:
        raise SystemExit("eval/results/calc_*.json 이 없습니다. calc_experiment.py를 먼저 실행하세요.")
    (RESULTS / "calc_accuracy.svg").write_text(accuracy_svg(data), encoding="utf-8")
    (RESULTS / "calc_by_difficulty.svg").write_text(difficulty_svg(data), encoding="utf-8")
    runs = next(iter(data.values()))["runs"]
    lines = ["# 계산 방식 비교", "",
             f"- 계산 문제 28개(eval/calc_questions.jsonl) x {runs}회, 정답과 1% 이내면 맞음",
             "- A, B, B2에는 공식 6개에 필요한 규정 발췌문 15개를 모두 줬다 (검색 오류의 영향 제외)",
             "- 거부 문제 4개: 값이 빠졌거나 적용 범위 밖이라 계산하면 안 되는 문제", "",
             "| 조건 | 방식 | 전체 (회차 최저~최고) | easy | medium | hard | refuse | 근거 조항 정확 | 지어낸 값 | 오류 | 평균 시간(초) |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for c, s in data.items():
        lines.append(f"| {c} | {s['label']} | {s['accuracy']:.1f}% ({s['accuracy_min']:.0f}~{s['accuracy_max']:.0f}) | " +
                     " | ".join(f"{s[lv]:.1f}%" for lv in LEVELS) +
                     f" | {s['clause_ok']:.1f}% | {s['fabricated']}/{s['refuse_total']} | {s['errors']} | {s['seconds']:.1f} |")
    lines += ["", "![조건별 정확도](calc_accuracy.svg)", "", "![난이도별 정확도](calc_by_difficulty.svg)", ""]
    (RESULTS / "calc_summary.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
