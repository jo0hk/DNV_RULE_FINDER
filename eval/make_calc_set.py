"""
eval/make_calc_set.py — 계산 문제 세트 만들기

    설계자가 쓸 법한 영어 문장으로 계산 문제를 만들고, 정답은 검증을 마친 공식 엔진(formulas)으로 계산한다.
    비교 실험(LLM 직접 계산 / 코드 생성 / 파이썬 엔진)의 채점 기준이 된다.

    난이도
      easy    : 필요한 값을 기호·단위 그대로 다 준다
      medium  : 강재 등급(D36 등)처럼 표를 거쳐야 하는 값, 설계자 말투
      hard    : 단위 환산(N/mm2 → kN/m2, m → mm)이나 조건 분기(응력 부호, 압력 쪽)가 필요
      refuse  : 적용 범위 밖이거나 필요한 값이 빠져 있어 계산하면 안 되는 문제 (지어내는지 확인)

    강재 등급 → R_eH 는 Pt.3 Ch.3 Sec.1 Table 1:
      A, B, D, E = 235 / A32, D32, E32, F32 = 315 / A36 ... = 355 / A40 ... = 390 / A47 ... = 460

실행:  python eval/make_calc_set.py   →  eval/calc_questions.jsonl, eval/calc_questions.md
"""
import json
import sys
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EVAL_DIR.parent))
from formulas import InputError, calculate  # noqa: E402
from formulas.core import fmt  # noqa: E402

TOLERANCE = 0.01        # 정답과 1% 안이면 맞음

# (id, 난이도, 질문, 공식, 엔진 입력, 메모)
QUESTIONS = [
    # ---- material factor
    ("c01", "easy", "What material factor k applies to hull steel with a specified minimum yield stress of 355 N/mm2?",
     "material_factor", {"reh": 355}, ""),
    ("c02", "medium", "We upgraded the bottom plates from grade A to D32. What is the material factor k now?",
     "material_factor", {"reh": 315}, "D32 -> R_eH 315 (Ch.3 Sec.1 Table 1)"),
    ("c03", "medium", "Deck plating changed to E40 steel and no fatigue assessment is planned. Which material factor k should we use?",
     "material_factor", {"reh": 390, "fatigue_assessed": "no"}, "E40 -> 390, without fatigue assessment k = 0.68"),
    # ---- minimum plate thickness
    ("c04", "medium", "Minimum net thickness of bottom shell plating for a ship with rule length 180 m, plates in A32 steel?",
     "min_plate_thickness", {"location": "shell_bottom", "length": 180, "reh": 315}, "A32 -> 315"),
    ("c05", "hard", "Rule length 320 m container ship, weather deck plating in D36. What is the minimum net plate thickness?",
     "min_plate_thickness", {"location": "deck_weather_strength", "length": 320, "reh": 355}, "L2 = 300 (L capped)"),
    ("c06", "easy", "Side shell plating between TSC + 4.6 m and TSC + 6.9 m, rule length 150 m, mild steel with ReH 235 N/mm2. Minimum net thickness?",
     "min_plate_thickness", {"location": "side_tsc+4.6_to_6.9", "length": 150, "reh": 235}, ""),
    ("c07", "medium", "Bulk carrier, L = 225 m: inner bottom plating in cargo holds loaded through hatches, D36 steel. Minimum net thickness?",
     "min_plate_thickness", {"location": "inner_bottom_hatch_cargo", "length": 225, "reh": 355}, ""),
    # ---- plating under lateral pressure
    ("c08", "easy", "Longitudinally stiffened bottom plating, design pressure 120 kN/m2, plate panel 3200 mm x 780 mm, ReH 315 N/mm2, "
     "hull girder stress 0, acceptance criteria AC-I. Required net thickness?",
     "plate_lateral_pressure", {"pressure": 120, "panel_length": 3200, "panel_breadth": 780, "reh": 315, "sigma_hg": 0,
                                "member": "AC-I/long_stiffened"}, ""),
    ("c09", "hard", "Transversely stiffened deck plating on a longitudinal member, lateral pressure 85 kN/m2, panel 2800 mm long and 700 mm wide, "
     "mild steel (grade A), hull girder stress -120 N/mm2, AC-I. Net thickness required?",
     "plate_lateral_pressure", {"pressure": 85, "panel_length": 2800, "panel_breadth": 700, "reh": 235, "sigma_hg": -120,
                                "member": "AC-I/trans_stiffened"}, "|sigma_hg| used in C_a"),
    ("c10", "medium", "Under AC-II, longitudinally stiffened side shell plating sees 210 kN/m2 with a hull girder stress of 90 N/mm2. "
     "Panel 4000 x 850 mm, D36 steel. Required net thickness?",
     "plate_lateral_pressure", {"pressure": 210, "panel_length": 4000, "panel_breadth": 850, "reh": 355, "sigma_hg": 90,
                                "member": "AC-II/long_stiffened"}, ""),
    ("c11", "hard", "Longitudinal stiffener spacing is 0.8 m and the plate field is 3.6 m long; design pressure 0.15 N/mm2 on A36 "
     "longitudinally stiffened bottom plating, AC-I, no hull girder stress. Net thickness?",
     "plate_lateral_pressure", {"pressure": 150, "panel_length": 3600, "panel_breadth": 800, "reh": 355, "sigma_hg": 0,
                                "member": "AC-I/long_stiffened"}, "0.15 N/mm2 = 150 kN/m2, 0.8 m = 800 mm"),
    ("c12", "hard", "Short plate panel 1200 mm long and 900 mm wide, pressure 60 kN/m2, mild steel (ReH 235), other member under AC-I, "
     "no hull girder stress. Required net plate thickness?",
     "plate_lateral_pressure", {"pressure": 60, "panel_length": 1200, "panel_breadth": 900, "reh": 235, "sigma_hg": 0,
                                "member": "AC-I/other"}, "alpha_p < 1.0"),
    # ---- stiffener section modulus
    ("c13", "easy", "Side longitudinal, T-profile with fixed ends, spacing 750 mm, bending span 3.2 m, pressure 150 kN/m2 acting on the plate side, "
     "ReH 355 N/mm2, hull girder stress 0, AC-I. Required net section modulus?",
     "stiffener_section_modulus", {"pressure": 150, "spacing": 750, "span": 3.2, "reh": 355, "sigma_hg": 0, "pressure_side": "plate",
                                   "end_fixity": "fixed_horizontal", "member": "AC-I/long", "profile": "flat_or_T"}, ""),
    ("c14", "medium", "Bottom longitudinal, bulb profile, both ends fixed, s = 800 mm, span 2.8 m, P = 180 kN/m2 on the plate side, A32 steel, "
     "hull girder stress -80 N/mm2 (compression), AC-I. Required net section modulus?",
     "stiffener_section_modulus", {"pressure": 180, "spacing": 800, "span": 2.8, "reh": 315, "sigma_hg": -80, "pressure_side": "plate",
                                   "end_fixity": "fixed_horizontal", "member": "AC-I/long", "profile": "bulb"},
     "fixed + compression + plate side -> C_s = beta_s - alpha_s |sigma|/R_eH"),
    ("c15", "hard", "Deck longitudinal with an angle (L) profile, fixed ends, spacing 700 mm, span 4.0 m, 95 kN/m2 on the plate side, "
     "hull girder tension 60 N/mm2, A36 steel, AC-II. Required net section modulus?",
     "stiffener_section_modulus", {"pressure": 95, "spacing": 700, "span": 4.0, "reh": 355, "sigma_hg": 60, "pressure_side": "plate",
                                   "end_fixity": "fixed_horizontal", "member": "AC-II/long", "profile": "L"},
     "fixed + tension + plate side -> f_m (1.60 for AC-II)"),
    ("c16", "hard", "Simply supported flat bar stiffener, spacing 600 mm, span 2.5 m, 70 kN/m2 acting on the stiffener side, "
     "hull girder tension 40 N/mm2, mild steel (ReH 235), longitudinal member, AC-I. Net section modulus?",
     "stiffener_section_modulus", {"pressure": 70, "spacing": 600, "span": 2.5, "reh": 235, "sigma_hg": 40, "pressure_side": "stiffener",
                                   "end_fixity": "simply_supported", "member": "AC-I/long", "profile": "flat_or_T"},
     "simply supported + tension + stiffener side -> C_s = C_s-max"),
    ("c17", "medium", "Vertical stiffener on a transverse bulkhead, checking the lower end (fixed ends), spacing 780 mm, span 3.5 m, "
     "130 kN/m2 on the plate side, D32 steel, T-profile, other member under AC-I, no hull girder stress. Required net section modulus?",
     "stiffener_section_modulus", {"pressure": 130, "spacing": 780, "span": 3.5, "reh": 315, "sigma_hg": 0, "pressure_side": "plate",
                                   "end_fixity": "fixed_vertical_lower", "member": "AC-I/other", "profile": "flat_or_T"}, "f_bdg = 10"),
    ("c18", "hard", "Longitudinal with one end fixed and the other simply supported, spacing 820 mm, span 3.0 m, pressure 110 kN/m2 on the "
     "stiffener side, hull girder compression 100 N/mm2, A36 bulb profile, AC-I. Net section modulus?",
     "stiffener_section_modulus", {"pressure": 110, "spacing": 820, "span": 3.0, "reh": 355, "sigma_hg": -100, "pressure_side": "stiffener",
                                   "end_fixity": "one_fixed_one_simple", "member": "AC-I/long", "profile": "bulb"},
     "fixed + compression + stiffener side -> f_m = 1.77"),
    # ---- hull girder section modulus
    ("c19", "medium", "Minimum midship section modulus for L = 250 m, B = 40 m, CB = 0.82, deck and bottom in A36 steel, unrestricted service.",
     "hull_girder_min_modulus", {"length": 250, "breadth": 40, "block_coefficient": 0.82, "reh": 355, "service_area": "R0"}, ""),
    ("c20", "hard", "Small vessel, rule length 85 m, breadth 14 m, block coefficient 0.68, mild steel hull, unrestricted service: "
     "minimum gross midship section modulus?",
     "hull_girder_min_modulus", {"length": 85, "breadth": 14, "block_coefficient": 0.68, "reh": 235, "service_area": "R0"},
     "L <= 90 -> C_w0 = 5.7 + 0.0222 L"),
    ("c21", "medium", "Ship with service area notation R1, L = 150 m, B = 24 m, CB = 0.75, deck and bottom in A32. Minimum midship section modulus?",
     "hull_girder_min_modulus", {"length": 150, "breadth": 24, "block_coefficient": 0.75, "reh": 315, "service_area": "R1"}, "f_r = 0.9"),
    ("c22", "easy", "L = 320 m, B = 48 m, CB = 0.65, ReH 355 N/mm2 for deck and bottom, service area R0. Rule minimum midship section modulus?",
     "hull_girder_min_modulus", {"length": 320, "breadth": 48, "block_coefficient": 0.65, "reh": 355, "service_area": "R0"}, "C_w = 10.75"),
    # ---- hull girder moment of inertia
    ("c23", "easy", "Minimum hull girder moment of inertia at midship for a self-propelled ship, L = 250 m, B = 40 m, CB = 0.82, service area R0.",
     "hull_girder_min_inertia", {"length": 250, "breadth": 40, "block_coefficient": 0.82, "service_area": "R0"}, ""),
    ("c24", "hard", "Self-propelled ship, L = 420 m, B = 60 m, CB = 0.70, service area R2. Minimum midship moment of inertia?",
     "hull_girder_min_inertia", {"length": 420, "breadth": 60, "block_coefficient": 0.70, "service_area": "R2"},
     "350 < L <= 500 branch of C_w; f_r multiplies directly"),
    # ---- 계산하면 안 되는 문제
    ("c25", "refuse", "Bottom plating of a 200 m ship made of steel with yield stress 500 N/mm2: what is the minimum net thickness?",
     "min_plate_thickness", {"location": "shell_bottom", "length": 200, "reh": 500},
     "R_eH above 460: k not defined in Table 2 (case-by-case)"),
    ("c26", "refuse", "Minimum midship moment of inertia for an 80 m self-propelled ship, B = 13 m, CB = 0.70?",
     "hull_girder_min_inertia", {"length": 80, "breadth": 13, "block_coefficient": 0.70},
     "[1.5.2] applies only for L above 90 m"),
    ("c27", "refuse", "Required net thickness of longitudinally stiffened side shell plating with 800 mm stiffener spacing and A36 steel?",
     "plate_lateral_pressure", {"panel_breadth": 800, "reh": 355}, "design pressure and panel length missing"),
    ("c28", "refuse", "Minimum midship section modulus for a 180 m ship with breadth 30 m and mild steel deck and bottom?",
     "hull_girder_min_modulus", {"length": 180, "breadth": 30, "reh": 235}, "block coefficient missing"),
]


def main():
    rows, md = [], ["# 계산 문제 세트", "",
                    f"- 문제 {len(QUESTIONS)}개, 정답은 formulas 엔진으로 계산, 정답과 {TOLERANCE:.0%} 안이면 맞음",
                    "- refuse: 계산하지 말고 범위 밖이거나 값이 빠졌다고 답해야 맞음", "",
                    "| id | 난이도 | 질문 | 공식 | 정답 | 메모 |", "|---|---|---|---|---|---|"]
    for qid, level, question, formula, inputs, note in QUESTIONS:
        row = {"id": qid, "difficulty": level, "question": question, "formula": formula, "inputs": inputs, "note": note,
               "tolerance": TOLERANCE}
        try:
            result = calculate(formula, **inputs)
            if level == "refuse":
                raise SystemExit(f"{qid}: refuse 문제인데 엔진이 계산해 버렸습니다")
            row["answer"] = {"symbol": result.symbol, "value": result.value, "unit": result.unit}
            row["expected"] = "value"
            shown = f"{result.symbol} = {fmt(result.value)} {'' if result.unit == '-' else result.unit}".strip()
        except InputError as error:
            if level != "refuse":
                raise SystemExit(f"{qid}: 계산 실패 {error}")
            row["answer"], row["expected"], row["refuse_reason"] = None, "refuse", str(error)
            shown = "계산 거부"
        rows.append(row)
        md.append(f"| {qid} | {level} | {question} | {formula} | {shown} | {note.replace('|', '')} |")
    (EVAL_DIR / "calc_questions.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    counts = {lv: sum(1 for r in rows if r["difficulty"] == lv) for lv in ("easy", "medium", "hard", "refuse")}
    md[2:2] = [f"- 난이도: " + ", ".join(f"{k} {v}" for k, v in counts.items())]
    (EVAL_DIR / "calc_questions.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"문제 {len(rows)}개 {counts} -> eval/calc_questions.jsonl, eval/calc_questions.md")


if __name__ == "__main__":
    main()
