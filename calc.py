"""
calc.py — 문장 속 계산 요청을 공식 엔진(formulas)으로 계산한다

    LLM이 하는 일:  어떤 공식인지 고르고, 문장에서 입력값을 뽑는다 (단위 환산, 강재 등급 → R_eH 포함)
    LLM이 안 하는 일: 숫자 계산. 계산은 반드시 formulas 패키지의 파이썬 함수가 한다.

    공식 6개를 LLM의 "함수(도구)"로 등록하고, 값이 빠졌거나 범위 밖이면 고를 수 있는
    cannot_calculate 함수도 함께 준다. 모델은 이 중 하나를 반드시 호출해야 한다(자유 답변 금지).
    LLM이 고른 값이 규정 적용 범위를 벗어나면 엔진이 다시 한 번 막는다.

실행:  python calc.py "Plate panel 2400 x 800 mm, 100 kN/m2, ReH 235, AC-I longitudinal stiffened, no hull girder stress"
"""
import sys
import time

from formulas import FORMULAS, InputError, calculate
from llm import call_function

REFUSE = "cannot_calculate"

STEEL_GRADES = ("Steel grade to R_eH (Pt.3 Ch.3 Sec.1 Table 1): A, B, D, E = 235; A32, D32, E32, F32 = 315; "
                "A36, D36, E36, F36 = 355; A40, D40, E40, F40 = 390; A47, D47, E47, F47 = 460. "
                "'Mild steel' or 'normal strength steel' = 235.")

SYSTEM_PROMPT = f"""You route ship structural calculation requests to DNV rule calculation functions.
The functions are implemented in Python from DNV-RU-SHIP Pt.3 and do all the arithmetic.

Rules:
- Never calculate anything yourself. Your only job is to call exactly one function with the right inputs.
- Pick the function whose result answers the question. Extract every input from the user's sentence.
- Convert units to the ones in the function description (for example 0.15 N/mm2 = 150 kN/m2, 0.8 m = 800 mm).
- {STEEL_GRADES}
- Hull girder stress: tension is positive, compression is negative. Use 0 only if the user says it is zero,
  none, or not considered.
- If a required input is not given in the sentence, or the request is outside these functions, call
  {REFUSE} and list what is missing. Never invent or assume a value that the user did not give,
  except the defaults stated in a parameter description."""


def tool_schema(formula):
    """formulas 의 입력 정의(Param)를 LLM 함수 호출용 JSON schema로 바꾼다"""
    properties, required = {}, []
    for p in formula.params:
        if p.choices is not None:
            options = "; ".join(f"{k} = {v}" for k, v in p.choices.items())
            properties[p.name] = {"type": "string", "enum": list(p.choices),
                                  "description": f"{p.description}. Options: {options}"}
        else:
            limits = f", range {p.minimum:g} to {p.maximum:g}" if p.minimum is not None else ""
            properties[p.name] = {"type": "number", "description": f"{p.symbol}: {p.description}, in {p.unit}{limits}"}
        if p.default is None:
            required.append(p.name)
        else:
            properties[p.name]["description"] += f". Default if not stated: {p.default}"
    return {"name": formula.id, "description": f"{formula.title} ({formula.ref}). {formula.summary}",
            "parameters": {"type": "object", "properties": properties, "required": required}}


TOOLS = [tool_schema(f) for f in FORMULAS.values()] + [{
    "name": REFUSE,
    "description": "Use when a required input is missing from the sentence, a value is outside the rule's "
                   "applicable range, or no function matches the request.",
    "parameters": {"type": "object", "properties": {
        "reason": {"type": "string", "description": "short explanation"},
        "missing_inputs": {"type": "array", "items": {"type": "string"}, "description": "names of missing inputs, if any"},
    }, "required": ["reason"]},
}]


def dispatch(call):
    """LLM이 고른 함수 호출을 실제로 실행한다. 계산은 여기서 formulas 엔진이 한다"""
    name, args = call["name"], call["args"]
    if name == REFUSE:
        return {"status": "refused", "by": "llm", "reason": args.get("reason", ""),
                "missing": list(args.get("missing_inputs") or [])}
    if name not in FORMULAS:
        return {"status": "error", "reason": f"unknown function {name!r}"}
    try:
        result = calculate(name, **args)
    except InputError as error:
        return {"status": "refused", "by": "engine", "reason": str(error), "missing": []}
    return {"status": "calculated", "result": result}


def solve(question, caller=call_function):
    """문장 하나 → {status, call, result | reason, seconds}"""
    started = time.time()
    try:
        call = caller(SYSTEM_PROMPT, question, TOOLS)
    except Exception as error:
        return {"status": "error", "reason": f"{type(error).__name__}: {error}", "call": None,
                "seconds": time.time() - started}
    outcome = dispatch(call)
    outcome.update(call=call, seconds=time.time() - started)
    return outcome


def main():
    question = " ".join(sys.argv[1:]).strip()
    if not question:
        raise SystemExit('사용법: python calc.py "<영어 문장>"')
    outcome = solve(question)
    print(f"LLM function call: {outcome['call']}")
    if outcome["status"] == "calculated":
        print(outcome["result"].to_markdown())
    else:
        print(f"[{outcome['status']}] {outcome.get('by', '')} {outcome['reason']} {outcome.get('missing') or ''}")


if __name__ == "__main__":
    main()
