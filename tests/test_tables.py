"""
tests/test_tables.py — 표 추출(tables.py) 품질 확인

    검증을 마친 공식 엔진(formulas/hull.py)의 표 값과, PDF에서 자동 추출한 표를 비교한다.
    table_db/tables.json 은 규정 내용이라 저장소에 없으므로, 파일이 없으면 건너뛴다 (python tables.py 로 생성).

실행:  python -m unittest discover tests -v
"""
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import tables  # noqa: E402
from formulas import hull  # noqa: E402

INDEX = tables.load()


def numbers(row):
    """행에서 숫자 칸만 (각주 표시 제거). '0.66/0.68 1)' 같은 칸은 그대로 문자열로"""
    out = []
    for cell in row:
        text = re.sub(r"\b\d\)", "", cell).strip()
        if re.fullmatch(r"-?\d+(\.\d+)?", text):
            out.append(float(text))
        elif re.fullmatch(r"\d+(\.\d+)?/\d+(\.\d+)?", text):
            out.append(text)
    return out


def table(key):
    return tables.merged_columns(INDEX[key])


@unittest.skipUnless(INDEX, "table_db/tables.json 없음 (python tables.py 로 생성)")
class FormulaTables(unittest.TestCase):
    def test_material_factor_spans_two_pages(self):
        t = INDEX["Pt.3 Ch.3 Sec.1 Table 2"]
        self.assertEqual(t["pages"], [86, 87])
        rows = [numbers(r) for r in table("Pt.3 Ch.3 Sec.1 Table 2")[1]]
        self.assertEqual(rows, [[235, 1.0], [315, 0.78], [355, 0.72], [390, "0.66/0.68"], [460, 0.62]])

    def test_min_thickness_merged_cells(self):
        rows = [numbers(r) for r in table("Pt.3 Ch.6 Sec.3 Table 1")[1]]
        self.assertEqual(rows, [[a, b] for a, b, _ in hull.MIN_T_TABLE.values()])

    def test_min_thickness_row_labels_not_leaked(self):
        _, rows = table("Pt.3 Ch.6 Sec.3 Table 1")
        deck = [r for r in rows if r[0] == "Deck"]
        self.assertTrue(deck and all("Elsewhere" not in " ".join(r) for r in deck))

    def test_plating_table(self):
        rows = [numbers(r) for r in table("Pt.3 Ch.6 Sec.4 Table 1")[1]]
        self.assertEqual(rows, [list(v) for v in hull.PLATE_TABLE.values()])

    def test_stiffener_table4_joined_across_pages(self):
        t = INDEX["Pt.3 Ch.6 Sec.5 Table 4"]
        self.assertEqual(t["pages"], [329, 330])
        rows = [numbers(r) for r in table("Pt.3 Ch.6 Sec.5 Table 4")[1]]
        self.assertEqual(rows, [list(v) for v in hull.STIFF_TABLE.values()])

    def test_stiffener_table5(self):
        rows = [numbers(r) for r in table("Pt.3 Ch.6 Sec.5 Table 5")[1]]
        self.assertEqual(rows[0], [12.0, 10.0, 8.0, 8.0])
        self.assertEqual(rows[1], [2.0, 2.33, 1.77])
        self.assertEqual(rows[2], [1.6, 1.86, 1.42])

    def test_main_data_header_is_one_row(self):
        t = INDEX["Pt.3 Ch.1 Sec.4 Table 2"]
        self.assertEqual(t["columns"], ["Symbol", "Meaning", "Units"])
        self.assertTrue(any(r[0] == "L 2" and "300 m" in r[1] for r in t["body"]))


class Links(unittest.TestCase):
    def test_mentions_inherit_own_section(self):
        keys = tables.mentioned("as defined in Table 1 and Sec.1 Table 2, see Ch.3 Sec.7 Table 4",
                                "DNV-RU-SHIP Pt.3 Ch.6 Sec.4 [1.1]")
        self.assertEqual(keys, ["Pt.3 Ch.6 Sec.4 Table 1", "Pt.3 Ch.6 Sec.1 Table 2", "Pt.3 Ch.3 Sec.7 Table 4"])


if __name__ == "__main__":
    unittest.main()
