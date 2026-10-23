"""Testes do gerador de reformulações, sem rede: python3 -m unittest discover -s 00_META/eval -v"""

import contextlib
import io
import json
import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import gen_rewrites as gr
import run_eval as ev

FAKE = r'''#!/usr/bin/env python3
import json, os, sys, time
mode = os.environ.get("FAKE_MODE", "ok")
stdin = sys.stdin.read()
cap = os.environ.get("FAKE_CAPTURE")
if cap:
    json.dump({"argv": sys.argv, "cwd": os.getcwd(), "stdin": stdin, "env_keys": sorted(os.environ)}, open(cap, "w"))
if mode == "fail_if_called":
    sys.exit(3)
if mode == "sleep":
    time.sleep(30)
haiku = {"claude-haiku-4-5-20251001": {"inputTokens": 1}}
body = json.dumps({"rewrites": ["alpha uma", "beta two", "gamma tres"]})
env = {"type": "result", "subtype": "success", "is_error": False, "result": body, "modelUsage": haiku}
if mode == "fenced":
    env["result"] = "```json\n" + body + "\n```"
elif mode == "garbage":
    env["result"] = "não é json"
elif mode == "is_error":
    env["is_error"] = True
    env["subtype"] = "error_during_execution"
elif mode == "sonnet":
    env["modelUsage"] = {"claude-sonnet-4-5": {"inputTokens": 1}}
print(json.dumps(env))
'''


def make_fake(tmp: str) -> str:
    path = Path(tmp) / "fakeclaude"
    path.write_text(FAKE, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | 0o755)
    return str(path)


def envelope(**over):
    env = {
        "is_error": False,
        "subtype": "success",
        "result": json.dumps({"rewrites": ["a1", "b2", "c3"]}),
        "modelUsage": {"claude-haiku-4-5-20251001": {}},
    }
    env.update(over)
    return json.dumps(env)


class PromptTest(unittest.TestCase):
    def test_g1_prompt_is_head_plus_query_only(self):
        for q in ev.load_golden(split="all"):
            self.assertEqual(gr.build_prompt(q.text), gr.PROMPT_HEAD + q.text.strip())
        head = gr.PROMPT_HEAD.casefold()
        for bad in ("/", ".md", "20_permanent_notes", "obsidian", "vault", str(ev.VAULT).casefold()):
            self.assertNotIn(bad, head)

    def test_g2_prompt_does_not_leak_titles_or_paths(self):
        stems = {Path(p).stem.casefold() for p in ev.manifest_paths() if len(Path(p).stem) >= 12}
        head = gr.PROMPT_HEAD.casefold()
        self.assertFalse([s for s in stems if s in head])
        rel = {r for q in ev.load_golden(split="all") for r in q.grades}
        self.assertFalse([p for p in rel if p in gr.PROMPT_HEAD])


class CommandTest(unittest.TestCase):
    def test_g4_flags(self):
        cmd = gr.build_command("claude")
        for flag in ("-p", "--safe-mode", "--no-session-persistence", "--system-prompt"):
            self.assertIn(flag, cmd)
        self.assertEqual(cmd[cmd.index("--model") + 1], "haiku")
        self.assertEqual(cmd[cmd.index("--output-format") + 1], "json")
        self.assertEqual(cmd[-2:], ["--tools", ""])
        self.assertNotIn("--bare", cmd)

    def test_build_command_custom_system_prompt_only_swaps_that(self):
        default = gr.build_command("claude")
        custom = gr.build_command("claude", system_prompt="X")
        self.assertEqual(custom[custom.index("--system-prompt") + 1], "X")
        idx = default.index("--system-prompt") + 1
        self.assertEqual(default[:idx] + default[idx + 1 :], custom[:idx] + custom[idx + 1 :])
        self.assertEqual(custom[-2:], ["--tools", ""])

    def test_g5_child_env(self):
        base = {"CLAUDECODE": "1", "CLAUDE_CODE_SESSION_ID": "x", "CLAUDE_PID": "1", "CLAUDE_EFFORT": "h", "FOO": "1", "PATH": "/bin"}
        env = gr.child_env(base)
        self.assertEqual(env["FOO"], "1")
        self.assertEqual(env["SECOND_BRAIN_HOOKS"], "0")
        self.assertEqual(env["JEV_TOOL_E"], "0")
        self.assertFalse([k for k in env if k.startswith("CLAUDE")])


class ParseTest(unittest.TestCase):
    def test_g8_valid_and_fenced(self):
        rw, model = gr.parse_response(envelope(), "consulta")
        self.assertEqual(rw, ["a1", "b2", "c3"])
        self.assertIn("haiku", model)
        fenced = envelope(result="```json\n" + json.dumps({"rewrites": ["a1", "b2"]}) + "\n```")
        self.assertEqual(gr.parse_response(fenced, "consulta")[0], ["a1", "b2"])

    def test_g9_fails_loudly(self):
        bad = [
            "não json",
            envelope(result="não é json"),
            envelope(is_error=True, subtype="error_x"),
            envelope(result=json.dumps({"rewrites": ["a1"]})),
            envelope(result=json.dumps({"rewrites": ["a", "b", "c", "d"]})),
            envelope(result=json.dumps({"rewrites": ["consulta", "x"]})),
            envelope(modelUsage={}),
            json.dumps({"is_error": False, "result": json.dumps({"rewrites": ["a", "b"]})}),
        ]
        for stdout in bad:
            with self.assertRaises(ValueError, msg=stdout):
                gr.parse_response(stdout, "consulta")

    def test_parse_envelope_returns_result_and_model(self):
        body = json.dumps({"x": 1})
        result, model = gr.parse_envelope(envelope(result="```json\n" + body + "\n```"))
        self.assertEqual(result, body)
        self.assertIn("haiku", model)
        with self.assertRaisesRegex(ValueError, "modelo inesperado"):
            gr.parse_envelope(envelope(modelUsage={"claude-sonnet-4-5": {}}))
        with self.assertRaisesRegex(ValueError, "envelope não é JSON"):
            gr.parse_envelope("nope")

    def test_g10_wrong_model(self):
        with self.assertRaisesRegex(ValueError, "modelo inesperado"):
            gr.parse_response(envelope(modelUsage={"claude-sonnet-4-5": {}}), "consulta")


class SubprocessTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.fake = make_fake(self.tmp.name)
        self.cap = str(Path(self.tmp.name) / "cap.json")

    def tearDown(self):
        self.tmp.cleanup()

    def run_fake(self, mode, query="minha consulta", timeout=20, **extra):
        env = {"FAKE_MODE": mode, "FAKE_CAPTURE": self.cap, **extra}
        with mock.patch.dict(os.environ, env):
            return gr.call_claude(gr.build_prompt(query), binary=self.fake, timeout=timeout)

    def test_g3_no_vault_in_argv_or_cwd_and_stdin_is_prompt(self):
        rw, model = self.run_fake("ok", CLAUDECODE="1", CLAUDE_CODE_SESSION_ID="x")
        cap = json.loads(Path(self.cap).read_text())
        self.assertFalse([a for a in cap["argv"] if str(ev.VAULT) in a])
        self.assertNotIn(str(ev.VAULT), str(Path(cap["cwd"]).resolve()))
        self.assertEqual(cap["stdin"], gr.build_prompt("minha consulta"))
        self.assertNotIn("CLAUDECODE", cap["env_keys"])
        self.assertNotIn("CLAUDE_CODE_SESSION_ID", cap["env_keys"])
        self.assertIn("FAKE_CAPTURE", cap["env_keys"])
        self.assertEqual(len(rw), 3)

    def test_g8_fenced_via_process(self):
        self.assertEqual(len(self.run_fake("fenced")[0]), 3)

    def test_g11_timeout(self):
        with self.assertRaisesRegex(RuntimeError, "timeout"):
            self.run_fake("sleep", timeout=1)

    def test_nonzero_exit_is_runtime_error(self):
        with self.assertRaises(RuntimeError):
            self.run_fake("fail_if_called")

    def test_g7_dry_run_calls_nothing_and_writes_nothing(self):
        out_path = Path(self.tmp.name) / "out.jsonl"
        buf = io.StringIO()
        with mock.patch.dict(os.environ, {"FAKE_MODE": "fail_if_called", "FAKE_CAPTURE": self.cap}):
            with contextlib.redirect_stdout(buf):
                gr.main(["--split", "dev", "--dry-run", "--claude", self.fake, "--out", str(out_path)])
        text = buf.getvalue()
        first = ev.load_golden(split="dev")[0]
        self.assertIn(f"### {first.id}", text)
        self.assertIn(gr.build_prompt(first.text), text)
        self.assertFalse(Path(self.cap).exists())
        self.assertFalse(out_path.exists())


class GenerateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = Path(self.tmp.name) / "rw.jsonl"
        self.q1 = ev.Query("q1", "texto q1", "lexical", {"a.md": 2})
        self.q2 = ev.Query("q2", "texto q2", "lexical", {"a.md": 2})

    def tearDown(self):
        self.tmp.cleanup()

    def row(self, q):
        return {"id": q.id, "query": q.text, "rewrites": ["r1", "r2"], "model": "claude-haiku-x", "created": "2026-10-22"}

    def test_g6_idempotent(self):
        self.out.write_text(json.dumps(self.row(self.q1), ensure_ascii=False) + "\n", encoding="utf-8")
        before_line = self.out.read_bytes()
        calls = []

        def call(q):
            calls.append(q.id)
            return ["r1", "r2"], "claude-haiku-x"

        existing = gr.read_existing(self.out)
        self.assertEqual(gr.generate([self.q1, self.q2], self.out, call, "2026-10-22", existing=existing), 1)
        self.assertEqual(calls, ["q2"])
        self.assertTrue(self.out.read_bytes().startswith(before_line))
        after = self.out.read_bytes()
        self.assertEqual(gr.generate([self.q1, self.q2], self.out, call, "2026-10-22", existing=gr.read_existing(self.out)), 0)
        self.assertEqual(calls, ["q2"])
        self.assertEqual(self.out.read_bytes(), after)

    def test_pending_detects_divergent_query(self):
        self.out.write_text(json.dumps(self.row(self.q1)) + "\n", encoding="utf-8")
        changed = ev.Query("q1", "outro texto", "lexical", {"a.md": 2})
        with self.assertRaisesRegex(ValueError, "query diverge"):
            gr.pending([changed], gr.read_existing(self.out))

    def test_g12_failure_keeps_progress(self):
        def bad(q):
            if q.id == "q2":
                raise RuntimeError("boom")
            return ["r1", "r2"], "claude-haiku-x"

        with self.assertRaises(RuntimeError):
            gr.generate([self.q1, self.q2], self.out, bad, "2026-10-22")
        self.assertEqual([json.loads(line)["id"] for line in self.out.read_text(encoding="utf-8").splitlines()], ["q1"])
        gr.generate([self.q1, self.q2], self.out, lambda q: (["r1", "r2"], "claude-haiku-x"), "2026-10-22")
        self.assertEqual([json.loads(line)["id"] for line in self.out.read_text(encoding="utf-8").splitlines()], ["q1", "q2"])


if __name__ == "__main__":
    unittest.main()
