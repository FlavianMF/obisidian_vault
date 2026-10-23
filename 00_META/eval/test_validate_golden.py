"""Testes do validador do golden set, sem rede: python3 -m unittest discover -s 00_META/eval -v"""

import contextlib
import copy
import io
import json
import tempfile
import unittest
from pathlib import Path

import run_eval as ev
import validate_golden as vg

SEED = 20261023
NOTES = ["20_Permanent_Notes/A.md", "20_Permanent_Notes/B.md"]


def baseline_rows():
    rows = []
    neg_dev = 0
    for i in range(1, 43):
        qid = f"q{i:03d}"
        test = qid in vg.BASELINE_TEST
        if test:
            neg = qid in ("q003", "q006")
        else:
            neg = neg_dev < 13 and i % 2 == 0
            neg_dev += neg
        rows.append(
            {
                "id": qid, "query": f"consulta basica {i} sobre tema{i}", "lang": "pt",
                "kind": "negative" if neg else "paraphrase", "source": vg.LEGACY_SOURCE, "validated": True,
                "repo": None, "relevant": [] if neg else [{"path": NOTES[0], "grade": 2}],
                "split": "test" if test else "dev", "vault_commit": "abc1234", "status": "active",
                "created": "2026-10-14", "notes": "",
            }
        )  # fmt: skip
    assert sum(r["kind"] == "negative" for r in rows) == 15
    return rows


def new_rows(n_pos=10, n_neg=8, seed=SEED):
    rows = []
    for i in range(n_pos + n_neg):
        neg = i >= n_pos
        rows.append(
            {
                "id": f"q{43 + i:03d}", "query": f"pergunta nova {i} sobre assunto{i}", "lang": "pt",
                "kind": "negative" if neg else "paraphrase", "source": "llm", "validated": True, "repo": None,
                "relevant": [] if neg else [{"path": NOTES[1], "grade": 2}], "split": "dev", "split_seed": seed,
                "vault_commit": "abc1234", "status": "active", "created": "2026-10-23", "notes": "",
                "approval": {"by": "user", "date": "2026-10-23", "draft": f"d{i + 1:03d}", "edited": False},
            }
        )  # fmt: skip
    base = baseline_rows()
    bp = sum(r["split"] == "test" and r["kind"] != "negative" for r in base)
    bn = sum(r["split"] == "test" and r["kind"] == "negative" for r in base)
    splits = vg.assign_splits(rows, seed, bp, bn)
    for r in rows:
        r["split"] = splits[r["id"]]
    return rows


def drafts_for(rows):
    return [{"draft_id": r["approval"]["draft"], "status": "approved"} for r in rows if "approval" in r]


class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.vault = Path(self.tmp.name) / "vault"
        (self.vault / "20_Permanent_Notes").mkdir(parents=True)
        for n in NOTES:
            (self.vault / n).write_text("x", encoding="utf-8")
        self.rows = baseline_rows() + new_rows()
        self.drafts = drafts_for(self.rows)

    def floors(self, rows=None, drafts=None, parse_errors=()):
        out = vg.check(self.rows if rows is None else rows, self.drafts if drafts is None else drafts, self.vault, parse_errors)
        return {n for n, _ in out}

    def new(self, i=0):
        return next(r for r in self.rows if r["id"] == f"q{43 + i:03d}")


class Floor1to3Test(Fixture):
    def test_valid_passes_all(self):
        self.assertEqual(vg.check(self.rows, self.drafts, self.vault), [])

    def test_floor1_fewer_than_60(self):
        rows = baseline_rows() + new_rows(9, 8)
        self.assertIn(1, self.floors(rows, drafts_for(rows)))

    def test_floor1_inactive_does_not_count(self):
        self.new()["status"] = "inactive"
        self.assertIn(1, self.floors())

    def test_floor2_test_positives_and_negatives(self):
        pos = next(r for r in self.rows if r["split"] == "test" and r["kind"] != "negative" and r["id"] not in vg.BASELINE_IDS)
        pos["split"] = "dev"
        self.assertIn(2, self.floors())
        self.setUp()
        neg = next(r for r in self.rows if r["split"] == "test" and r["kind"] == "negative" and r["id"] not in vg.BASELINE_IDS)
        neg["split"] = "dev"
        self.assertIn(2, self.floors())

    def test_floor3_negative_share(self):
        rows = baseline_rows() + new_rows(36, 8)
        self.assertIn(3, self.floors(rows, drafts_for(rows)))


class Floor4Test(Fixture):
    def test_baseline_moved(self):
        next(r for r in self.rows if r["id"] == "q003")["split"] = "dev"
        self.assertIn(4, self.floors())

    def test_missing_seed(self):
        del self.new()["split_seed"]
        self.assertIn(4, self.floors())

    def test_hand_swapped_split(self):
        a = next(r for r in self.rows if r["id"] not in vg.BASELINE_IDS and r["kind"] != "negative" and r["split"] == "test")
        b = next(r for r in self.rows if r["id"] not in vg.BASELINE_IDS and r["kind"] != "negative" and r["split"] == "dev")
        a["split"], b["split"] = "dev", "test"
        self.assertEqual(self.floors(), {4})

    def test_two_seeds(self):
        self.new()["split_seed"] = SEED + 1
        self.assertIn(4, self.floors())


class Floor5Test(Fixture):
    def test_missing_path(self):
        self.new()["relevant"] = [{"path": "20_Permanent_Notes/Nope.md", "grade": 2}]
        self.assertIn(5, self.floors())

    def test_duplicate_id(self):
        dup = copy.deepcopy(self.new())
        dup["query"] = "outra coisa totalmente diferente xyz"
        self.assertIn(5, self.floors(self.rows + [dup]))

    def test_duplicate_query_exact_and_normalized(self):
        self.new(1)["query"] = self.new(0)["query"]
        self.assertIn(5, self.floors())
        self.setUp()
        self.new(0)["query"] = "Por que o Ollama?"
        self.new(1)["query"] = "por que o ollama"
        self.assertIn(5, self.floors())

    def test_duplicate_of_baseline_query(self):
        self.new()["query"] = "Consulta  BÁSICA 1 sobre tema1!"
        self.assertIn(5, self.floors())

    def test_negative_with_relevant(self):
        neg = next(r for r in self.rows if r["kind"] == "negative" and r["id"] not in vg.BASELINE_IDS)
        neg["relevant"] = [{"path": NOTES[1], "grade": 2}]
        self.assertIn(5, self.floors())

    def test_positive_without_grade2(self):
        self.new()["relevant"] = [{"path": NOTES[1], "grade": 1}]
        self.assertIn(5, self.floors())

    def test_bad_kind_and_missing_field(self):
        self.new()["kind"] = "weird"
        self.assertIn(5, self.floors())
        self.setUp()
        del self.new()["query"]
        self.assertIn(5, self.floors())

    def test_parse_errors_become_floor5(self):
        out = vg.check(self.rows, self.drafts, self.vault, [(3, "linha 3 não é JSON")])
        self.assertEqual([n for n, _ in out], [5])


class Floor6Test(Fixture):
    def test_llm_without_approval(self):
        del self.new()["approval"]
        self.assertIn(6, self.floors())

    def test_approval_by_not_user(self):
        self.new()["approval"]["by"] = "claude"
        self.assertIn(6, self.floors())

    def test_bad_date(self):
        self.new()["approval"]["date"] = "23/10/2026"
        self.assertIn(6, self.floors())

    def test_draft_missing_or_not_approved(self):
        self.assertIn(6, self.floors(drafts=self.drafts[1:]))
        drafts = copy.deepcopy(self.drafts)
        drafts[0]["status"] = "pending"
        self.assertIn(6, self.floors(drafts=drafts))

    def test_new_with_legacy_source(self):
        self.new()["source"] = vg.LEGACY_SOURCE
        self.assertIn(6, self.floors())

    def test_manual_does_not_need_draft_entry(self):
        r = self.new()
        r["source"] = "manual"
        self.assertEqual(self.floors(drafts=self.drafts[1:]), set())

    def test_baseline_source_must_be_legacy(self):
        self.rows[0]["source"] = "llm"
        self.assertIn(6, self.floors())


class AssignSplitsTest(unittest.TestCase):
    def rows(self, p, n):
        return [{"id": f"q{100 + i}", "kind": "paraphrase"} for i in range(p)] + [
            {"id": f"q{200 + i}", "kind": "negative"} for i in range(n)
        ]

    def test_quotas(self):
        rows = self.rows(10, 8)
        out = vg.assign_splits(rows, SEED, 8, 2)
        self.assertEqual(sum(out[r["id"]] == "test" for r in rows if r["kind"] != "negative"), 8)
        self.assertEqual(sum(out[r["id"]] == "test" for r in rows if r["kind"] == "negative"), 6)
        self.assertEqual(set(out.values()), {"dev", "test"})

    def test_deterministic_and_seed_sensitive(self):
        rows = self.rows(20, 16)
        self.assertEqual(vg.assign_splits(rows, SEED, 8, 2), vg.assign_splits(list(reversed(rows)), SEED, 8, 2))
        self.assertNotEqual(vg.assign_splits(rows, SEED, 8, 2), vg.assign_splits(rows, SEED + 7, 8, 2))

    def test_deficit_not_covered(self):
        with self.assertRaises(ValueError):
            vg.assign_splits(self.rows(7, 8), SEED, 8, 2)
        with self.assertRaises(ValueError):
            vg.assign_splits(self.rows(10, 5), SEED, 8, 2)


class CliTest(Fixture):
    def run_cli(self, rows, *extra, raw=None):
        g = Path(self.tmp.name) / "golden.jsonl"
        g.write_text(raw if raw is not None else "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
        d = Path(self.tmp.name) / "drafts.jsonl"
        d.write_text("".join(json.dumps(r) + "\n" for r in drafts_for(rows)), encoding="utf-8")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = vg.main(["--golden", str(g), "--drafts", str(d), "--vault", str(self.vault), *extra])
        return code, buf.getvalue()

    def test_exit_codes(self):
        code, out = self.run_cli(self.rows)
        self.assertEqual(code, 0)
        self.assertIn("piso 1: PASS", out)
        small = baseline_rows()
        code, out = self.run_cli(small)
        self.assertEqual(code, 1)
        self.assertIn("piso 1: FAIL", out)

    def test_only_ignores_other_floors(self):
        code, out = self.run_cli(baseline_rows(), "--only", "5")
        self.assertEqual(code, 0)
        self.assertNotIn("piso 1", out)

    def test_invalid_json_line_is_floor5_not_traceback(self):
        raw = "".join(json.dumps(r) + "\n" for r in self.rows) + "{nao json\n"
        code, out = self.run_cli(self.rows, raw=raw)
        self.assertEqual(code, 1)
        self.assertIn("piso 5: FAIL", out)

    def test_missing_drafts_file_is_empty(self):
        g = Path(self.tmp.name) / "g.jsonl"
        g.write_text("".join(json.dumps(r) + "\n" for r in baseline_rows()), encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            code = vg.main(["--golden", str(g), "--drafts", str(Path(self.tmp.name) / "nope.jsonl"), "--vault", str(self.vault), "--only", "4,5"])
        self.assertEqual(code, 0)


class RealFileTest(unittest.TestCase):
    def test_real_golden_floors_4_5_6_pass_today(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(vg.main(["--only", "4,5,6"]), 0)

    @unittest.skipUnless(len(ev.load_golden()) >= 60, "golden ainda tem menos de 60 queries")
    def test_real_golden_all_floors(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(vg.main([]), 0)


if __name__ == "__main__":
    unittest.main()
