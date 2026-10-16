"""Testes do observer determinístico: python3 -m unittest discover -s 00_META/skills/second-brain-sync/scripts -v

Credenciais abaixo são FALSAS e montadas em tempo de execução.
"""

import json
import os
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

import candidates
import observe
import sb

SB = Path(sb.__file__)


def payload(tool="Read", path="/repo/a.py", response="x", session="s1", **extra):
    return {"session_id": session, "tool_name": tool, "tool_input": {"file_path": path},
            "tool_response": response, **extra}


class ObserveFixture(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.state = Path(self._tmp.name) / "state"


class RecordTest(ObserveFixture):
    def test_writes_metadata_only_with_mode_0600(self):
        secret_body = "".join(["ghp_", "A1b2C3d4E5f6G7h8I9j0", "K1l2M3n4O5p6Q7r8S9t0"])
        self.assertTrue(observe.record(self.state, payload(response=secret_body)))
        path = observe.log_path(self.state, "s1")
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        self.assertNotIn("ghp_", path.read_text())
        entry = json.loads(path.read_text())
        self.assertEqual((entry["tool"], entry["path"], entry["size"]), ("Read", "/repo/a.py", len(secret_body)))

    def test_bash_command_is_never_stored(self):
        data = {"session_id": "s1", "tool_name": "Bash", "tool_input": {"command": "curl -H 'x: SEGREDO' u"},
                "tool_response": "ok"}
        observe.record(self.state, data)
        self.assertNotIn("SEGREDO", observe.log_path(self.state, "s1").read_text())

    def test_secret_paths_and_subagents_are_skipped(self):
        for skipped in ("/home/u/.ssh/id_rsa", "/home/u/.aws/credentials", "/r/.env.local", "/d/secrets/k.env"):
            self.assertFalse(observe.record(self.state, payload(path=skipped)))
        self.assertFalse(observe.record(self.state, payload(agent_id="sub1")))
        self.assertFalse(observe.log_path(self.state, "s1").exists())

    def test_session_id_cannot_escape_the_log_directory(self):
        observe.record(self.state, payload(session="../../evil"))
        files = list((self.state / observe.LOG_DIR).iterdir())
        self.assertEqual([f.name for f in files], ["evil.jsonl"])

    def test_old_logs_are_dropped_when_a_new_session_starts(self):
        observe.record(self.state, payload(session="old"))
        old = observe.log_path(self.state, "old")
        past = time.time() - (observe.LOG_TTL_DAYS + 1) * 86400
        os.utime(old, (past, past))
        observe.record(self.state, payload(session="new"))
        self.assertFalse(old.exists())


class SummarizeTest(ObserveFixture):
    def test_reread_and_big_read_become_candidates(self):
        for _ in range(3):
            observe.record(self.state, payload(path="/repo/big.py", response="y" * 50_000))
        result = observe.summarize(self.state, "s1", "repo")
        self.assertEqual((result["calls"], result["findings"], result["queued"]), (3, 2, 2))
        items, _ = candidates.load(self.state)
        self.assertEqual({i.source for i in items}, {"observer"})
        self.assertTrue(all(i.project == "repo" for i in items))

    def test_summarize_twice_does_not_duplicate(self):
        for _ in range(3):
            observe.record(self.state, payload())
        observe.summarize(self.state, "s1", "repo")
        again = observe.summarize(self.state, "s1", "repo")
        self.assertEqual(again["queued"], 0)
        self.assertEqual(len(candidates.load(self.state)[0]), 1)

    def test_at_most_max_candidates(self):
        for n in range(6):
            for _ in range(3):
                observe.record(self.state, payload(path=f"/repo/f{n}.py"))
        self.assertEqual(observe.summarize(self.state, "s1", "repo")["queued"], observe.MAX_CANDIDATES)

    def test_quiet_session_queues_nothing(self):
        observe.record(self.state, payload())
        self.assertEqual(observe.summarize(self.state, "s1", "repo")["queued"], 0)

    def test_expensive_turns_count_numbers_only(self):
        transcript = Path(self._tmp.name) / "t.jsonl"
        lines = [{"type": "assistant", "message": {"usage": {"cache_creation_input_tokens": n}, "content": "SEGREDO"}}
                 for n in (100, 40_000, 90_000)]
        transcript.write_text("\n".join(json.dumps(x) for x in lines) + "\nnot json\n")
        self.assertEqual(observe.expensive_turns(transcript), 2)
        self.assertEqual(observe.expensive_turns(Path(self._tmp.name) / "missing"), 0)


class CliTest(ObserveFixture):
    def run_sb(self, *argv, stdin=""):
        env = dict(os.environ, SECOND_BRAIN_STATE_DIR=str(self.state))
        return subprocess.run([sys.executable, str(SB), *argv], input=stdin, capture_output=True, text=True,
                              env=env, check=False)

    def test_record_then_summarize_through_the_cli(self):
        for _ in range(3):
            done = self.run_sb("observe", "record", stdin=json.dumps(payload()))
            self.assertEqual((done.returncode, done.stdout), (0, ""))
        out = self.run_sb("observe", "summarize", "--session", "s1", "--project", "repo")
        self.assertEqual(out.returncode, 0)
        self.assertIn("1 queued", out.stdout)

    def test_record_ignores_garbage_on_stdin(self):
        self.assertEqual(self.run_sb("observe", "record", stdin="not json").returncode, 0)


if __name__ == "__main__":
    unittest.main()
