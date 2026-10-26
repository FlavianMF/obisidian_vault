"""Testes do origin_breakdown: python3 -m unittest discover -s 00_META/eval -v"""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import origin_breakdown as ob

APPROVAL = {"by": "user", "date": "2026-10-23", "draft": "d001", "edited": False}


def golden_rows() -> list[dict]:
    return [
        {"id": "p1", "kind": "lexical"},
        {"id": "p2", "kind": "paraphrase"},
        {"id": "p3", "kind": "lexical", "approval": APPROVAL},
        {"id": "p4", "kind": "multihop", "approval": APPROVAL},
        {"id": "n1", "kind": "negative"},
        {"id": "n2", "kind": "negative", "approval": APPROVAL},
    ]


def pos(success: float) -> dict:
    return {"neg": 0.0, "success": success}


def neg(returned: float) -> dict:
    return {"neg": 1.0, "returned_any": returned}


def make_run() -> dict:
    return {
        "k": 5,
        "split": "dev",
        "results": {
            "m1": {"per_query": {"p1": pos(1.0), "p2": pos(0.0), "p3": pos(1.0), "p4": pos(1.0), "n1": neg(1.0), "n2": neg(0.0)}},
            "m2": {"per_query": {"p1": pos(0.0), "p2": pos(0.0), "p3": pos(1.0), "p4": pos(0.0), "n1": neg(0.0), "n2": neg(1.0)}},
        },
    }


class OriginBreakdownTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.golden = self.dir / "golden.jsonl"
        self.golden.write_text("\n".join(json.dumps(r) for r in golden_rows()) + "\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def write_run(self, run: dict) -> Path:
        path = self.dir / "run.json"
        path.write_text(json.dumps(run), encoding="utf-8")
        return path

    def test_origin(self):
        self.assertEqual(ob.origin({"id": "a"}), "antiga")
        self.assertEqual(ob.origin({"id": "a", "approval": APPROVAL}), "nova")

    def test_counts_per_group(self):
        out = ob.breakdown(make_run(), golden_rows())
        self.assertEqual(out["m1"], {"pos_antiga": (1.0, 2), "pos_nova": (2.0, 2), "neg_antiga": (1.0, 1), "neg_nova": (0.0, 1)})
        self.assertEqual(out["m2"], {"pos_antiga": (0.0, 2), "pos_nova": (1.0, 2), "neg_antiga": (0.0, 1), "neg_nova": (1.0, 1)})

    def test_unknown_id_raises(self):
        run = make_run()
        run["results"]["m1"]["per_query"]["zzz"] = pos(1.0)
        with self.assertRaises(ValueError):
            ob.breakdown(run, golden_rows())

    def test_main_prints_header_and_rows(self):
        run_path = self.write_run(make_run())
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = ob.main([str(run_path), "--golden", str(self.golden)])
        self.assertEqual(code, 0)
        lines = buf.getvalue().splitlines()
        self.assertIn("split=dev k=5", lines)
        self.assertEqual(sum(1 for l in lines if l.startswith("| m1 ")), 1)
        self.assertEqual(sum(1 for l in lines if l.startswith("| m2 ")), 1)
        self.assertIn("| m1 | 1/2 | 2/2 | 1/1 | 0/1 |", lines)

    def test_fractional_sum_one_decimal(self):
        run = make_run()
        run["results"]["m1"]["per_query"]["p1"] = pos(0.5)
        run_path = self.write_run(run)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            ob.main([str(run_path), "--golden", str(self.golden)])
        self.assertIn("| m1 | 0.5/2 |", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
