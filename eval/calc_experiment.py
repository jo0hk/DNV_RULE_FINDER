"""
eval/calc_experiment.py — 계산 문제 세트로 계산 방식별 정확도 비교

    A  : 규정 발췌문(공식 빠진 원래 chunk)을 보고 LLM이 직접 계산
    B  : 공식을 텍스트로 붙인 발췌문을 보고 LLM이 직접 계산
    B2 : B와 같은 발췌문을 보고 LLM이 파이썬 코드를 써서 계산 (코드는 이 컴퓨터에서 실행)
    C  : LLM은 함수 선택과 입력값 추출만, 계산은 검증한 파이썬 공식 엔진 (calc.py)

    A, B, B2에는 공식 6개에 필요한 발췌문을 모두 준다(eval/formula_context.py). 검색 오류의 영향은 빼고
    "계산을 누가, 무엇을 보고 하느냐"의 차이만 본다. 모델은 서비스와 같은 LLM(.env 설정)이다.

    채점
      값 문제:   정답과 상대오차 1% 이내면 맞음. 근거 조항(공식 선택)이 맞았는지도 따로 기록
      거부 문제: 계산하지 않고 거부하면 맞음 (숫자를 내놓으면 "지어낸 값")

실행:  python eval/calc_experiment.py --condition A --runs 3
결과:  eval/results/calc_<조건>.md, .json
"""
import argparse
import json
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EVAL_DIR.parent))
from formulas import FORMULAS  # noqa: E402
from formulas.core import fmt  # noqa: E402

QUESTIONS = EVAL_DIR / "calc_questions.jsonl"
UNITS = ("Give the result in the unit the rule formula produces: k without unit, plate thickness in mm, "
         "stiffener section modulus in cm3, hull girder section modulus in m3, moment of inertia in m4.")

DIRECT_PROMPT = f"""You are a ship structural engineer applying DNV rules for classification of ships.
Answer the user's calculation request using the DNV rule excerpts below. Do the calculation yourself.
If a required input is not given, or the request is outside the rule's applicable range, do not calculate: refuse.
{UNITS}

Answer with JSON only:
{{"value": <number or null>, "unit": "<unit>", "clause": "<rule clause of the formula you used>",
  "refuse": <true or false>, "reason": "<short reason if refused>"}}

DNV rule excerpts:
"""

CODE_PROMPT = f"""You are a ship structural engineer applying DNV rules for classification of ships.
For the user's calculation request, write a short Python program that computes the answer from the DNV rule excerpts below.
The program may import only the math and json modules and must end by printing exactly one line of JSON with json.dumps:
{{"value": <number>, "unit": "<unit>", "clause": "<rule clause of the formula used>"}}
If a required input is not given, or the request is outside the rule's applicable range, do not write code;
answer with one line: REFUSE: <short reason>
{UNITS}

Answer with only the program in one ```python code block, or the REFUSE line.

DNV rule excerpts:
"""


def parse_json(text):
    match = re.search(r"\{.*\}", text or "", re.S)
    if not match:
        raise ValueError(f"no JSON in answer: {str(text)[:200]!r}")
    return json.loads(match.group(0))


def as_number(value):
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


# ------------------------------------------------------------------ 조건별 실행
_context = {}


def context(kind):
    if kind not in _context:
        import formula_context
        _context[kind] = formula_context.load(kind)
    return _context[kind]


def run_direct(question, kind):
    from llm import chat
    answer = parse_json(chat(DIRECT_PROMPT + context(kind), question["question"]))
    value = None if answer.get("refuse") else as_number(answer.get("value"))
    return {"status": "calculated" if value is not None else "refused", "value": value,
            "clause": str(answer.get("clause") or ""), "reason": answer.get("reason"), "raw": answer}


FORBIDDEN = {"os", "sys", "subprocess", "socket", "shutil", "pathlib", "urllib", "requests",
             "open", "eval", "exec", "compile", "__import__", "input", "globals", "getattr", "setattr", "__builtins__"}


def safety_check(code):
    """코드를 문법 트리로 읽어 검사한다 (주석과 문자열 속 단어는 보지 않는다).
    math, json 외 import와 파일·프로세스·네트워크·동적 실행 관련 이름을 쓰면 실행하지 않는다"""
    import ast
    tree = ast.parse(code)
    modules, names = set(), set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules |= {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom):
            modules.add((node.module or "").split(".")[0])
        elif isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
    bad = (modules - {"math", "json"}) | (names & FORBIDDEN)
    if bad:
        raise ValueError(f"code rejected by safety check: {sorted(bad)}")


def execute(code):
    """LLM이 쓴 코드를 안전 검사 후 별도 프로세스에서 실행한다 (10초 제한, 임시 폴더)"""
    safety_check(code)
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "llm_code.py"
        path.write_text(code, encoding="utf-8")
        done = subprocess.run([sys.executable, "-I", str(path)], cwd=folder, capture_output=True, text=True, timeout=10)
    if done.returncode != 0:
        raise ValueError(f"code failed: {done.stderr.strip()[-300:]}")
    last = done.stdout.strip().splitlines()[-1] if done.stdout.strip() else ""
    if last.lstrip().startswith("REFUSE"):            # 코드 안에서 거부를 출력한 경우
        return {"refuse": last}
    return parse_json(last)


def run_code(question):
    from llm import chat
    text = chat(CODE_PROMPT + context("formula"), question["question"])
    block = re.search(r"```(?:python)?\s*\n(.*?)```", text or "", re.S)
    if not block:
        reason = re.sub(r"^\s*REFUSE:\s*", "", (text or "").strip())[:300]
        return {"status": "refused", "value": None, "clause": "", "reason": reason, "raw": text}
    code = block.group(1)
    if code.lstrip().startswith("REFUSE"):            # 코드 블록 안에 거부 문장만 쓴 경우
        return {"status": "refused", "value": None, "clause": "", "reason": code.strip()[:300], "raw": text}
    try:
        output = execute(code)
    except Exception as error:
        return {"status": "error", "value": None, "clause": "", "reason": str(error), "raw": code}
    value = None if output.get("refuse") else as_number(output.get("value"))
    return {"status": "calculated" if value is not None else "refused", "value": value,
            "clause": str(output.get("clause") or ""), "reason": output.get("refuse"), "raw": code}


def run_engine(question):
    import calc
    out = calc.solve(question["question"])
    record = {"status": out["status"], "value": None, "clause": "", "reason": out.get("reason"),
              "refused_by": out.get("by"), "raw": out["call"]}
    if out["status"] == "calculated":
        record["value"], record["clause"] = out["result"].value, out["result"].ref
    return record


CONDITIONS = {
    "A": ("LLM calculates from rule excerpts as stored (formulas missing)", lambda q: run_direct(q, "plain")),
    "B": ("LLM calculates from rule excerpts with formulas added as text", lambda q: run_direct(q, "formula")),
    "B2": ("LLM writes Python code from rule excerpts with formulas added", run_code),
    "C": ("LLM selects function and inputs, verified Python engine calculates", run_engine),
}


# ------------------------------------------------------------------ 채점
CLAUSE_RE = re.compile(r"Ch\.\s*(\d+)\s*Sec\.\s*(\d+)\s*\[([\d.]+)\]")


def clause_ok(clause, formula_id):
    """답이 밝힌 근거 조항이 정답 공식의 조항과 같은지 (예: [1.1]과 [1.1.1]은 같은 것으로 봄)"""
    expected = CLAUSE_RE.search(FORMULAS[formula_id].ref).groups()
    for ch, sec, num in CLAUSE_RE.findall(clause or ""):
        if (ch, sec) == expected[:2] and (num.startswith(expected[2]) or expected[2].startswith(num)):
            return True
    return False


def score(question, record):
    if question["expected"] == "refuse":
        return {"correct": record["status"] == "refused", "formula_ok": None,
                "fabricated": record.get("value") is not None}
    value, answer = record.get("value"), question["answer"]["value"]
    correct = value is not None and abs(value - answer) <= question["tolerance"] * abs(answer)
    return {"correct": correct, "formula_ok": clause_ok(record.get("clause"), question["formula"]), "fabricated": False}


def run_once(runner, q):
    for attempt in range(5):                       # 서버 혼잡(429/503) 같은 일시 오류만 다시 시도
        started = time.time()
        try:
            record = runner(q)
        except Exception as error:
            record = {"status": "error", "value": None, "clause": "", "reason": f"{type(error).__name__}: {error}", "raw": None}
        record["seconds"] = round(time.time() - started, 2)
        transient = record["status"] == "error" and re.search(r"\b(429|500|503)\b|UNAVAILABLE|RESOURCE_EXHAUSTED", str(record["reason"]))
        if not transient:
            return record
        time.sleep(5 * 2 ** attempt)
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--condition", required=True, choices=list(CONDITIONS))
    parser.add_argument("--runs", type=int, default=3, help="LLM 답이 매번 달라서 여러 번 돌려 평균을 낸다")
    args = parser.parse_args()
    label, runner = CONDITIONS[args.condition]
    questions = [json.loads(line) for line in QUESTIONS.read_text(encoding="utf-8").splitlines() if line.strip()]

    records = []
    for run in range(1, args.runs + 1):
        for q in questions:
            record = run_once(runner, q)
            record.update(run=run, id=q["id"], difficulty=q["difficulty"], **score(q, record))
            records.append(record)
            got = fmt(record["value"]) if record.get("value") is not None else record["status"]
            want = fmt(q["answer"]["value"]) if q["answer"] else "refuse"
            print(f"  run{run} {q['id']} {q['difficulty']:6} {'O' if record['correct'] else 'X'}  got {got:>10}  expected {want}", flush=True)

    levels = ["easy", "medium", "hard", "refuse"]

    def pct(rows, key="correct"):
        return 100 * sum(bool(r[key]) for r in rows) / len(rows) if rows else float("nan")

    per_run = [pct([r for r in records if r["run"] == n]) for n in range(1, args.runs + 1)]
    value_rows = [r for r in records if r["difficulty"] != "refuse"]
    refuse_rows = [r for r in records if r["difficulty"] == "refuse"]
    summary = {
        "condition": args.condition, "label": label, "runs": args.runs, "questions": len(questions),
        "accuracy": pct(records), "accuracy_min": min(per_run), "accuracy_max": max(per_run),
        **{lv: pct([r for r in records if r["difficulty"] == lv]) for lv in levels},
        "clause_ok": pct(value_rows, "formula_ok"),
        "fabricated": sum(r["fabricated"] for r in refuse_rows), "refuse_total": len(refuse_rows),
        "errors": sum(r["status"] == "error" for r in records),
        "seconds": sum(r["seconds"] for r in records) / len(records),
    }
    lines = [f"# 계산 정확도: 조건 {args.condition}", "", f"- 방식: {label}",
             f"- 문제 {len(questions)}개 x {args.runs}회, 정답과 1% 이내면 맞음 (괄호는 회차별 최저~최고)", "",
             "| 전체 | easy | medium | hard | refuse | 근거 조항 정확 | 지어낸 값 | 오류 | 평균 시간(초) |",
             "|---|---|---|---|---|---|---|---|---|",
             f"| {summary['accuracy']:.1f}% ({summary['accuracy_min']:.0f}~{summary['accuracy_max']:.0f}) | " +
             " | ".join(f"{summary[lv]:.1f}%" for lv in levels) +
             f" | {summary['clause_ok']:.1f}% | {summary['fabricated']}/{summary['refuse_total']} | {summary['errors']}"
             f" | {summary['seconds']:.1f} |", "",
             "## 틀린 답", "", "| 회차 | id | 난이도 | 상태 | 받은 값 | 정답 | 근거 조항 / 이유 |", "|---|---|---|---|---|---|---|"]
    answers = {q["id"]: q for q in questions}
    for r in records:
        if not r["correct"]:
            got = fmt(r["value"]) if r.get("value") is not None else "-"
            want = fmt(answers[r["id"]]["answer"]["value"]) if answers[r["id"]]["answer"] else "refuse"
            why = (r.get("clause") or "") + (" / " + str(r["reason"]) if r.get("reason") else "")
            lines.append(f"| {r['run']} | {r['id']} | {r['difficulty']} | {r['status']} | {got} | {want} | {why.replace('|', '/')[:160]} |")
    report = "\n".join(lines) + "\n"
    out = EVAL_DIR / "results"
    out.mkdir(exist_ok=True)
    (out / f"calc_{args.condition}.md").write_text(report, encoding="utf-8")
    (out / f"calc_{args.condition}.json").write_text(json.dumps({"summary": summary, "records": records},
                                                                ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
