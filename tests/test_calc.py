"""
tests/test_calc.py — 계산 연결(calc.py) 검증. LLM은 부르지 않고 가짜 응답으로 확인한다

실행:  python -m unittest discover tests -v
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import calc  # noqa: E402
from formulas import FORMULAS  # noqa: E402


def fake(name, **args):
    return lambda system, user, tools: {"name": name, "args": args}


class ToolSchema(unittest.TestCase):
    def test_one_tool_per_formula_plus_refuse(self):
        names = [t["name"] for t in calc.TOOLS]
        self.assertEqual(names, list(FORMULAS) + [calc.REFUSE])

    def test_required_inputs_have_no_default(self):
        schema = calc.tool_schema(FORMULAS["plate_lateral_pressure"])["parameters"]
        self.assertEqual(schema["required"], ["pressure", "panel_length", "panel_breadth", "reh"])
        self.assertEqual(schema["properties"]["member"]["enum"][0], "AC-I/long_stiffened")
        self.assertIn("kN/m2", schema["properties"]["pressure"]["description"])


class Dispatch(unittest.TestCase):
    def test_calculation_is_done_by_engine(self):
        out = calc.solve("q", caller=fake("plate_lateral_pressure", pressure=100, panel_length=2400, panel_breadth=800, reh=235))
        self.assertEqual(out["status"], "calculated")
        self.assertAlmostEqual(out["result"].value, 9.2187, places=3)

    def test_llm_refusal(self):
        out = calc.solve("q", caller=fake(calc.REFUSE, reason="pressure missing", missing_inputs=["pressure"]))
        self.assertEqual((out["status"], out["by"], out["missing"]), ("refused", "llm", ["pressure"]))

    def test_engine_blocks_out_of_range_value(self):
        out = calc.solve("q", caller=fake("min_plate_thickness", location="shell_bottom", length=200, reh=500))
        self.assertEqual((out["status"], out["by"]), ("refused", "engine"))

    def test_engine_blocks_missing_value(self):
        out = calc.solve("q", caller=fake("hull_girder_min_modulus", length=180, breadth=30, reh=235))
        self.assertEqual((out["status"], out["by"]), ("refused", "engine"))

    def test_unknown_function(self):
        self.assertEqual(calc.solve("q", caller=fake("web_thickness"))["status"], "error")

    def test_llm_failure_is_reported(self):
        def broken(system, user, tools):
            raise ValueError("no function call")
        self.assertEqual(calc.solve("q", caller=broken)["status"], "error")


if __name__ == "__main__":
    unittest.main()
