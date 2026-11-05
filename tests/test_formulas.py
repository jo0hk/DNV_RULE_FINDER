"""
tests/test_formulas.py — 공식 엔진 검증

    기대값은 코드를 돌려서 얻은 값이 아니라, 규정 식에 숫자를 넣어 손으로 계산한 값이다.
    (계산 과정을 주석에 남겼다)

실행:  python -m unittest discover tests -v
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from formulas import InputError, calculate, describe  # noqa: E402


class MaterialFactor(unittest.TestCase):
    def k(self, reh, **kw):
        return calculate("material_factor", reh=reh, **kw).value

    def test_table_values(self):
        for reh, k in [(235, 1.00), (315, 0.78), (355, 0.72), (390, 0.68), (460, 0.62)]:
            self.assertAlmostEqual(self.k(reh), k)

    def test_390_with_fatigue_assessment(self):
        self.assertAlmostEqual(self.k(390, fatigue_assessed="yes"), 0.66)

    def test_interpolation(self):
        # 335: 0.78 + (0.72 - 0.78) x 20/40 = 0.75
        self.assertAlmostEqual(self.k(335), 0.75)
        # 400: 0.68 + (0.62 - 0.68) x 10/70 = 0.671429
        self.assertAlmostEqual(self.k(400), 0.671429, places=5)

    def test_out_of_range(self):
        with self.assertRaises(InputError):
            self.k(500)
        with self.assertRaises(InputError):
            self.k(200)


class MinPlateThickness(unittest.TestCase):
    def test_bottom(self):
        # a = 4.5, b = 0.035, L2 = 200, k(355) = 0.72
        # t = 4.5 + 0.035 x 200 x sqrt(0.72) = 4.5 + 7 x 0.848528 = 10.4397
        r = calculate("min_plate_thickness", location="shell_bottom", length=200, reh=355)
        self.assertAlmostEqual(r.value, 10.4397, places=3)

    def test_l2_capped_at_300(self):
        # L = 350 -> L2 = 300: t = 4.5 + 0.035 x 300 x 1 = 15.0
        r = calculate("min_plate_thickness", location="shell_bottom", length=350, reh=235)
        self.assertAlmostEqual(r.value, 15.0)

    def test_no_length_term(self):
        r = calculate("min_plate_thickness", location="accommodation_wall", length=200, reh=235)
        self.assertAlmostEqual(r.value, 4.5)

    def test_unknown_location(self):
        with self.assertRaises(InputError):
            calculate("min_plate_thickness", location="roof", length=200, reh=235)


class PlateLateralPressure(unittest.TestCase):
    def test_basic(self):
        # alpha_p = 1.2 - 800/(2.1 x 2400) = 1.0413 -> 1.0
        # C_a = min(0.90 - 0.5 x 0/235, 0.80) = 0.80
        # t = 0.0158 x 1.0 x 800 x sqrt(100 / (0.8 x 235)) = 12.64 x 0.729325 = 9.2187
        r = calculate("plate_lateral_pressure", pressure=100, panel_length=2400, panel_breadth=800, reh=235)
        self.assertAlmostEqual(r.value, 9.2187, places=3)

    def test_hull_girder_stress_reduces_ca(self):
        # C_a = 0.90 - 0.5 x 150/355 = 0.688732 (< 0.80)
        # t = 0.0158 x 1.0 x 750 x sqrt(200 / (0.688732 x 355)) = 11.85 x 0.904431 = 10.7175
        r = calculate("plate_lateral_pressure", pressure=200, panel_length=3000, panel_breadth=750, reh=355, sigma_hg=150)
        self.assertAlmostEqual(r.steps[2].value, 0.688732, places=5)
        self.assertAlmostEqual(r.value, 10.7175, places=2)

    def test_aspect_ratio_factor_below_one(self):
        # alpha_p = 1.2 - 900/(2.1 x 1000) = 0.771429
        r = calculate("plate_lateral_pressure", pressure=100, panel_length=1000, panel_breadth=900, reh=235)
        self.assertAlmostEqual(r.steps[0].value, 0.771429, places=5)

    def test_missing_input(self):
        with self.assertRaises(InputError):
            calculate("plate_lateral_pressure", panel_length=2400, panel_breadth=800, reh=235)


class StiffenerSectionModulus(unittest.TestCase):
    BASE = dict(pressure=100, spacing=800, span=3.0, reh=355)   # f_u |P| s l^2 = 100 x 800 x 9 = 720000

    def z(self, **kw):
        return calculate("stiffener_section_modulus", **{**self.BASE, **kw})

    def test_fixed_tension_plate_side_uses_fm(self):
        # Table 3: fixed, tension, plate side -> C_s = f_m (beta_s - ...) = 2.0 x 0.95 = 1.9 -> C_s-max 0.85
        # Z = 720000 / (12 x 0.85 x 355) = 198.84
        self.assertAlmostEqual(self.z().value, 198.84, places=1)

    def test_fixed_compression_plate_side(self):
        # Table 3: fixed, compression, plate side -> C_s = 0.95 - 1.0 x 100/355 = 0.668310
        # Z = 720000 / (12 x 0.668310 x 355) = 252.90
        r = self.z(sigma_hg=-100)
        self.assertAlmostEqual(r.steps[3].value, 0.668310, places=5)
        self.assertAlmostEqual(r.value, 252.90, places=1)

    def test_simply_supported_tension_stiffener_side(self):
        # Table 3: simply supported, tension, stiffener side -> C_s = C_s-max = 0.85
        # Z = 720000 / (8 x 0.85 x 355) = 298.26
        r = self.z(end_fixity="simply_supported", pressure_side="stiffener", sigma_hg=50)
        self.assertAlmostEqual(r.value, 298.26, places=1)

    def test_ac2_uses_its_own_fm(self):
        # AC-II long: beta 1.10, C_s-max 0.95, f_m 1.60 -> 1.6 x (1.10 - 100/355) = 1.309 -> 0.95
        # Z = 720000 / (12 x 0.95 x 355) = 177.91
        self.assertAlmostEqual(self.z(member="AC-II/long", sigma_hg=100).value, 177.91, places=1)

    def test_profile_factor(self):
        # L profile f_u = 1.15 -> 198.84 x 1.15 = 228.67
        self.assertAlmostEqual(self.z(profile="L").value, 228.67, places=1)


class HullGirder(unittest.TestCase):
    MAIN = dict(length=200, breadth=32, block_coefficient=0.8)

    def test_min_modulus(self):
        # C_w = 10.75 - ((300 - 200)/100)^1.5 = 9.75
        # Z = 1.0 x 1.0 x 9.75 x 200^2 x 32 x (0.8 + 0.7) x 1e-6 = 18.72
        r = calculate("hull_girder_min_modulus", reh=235, **self.MAIN)
        self.assertAlmostEqual(r.value, 18.72, places=4)

    def test_min_modulus_service_restriction(self):
        # R2: f_r = 0.8 -> (1 + 0.8)/2 = 0.9 -> 18.72 x 0.9 = 16.848
        r = calculate("hull_girder_min_modulus", reh=235, service_area="R2", **self.MAIN)
        self.assertAlmostEqual(r.value, 16.848, places=4)

    def test_min_modulus_short_ship(self):
        # L = 80 -> C_w0 = 5.7 + 0.0222 x 80 = 7.476
        # Z = 7.476 x 80^2 x 14 x (0.7 + 0.7) x 1e-6 = 0.937789
        r = calculate("hull_girder_min_modulus", length=80, breadth=14, block_coefficient=0.7, reh=235)
        self.assertAlmostEqual(r.value, 0.937789, places=5)

    def test_min_inertia(self):
        # I = 3 x 1.0 x 9.75 x 200^3 x 32 x 1.5 x 1e-8 = 112.32
        self.assertAlmostEqual(calculate("hull_girder_min_inertia", **self.MAIN).value, 112.32, places=3)

    def test_inertia_needs_length_above_90(self):
        with self.assertRaises(InputError):
            calculate("hull_girder_min_inertia", length=90, breadth=14, block_coefficient=0.7)

    def test_wave_coefficient_ranges(self):
        # 300 < L <= 350 -> 10.75 ; L = 400 -> 10.75 - (50/150)^1.5 = 10.557550
        r = calculate("hull_girder_min_inertia", length=320, breadth=40, block_coefficient=0.8)
        self.assertAlmostEqual(r.steps[1].value, 10.75)
        r = calculate("hull_girder_min_inertia", length=400, breadth=50, block_coefficient=0.8)
        self.assertAlmostEqual(r.steps[1].value, 10.557550, places=5)


class Describe(unittest.TestCase):
    def test_every_formula_runs_its_markdown(self):
        ids = [f["id"] for f in describe()]
        self.assertEqual(len(ids), 6)
        r = calculate("plate_lateral_pressure", pressure=100, panel_length=2400, panel_breadth=800, reh=235)
        self.assertIn("| t |", r.to_markdown())


if __name__ == "__main__":
    unittest.main()
