"""
formulas — DNV 규정 공식 계산 엔진

    from formulas import calculate, describe
    result = calculate("plate_lateral_pressure", pressure=100, panel_length=2400, panel_breadth=800, reh=235)
    print(result.to_markdown())

    describe()는 공식마다 필요한 입력(기호, 단위, 범위, 선택지)을 돌려준다.
    다음 단계에서 화면의 입력 폼과, 문장에서 수치를 뽑는 LLM 프롬프트가 이것을 쓴다.

실행 예:  python -m formulas                 (공식 목록)
          python -m formulas demo            (예제 계산 표)
"""
from dataclasses import asdict

from .core import InputError, Result
from .hull import FORMULAS

__all__ = ["FORMULAS", "InputError", "Result", "calculate", "describe"]


def calculate(formula_id, **inputs):
    if formula_id not in FORMULAS:
        raise InputError(f"Unknown formula '{formula_id}'. Available: {sorted(FORMULAS)}")
    return FORMULAS[formula_id].calculate(**inputs)


def describe():
    return [{"id": f.id, "title": f.title, "ref": f.ref, "summary": f.summary,
             "params": [asdict(p) for p in f.params]} for f in FORMULAS.values()]
