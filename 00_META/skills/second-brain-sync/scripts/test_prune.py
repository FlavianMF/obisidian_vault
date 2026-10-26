"""Testes do pruner de saída de ferramenta."""

import io
import json
import os
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

import prune
import sb

SB = Path(sb.__file__)
SENTINEL = "SENTINELA-CONTEUDO-XYZ"


def bash(command, stdout="", stderr="", **extra):
    resp = {"stdout": stdout, "stderr": stderr, "interrupted": False, "isImage": False, "noOutputExpected": False}
    return {"session_id": "s/1", "tool_use_id": "toolu_01", "tool_name": "Bash",
            "tool_input": {"command": command}, "tool_response": resp, **extra}


def numbered(n, prefix="linha"):
    return "\n".join(f"{prefix} {i} {SENTINEL}" for i in range(n)) + "\n"


class PruneFixture(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.state = self.root / "state"
        self.env = {}

    def hook(self, payload):
        out = prune.hook_output(self.state, payload, self.env)
        return json.loads(out) if out else None

    def updated(self, payload):
        data = self.hook(payload)
        return data["hookSpecificOutput"]["updatedToolOutput"] if data else None


class RuleTests(PruneFixture):
    def test_tests_passing_cut_and_failure_kept(self):
        body = "".join(f"tests/test_a.py::test_{i} PASSED\n" for i in range(300))
        body += "FAILED tests/test_a.py::test_x - AssertionError: boom\n" + "".join(f"ok {i}\n" for i in range(50))
        out = self.updated(bash("cd /x && pytest -q", body))
        self.assertIn("AssertionError: boom", out["stdout"])
        self.assertIn("(regra R1)", out["stdout"])
        self.assertNotIn("test_5 PASSED", out["stdout"])

    def test_tests_passed_with_error_in_name_still_cut(self):
        body = "".join(f"tests/t.py::test_error_case_{i} PASSED\n" for i in range(300)) + "300 passed in 1s\n"
        out = self.updated(bash("pytest", body))
        self.assertLess(len(out["stdout"]), len(body) / 3)

    def test_tests_all_pass_only_tail_kept(self):
        body = "".join(f"tests/t.py::test_{i} PASSED\n" for i in range(300)) + "300 passed in 1s\n"
        out = self.updated(bash("python3 -m unittest discover", body))
        self.assertIn("300 passed", out["stdout"])
        self.assertLess(len(out["stdout"]), len(body) / 3)

    def test_tests_small_output_untouched(self):
        self.assertIsNone(self.hook(bash("pytest", "ok\n" * 100)))

    def test_ls_long(self):
        out = self.updated(bash("ls -la /big", numbered(200)))
        self.assertIn("80 de 200 linhas mostradas (regra R2)", out["stdout"])
        self.assertIn("linha 79 ", out["stdout"])
        self.assertNotIn("linha 80 ", out["stdout"])

    def test_cat_and_head_pipeline_exempt(self):
        big = numbered(2000)
        self.assertIsNone(self.hook(bash("cat file", big)))
        self.assertIsNone(self.hook(bash("find . -name x | head -50", big)))
        self.assertIsNone(self.hook(bash("rg foo | wc -l", big)))
        self.assertIsNone(self.hook(bash("cd d && sed -n '1,5p' f", big)))
        self.assertIsNone(self.hook(bash("ls | sed -n 1,3p", big)))

    def test_generic_head_and_tail(self):
        out = self.updated(bash("make build", numbered(1000)))
        self.assertIn("100 de 1000 linhas mostradas (regra R3)", out["stdout"])
        self.assertIn("linha 59 ", out["stdout"])
        self.assertIn("linha 960 ", out["stdout"])
        self.assertNotIn("linha 500 ", out["stdout"])

    def test_git_diff_threshold(self):
        mid = numbered(600)  # ~ 17k chars: acima de 10k, abaixo de 30k
        self.assertGreater(len(mid), 10000)
        self.assertLess(len(mid), 30000)
        self.assertIsNone(self.hook(bash("git diff HEAD", mid)))
        self.assertIsNotNone(self.hook(bash("git status", mid)))
        self.assertIsNotNone(self.hook(bash("git diff", numbered(1500))))

    def test_prefix_and_var_stripped(self):
        self.assertIsNone(self.hook(bash("cd a && FOO=1 cat f", numbered(2000))))

    def test_min_chars_env(self):
        self.env = {"SB_PRUNE_MIN_CHARS": "100000"}
        self.assertIsNone(self.hook(bash("make", numbered(1000))))

    def test_below_threshold_silent(self):
        self.assertIsNone(self.hook(bash("make", numbered(50))))


class FormatTests(PruneFixture):
    def test_same_keys_and_types(self):
        payload = bash("make", numbered(1000), stderr="warn\n")
        out = self.updated(payload)
        resp = payload["tool_response"]
        self.assertEqual(list(out), list(resp))
        for key in resp:
            self.assertIs(type(out[key]), type(resp[key]))
        self.assertEqual(out["stderr"], "warn\n")
        self.assertEqual(out["interrupted"], False)

    def test_envelope(self):
        data = self.hook(bash("make", numbered(1000)))
        self.assertEqual(list(data), ["hookSpecificOutput"])
        self.assertEqual(data["hookSpecificOutput"]["hookEventName"], "PostToolUse")

    def test_marker_on_own_line(self):
        out = self.updated(bash("make", numbered(1000)))["stdout"]
        last = out.split("\n")[-1]
        self.assertTrue(last.startswith("[sb-prune: 100 de 1000 linhas mostradas (regra R3); saída completa em "))
        self.assertIn("# sb:raw]", last)

    def test_grep_content_and_filenames(self):
        resp = {"mode": "content", "numLines": 200, "totalLines": 200, "content": numbered(200), "filenames": ["a"]}
        out = self.updated({"session_id": "s", "tool_use_id": "t", "tool_name": "Grep", "tool_input": {},
                            "tool_response": resp})
        self.assertEqual(list(out), list(resp))
        self.assertEqual(out["numLines"], 80)
        self.assertEqual(out["totalLines"], 200)
        self.assertIn("regra R2", out["content"])
        names = [f"/p/f{i}" for i in range(200)]
        resp = {"filenames": names, "numFiles": 200, "truncated": False, "totalMatches": 200}
        out = self.updated({"session_id": "s", "tool_use_id": "t2", "tool_name": "Glob", "tool_input": {},
                            "tool_response": resp})
        self.assertEqual(len(out["filenames"]), 81)
        self.assertTrue(all(isinstance(x, str) for x in out["filenames"]))
        self.assertEqual((out["numFiles"], out["totalMatches"], out["truncated"]), (200, 200, True))
        self.assertIn("sb-prune", out["filenames"][-1])

    def test_unknown_shapes_noop(self):
        for resp in ("texto", {"foo": "bar"}, {"content": 5}, {"filenames": ["a"] * 200 + [3]}):
            self.assertIsNone(self.hook({"session_id": "s", "tool_use_id": "t", "tool_name": "Grep",
                                         "tool_input": {}, "tool_response": resp}))
        self.assertIsNone(self.hook({"session_id": "s", "tool_name": "Read", "tool_input": {},
                                     "tool_response": {"content": numbered(500)}}))
        self.assertIsNone(self.hook(bash("make", stdout=None)))


class SpillTests(PruneFixture):
    def test_spill_modes_and_full_content(self):
        payload = bash("make", numbered(1000), stderr="erro-final\n")
        payload["tool_use_id"] = "../toolu 01"
        self.hook(payload)
        files = list((self.state / "spill").glob("*/*.txt"))
        self.assertEqual(len(files), 1)
        spill = files[0]
        self.assertEqual(spill.parent.parent, self.state / "spill")
        self.assertEqual(stat.S_IMODE(spill.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(spill.parent.stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE((self.state / "spill").stat().st_mode), 0o700)
        text = spill.read_text()
        self.assertIn("linha 500 ", text)
        self.assertIn("erro-final", text)
        self.assertIn("== stdout ==", text)
        self.assertNotIn("/", spill.name)
        self.assertNotIn("..", spill.parent.name)

    def test_marker_path_points_to_spill(self):
        out = self.updated(bash("make", numbered(1000)))["stdout"]
        path = out.split("saída completa em ")[1].split(";")[0]
        self.assertTrue(Path(path).is_file())

    def test_gc_removes_old_once_a_day(self):
        self.hook(bash("make", numbered(1000)))
        spill = next((self.state / "spill").glob("*/*.txt"))
        old = time.time() - 8 * 86400
        os.utime(spill, (old, old))
        stamp = self.state / "spill" / ".gc"
        self.assertTrue(stamp.exists())
        self.assertEqual(prune.gc(self.state), 0)  # carimbo de hoje
        self.assertTrue(spill.exists())
        os.utime(stamp, (old, old))
        self.assertEqual(prune.gc(self.state), 1)
        self.assertFalse(spill.exists())

    def test_gc_forced(self):
        self.hook(bash("make", numbered(1000)))
        spill = next((self.state / "spill").glob("*/*.txt"))
        old = time.time() - 8 * 86400
        os.utime(spill, (old, old))
        self.assertEqual(prune.gc(self.state, force=True), 1)


class SwitchTests(PruneFixture):
    def test_env_off(self):
        for value in ("0", "false", "off", "no", "OFF"):
            self.env = {"SB_PRUNE": value}
            self.assertIsNone(self.hook(bash("make", numbered(1000))), value)

    def test_disabled_file(self):
        self.state.mkdir()
        (self.state / "DISABLED").write_text("")
        self.assertIsNone(self.hook(bash("make", numbered(1000))))

    def test_raw_comment(self):
        self.assertIsNone(self.hook(bash("make # sb:raw", numbered(1000))))

    def test_exception_empty_stdout(self):
        out = io.StringIO()
        self.assertEqual(prune.run("hook", self.state, io.StringIO("não json"), out, {}), 0)
        self.assertEqual(out.getvalue(), "")
        out = io.StringIO()
        self.assertEqual(prune.run("hook", self.state, io.StringIO(json.dumps(bash("make", 5))), out, {}), 0)
        self.assertEqual(out.getvalue(), "")
        orig = prune.hook_output
        prune.hook_output = lambda *a: 1 / 0
        self.addCleanup(setattr, prune, "hook_output", orig)
        out = io.StringIO()
        self.assertEqual(prune.run("hook", self.state, io.StringIO(json.dumps(bash("make", "x"))), out, {}), 0)
        self.assertEqual(out.getvalue(), "")


class LogTests(PruneFixture):
    def test_log_has_no_content(self):
        self.hook(bash(f"cd /x && make {SENTINEL} --flag", numbered(1000)))
        raw = (self.state / "prune.jsonl").read_text()
        self.assertNotIn(SENTINEL, raw)
        entry = json.loads(raw)
        self.assertEqual(set(entry), {"ts", "session_id", "tool", "prog", "rule", "chars_in", "chars_out",
                                      "lines_in", "lines_out"})
        self.assertEqual((entry["prog"], entry["rule"], entry["tool"]), ("make", "R3", "Bash"))
        self.assertEqual(stat.S_IMODE((self.state / "prune.jsonl").stat().st_mode), 0o600)


class CliTests(PruneFixture):
    def run_cli(self, *args, raw="", env=None):
        e = {**os.environ, "SECOND_BRAIN_STATE_DIR": str(self.state), **(env or {})}
        return subprocess.run([sys.executable, str(SB), "prune", *args], input=raw, capture_output=True, text=True, env=e)

    def test_hook_cli(self):
        done = self.run_cli("hook", raw=json.dumps(bash("make", numbered(1000))))
        self.assertEqual(done.returncode, 0)
        self.assertIn("updatedToolOutput", json.loads(done.stdout)["hookSpecificOutput"])
        quiet = self.run_cli("hook", raw=json.dumps(bash("make", "ok")))
        self.assertEqual((quiet.returncode, quiet.stdout), (0, ""))
        junk = self.run_cli("hook", raw="lixo")
        self.assertEqual((junk.returncode, junk.stdout), (0, ""))
        self.assertEqual(self.run_cli("gc").returncode, 0)

    def test_replay_synthetic(self):
        proj = self.root / "-proj-dir"
        (proj / "sess" / "subagents").mkdir(parents=True)

        def use(i, name, inp):
            return {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": i, "name": name, "input": inp}]}}

        def res(i, text):
            return {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": i, "content": text}]}}

        rows = [use("a", "Bash", {"command": "make"}), res("a", numbered(1000)),
                use("b", "Bash", {"command": "cat f"}), res("b", numbered(1000)),
                use("c", "Grep", {"pattern": "x"}), res("c", [{"type": "text", "text": numbered(200)}]),
                use("d", "Read", {}), res("d", numbered(100)),
                use("e", "Bash", {"command": "make"}), res("e", numbered(1000))]
        rows[-1]["message"]["content"][0]["is_error"] = True
        (proj / "sess.jsonl").write_text("\n".join(json.dumps(r) for r in rows[:4] + rows[8:]) + "\n")
        (proj / "sess" / "subagents" / "agent-1.jsonl").write_text("\n".join(json.dumps(r) for r in rows[4:8]) + "\nlixo\n")
        done = self.run_cli("replay", "--projects", str(proj))
        self.assertEqual(done.returncode, 0)
        self.assertNotIn(SENTINEL, done.stdout)
        table = [x.split("\t") for x in done.stdout.splitlines()]
        self.assertEqual(table[0], ["rule", "n", "chars_in", "chars_out", "saved_pct"])
        by_rule = {r[0]: r for r in table[1:]}
        self.assertEqual(by_rule["R3"][1], "1")
        self.assertEqual(by_rule["R2"][1], "1")
        self.assertEqual(by_rule["total"][1], "2")
        self.assertFalse((self.state / "spill").exists())
        self.assertFalse((self.state / "prune.jsonl").exists())
        as_json = json.loads(self.run_cli("replay", "--projects", str(proj), "--json").stdout)
        self.assertIn("R3", as_json["rules"])


if __name__ == "__main__":
    unittest.main()
