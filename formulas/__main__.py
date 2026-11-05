"""python -m formulas [demo] — 공식 목록 또는 예제 계산 표를 출력한다"""
import sys

from . import FORMULAS, calculate

EXAMPLES = [
    ("material_factor", {"reh": 335}),
    ("min_plate_thickness", {"location": "shell_bottom", "length": 200, "reh": 355}),
    ("plate_lateral_pressure", {"pressure": 100, "panel_length": 2400, "panel_breadth": 800, "reh": 235}),
    ("stiffener_section_modulus", {"pressure": 100, "spacing": 800, "span": 3.0, "reh": 355}),
    ("hull_girder_min_modulus", {"length": 200, "breadth": 32, "block_coefficient": 0.8, "reh": 235}),
    ("hull_girder_min_inertia", {"length": 200, "breadth": 32, "block_coefficient": 0.8}),
]

if __name__ == "__main__":
    if sys.argv[1:] == ["demo"]:
        for formula_id, inputs in EXAMPLES:
            print(calculate(formula_id, **inputs).to_markdown(), end="\n\n")
    else:
        for f in FORMULAS.values():
            print(f"{f.id:28} {f.ref:38} inputs: {', '.join(p.symbol for p in f.params)}")
