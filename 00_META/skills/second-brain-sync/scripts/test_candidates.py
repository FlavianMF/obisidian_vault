"""Testes da fila de candidatos (I3): python3 -m unittest discover -s 00_META/skills/second-brain-sync/scripts -v

Credenciais abaixo são FALSAS e montadas em tempo de execução.
"""

import datetime as dt
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import candidates
import sb
from lib import secret_scan  # noqa: F401  (the scanner the queue relies on)

SB = Path(sb.__file__)


def fake_token() -> str:
    return "".join(["ghp_", "A1b2C3d4E5f6G7h8I9j0", "K1l2M3n4O5p6Q7r8S9t0"])


class QueueFixture(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.state = Path(self._tmp.name) / "state"

    def add(self, title="Quoting do zsh quebra o hook", kind="trap", **kw):
        return candidates.add(self.state, kind=kind, title=title, summary=kw.pop("summary", "x"),
                              project=kw.pop("project", "dotfiles"), **kw)

    def write_raw(self, entries):
        self.state.mkdir(parents=True, exist_ok=True)
        text = "".join((e if isinstance(e, str) else json.dumps(e)) + "\n" for e in entries)
        candidates.queue_path(self.state).write_text(text)

    @staticmethod
    def entry(title, days_old, kind="trap"):
        ts = (candidates.utcnow() - dt.timedelta(days=days_old)).isoformat(timespec="seconds")
        return {"id": candidates.candidate_id(kind, title, "p"), "ts": ts, "kind": kind, "title": title,
                "summary": "", "project": "p", "source": "agent"}


class AddTest(QueueFixture):
    def test_add_writes_one_line_with_mode_0600(self):
        cid, created = self.add()
        self.assertTrue(created)
        path = candidates.queue_path(self.state)
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(self.state.stat().st_mode), 0o700)
        lines = path.read_text().splitlines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(json.loads(lines[0])["id"], cid)

    def test_identical_candidate_is_queued_once(self):
        self.add()
        _, created = self.add(title="  quoting do ZSH   quebra o hook ")
        self.assertFalse(created)
        self.assertEqual(len(candidates.load(self.state)[0]), 1)

    def test_same_title_in_another_project_is_a_new_candidate(self):
        self.add()
        _, created = self.add(project="outro")
        self.assertTrue(created)

    def test_refuses_a_secret_and_never_echoes_it(self):
        token = fake_token()
        with self.assertRaises(candidates.QueueError) as ctx:
            self.add(summary=f"usei {token} no curl")
        self.assertNotIn(token, str(ctx.exception))
        self.assertFalse(candidates.queue_path(self.state).exists())

    def test_refuses_bad_kind_empty_title_and_long_text(self):
        for kwargs in ({"kind": "note"}, {"title": "  "}, {"title": "x" * 121}, {"summary": "y" * 501}):
            with self.assertRaises(candidates.QueueError, msg=str(kwargs)):
                self.add(**kwargs)

    def test_newlines_in_text_collapse_so_one_candidate_is_one_line(self):
        self.add(summary="linha um\nlinha dois")
        self.assertEqual(len(candidates.queue_path(self.state).read_text().splitlines()), 1)


class TtlTest(QueueFixture):
    def test_expired_candidates_are_not_live_and_prune_is_a_dry_run_by_default(self):
        self.write_raw([self.entry("velho", 31), self.entry("novo", 2)])
        items, _ = candidates.load(self.state)
        self.assertEqual([i.title for i in candidates.live(items)], ["novo"])
        removed = candidates.prune(self.state, apply=False)
        self.assertEqual([r.title for r in removed], ["velho"])
        self.assertEqual(len(candidates.read_lines(candidates.queue_path(self.state))), 2)

    def test_prune_apply_drops_expired_keeps_the_rest_and_the_mode(self):
        self.write_raw([self.entry("velho", 30), self.entry("novo", 29), "linha quebrada"])
        candidates.prune(self.state, apply=True)
        path = candidates.queue_path(self.state)
        kept = path.read_text().splitlines()
        self.assertEqual(len(kept), 2)
        self.assertIn("linha quebrada", kept)
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)

    def test_list_flags_candidates_in_the_last_week(self):
        self.write_raw([self.entry("quase", 24), self.entry("fresco", 3)])
        items, bad = candidates.load(self.state)
        text = candidates.format_list(candidates.live(items), 0, bad)
        quase = next(line for line in text.splitlines() if "quase" in line)
        fresco = next(line for line in text.splitlines() if "fresco" in line)
        self.assertIn("expires soon", quase)
        self.assertNotIn("expires soon", fresco)

    def test_summary_line_counts_pending_soon_expired_and_unreadable(self):
        self.write_raw([self.entry("a", 25), self.entry("b", 1), self.entry("c", 40), "lixo"])
        self.assertEqual(candidates.summary_line(self.state),
                         "2 pending, 1 expire within 7 days, 1 expired, 1 unreadable")

    def test_empty_queue_summary(self):
        self.assertEqual(candidates.summary_line(self.state), "0 pending")


class CliTest(QueueFixture):
    def run_sb(self, *args):
        env = dict(os.environ, SECOND_BRAIN_STATE_DIR=str(self.state))
        return subprocess.run([sys.executable, str(SB), "candidate", *args], capture_output=True, text=True, env=env)

    def test_add_then_list_then_prune_dry_run(self):
        added = self.run_sb("add", "--kind", "trap", "--title", "Hook sem aspas", "--summary", "s", "--project", "dotfiles")
        self.assertEqual((added.returncode, added.stdout.startswith("queued: ")), (0, True))
        again = self.run_sb("add", "--kind", "trap", "--title", "Hook sem aspas", "--project", "dotfiles")
        self.assertIn("already queued", again.stdout)
        listed = self.run_sb("list")
        self.assertIn("dotfiles: Hook sem aspas", listed.stdout)
        self.assertIn("queue: 1 pending", listed.stdout)
        self.assertIn("nothing expired", self.run_sb("prune").stdout)

    def test_secret_exits_two_with_label_only(self):
        token = fake_token()
        result = self.run_sb("add", "--kind", "trap", "--title", "t", "--summary", token)
        self.assertEqual(result.returncode, 2)
        self.assertNotIn(token, result.stdout + result.stderr)

    def test_list_json_is_parsable(self):
        self.run_sb("add", "--kind", "pattern", "--title", "Fila local", "--project", "p")
        data = json.loads(self.run_sb("list", "--json").stdout)
        self.assertEqual([d["title"] for d in data], ["Fila local"])
        self.assertEqual(data[0]["days_left"], 30)

    def test_status_shows_the_queue(self):
        vault = Path(self._tmp.name) / "vault"
        (vault / "20_Permanent_Notes").mkdir(parents=True)
        self.add()
        text = sb.run_status(vault, self.state, {})
        self.assertIn("candidates: 1 pending", text)


if __name__ == "__main__":
    unittest.main()
