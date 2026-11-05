"""
formulas/hull.py — DNV-RU-SHIP Pt.3 (Hull) 공식

    규정 PDF의 공식은 이미지라서 텍스트로 추출되지 않는다. 아래 공식과 표 값은
    "DNV Rule SHIP Part 3 Hull - 2026" PDF 원문 페이지를 보고 손으로 옮겼다.
    (괄호 안은 PDF 쪽 번호, 각 장의 Edition 표기)

    material_factor             Ch.3 Sec.1 [2.2] Table 2        (p.86, Ch.3 July 2026)
    min_plate_thickness         Ch.6 Sec.3 [1.1.1] Table 1      (p.315, Ch.6 July 2025)
    plate_lateral_pressure      Ch.6 Sec.4 [1.1.1] Table 1      (p.318-319)
    stiffener_section_modulus   Ch.6 Sec.5 [1.1.2] Table 3-5    (p.329-330)
    hull_girder_min_modulus     Ch.5 Sec.2 [1.3]                (p.285, Ch.5 July 2022)
    hull_girder_min_inertia     Ch.5 Sec.2 [1.5.2]              (p.285)
    보조 정의: Cw  Ch.4 Sec.4 Symbols (p.209), fr  Ch.4 Sec.3 Symbols (p.202-203),
              L2, s, b 등 단위  Ch.1 Sec.4 Table 2, Table 5 (p.28, p.32)

    모든 두께·단면계수는 규정이 말하는 대로 net(부식 여유 제외) 값이다. 단, hull girder는 gross.
"""
import math
from dataclasses import dataclass
from typing import Callable

from .core import InputError, Param, Result, Step, check_range, fmt

P3 = "DNV-RU-SHIP Pt.3"


@dataclass
class Formula:
    id: str
    title: str
    ref: str
    params: list
    run: Callable
    summary: str

    def calculate(self, **inputs):
        unknown = set(inputs) - {p.name for p in self.params}
        if unknown:
            raise InputError(f"Unknown input(s) for {self.id}: {sorted(unknown)}")
        values = {}
        for param in self.params:
            raw = inputs.get(param.name, param.default)
            if raw is None:
                raise InputError(f"Missing input: {param.symbol} ({param.description}, {param.unit})")
            values[param.name] = check_range(param, raw)
        return self.run(**values)


def interpolate(x, table):
    """표 값 사이를 선형 보간. table = [(x, y), ...] 오름차순"""
    for (x0, y0), (x1, y1) in zip(table, table[1:]):
        if x0 <= x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    raise InputError(f"{x} is outside the table range {table[0][0]}-{table[-1][0]}")


# ---------------------------------------------------------------- material factor k
K_TABLE_REF = f"{P3} Ch.3 Sec.1 [2.2] Table 2"


def k_from_reh(reh, fatigue_assessed=False):
    """Table 2. ReH 390은 피로 평가를 하면 0.66, 아니면 0.68 (Table 2 각주 1)"""
    k390 = 0.66 if fatigue_assessed else 0.68
    return interpolate(reh, [(235, 1.00), (315, 0.78), (355, 0.72), (390, k390), (460, 0.62)])


def _material_factor(reh, fatigue_assessed):
    k = k_from_reh(reh, fatigue_assessed == "yes")
    notes = []
    if reh not in (235, 315, 355, 390, 460):
        notes.append("k obtained by linear interpolation between the values of Table 2.")
    if reh > 355:
        notes.append("Between 355 and 460 N/mm2 the 390 N/mm2 point is "
                     f"{0.66 if fatigue_assessed == 'yes' else 0.68} (Table 2 note 1: 0.66 only with a fatigue assessment).")
    return Result("material_factor", "Material factor k", K_TABLE_REF, "k", k, "-",
                  {"R_eH": reh, "fatigue assessment": fatigue_assessed},
                  [Step("k", "Table 2 (linear interpolation in R_eH)", f"R_eH = {fmt(reh)}", k, "-", K_TABLE_REF)], notes)


REH = Param("reh", "R_eH", "N/mm2", "specified minimum yield stress of the steel", 235, 460)
FATIGUE = Param("fatigue_assessed", "fatigue", "-", "fatigue assessment performed (only matters near 390 N/mm2)",
                default="no", choices={"no": "no fatigue assessment (k = 0.68 at 390)", "yes": "fatigue assessed (k = 0.66 at 390)"})


# ---------------------------------------------------------------- minimum plate thickness
MIN_T_REF = f"{P3} Ch.6 Sec.3 [1.1.1]"
# Table 1 Minimum net thickness for plating: 위치 → (a, b, 설명)
MIN_T_TABLE = {
    "shell_bottom":            (4.5, 0.035, "Shell: keel, bottom, bilge and sea chest boundaries"),
    "side_to_tsc+4.6":         (4.0, 0.035, "Side shell: upper end of bilge plating to TSC + 4.6 m"),
    "side_tsc+4.6_to_6.9":     (4.0, 0.025, "Side shell: TSC + 4.6 m to TSC + 6.9 m"),
    "side_tsc+6.9_to_9.2":     (4.0, 0.015, "Side shell: TSC + 6.9 m to TSC + 9.2 m"),
    "side_elsewhere":          (4.0, 0.01,  "Side shell and superstructure side: elsewhere"),
    "deck_weather_strength":   (4.5, 0.02,  "Deck: weather deck and strength deck"),
    "deck_tank_boundary":      (4.5, 0.015, "Deck: boundary for cargo tanks, water ballast tanks and holds for cargo in bulk"),
    "deck_other":              (4.5, 0.01,  "Deck: other decks"),
    "inner_bottom_hatch_cargo": (5.5, 0.025, "Inner bottom: cargo spaces loaded through cargo hatches except container holds"),
    "inner_bottom_other":      (4.5, 0.02,  "Inner bottom: other spaces"),
    "bhd_cargo_ballast_tank":  (4.5, 0.015, "Bulkheads: for cargo tanks, water ballast tanks and holds for cargo in bulk"),
    "bhd_peak":                (4.5, 0.015, "Bulkheads: peak bulkheads"),
    "bhd_watertight_other_tank": (4.5, 0.01, "Bulkheads: watertight bulkheads and other tank bulkheads"),
    "bhd_nontight_in_tank":    (5.0, 0.005, "Bulkheads: non-tight bulkheads in tanks"),
    "bhd_nontight_other":      (5.0, 0.0,   "Bulkheads: other non-tight bulkheads"),
    "accommodation_wall":      (4.5, 0.0,   "Walls in accommodation"),
}


def _min_plate_thickness(location, length, reh, fatigue_assessed):
    a, b, label = MIN_T_TABLE[location]
    k = k_from_reh(reh, fatigue_assessed == "yes")
    l2 = min(length, 300.0)
    t = a + b * l2 * math.sqrt(k)
    steps = [
        Step("k", "Table 2", f"R_eH = {fmt(reh)}", k, "-", K_TABLE_REF),
        Step("L2", "L, but need not be taken greater than 300 m", f"min({fmt(length)}, 300)", l2, "m", f"{P3} Ch.1 Sec.4 Table 2"),
        Step("a, b", f"Table 1: {label}", f"a = {a}, b = {b}", a, "mm", f"{MIN_T_REF} Table 1"),
        Step("t", "a + b L2 sqrt(k)", f"{a} + {b} x {fmt(l2)} x sqrt({fmt(k)})", t, "mm", MIN_T_REF),
    ]
    notes = ["Net thickness (corrosion addition not included).",
             "Footnotes 1)-9) of Table 1 (e.g. reductions above 1.7 Cw from the waterline, 5.0 mm cap for some "
             "watertight bulkheads) are not applied; check them for the actual member."]
    return Result("min_plate_thickness", "Minimum net plate thickness", MIN_T_REF, "t", t, "mm",
                  {"location": label, "L": length, "R_eH": reh}, steps, notes)


# ---------------------------------------------------------------- plating under lateral pressure
PLATE_REF = f"{P3} Ch.6 Sec.4 [1.1.1]"
# Table 1: (기준, 부재) → (beta_a, alpha_a, Ca_max)
PLATE_TABLE = {
    "AC-I/long_stiffened":            (0.90, 0.50, 0.80),
    "AC-I/trans_stiffened":           (0.90, 1.00, 0.80),
    "AC-I/other":                     (0.80, 0.00, 0.80),
    "AC-II/long_stiffened":           (1.05, 0.50, 0.95),
    "AC-II/trans_stiffened":          (1.05, 1.00, 0.95),
    "AC-II/other":                    (0.95, 0.00, 0.95),
    "AC-III/long_bhd_long_stiffened": (1.25, 0.50, 1.15),
    "AC-III/long_bhd_trans_stiffened": (1.15, 1.00, 1.15),
    "AC-III/other_long_long_stiffened": (1.10, 0.50, 1.00),
    "AC-III/other_long_trans_stiffened": (1.10, 1.00, 1.00),
    "AC-III/transverse_tank_boundary": (1.15, 0.00, 1.15),
    "AC-III/other":                   (1.00, 0.00, 1.00),
    "AC-III/long_watertight_long_stiffened": (1.25, 0.50, 1.15),
    "AC-III/long_watertight_trans_stiffened": (1.15, 1.00, 1.15),
    "AC-III/other_watertight":        (1.15, 0.00, 1.15),
}
PLATE_MEMBERS = {
    "AC-I/long_stiffened": "AC-I, longitudinal member, longitudinally stiffened plating",
    "AC-I/trans_stiffened": "AC-I, longitudinal member, transversely stiffened plating",
    "AC-I/other": "AC-I, other members",
    "AC-II/long_stiffened": "AC-II, longitudinal member, longitudinally stiffened plating",
    "AC-II/trans_stiffened": "AC-II, longitudinal member, transversely stiffened plating",
    "AC-II/other": "AC-II, other members",
    "AC-III/long_bhd_long_stiffened": "AC-III, longitudinal bulkhead between tanks and dry spaces, longitudinally stiffened",
    "AC-III/long_bhd_trans_stiffened": "AC-III, longitudinal bulkhead between tanks and dry spaces, transversely stiffened",
    "AC-III/other_long_long_stiffened": "AC-III, other longitudinal members, longitudinally stiffened",
    "AC-III/other_long_trans_stiffened": "AC-III, other longitudinal members, transversely stiffened",
    "AC-III/transverse_tank_boundary": "AC-III, transverse boundaries of ballast tanks / between tanks and dry spaces",
    "AC-III/other": "AC-III, other members",
    "AC-III/long_watertight_long_stiffened": "AC-III, longitudinal watertight boundary, longitudinally stiffened (flooding only)",
    "AC-III/long_watertight_trans_stiffened": "AC-III, longitudinal watertight boundary, transversely stiffened (flooding only)",
    "AC-III/other_watertight": "AC-III, other watertight boundaries (flooding only)",
}


def _plate_lateral_pressure(pressure, panel_length, panel_breadth, reh, sigma_hg, member):
    beta, alpha, ca_max = PLATE_TABLE[member]
    alpha_p_raw = 1.2 - panel_breadth / (2.1 * panel_length)
    alpha_p = min(alpha_p_raw, 1.0)
    ca_raw = beta - alpha * abs(sigma_hg) / reh
    ca = min(ca_raw, ca_max)
    if ca <= 0:
        raise InputError(f"C_a = {fmt(ca)} <= 0: the hull girder stress uses up the whole permissible stress.")
    t = 0.0158 * alpha_p * panel_breadth * math.sqrt(abs(pressure) / (ca * reh))
    steps = [
        Step("alpha_p", "1.2 - b / (2.1 a), not greater than 1.0",
             f"min(1.2 - {fmt(panel_breadth)} / (2.1 x {fmt(panel_length)}), 1.0)", alpha_p, "-", f"{P3} Ch.6 Sec.4 Symbols"),
        Step("beta_a, alpha_a, C_a-max", f"Table 1: {PLATE_MEMBERS[member]}", f"{beta}, {alpha}, {ca_max}", beta, "-", f"{PLATE_REF} Table 1"),
        Step("C_a", "beta_a - alpha_a abs(sigma_hg) / R_eH, not greater than C_a-max",
             f"min({beta} - {alpha} x {fmt(abs(sigma_hg))} / {fmt(reh)}, {ca_max})", ca, "-", PLATE_REF),
        Step("t", "0.0158 alpha_p b sqrt(abs(P) / (C_a R_eH))",
             f"0.0158 x {fmt(alpha_p)} x {fmt(panel_breadth)} x sqrt({fmt(abs(pressure))} / ({fmt(ca)} x {fmt(reh)}))", t, "mm", PLATE_REF),
    ]
    notes = ["Net thickness for one design load set; the rule requires the greatest value over all applicable "
             "design load sets (Sec.2 [2.1.3]).",
             "Corrosion addition and the minimum thickness of Sec.3 are checked separately."]
    if panel_breadth > panel_length:
        notes.append("b is larger than a: b should be the shorter side (breadth) of the elementary plate panel.")
    return Result("plate_lateral_pressure", "Plating subjected to lateral pressure", PLATE_REF, "t", t, "mm",
                  {"P": pressure, "a": panel_length, "b": panel_breadth, "R_eH": reh, "sigma_hg": sigma_hg,
                   "member": PLATE_MEMBERS[member]}, steps, notes)


# ---------------------------------------------------------------- stiffener section modulus
STIFF_REF = f"{P3} Ch.6 Sec.5 [1.1.2]"
# Table 4: (beta_s, alpha_s, Cs_max)
STIFF_TABLE = {
    "AC-I/long": (0.95, 1.00, 0.85),
    "AC-I/other": (0.85, 0.00, 0.85),
    "AC-II/long": (1.10, 1.00, 0.95),
    "AC-II/other": (0.95, 0.00, 0.95),
    "AC-III/long": (1.20, 1.00, 1.00),
    "AC-III/long_watertight": (1.20, 1.00, 1.15),
    "AC-III/other": (1.00, 0.00, 1.00),
    "AC-III/other_watertight": (1.15, 0.00, 1.15),
}
STIFF_MEMBERS = {
    "AC-I/long": "AC-I, longitudinal members", "AC-I/other": "AC-I, other members",
    "AC-II/long": "AC-II, longitudinal members", "AC-II/other": "AC-II, other members",
    "AC-III/long": "AC-III, longitudinal members, in general",
    "AC-III/long_watertight": "AC-III, longitudinal members on watertight boundaries (flooding only)",
    "AC-III/other": "AC-III, other members, in general",
    "AC-III/other_watertight": "AC-III, other members on watertight boundaries (flooding only)",
}
# Table 5: 끝단 조건 → (f_bdg, f_m for AC-I, f_m for AC-II/III, 설명)
END_TABLE = {
    "fixed_horizontal": (12.0, 2.00, 1.60, "fixed ends, horizontal stiffener or upper end of vertical stiffener"),
    "fixed_vertical_lower": (10.0, 2.33, 1.86, "fixed ends, lower end of vertical stiffener"),
    "one_fixed_one_simple": (8.0, 1.77, 1.42, "one fixed end and one simply supported end"),
    "simply_supported": (8.0, None, None, "simply supported ends"),
}
PROFILE_FU = {"flat_or_T": (1.00, "flat bar or symmetrical (T) profile"),
              "bulb": (1.03, "bulb profile"),
              "L": (1.15, "unsymmetrical (L) profile")}


def _stiffener_section_modulus(pressure, spacing, span, reh, sigma_hg, pressure_side, end_fixity, member, profile):
    beta, alpha, cs_max = STIFF_TABLE[member]
    f_bdg, fm_1, fm_23, end_label = END_TABLE[end_fixity]
    f_u, profile_label = PROFILE_FU[profile]
    fm = fm_1 if member.startswith("AC-I/") else fm_23
    tension = sigma_hg >= 0                       # 규정: tension (positive), compression (negative)
    base = beta - alpha * abs(sigma_hg) / reh
    base_text = f"{beta} - {alpha} x {fmt(abs(sigma_hg))} / {fmt(reh)}"
    # Table 3: 끝단 조건, 응력 부호, 압력이 걸리는 쪽에 따라 Cs 식이 달라진다
    if end_fixity != "simply_supported":
        if tension == (pressure_side == "stiffener"):
            cs_raw, expr, sub = base, "beta_s - alpha_s abs(sigma_hg) / R_eH, not greater than C_s-max", f"min({base_text}, {cs_max})"
        else:
            cs_raw, expr, sub = fm * base, "f_m (beta_s - alpha_s abs(sigma_hg) / R_eH), not greater than C_s-max", f"min({fm} x ({base_text}), {cs_max})"
    else:
        if tension == (pressure_side == "plate"):
            cs_raw, expr, sub = base, "beta_s - alpha_s abs(sigma_hg) / R_eH, not greater than C_s-max", f"min({base_text}, {cs_max})"
        else:
            cs_raw, expr, sub = cs_max, "C_s-max", f"{cs_max}"
    cs = min(cs_raw, cs_max)
    if cs <= 0:
        raise InputError(f"C_s = {fmt(cs)} <= 0: the hull girder stress uses up the whole permissible stress.")
    z = f_u * abs(pressure) * spacing * span ** 2 / (f_bdg * cs * reh)
    situation = (f"{'tension' if tension else 'compression'} (sigma_hg = {fmt(sigma_hg)}), "
                 f"pressure on {pressure_side} side, {end_label}")
    steps = [
        Step("f_u", profile_label, f"{f_u}", f_u, "-", STIFF_REF),
        Step("f_bdg" + (", f_m" if fm else ""), f"Table 5: {end_label}",
             f"f_bdg = {f_bdg}" + (f", f_m = {fm}" if fm else ""), f_bdg, "-", f"{STIFF_REF} Table 5"),
        Step("beta_s, alpha_s, C_s-max", f"Table 4: {STIFF_MEMBERS[member]}", f"{beta}, {alpha}, {cs_max}", beta, "-", f"{STIFF_REF} Table 4"),
        Step("C_s", f"Table 3 ({situation}): {expr}", sub, cs, "-", f"{STIFF_REF} Table 3"),
        Step("Z", "f_u abs(P) s l_bdg^2 / (f_bdg C_s R_eH)",
             f"{f_u} x {fmt(abs(pressure))} x {fmt(spacing)} x {fmt(span)}^2 / ({f_bdg} x {fmt(cs)} x {fmt(reh)})", z, "cm3", STIFF_REF),
    ]
    notes = ["Net section modulus for one design load set; the rule requires the greatest value over all applicable "
             "design load sets (Sec.2 [2.1.3]).",
             "Stiffeners with end fixity other than Table 5, complex load patterns or grillages: use [1.2] instead.",
             "Web thickness [1.1.1] and the different-material check [1.1.4] are not included."]
    return Result("stiffener_section_modulus", "Stiffener section modulus under lateral pressure", STIFF_REF, "Z", z, "cm3",
                  {"P": pressure, "s": spacing, "l_bdg": span, "R_eH": reh, "sigma_hg": sigma_hg,
                   "pressure side": pressure_side, "end fixity": end_label, "member": STIFF_MEMBERS[member],
                   "profile": profile_label}, steps, notes)


# ---------------------------------------------------------------- hull girder
HG_Z_REF = f"{P3} Ch.5 Sec.2 [1.3]"
HG_I_REF = f"{P3} Ch.5 Sec.2 [1.5.2]"
CW_REF = f"{P3} Ch.4 Sec.4 Symbols"
FR_REF = f"{P3} Ch.4 Sec.3 Symbols"
SERVICE_FR = {"R0": 1.0, "R1": 0.9, "R2": 0.8, "R3": 0.7, "R4": 0.6, "RE": 0.5}


def wave_coefficient(length):
    """Cw, Ch.4 Sec.4. (식, 대입, 값)"""
    if length < 90:
        return "0.0856 L", f"0.0856 x {fmt(length)}", 0.0856 * length
    if length <= 300:
        return "10.75 - ((300 - L) / 100)^1.5", f"10.75 - ((300 - {fmt(length)}) / 100)^1.5", 10.75 - ((300 - length) / 100) ** 1.5
    if length <= 350:
        return "10.75", "10.75", 10.75
    return "10.75 - ((L - 350) / 150)^1.5", f"10.75 - (({fmt(length)} - 350) / 150)^1.5", 10.75 - ((length - 350) / 150) ** 1.5


def _hull_girder_min_modulus(length, breadth, block_coefficient, reh, fatigue_assessed, service_area):
    k = k_from_reh(reh, fatigue_assessed == "yes")
    fr = SERVICE_FR[service_area]
    if length > 90:
        cw_expr, cw_sub, cw = wave_coefficient(length)
        cw0_step = Step("C_w0", f"C_w (L > 90 m), C_w = {cw_expr}", cw_sub, cw, "-", f"{HG_Z_REF}, {CW_REF}")
    else:
        cw = 5.7 + 0.0222 * length
        cw0_step = Step("C_w0", "5.7 + 0.0222 L (L <= 90 m)", f"5.7 + 0.0222 x {fmt(length)}", cw, "-", HG_Z_REF)
    z = k * (1 + fr) / 2 * cw * length ** 2 * breadth * (block_coefficient + 0.7) * 1e-6
    steps = [
        Step("k", "Table 2", f"R_eH = {fmt(reh)}", k, "-", K_TABLE_REF),
        Step("f_r", f"service area notation {service_area}", f"{fr}", fr, "-", FR_REF),
        cw0_step,
        Step("Z_R-gr", "k ((1 + f_r) / 2) C_w0 L^2 B (C_B + 0.7) 10^-6",
             f"{fmt(k)} x ((1 + {fr}) / 2) x {fmt(cw)} x {fmt(length)}^2 x {fmt(breadth)} x ({fmt(block_coefficient)} + 0.7) x 10^-6",
             z, "m3", HG_Z_REF),
    ]
    notes = ["Gross section modulus at the equivalent deck line and at the bottom, midship.",
             "k is that of the bottom and deck members contributing to hull girder strength (Ch.5 Sec.2 [1.1.2]).",
             "The section modulus from the actual bending moments ([1.4]) must also be satisfied."]
    return Result("hull_girder_min_modulus", "Minimum hull girder section modulus midship", HG_Z_REF, "Z_R-gr", z, "m3",
                  {"L": length, "B": breadth, "C_B": block_coefficient, "R_eH": reh, "service area": service_area}, steps, notes)


def _hull_girder_min_inertia(length, breadth, block_coefficient, service_area):
    if length <= 90:
        raise InputError("The minimum moment of inertia [1.5.2] applies only to ships with length above 90 m.")
    fr = SERVICE_FR[service_area]
    cw_expr, cw_sub, cw = wave_coefficient(length)
    inertia = 3 * fr * cw * length ** 3 * breadth * (block_coefficient + 0.7) * 1e-8
    steps = [
        Step("f_r", f"service area notation {service_area}", f"{fr}", fr, "-", FR_REF),
        Step("C_w", cw_expr, cw_sub, cw, "-", CW_REF),
        Step("I_yR-gr", "3 f_r C_w L^3 B (C_B + 0.7) 10^-8",
             f"3 x {fr} x {fmt(cw)} x {fmt(length)}^3 x {fmt(breadth)} x ({fmt(block_coefficient)} + 0.7) x 10^-8",
             inertia, "m4", HG_I_REF),
    ]
    notes = ["Gross moment of inertia about the horizontal axis at the midship point.",
             "Applies to self-propelled ships with length above 90 m ([1.5.1])."]
    return Result("hull_girder_min_inertia", "Minimum hull girder moment of inertia midship", HG_I_REF, "I_yR-gr", inertia, "m4",
                  {"L": length, "B": breadth, "C_B": block_coefficient, "service area": service_area}, steps, notes)


# ---------------------------------------------------------------- 입력 정의와 목록
LENGTH = Param("length", "L", "m", "rule length", 1, 500)
BREADTH = Param("breadth", "B", "m", "moulded breadth", 1, 100)
CB = Param("block_coefficient", "C_B", "-", "block coefficient at scantling draught", 0.3, 1.0)
SERVICE = Param("service_area", "service area", "-", "service area notation", default="R0",
                choices={k: f"f_r = {v}" for k, v in SERVICE_FR.items()})
PRESSURE = Param("pressure", "P", "kN/m2", "design pressure for the design load set", 0, 5000)
SIGMA_HG = Param("sigma_hg", "sigma_hg", "N/mm2", "hull girder longitudinal stress (tension positive)", -460, 460, default=0)

FORMULAS = {f.id: f for f in [
    Formula("material_factor", "Material factor k", K_TABLE_REF, [REH, FATIGUE], _material_factor,
            "Material factor k of hull steel from its yield stress."),
    Formula("min_plate_thickness", "Minimum net plate thickness", MIN_T_REF,
            [Param("location", "location", "-", "plating location (Table 1)", choices={k: v[2] for k, v in MIN_T_TABLE.items()}),
             LENGTH, REH, FATIGUE], _min_plate_thickness,
            "Rule minimum net thickness of plating for a given location and ship length."),
    Formula("plate_lateral_pressure", "Plating subjected to lateral pressure", PLATE_REF,
            [PRESSURE,
             Param("panel_length", "a", "mm", "length of the elementary plate panel (longer side)", 1, 20000),
             Param("panel_breadth", "b", "mm", "breadth of the elementary plate panel (stiffener spacing)", 1, 10000),
             REH, SIGMA_HG,
             Param("member", "member", "-", "acceptance criteria and structural member (Table 1)", default="AC-I/long_stiffened",
                   choices=PLATE_MEMBERS)], _plate_lateral_pressure,
            "Required net plate thickness from the lateral design pressure."),
    Formula("stiffener_section_modulus", "Stiffener section modulus under lateral pressure", STIFF_REF,
            [PRESSURE,
             Param("spacing", "s", "mm", "stiffener spacing", 1, 10000),
             Param("span", "l_bdg", "m", "effective bending span", 0.1, 30),
             REH, SIGMA_HG,
             Param("pressure_side", "pressure side", "-", "side the lateral pressure acts on", default="plate",
                   choices={"plate": "pressure acting on plate side", "stiffener": "pressure acting on stiffener side"}),
             Param("end_fixity", "end fixity", "-", "end support condition (Table 5)", default="fixed_horizontal",
                   choices={k: v[3] for k, v in END_TABLE.items()}),
             Param("member", "member", "-", "acceptance criteria and structural member (Table 4)", default="AC-I/long",
                   choices=STIFF_MEMBERS),
             Param("profile", "profile", "-", "profile type", default="flat_or_T",
                   choices={k: v[1] for k, v in PROFILE_FU.items()})], _stiffener_section_modulus,
            "Required net section modulus of a stiffener from the lateral design pressure."),
    Formula("hull_girder_min_modulus", "Minimum hull girder section modulus midship", HG_Z_REF,
            [LENGTH, BREADTH, CB, REH, FATIGUE, SERVICE], _hull_girder_min_modulus,
            "Rule minimum gross midship section modulus from main dimensions."),
    Formula("hull_girder_min_inertia", "Minimum hull girder moment of inertia midship", HG_I_REF,
            [Param("length", "L", "m", "rule length (above 90 m)", 90, 500), BREADTH, CB, SERVICE], _hull_girder_min_inertia,
            "Rule minimum gross midship moment of inertia from main dimensions."),
]}
