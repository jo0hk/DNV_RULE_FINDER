"""
eval/calc_experiment.py — 계산 문제 세트로 계산 방식별 정확도 비교

    조건 C: LLM은 함수 선택과 입력값 추출만, 계산은 파이썬 공식 엔진 (calc.py)
    (조건 A, B, B2 등 LLM이 직접 계산하는 방식은 다음 단계에서 이 파일에 추가한다)

    채점
      값 문제:   정답과 상대오차 1% 이내면 맞음. 공식 선택이 맞았는지도 따로 기록
      거부 문제: 계산하지 않고 거부하면 맞음 (숫자를 내놓으면 지어낸 것으로 봄)

실행:  python eval/calc_experiment.py --condition C
결과:  eval/results/calc_<조건>.md, .json
"""
import argparse
import json
import sys
import time
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EVAL_DIR.parent))
from formulas.core import fmt  # noqa: E402

QUESTIONS = EVAL_DIR / "calc_questions.jsonl"


def run_c(question):
    import calc
    out = calc.solve(question["question"])
    record = {"status": out["status"], "seconds": round(out["seconds"], 2), "call": out["call"],
              "reason": out.get("reason"), "refused_by": out.get("by")}
    if out["status"] == "calculated":
        record["value"], record["formula"] = out["result"].value, out["result"].formula
    return record


CONDITIONS = {"C": ("LLM selects function and inputs, Python engine calculates", run_c)}


def score(question, record):
    if question["expected"] == "refuse":
        correct = record["status"] == "refused"
        return {"correct": correct, "formula_ok": None, "fabricated": record.get("value") is not None}
    value = record.get("value")
    answer = question["answer"]["value"]
    correct = value is not None and abs(value - answer) <= question["tolerance"] * abs(answer)
    return {"correct": correct, "formula_ok": record.get("formula") == question["formula"], "fabricated": False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--condition", default="C", choices=list(CONDITIONS))
    args = parser.parse_args()
    label, runner = CONDITIONS[args.condition]
    questions = [json.loads(line) for line in QUESTIONS.read_text(encoding="utf-8").splitlines() if line.strip()]

    records = []
    for q in questions:
        for attempt in range(4):                    # 서버 혼잡(503) 등 일시 오류만 다시 시도
            record = runner(q)
            if record["status"] != "error" or "503" not in str(record.get("reason")):
                break
            time.sleep(5 * 2 ** attempt)
        record.update(id=q["id"], difficulty=q["difficulty"], **score(q, record))
        records.append(record)
        mark = "O" if record["correct"] else "X"
        got = fmt(record["value"]) if record.get("value") is not None else record["status"]
        want = fmt(q["answer"]["value"]) if q["answer"] else "refuse"
        print(f"  {q['id']} {q['difficulty']:6} {mark}  got {got:>10}  expected {want}", flush=True)

    levels = ["easy", "medium", "hard", "refuse"]
    def rate(rows):
        return f"{sum(r['correct'] for r in rows)}/{len(rows)}" if rows else "-"
    value_rows = [r for r in records if r["difficulty"] != "refuse"]
    lines = [f"# 계산 정확도: 조건 {args.condition}", "", f"- 방식: {label}", f"- 문제 {len(records)}개, 정답과 1% 이내면 맞음", "",
             "| 전체 | " + " | ".join(levels) + " | 공식 선택 정확 | 지어낸 값 | 평균 시간(초) |",
             "|---|" + "---|" * (len(levels) + 3),
             f"| {rate(records)} | " + " | ".join(rate([r for r in records if r['difficulty'] == lv]) for lv in levels) +
             f" | {sum(bool(r['formula_ok']) for r in value_rows)}/{len(value_rows)}"
             f" | {sum(r['fabricated'] for r in records)}"
             f" | {sum(r['seconds'] for r in records) / len(records):.1f} |", "",
             "## 틀린 문제", "", "| id | 난이도 | 상태 | 받은 값 | 이유 / 호출 |", "|---|---|---|---|---|"]
    for r in records:
        if not r["correct"]:
            got = fmt(r["value"]) if r.get("value") is not None else "-"
            lines.append(f"| {r['id']} | {r['difficulty']} | {r['status']} | {got} | {str(r.get('reason') or r['call'])[:200]} |")
    report = "\n".join(lines) + "\n"
    out = EVAL_DIR / "results"
    out.mkdir(exist_ok=True)
    (out / f"calc_{args.condition}.md").write_text(report, encoding="utf-8")
    (out / f"calc_{args.condition}.json").write_text(json.dumps(records, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
