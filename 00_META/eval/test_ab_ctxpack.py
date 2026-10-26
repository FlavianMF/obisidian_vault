"""Testes do ab_ctxpack.py: python3 -m unittest discover -s 00_META/eval -v"""

import io
import json
import os
import random
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

import ab_ctxpack as ab


def metrics(task, arm, grade, sub_eq, repeated, subs=2):
    return {"task": task, "arm": arm, "grade": grade, "main_eq": 100, "sub_eq": sub_eq,
            "reads_sub": 10, "repeated": repeated, "subs": subs}


class PlanTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tasks_file(self, text):
        path = self.tmp / "tasks.tsv"
        path.write_text(text, encoding="utf-8")
        return path

    def test_each_task_gets_both_arms_with_distinct_sessions(self):
        path = self.tasks_file(f"# comentário\na\t{self.tmp}\tfaça A\nb\t{self.tmp}\tfaça B\n")
        runs = ab.plan(ab.load_tasks(path), random.Random(1))
        self.assertEqual(len(runs), 4)
        for task in ("a", "b"):
            self.assertEqual(sorted(r["arm"] for r in runs if r["task"] == task), sorted(ab.ARMS))
        self.assertEqual(len({r["session"] for r in runs}), 4)

    def test_reps_make_one_pair_per_rep_and_verdict_counts_each_pair(self):
        path = self.tasks_file(f"a\t{self.tmp}\tfaça A\n")
        runs = ab.plan(ab.load_tasks(path), random.Random(1), reps=3)
        self.assertEqual([r["slot"] for r in runs], [f"{i}/6" for i in range(1, 7)])
        for rep in ("1", "2", "3"):
            self.assertEqual(sorted(r["arm"] for r in runs if r["rep"] == rep), sorted(ab.ARMS))
        rows = [{**metrics("a", r["arm"], "pass", 1000 if r["arm"] == "shadow" else 800, 4), "rep": r["rep"]} for r in runs]
        self.assertEqual(ab.verdict(rows)["valid"], 3)

    def test_bad_lines_are_rejected(self):
        for text in (f"a\t{self.tmp}\n", "a\t/nao/existe\tp\n", f"a\t{self.tmp}\tp\na\t{self.tmp}\tq\n"):
            with self.assertRaises(ValueError):
                ab.load_tasks(self.tasks_file(text))

    def test_state_files_are_private(self):
        path = self.tmp / "st" / "runs.tsv"
        ab.write_private(path, [{"x": "1"}], ["x"])
        self.assertEqual(os.stat(path).st_mode & 0o777, 0o600)
        self.assertEqual(ab.read_rows(path), [{"x": "1"}])


class VerdictTest(unittest.TestCase):
    def test_keeps_active_when_both_floors_are_met(self):
        rows = [metrics("t", "shadow", "pass", 1000, 10), metrics("t", "active", "pass", 800, 5)]
        v = ab.verdict(rows)
        self.assertEqual(v["decision"], "mantém active")
        self.assertAlmostEqual(v["reread_drop"], 0.5)
        self.assertAlmostEqual(v["sub_eq_drop"], 0.2)

    def test_regression_turns_it_off(self):
        rows = [metrics("t", "shadow", "pass", 1000, 10), metrics("t", "active", "fail", 500, 0)]
        v = ab.verdict(rows)
        self.assertEqual(v["regressions"], ["t"])
        self.assertTrue(v["decision"].startswith("desliga"))

    def test_gain_below_floor_turns_it_off(self):
        rows = [metrics("t", "shadow", "pass", 1000, 10), metrics("t", "active", "pass", 950, 5)]
        self.assertTrue(ab.verdict(rows)["decision"].startswith("desliga"))

    def test_task_with_one_subagent_is_invalid(self):
        rows = [metrics("t", "shadow", "pass", 1000, 10, subs=1), metrics("t", "active", "pass", 800, 5)]
        v = ab.verdict(rows)
        self.assertEqual(v["valid"], 0)
        self.assertEqual(v["decision"], "incompleto")

    def test_missing_grade_is_incomplete(self):
        rows = [metrics("t", "shadow", "-", 1000, 10), metrics("t", "active", "pass", 800, 5)]
        self.assertEqual(ab.verdict(rows)["decision"], "incompleto")


class CliTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.projects = self.tmp / "projects"
        (self.projects / "p").mkdir(parents=True)
        self.env = mock.patch.dict(os.environ, {"SECOND_BRAIN_STATE_DIR": str(self.tmp / "state")})
        self.env.start()
        self.addCleanup(self.env.stop)
        tasks = self.tmp / "tasks.tsv"
        tasks.write_text(f"t\t{self.tmp}\tprompt\n", encoding="utf-8")
        self.call("plan", str(tasks), "--seed", "3")
        self.runs = ab.read_rows(ab.state_dir() / ab.RUNS)

    def call(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = ab.main(["--projects", str(self.projects), *argv])
        return code, out.getvalue(), err.getvalue()

    def test_status_does_not_reveal_the_arm(self):
        code, out, _ = self.call("status")
        self.assertEqual(code, 0)
        self.assertNotIn("shadow", out)
        self.assertNotIn("active", out)

    def test_report_stays_blind_until_every_session_is_graded(self):
        code, out, err = self.call("report")
        self.assertEqual(code, 1)
        self.assertNotIn("shadow", out + err)
        self.assertEqual(self.call("grade", self.runs[0]["session"][:8], "pass")[0], 0)
        self.assertEqual(self.call("grade", self.runs[1]["session"][:8], "pass")[0], 0)
        for r in self.runs:
            row = {"type": "assistant", "timestamp": "2026-10-26T10:00:00Z",
                   "message": {"id": r["session"], "model": "m", "content": [],
                               "usage": {"output_tokens": 1, "input_tokens": 10}}}
            (self.projects / "p" / f"{r['session']}.jsonl").write_text(json.dumps(row) + "\n")
        code, out, _ = self.call("report")
        self.assertEqual(code, 0)
        self.assertIn("menos de 2 subagentes", out)
        self.assertIn("decisão D1: incompleto", out)

    def test_run_is_headless_read_only_and_sets_the_arm(self):
        seen = {}

        def fake_run(argv, cwd, env, input, **kw):
            seen.update(argv=argv, arm=env["SB_CTXPACK"], input=input)
            return mock.Mock(returncode=0, stdout="resposta", stderr="")

        with mock.patch.object(ab.subprocess, "run", fake_run):
            code, out, _ = self.call("run")
        self.assertEqual(code, 0)
        self.assertEqual(seen["arm"], self.runs[0]["arm"])
        self.assertNotIn(self.runs[0]["arm"], out)
        self.assertIn("-p", seen["argv"])
        self.assertIn(f"--allowedTools={ab.READ_ONLY_TOOLS}", seen["argv"])
        self.assertNotIn("prompt", seen["argv"])
        self.assertEqual(seen["input"], "prompt")
        saved = ab.state_dir() / "out" / f"{self.runs[0]['session']}.txt"
        self.assertEqual(saved.read_text(), "resposta")

    def test_requeue_gives_new_session_same_arm(self):
        old = self.runs[0]
        self.call("grade", old["session"][:8], "fail")
        code, out, _ = self.call("requeue", old["session"][:8])
        self.assertEqual(code, 0)
        self.assertNotIn(old["arm"], out)
        new = ab.read_rows(ab.state_dir() / ab.RUNS)[0]
        self.assertNotEqual(new["session"], old["session"])
        self.assertEqual((new["arm"], new["task"], new["slot"]), (old["arm"], old["task"], old["slot"]))
        self.assertEqual(ab.read_rows(ab.state_dir() / ab.GRADES), [])

    def test_plan_refuses_to_overwrite_without_force(self):
        code, _, err = self.call("plan", str(self.tmp / "tasks.tsv"))
        self.assertEqual(code, 1)
        self.assertIn("--force", err)


if __name__ == "__main__":
    unittest.main()
