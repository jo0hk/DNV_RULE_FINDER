"""
formulas/core.py — 공식 계산 결과를 담는 틀

    공식 하나를 계산하면 최종 값만이 아니라 중간 계산(단계)을 모두 남긴다.
    화면에서는 이 단계들을 표로 보여 주고, 각 단계에 근거 조항을 붙인다.
    LLM은 숫자 계산에 쓰지 않는다. 계산은 전부 이 패키지의 파이썬 코드가 한다.
"""
from dataclasses import asdict, dataclass, field


class InputError(ValueError):
    """입력값이 공식의 적용 범위를 벗어났을 때"""


@dataclass
class Param:
    """공식 입력 하나의 정의 (화면의 입력 칸과 LLM 추출의 기준이 된다)"""
    name: str                  # 파이썬 인자 이름
    symbol: str                # 규정의 기호, 예: "R_eH"
    unit: str
    description: str
    minimum: float | None = None
    maximum: float | None = None
    default: object = None
    choices: dict | None = None     # 선택형 입력: {값: 설명}


@dataclass
class Step:
    """계산 한 단계: 기호 = 식 = 대입 = 값"""
    symbol: str
    expression: str            # 규정의 식 (일반 텍스트)
    substituted: str           # 숫자를 넣은 식
    value: float
    unit: str
    ref: str                   # 근거 조항


@dataclass
class Result:
    formula: str
    title: str
    ref: str
    symbol: str
    value: float
    unit: str
    inputs: dict
    steps: list = field(default_factory=list)
    notes: list = field(default_factory=list)      # 가정, 적용하지 않은 각주 등

    def to_dict(self):
        return asdict(self)

    def to_markdown(self):
        lines = [f"**{self.title}** ({self.ref})", "",
                 f"Result: **{self.symbol} = {fmt(self.value)}{unit(self.unit)}**", "",
                 "| Step | Formula | Substituted | Value | Unit | Reference |", "|---|---|---|---|---|---|"]
        lines += [f"| {cell(s.symbol)} | {cell(s.expression)} | {cell(s.substituted)} | {fmt(s.value)} | {s.unit} | {s.ref} |" for s in self.steps]
        if self.notes:
            lines += ["", *[f"- {note}" for note in self.notes]]
        return "\n".join(lines)


def unit(text):
    return "" if text == "-" else f" {text}"


def cell(text):
    """표 칸 안의 | 는 표를 깨뜨리므로 이스케이프"""
    return str(text).replace("|", "\\|")


def fmt(value, digits=4):
    """화면 표시용 숫자 (유효숫자 기준). 계산 자체는 반올림하지 않는다"""
    if value == 0:
        return "0"
    text = f"{value:.{digits}g}"
    return text if "e" not in text else f"{value:.{digits}e}"


def check_range(param, value):
    if param.choices is not None:
        if value not in param.choices:
            raise InputError(f"{param.symbol}: '{value}' is not one of {list(param.choices)}")
        return value
    try:
        value = float(value)
    except (TypeError, ValueError):
        raise InputError(f"{param.symbol} must be a number, got {value!r}") from None
    if param.minimum is not None and value < param.minimum:
        raise InputError(f"{param.symbol} = {value} {param.unit} is below the applicable range (min {param.minimum})")
    if param.maximum is not None and value > param.maximum:
        raise InputError(f"{param.symbol} = {value} {param.unit} is above the applicable range (max {param.maximum})")
    return value
