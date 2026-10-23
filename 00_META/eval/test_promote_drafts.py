"""Testes da aprovação e promoção de rascunhos, sem rede: python3 -m unittest discover -s 00_META/eval -v"""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import promote_drafts as pd
import validate_golden as vg
from test_validate_golden import NOTES, baseline_rows

SEED = 20261023
TITLE = "Ollama Ignora Contexto"
TITLES = {NOTES[1]: TITLE}
DATE = "2026-10-23"


def draft(i, polarity="positive", origin="llm", **over):
    row = {
        "draft_id": f"d{i:03d}", "origin": origin, "polarity": polarity, "query": f"pergunta rascunho {i} sobre assunto{i}",
        "lang": "pt", "from_path": NOTES[1] if polarity == "positive" and origin == "llm" else None, "title_hits": 0,
        "flavor": "near" if polarity == "negative" else None, "shadow_ts": None, "model": "claude-haiku-4-5",
        "created": "2026-10-22", "status": "pending", "reason": "", "decision": None,
    }  # fmt: skip
    row.update(over)
    return row


def batch(n_pos=10, n_neg=8):
    return [draft(i) for i in range(1, n_pos + 1)] + [draft(n_pos + i, "negative") for i in range(1, n_neg + 1)]


def approve_all(drafts):
    return [{"draft_id": d["draft_id"], "decision": "approve"} for d in drafts]


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.vault = self.root / "vault"
        (self.vault / "20_Permanent_Notes").mkdir(parents=True)
        for n in NOTES:
            (self.vault / n).write_text("x", encoding="utf-8")
        self.golden = self.root / "golden.jsonl"
        self.golden.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in baseline_rows()), encoding="utf-8")
        self.drafts = self.root / "drafts.jsonl"

    def write_drafts(self, rows):
        self.drafts.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")

    def approved_batch(self, n_pos=10, n_neg=8):
        rows = batch(n_pos, n_neg)
        done = pd.apply_decisions(rows, approve_all(rows), DATE, self.vault, TITLES)
        self.write_drafts(done)
        return done

    def promote(self, **kw):
        args = dict(golden_path=self.golden, drafts_path=self.drafts, seed=SEED, vault=self.vault, today=DATE,
                    commit_fn=lambda: "abc1234")  # fmt: skip
        args.update(kw)
        return pd.promote(**args)


class DecideTest(Base):
    def decide(self, rows, decisions):
        return pd.apply_decisions(rows, decisions, DATE, self.vault, TITLES)

    def test_llm_positive_gets_from_path_grade2(self):
        out = self.decide([draft(1)], [{"draft_id": "d001", "decision": "approve"}])[0]
        self.assertEqual(out["status"], "approved")
        d = out["decision"]
        self.assertEqual(d["by"], "user")
        self.assertEqual(d["date"], DATE)
        self.assertFalse(d["edited"])
        self.assertEqual(d["kind"], "paraphrase")
        self.assertEqual(d["relevant"], [{"path": NOTES[1], "grade": 2}])

    def test_extra_relevant_only_grade1(self):
        ok = self.decide([draft(1)], [{"draft_id": "d001", "decision": "approve", "relevant": [{"path": NOTES[0], "grade": 1}]}])[0]
        self.assertEqual(len(ok["decision"]["relevant"]), 2)
        with self.assertRaises(ValueError):
            self.decide([draft(1)], [{"draft_id": "d001", "decision": "approve", "relevant": [{"path": NOTES[0], "grade": 2}]}])

    def test_edit_rechecks_title_hits(self):
        out = self.decide([draft(1)], [{"draft_id": "d001", "decision": "approve", "query": "como o modelo local esquece o começo"}])[0]
        self.assertTrue(out["decision"]["edited"])
        self.assertEqual(out["decision"]["query"], "como o modelo local esquece o começo")
        with self.assertRaisesRegex(ValueError, "title_hits"):
            self.decide([draft(1)], [{"draft_id": "d001", "decision": "approve", "query": "Ollama ignora o contexto"}])

    def test_shadow_needs_kind_and_relevant(self):
        sh = draft(1, None, origin="shadow", shadow_ts="t1")
        with self.assertRaisesRegex(ValueError, "kind"):
            self.decide([sh], [{"draft_id": "d001", "decision": "approve"}])
        with self.assertRaisesRegex(ValueError, "grau 2"):
            self.decide([sh], [{"draft_id": "d001", "decision": "approve", "kind": "lexical"}])
        out = self.decide([sh], [{"draft_id": "d001", "decision": "approve", "kind": "lexical", "relevant": [{"path": NOTES[0], "grade": 2}]}])[0]
        self.assertEqual(out["polarity"], "positive")
        neg = self.decide([sh], [{"draft_id": "d001", "decision": "approve", "kind": "negative"}])[0]
        self.assertEqual((neg["polarity"], neg["decision"]["relevant"]), ("negative", []))

    def test_negative_forces_empty_relevant(self):
        out = self.decide(
            [draft(1, "negative")], [{"draft_id": "d001", "decision": "approve", "relevant": [{"path": NOTES[0], "grade": 2}]}]
        )[0]  # fmt: skip
        self.assertEqual((out["decision"]["kind"], out["decision"]["relevant"]), ("negative", []))

    def test_missing_path_fails(self):
        with self.assertRaises(ValueError):
            self.decide([draft(1)], [{"draft_id": "d001", "decision": "approve", "relevant": [{"path": "nope.md", "grade": 1}]}])

    def test_reject_unknown_and_not_pending(self):
        out = self.decide([draft(1)], [{"draft_id": "d001", "decision": "reject"}])[0]
        self.assertEqual((out["status"], out["decision"]["by"]), ("rejected", "user"))
        with self.assertRaisesRegex(ValueError, "d009"):
            self.decide([draft(1)], [{"draft_id": "d009", "decision": "reject"}])
        with self.assertRaises(ValueError):
            self.decide([draft(1, status="auto_rejected")], [{"draft_id": "d001", "decision": "approve"}])
        with self.assertRaises(ValueError):
            self.decide([draft(1)], [{"draft_id": "d001", "decision": "talvez"}])

    def test_input_not_mutated(self):
        rows = [draft(1)]
        self.decide(rows, [{"draft_id": "d001", "decision": "approve"}])
        self.assertEqual(rows[0]["status"], "pending")

    def test_cli_decide_rewrites_file_and_review_lists(self):
        self.write_drafts([draft(1), draft(2, "negative")])
        dec = self.root / "decisions.json"
        dec.write_text(json.dumps([{"draft_id": "d001", "decision": "approve"}, {"draft_id": "d002", "decision": "reject"}]), encoding="utf-8")
        mdir = self.root / "m"
        mdir.mkdir()
        (mdir / "pattern.md").write_text(
            "| Path | Title | Tags | Created | Provenance | Confidence | Seen in | Summary |\n| --- | --- | --- | --- | --- | --- | --- | --- |\n"
            f"| {NOTES[1]} | {TITLE} | docker | 2026-01-01 | x |  |  | resumo |\n", encoding="utf-8")  # fmt: skip
        common = ["--drafts", str(self.drafts), "--manifests", str(mdir), "--vault", str(self.vault)]
        pre = io.StringIO()
        with contextlib.redirect_stdout(pre):
            pd.main(["review", *common])
        self.assertIn("d001", pre.getvalue())
        self.assertIn(TITLE, pre.getvalue())
        self.assertIn("| draft_id |", pre.getvalue())
        with contextlib.redirect_stdout(io.StringIO()):
            pd.main(["decide", "--file", str(dec), "--date", DATE, *common])
        rows = [json.loads(x) for x in self.drafts.read_text().splitlines()]
        self.assertEqual([r["status"] for r in rows], ["approved", "rejected"])
        self.assertEqual([p.name for p in self.root.iterdir() if p.suffix == ".tmp"], [])


class AssignSplitsViaPromoteTest(Base):
    def test_deficit_is_exact(self):
        rows = [{"id": f"q{100 + i}", "kind": "paraphrase"} for i in range(10)] + [
            {"id": f"q{200 + i}", "kind": "negative"} for i in range(8)
        ]
        out = vg.assign_splits(rows, SEED, 8, 2)
        self.assertEqual(sum(v == "test" for k, v in out.items() if k.startswith("q1")), 8)
        self.assertEqual(sum(v == "test" for k, v in out.items() if k.startswith("q2")), 6)


class PromoteTest(Base):
    def test_promote_writes_valid_golden_and_keeps_baseline(self):
        self.approved_batch()
        before = self.golden.read_bytes()
        self.promote()
        after = self.golden.read_bytes()
        self.assertTrue(after.startswith(before))
        rows = [json.loads(x) for x in after.decode().splitlines()]
        self.assertEqual(len(rows), 60)
        new = rows[42:]
        self.assertEqual(new[0]["id"], "q043")
        self.assertEqual(new[-1]["id"], "q060")
        for r in new:
            self.assertEqual(r["split_seed"], SEED)
            self.assertEqual(r["vault_commit"], "abc1234")
            self.assertEqual(r["approval"]["by"], "user")
            self.assertEqual(r["source"], "llm")
            self.assertEqual(r["status"], "active")
        self.assertEqual(vg.check(rows, [json.loads(x) for x in self.drafts.read_text().splitlines()], self.vault), [])
        self.assertEqual(sum(r["split"] == "test" for r in new), 14)

    def test_same_seed_same_split_other_seed_differs(self):
        self.approved_batch(14, 12)
        a = self.promote(dry_run=True)
        b = self.promote(dry_run=True)
        c = self.promote(dry_run=True, seed=SEED + 5)
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)

    def test_refuses_second_batch(self):
        self.approved_batch()
        self.promote()
        with self.assertRaisesRegex(ValueError, "split_seed"):
            self.promote()

    def test_does_not_write_when_validator_fails(self):
        self.approved_batch(10, 7)  # 59 queries: piso 1 falha
        before = self.golden.read_bytes()
        with self.assertRaises(ValueError):
            self.promote()
        self.assertEqual(self.golden.read_bytes(), before)

    def test_does_not_write_when_deficit_not_covered(self):
        self.approved_batch(5, 8)
        before = self.golden.read_bytes()
        with self.assertRaises(ValueError):
            self.promote()
        self.assertEqual(self.golden.read_bytes(), before)

    def test_dry_run_does_not_write(self):
        self.approved_batch()
        before = self.golden.read_bytes()
        text = self.promote(dry_run=True)
        self.assertEqual(self.golden.read_bytes(), before)
        self.assertIn("q043", text)
        self.assertIn("| id | split | kind | query |", text)

    def test_duplicate_of_baseline_query_is_blocked(self):
        rows = batch()
        rows[0]["query"] = "Consulta básica 1 sobre tema1"
        self.write_drafts(pd.apply_decisions(rows, approve_all(rows), DATE, self.vault, TITLES))
        before = self.golden.read_bytes()
        with self.assertRaises(ValueError):
            self.promote()
        self.assertEqual(self.golden.read_bytes(), before)

    def test_edited_query_is_used(self):
        rows = batch()
        decisions = approve_all(rows)
        decisions[0]["query"] = "texto editado pelo usuario sobre outro assunto"
        self.write_drafts(pd.apply_decisions(rows, decisions, DATE, self.vault, TITLES))
        self.promote()
        new = [json.loads(x) for x in self.golden.read_text().splitlines()][42:]
        self.assertEqual(new[0]["query"], "texto editado pelo usuario sobre outro assunto")
        self.assertTrue(new[0]["approval"]["edited"])

    def test_cli_promote_dry_run(self):
        self.approved_batch()
        out = io.StringIO()
        with mock.patch.object(pd, "git_commit", lambda: "abc1234"), contextlib.redirect_stdout(out):
            code = pd.main(["promote", "--seed", str(SEED), "--dry-run", "--golden", str(self.golden), "--drafts", str(self.drafts), "--vault", str(self.vault)])
        self.assertEqual(code, 0)
        self.assertIn("q060", out.getvalue())


if __name__ == "__main__":
    unittest.main()
