"""Testes do usage_baseline.sh: python3 -m unittest discover -s 00_META/eval -v"""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("usage_baseline.sh")


def assistant(msg_id, ts, out, read, create, inp, model="claude-x", side=False):
    return {
        "type": "assistant",
        "isSidechain": side,
        "timestamp": ts,
        "message": {
            "id": msg_id,
            "model": model,
            "content": [{"type": "text", "text": "segredo que não pode vazar"}],
            "usage": {
                "output_tokens": out,
                "cache_read_input_tokens": read,
                "cache_creation_input_tokens": create,
                "input_tokens": inp,
            },
        },
    }


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


def run(*args):
    out = subprocess.run(["bash", str(SCRIPT), *args], capture_output=True, text=True, check=True)
    return [line.split("\t") for line in out.stdout.splitlines()]


class UsageBaselineTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.main = root / "abcdef12-sess.jsonl"
        # m2 vem antes no arquivo mas tem timestamp maior; m1 aparece duas vezes (dois blocos).
        write_jsonl(self.main, [
            {"type": "user", "message": {"content": "oi"}},
            assistant("m2", "2026-01-01T00:00:02Z", 5, 1000, 0, 1),
            assistant("m1", "2026-01-01T00:00:01Z", 10, 0, 400, 2),
            assistant("m1", "2026-01-01T00:00:01Z", 10, 0, 400, 2),
        ])
        sub = root / "abcdef12-sess" / "subagents" / "agent-a1.jsonl"
        write_jsonl(sub, [
            assistant("s1", "2026-01-01T00:00:03Z", 7, 200, 100, 3, model="claude-haiku", side=True),
            assistant("s1", "2026-01-01T00:00:03Z", 7, 200, 100, 3, model="claude-haiku", side=True),
        ])
        (sub.parent / "agent-a1.meta.json").write_text(
            json.dumps({"agentType": "Explore", "description": "texto livre"}), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_default_dedups_by_message_id_and_keeps_first_context(self):
        rows = run(str(self.main))
        self.assertEqual(rows, [["abcdef12", "402", "2", "15", "1000", "400", "3"]])

    def test_sidechain_splits_main_and_subagents(self):
        rows = run("--sidechain", str(self.main))
        self.assertEqual(rows[0], ["abcdef12", "main", "-", "claude-x", "2", "15", "1000", "400", "3", "603"])
        self.assertEqual(rows[1], ["abcdef12", "sub", "Explore", "claude-haiku", "1", "7", "200", "100", "3", "148"])

    def test_never_prints_content_or_description(self):
        out = subprocess.run(["bash", str(SCRIPT), "--sidechain", str(self.main)],
                             capture_output=True, text=True, check=True).stdout
        self.assertNotIn("segredo", out)
        self.assertNotIn("texto livre", out)


def read_msg(ts, *calls):
    return {"type": "assistant", "timestamp": ts, "message": {"id": "r" + ts, "content": [
        {"type": "tool_use", "id": i, "name": n, "input": {"file_path": p}} for i, n, p in calls]}}


class RereadsAndRouterTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.main = self.root / "abcdef12-sess.jsonl"
        write_jsonl(self.main, [
            read_msg("2026-01-01T00:00:01Z", ("t1", "Read", "/x/a.md"), ("t2", "Bash", "/x/zzz")),
            read_msg("2026-01-01T00:00:01Z", ("t1", "Read", "/x/a.md")),  # duplicado por id
        ])
        sd = self.root / "abcdef12-sess" / "subagents"
        write_jsonl(sd / "agent-a1.jsonl", [read_msg("2026-01-01T00:00:03Z", ("u1", "Read", "/x/a.md"))])
        write_jsonl(sd / "agent-a2.jsonl", [
            read_msg("2026-01-01T00:00:05Z", ("v1", "Read", "/x/a.md"), ("v2", "Read", "/x/b.md"))])
        write_jsonl(sd / "agent-a3.jsonl", [assistant("s", "2026-01-01T00:00:09Z", 1, 1, 1, 1, side=True)])

    def tearDown(self):
        self.tmp.cleanup()

    def env_run(self, state, *args):
        import os
        env = {**os.environ, "SECOND_BRAIN_STATE_DIR": str(state)}
        out = subprocess.run(["bash", str(SCRIPT), *args], capture_output=True, text=True, check=True, env=env)
        return [line.split("\t") for line in out.stdout.splitlines()]

    def test_rereads_counts_by_id_and_cross_agent_repeats(self):
        rows = self.env_run(self.root, "--rereads", str(self.main))
        # main 1 (dedup), subs 3, a2 relê a.md de a1 -> 1 repetida (a1 foi o primeiro), a.md em main e sub -> 1
        self.assertEqual(rows, [["abcdef12", "1", "3", "1", "1"]])

    def test_rereads_prints_no_paths(self):
        out = subprocess.run(["bash", str(SCRIPT), "--rereads", str(self.main)],
                             capture_output=True, text=True, check=True).stdout
        self.assertNotIn("/x/", out)

    def test_router_row_zero_without_file(self):
        rows = self.env_run(self.root / "vazio", "--sidechain", str(self.main))
        self.assertEqual(rows[-1], ["abcdef12", "router", "-", "-", "0", "0"])

    def test_router_row_counts_fires_and_subagents_after_first(self):
        state = self.root / "state"
        state.mkdir()
        lines = [
            {"ts": "2026-01-01T00:00:04Z", "session_id": "abcdef12-sess", "class": "qualquer coisa"},
            {"ts": "2026-01-01T00:00:08Z", "session_id": "abcdef12-sess", "class": "x"},
            {"ts": "2026-01-01T00:00:01Z", "session_id": "outra", "class": "x"},
        ]
        (state / "router.jsonl").write_text("".join(json.dumps(r) + "\n" for r in lines), encoding="utf-8")
        rows = self.env_run(state, "--sidechain", str(self.main))
        # a2 (00:05) e a3 (00:09) começam depois de 00:04; a1 (00:03) não.
        self.assertEqual(rows[-1], ["abcdef12", "router", "-", "-", "2", "2"])


if __name__ == "__main__":
    unittest.main()
