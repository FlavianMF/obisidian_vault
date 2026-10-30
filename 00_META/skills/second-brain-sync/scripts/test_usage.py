"""Testes do registro de uso: python3 -m unittest discover -s 00_META/skills/second-brain-sync/scripts -v

Credenciais abaixo são FALSAS. Toda linha que as contém leva o marcador do scanner.
"""

import ast
import datetime as dt
import hashlib
import json
import os
import statistics
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

import candidates
import observe
import sb
import usage
from lib import secret_scan

SB = Path(sb.__file__)
BASELINE = SB.resolve().parents[3] / "eval" / "usage_baseline.sh"
SENTINEL = "SENTINELA-NAO-GRAVAR"
FAKE_TOKEN = "ghp_" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4"  # sb-allow-secret
LIMIT_TEXT = "Usage limit reached · continuing automatically at 12:40pm · esc to cancel"
TODAY = dt.date(2026, 10, 29)


def reply(msg_id, out=0, read=0, create=0, inp=0, ts="2026-10-20T10:00:00.000Z", uuid=None, **extra):
    entry = {"type": "assistant", "timestamp": ts, "uuid": uuid or f"u-{msg_id}",
             "message": {"id": msg_id, "model": "claude-x", "content": [{"type": "text", "text": "texto"}],
                         "usage": {"output_tokens": out, "cache_read_input_tokens": read,
                                   "cache_creation_input_tokens": create, "input_tokens": inp}}}
    entry.update(extra)
    return entry


def limit(ts="2026-10-20T11:00:00.000Z", uuid=None, text=LIMIT_TEXT, **extra):
    entry = {"type": "system", "subtype": "informational", "level": "notice", "content": text, "timestamp": ts}
    if uuid:
        entry["uuid"] = uuid
    entry.update(extra)
    return entry


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


def tree_hash(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if path.is_file():
            digest.update(str(path.relative_to(root)).encode())
            digest.update(oct(path.stat().st_mode).encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


class Fixture(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.state = self.root / "state"
        self.transcript = self.root / "t1.jsonl"

    def run_sb(self, *argv, stdin="", env=None, cwd=None, umask=None):
        base = {k: v for k, v in os.environ.items() if k != "CLAUDE_CODE_SESSION_ID"}
        base.update(SECOND_BRAIN_STATE_DIR=str(self.state), PYTHONDONTWRITEBYTECODE="1")
        base.update(env or {})
        return subprocess.run([sys.executable, str(SB), *argv], input=stdin, capture_output=True, text=True,
                              env=base, cwd=cwd, check=False,
                              preexec_fn=(lambda: os.umask(umask)) if umask is not None else None)

    def summarize(self, session="s1", transcript=None, project="repo", **kwargs):
        argv = ["observe", "summarize", "--session", session, "--project", project]
        if transcript is not None:
            argv += ["--transcript", str(transcript)]
        return self.run_sb(*argv, **kwargs)

    def update(self, rows=None, session="s1", project="repo"):
        if rows is not None:
            write_jsonl(self.transcript, rows)
        return usage.update(self.state, session, project, self.transcript)

    def record(self, session="s1"):
        return json.loads((usage.usage_dir(self.state) / f"{session}.json").read_text(encoding="utf-8"))

    def state_bytes(self) -> bytes:
        return b"".join(p.read_bytes() for p in sorted(self.state.rglob("*")) if p.is_file())

    def lock_dir(self, mode):
        directory = usage.usage_dir(self.state)
        directory.mkdir(parents=True, exist_ok=True)
        directory.chmod(mode)
        self.addCleanup(directory.chmod, 0o700)


class TaskSetTest(Fixture):
    def test_each_category_is_saved_with_private_modes(self):
        for category in usage.CATEGORIES:
            with self.subTest(category):
                done = self.run_sb("task", "set", category, "--session", "abc", umask=0)
                self.assertEqual((done.returncode, done.stdout), (0, f"task: {category} (sessao abc)\n"))
                task = usage.usage_dir(self.state) / "abc.task"
                self.assertEqual(task.read_text().strip(), category)
                self.assertEqual(task.stat().st_mode & 0o777, 0o600)
                self.assertEqual(task.parent.stat().st_mode & 0o777, 0o700)

    def test_an_unknown_category_is_refused_and_nothing_is_written(self):
        done = self.run_sb("task", "set", "ruim", "--session", "abc")
        self.assertEqual(done.returncode, 2)
        for name in usage.CATEGORIES:
            self.assertIn(name, done.stderr)
        self.assertFalse(usage.usage_dir(self.state).exists())

    def test_without_a_session_nothing_is_written(self):
        done = self.run_sb("task", "set", "docs")
        self.assertEqual(done.returncode, 2)
        self.assertIn("CLAUDE_CODE_SESSION_ID", done.stderr)
        self.assertIn("--session", done.stderr)
        self.assertFalse(usage.usage_dir(self.state).exists())

    def test_the_environment_supplies_the_session_and_the_flag_wins(self):
        self.run_sb("task", "set", "docs", env={"CLAUDE_CODE_SESSION_ID": "from-env"})
        self.run_sb("task", "set", "bugfix", "--session", "from-flag", env={"CLAUDE_CODE_SESSION_ID": "from-env"})
        names = sorted(p.name for p in usage.usage_dir(self.state).iterdir())
        self.assertEqual(names, ["from-env.task", "from-flag.task"])

    def test_the_session_id_cannot_escape_the_usage_directory(self):
        self.run_sb("task", "set", "docs", "--session", "../../evil")
        self.assertEqual([p.name for p in usage.usage_dir(self.state).iterdir()], ["evil.task"])
        self.assertEqual([p.name for p in self.state.iterdir()], ["usage"])
        self.assertEqual(list(self.root.glob("evil*")), [])

    def test_a_session_that_is_empty_after_cleaning_is_refused(self):
        done = self.run_sb("task", "set", "docs", "--session", "///", env={"CLAUDE_CODE_SESSION_ID": "from-env"})
        self.assertEqual(done.returncode, 2)
        self.assertFalse(usage.usage_dir(self.state).exists())

    def test_the_last_category_wins_in_one_file(self):
        self.run_sb("task", "set", "docs", "--session", "abc")
        self.run_sb("task", "set", "feature", "--session", "abc")
        self.assertEqual([p.name for p in usage.usage_dir(self.state).iterdir()], ["abc.task"])
        self.assertEqual(usage.read_task(self.state, "abc"), "feature")

    def test_a_write_failure_exits_2_without_a_traceback(self):
        self.state.mkdir()
        (self.state / "usage").write_text("not a directory")
        done = self.run_sb("task", "set", "docs", "--session", "abc")
        self.assertEqual(done.returncode, 2)
        self.assertNotIn("Traceback", done.stderr)
        shutil_dir = tempfile.mkdtemp(dir=self.root)
        self.state = Path(shutil_dir) / "state"
        self.lock_dir_state_readonly()
        done = self.run_sb("task", "set", "docs", "--session", "abc")
        self.assertEqual(done.returncode, 2)
        self.assertNotIn("Traceback", done.stderr)
        self.assertEqual(len(done.stderr.strip().splitlines()), 1)

    def lock_dir_state_readonly(self):
        self.lock_dir(0o500)


class RecordNumbersTest(Fixture):
    def test_the_record_has_exactly_the_13_keys_in_sorted_order(self):
        self.update([reply("m1", out=5, read=1000, create=400, inp=2), limit()])
        raw = (usage.usage_dir(self.state) / "s1.json").read_text(encoding="utf-8")
        record = json.loads(raw)
        self.assertEqual(set(record), usage.RECORD_KEYS)
        self.assertEqual(len(record), 13)
        self.assertEqual(list(record), sorted(record))
        self.assertEqual((record["eq"], record["output"], record["limit_hits"]), (2 + 500 + 100, 5, 1))
        self.assertTrue(usage.valid_record(record))

    def test_the_numbers_equal_usage_baseline_sidechain_on_the_same_transcript(self):
        rows = [
            {"type": "user", "message": {"content": "oi"}},
            reply("m2", out=5, read=3_000_000, create=0, inp=1, ts="2026-10-20T10:00:02Z"),
            reply("m1", out=10, read=2_500_000, create=400, inp=2, ts="2026-10-20T10:00:01Z"),
            reply("m1", out=99, read=9_999_999, create=9, inp=9, ts="2026-10-20T10:00:01Z", uuid="other"),
            reply("m1", out=10, read=2_500_000, create=400, inp=2, ts="2026-10-20T10:00:01Z", uuid="third"),
            {**reply("m3", out=7, read=11, create=13, inp=17, isSidechain=True)},
            {"type": "assistant", "uuid": "noid", "message": {"usage": {"output_tokens": 4, "input_tokens": 3}}},
            {"type": "assistant", "message": {"id": "m4", "usage": {}}},
            {"type": "assistant", "message": {"id": "m5", "usage": None}},
            {"type": "assistant", "message": {"usage": {"output_tokens": 8}}},
        ]
        write_jsonl(self.transcript, rows)
        sub_dir = self.root / "t1" / "subagents"
        write_jsonl(sub_dir / "agent-a1.jsonl", [reply("s1", out=7, read=200, create=100, inp=3, isSidechain=True)] * 2)
        write_jsonl(sub_dir / "agent-b2.jsonl", [reply("s2", out=1, read=5, create=0, inp=0, isSidechain=True),
                                                 reply("s3", out=2, read=5, create=0, inp=0, isSidechain=True)])
        (sub_dir / "agent-a1.meta.json").write_text(json.dumps({"agentType": "Explore"}))
        (sub_dir / "agent-b2.meta.json").write_text(json.dumps({"agentType": "Plan"}))
        write_jsonl(sub_dir / "notes.jsonl", [reply("n1", out=1000, read=1000, create=1000, inp=1000)])
        out = subprocess.run(["bash", str(BASELINE), "--sidechain", str(self.transcript)], capture_output=True,
                             text=True, check=True).stdout
        table = [line.split("\t") for line in out.splitlines() if "\trouter\t" not in line]
        main_rows = [r for r in table if r[1] == "main"]
        sub_rows = [r for r in table if r[1] == "sub"]
        self.assertEqual((len(main_rows), len(sub_rows)), (1, 2))
        self.update()
        record = self.record()
        self.assertEqual((record["main_eq"], record["main_output"]), (int(main_rows[0][9]), int(main_rows[0][5])))
        self.assertEqual((record["sub_eq"], record["sub_output"]),
                         (sum(int(r[9]) for r in sub_rows), sum(int(r[5]) for r in sub_rows)))
        self.assertEqual(record["eq"], record["main_eq"] + record["sub_eq"])
        self.assertEqual(record["output"], record["main_output"] + record["sub_output"])

    def test_a_message_id_in_three_blocks_counts_once_and_the_first_block_wins(self):
        self.update([reply("m1", out=10, uuid="a"), reply("m1", out=10, uuid="b"), reply("m1", out=99, uuid="c")])
        self.assertEqual(self.record()["output"], 10)

    def test_a_reply_without_id_uses_the_uuid_and_two_without_both_share_one_key(self):
        bare = {"type": "assistant", "message": {"usage": {"output_tokens": 4}}}
        self.update([{"type": "assistant", "uuid": "x", "message": {"usage": {"output_tokens": 3}}},
                     {"type": "assistant", "uuid": "y", "message": {"usage": {"output_tokens": 5}}},
                     bare, {**bare, "message": {"usage": {"output_tokens": 100}}}])
        self.assertEqual(self.record()["output"], 3 + 5 + 4)

    def test_a_sidechain_entry_in_the_main_file_counts_like_the_sidechain_mode(self):
        self.update([reply("m1", out=3), reply("m2", out=4, isSidechain=True)])
        self.assertEqual(self.record()["main_output"], 7)

    def test_eq_truncates_per_file_not_per_reply(self):
        self.update([reply("m1", read=5), reply("m2", read=5)])
        self.assertEqual(self.record()["eq"], 1)

    def test_values_that_are_not_whole_numbers_count_zero_without_a_traceback(self):
        bad = ["true-placeholder", "7", None, float("nan"), float("inf"), float("-inf"), 1.5]
        rows = [reply("good", out=7), reply("neg", out=-100)]
        rows.append(reply("bool", out=True))
        for n, value in enumerate(bad[1:], start=1):
            rows.append(reply(f"bad{n}", out=value, read=value, create=value, inp=value))
        rows.append({"type": "assistant", "message": {"id": "scalar", "usage": "texto"}})
        rows.append({"type": "assistant", "message": {"id": "gone", "usage": {"output_tokens": 2.0}}})
        write_jsonl(self.transcript, rows)
        self.update()
        record = self.record()
        self.assertEqual(record["output"], 7 - 100 + 2)
        self.assertEqual(record["eq"], 0)

    def test_entries_without_usage_and_non_assistant_entries_do_not_add(self):
        self.update([{"type": "user", "message": {"usage": {"output_tokens": 50}}},
                     {"type": "system", "message": {"usage": {"output_tokens": 50}}},
                     {"type": "assistant", "message": {"id": "z"}}, reply("m1", out=2)])
        self.assertEqual(self.record()["output"], 2)

    def test_bad_lines_are_skipped(self):
        self.transcript.write_text(
            "not json\n\n[1, 2]\n\"text\"\n" + json.dumps(reply("m1", out=6)) + "\n{\"type\": \"assistant\"\n",
            encoding="utf-8")
        self.update()
        self.assertEqual(self.record()["output"], 6)

    def test_subagent_files_are_summed_apart_and_other_files_are_ignored(self):
        write_jsonl(self.transcript, [reply("m1", out=1, inp=10)])
        sub_dir = self.root / "t1" / "subagents"
        write_jsonl(sub_dir / "agent-one.jsonl", [reply("a", out=2, inp=20)])
        write_jsonl(sub_dir / "agent-two.jsonl", [reply("b", out=3, inp=30)])
        write_jsonl(sub_dir / "notes.jsonl", [reply("c", out=1000, inp=1000)])
        (sub_dir / "agent-bad.jsonl").mkdir()
        self.update()
        record = self.record()
        self.assertEqual((record["sub_eq"], record["sub_output"]), (50, 5))
        self.assertEqual((record["main_eq"], record["eq"], record["output"]), (10, 60, 6))


class RecordLimitTest(Fixture):
    def test_the_real_sample_counts_once_with_its_timestamp(self):
        self.update([reply("m1", out=1), limit(ts="2026-10-13T15:40:00.123Z")])
        record = self.record()
        self.assertEqual((record["limit_hits"], record["limit_at"]), (1, ["2026-10-13T15:40:00.123Z"]))

    def test_only_a_system_informational_entry_that_starts_with_the_prefix_counts(self):
        self.update([
            reply("m1", out=1),
            limit(subtype="other"), limit(text="ok. " + LIMIT_TEXT), limit(text=["Usage limit reached"]),
            {**limit(), "type": "assistant", "message": {"content": LIMIT_TEXT}},
            {**limit(), "type": "user"}, {**limit(), "type": "attachment"},
            limit(uuid="real"),
        ])
        self.assertEqual(self.record()["limit_hits"], 1)

    def test_a_notice_in_a_subagent_file_does_not_count(self):
        write_jsonl(self.transcript, [reply("m1", out=1)])
        write_jsonl(self.root / "t1" / "subagents" / "agent-a.jsonl", [reply("s", out=1), limit(uuid="sub")])
        self.update()
        self.assertEqual(self.record()["limit_hits"], 0)

    def test_the_same_uuid_counts_once_and_entries_without_uuid_always_count(self):
        self.update([reply("m1", out=1), limit(uuid="same"), limit(uuid="same"), limit(uuid="other"),
                     limit(ts="2026-10-21T00:00:00Z"), limit(ts="2026-10-22T00:00:00Z")])
        record = self.record()
        self.assertEqual(record["limit_hits"], 4)
        self.assertEqual(len(record["limit_at"]), record["limit_hits"])

    def test_limit_at_keeps_file_order_and_blanks_an_invalid_timestamp(self):
        self.update([limit(ts="2026-10-22T00:00:00Z"), limit(ts=SENTINEL), limit(ts="2026-13-45T00:00:00Z"),
                     limit(ts="2026-10-20T00:00:00Z")])
        self.assertEqual(self.record()["limit_at"], ["2026-10-22T00:00:00Z", "", "", "2026-10-20T00:00:00Z"])

    def test_a_transcript_with_only_a_notice_still_writes_a_record(self):
        self.update([limit()])
        record = self.record()
        self.assertEqual((record["eq"], record["limit_hits"]), (0, 1))

    def test_the_notice_text_is_never_stored(self):
        self.update([reply("m1", out=1), limit(text=f"Usage limit reached {SENTINEL}")])
        self.assertNotIn(SENTINEL.encode(), self.state_bytes())


class RecordFieldsTest(Fixture):
    def test_date_is_the_first_valid_timestamp_in_file_order(self):
        self.update([{"type": "user", "timestamp": SENTINEL}, reply("m1", out=1, ts="2026-10-22T23:00:00Z"),
                     reply("m2", out=1, ts="2026-10-20T01:00:00Z")])
        self.assertEqual(self.record()["date"], "2026-10-22")

    def test_without_a_timestamp_the_date_is_kept_then_falls_back_to_today(self):
        self.update([{"type": "assistant", "message": {"id": "a", "usage": {"output_tokens": 1}}}])
        self.assertEqual(self.record()["date"], usage.utcnow().date().isoformat())
        path = usage.usage_dir(self.state) / "s1.json"
        record = json.loads(path.read_text())
        record["date"] = "2026-01-02"
        path.write_text(json.dumps(record, sort_keys=True) + "\n")
        self.update()
        self.assertEqual(self.record()["date"], "2026-01-02")

    def test_a_calendar_impossible_timestamp_is_not_a_date(self):
        self.update([reply("m1", out=1, ts="2026-02-30T10:00:00Z"), reply("m2", out=1, ts="2026-03-01T10:00:00Z")])
        self.assertEqual(self.record()["date"], "2026-03-01")

    def test_project_is_normalized_cut_and_scanned(self):
        cases = {
            f"ghp_{'A1b2C3d4E5f6G7h8I9j0K1l2M3n4'}": "-",  # sb-allow-secret
            f"/r/sb-allow-secret/{FAKE_TOKEN}": "-",  # sb-allow-secret
            "x" * 300: "x" * 120,
            "projeção".replace("çã", "çã"): "projeção",
            "pro\nj\x00eto": "projeto",
            "  ": "",
        }
        for raw, expected in cases.items():
            with self.subTest(raw[:20]):
                self.assertEqual(usage.clean_project(raw), expected)
        self.update([reply("m1", out=1)], project="a\nb")
        self.assertEqual(self.record()["project"], "ab")

    def test_the_category_comes_from_the_task_file_and_follows_changes(self):
        self.update([reply("m1", out=1)])
        self.assertIsNone(self.record()["category"])
        usage.write_task(self.state, "s1", "bugfix")
        self.update()
        self.assertEqual(self.record()["category"], "bugfix")
        usage.write_task(self.state, "s1", "docs")
        self.update()
        self.assertEqual(self.record()["category"], "docs")

    def test_a_tampered_task_file_gives_no_category(self):
        self.update([reply("m1", out=1)])
        (usage.usage_dir(self.state) / "s1.task").write_text("xpto\n")
        self.update()
        self.assertIsNone(self.record()["category"])

    def test_summarize_with_a_bad_session_id_writes_nothing_outside_usage(self):
        write_jsonl(self.transcript, [reply("m1", out=1)])
        for session in ("", "///"):
            with self.subTest(session):
                self.assertEqual(self.summarize(session, self.transcript).returncode, 0)
                self.assertFalse((usage.usage_dir(self.state) / ".json").exists())
        self.assertEqual(self.summarize("../../x", self.transcript).returncode, 0)
        self.assertEqual([p.name for p in usage.usage_dir(self.state).iterdir()], ["x.json"])
        self.assertEqual({p.name for p in self.state.iterdir()}, {"usage"})
        self.assertEqual(list(self.root.glob("x*")), [])

    def test_without_a_readable_transcript_no_record_is_written_and_an_old_one_stays(self):
        self.assertEqual(self.summarize("s1").returncode, 0)
        self.assertEqual(self.summarize("s1", self.root / "missing.jsonl").returncode, 0)
        self.assertEqual(self.summarize("s1", self.root).returncode, 0)
        self.assertFalse(usage.usage_dir(self.state).exists())
        self.update([reply("m1", out=4)])
        before = (usage.usage_dir(self.state) / "s1.json").read_bytes()
        for transcript in (None, self.root / "missing.jsonl", self.root):
            self.assertIsNone(usage.update(self.state, "s1", "repo", transcript))
        self.assertEqual((usage.usage_dir(self.state) / "s1.json").read_bytes(), before)

    def test_an_empty_transcript_or_one_with_only_user_entries_writes_nothing(self):
        for rows in ([], [{"type": "user", "message": {"content": "oi"}}]):
            self.assertIsNone(self.update(rows))
        self.assertFalse(usage.usage_dir(self.state).exists())

    def test_the_project_is_the_folder_name_outside_git_and_accents_work(self):
        folder = self.root / "projeção"
        folder.mkdir()
        transcript = folder / "ção.jsonl"
        write_jsonl(transcript, [reply("m1", out=1)])
        done = self.run_sb("observe", "summarize", "--session", "s1", "--transcript", str(transcript), cwd=folder)
        self.assertEqual(done.returncode, 0)
        self.assertEqual(self.record()["project"], "projeção")


class IdempotencyTest(Fixture):
    def prepare(self):
        write_jsonl(self.transcript, [reply("m1", out=5, read=1000, create=400, inp=2), limit()])
        for _ in range(3):
            payload = {"session_id": "s1", "tool_name": "Read", "tool_input": {"file_path": "/repo/a.py"},
                       "tool_response": "x"}
            self.run_sb("observe", "record", stdin=json.dumps(payload))
        usage.write_task(self.state, "s1", "feature")

    def test_three_stops_leave_the_same_state_as_one(self):
        self.prepare()
        self.assertEqual(self.summarize("s1", self.transcript).returncode, 0)
        self.assertTrue(candidates.load(self.state)[0], "the log must queue a candidate")
        after_one = tree_hash(self.state)
        self.summarize("s1", self.transcript)
        self.summarize("s1", self.transcript)
        self.assertEqual(tree_hash(self.state), after_one)

    def test_a_growing_transcript_shows_its_total_not_the_sum_of_runs(self):
        self.update([reply("m1", out=5)])
        self.update([reply("m1", out=5), reply("m2", out=7)])
        self.assertEqual(self.record()["output"], 12)
        self.update()
        self.assertEqual(self.record()["output"], 12)

    def test_an_unchanged_record_is_not_rewritten(self):
        self.update([reply("m1", out=5)])
        path = usage.usage_dir(self.state) / "s1.json"
        before = path.stat().st_mtime_ns
        time.sleep(0.01)
        self.update()
        self.assertEqual(path.stat().st_mtime_ns, before)

    def test_four_parallel_stops_leave_one_valid_record_and_no_temp_file(self):
        write_jsonl(self.transcript, [reply("m1", out=5, read=1000), reply("m2", out=7), limit()])
        self.update()
        expected = (usage.usage_dir(self.state) / "s1.json").read_bytes()
        for round_ in range(5):
            (usage.usage_dir(self.state) / "s1.json").unlink()
            argv = [sys.executable, str(SB), "observe", "summarize", "--session", "s1", "--project", "repo",
                    "--transcript", str(self.transcript)]
            env = dict(os.environ, SECOND_BRAIN_STATE_DIR=str(self.state), PYTHONDONTWRITEBYTECODE="1")
            procs = [subprocess.Popen(argv, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                     for _ in range(4)]
            for proc in procs:
                _, err = proc.communicate()
                self.assertEqual((proc.returncode, err), (0, ""), f"round {round_}")
            self.assertEqual((usage.usage_dir(self.state) / "s1.json").read_bytes(), expected)
            self.assertEqual([p.name for p in usage.usage_dir(self.state).iterdir() if p.suffix == ".tmp"], [])


class StateTest(Fixture):
    def test_modes_are_private_even_with_umask_zero(self):
        write_jsonl(self.transcript, [reply("m1", out=5)])
        self.run_sb("task", "set", "docs", "--session", "s1", umask=0)
        self.summarize("s1", self.transcript, umask=0)
        directory = usage.usage_dir(self.state)
        self.assertEqual(directory.stat().st_mode & 0o777, 0o700)
        for name in ("s1.json", "s1.task"):
            self.assertEqual((directory / name).stat().st_mode & 0o777, 0o600, name)

    def test_a_new_record_sweeps_files_older_than_90_days_only(self):
        directory = usage.usage_dir(self.state)
        directory.mkdir(parents=True)
        now = time.time()
        files = {"old.json": 91, "old.task": 91, "orphan.task": 91, "young.json": 89, "young.task": 89}
        for name, age in files.items():
            (directory / name).write_text("x")
            os.utime(directory / name, (now - age * 86400, now - age * 86400))
        (directory / "w-stale.tmp").write_text("x")
        os.utime(directory / "w-stale.tmp", (now - 7200, now - 7200))
        (directory / "w-fresh.tmp").write_text("x")
        self.update([reply("m1", out=1)])
        self.assertEqual(sorted(p.name for p in directory.iterdir()),
                         ["s1.json", "w-fresh.tmp", "young.json", "young.task"])

    def test_the_full_flow_leaves_only_the_expected_state(self):
        write_jsonl(self.transcript, [reply("m1", out=5)])
        for _ in range(3):
            self.run_sb("observe", "record", stdin=json.dumps(
                {"session_id": "s1", "tool_name": "Read", "tool_input": {"file_path": "/r/a.py"}, "tool_response": "x"}))
        self.run_sb("task", "set", "docs", "--session", "s1")
        self.summarize("s1", self.transcript)
        top = {p.name for p in self.state.iterdir()}
        self.assertLessEqual(top, {"observe", "usage", "queue.jsonl", "queue.lock"})
        self.assertIn("usage", top)

    def test_a_fresh_state_root_is_created_private(self):
        root = self.root / "fresh" / "state"
        self.state = root
        self.run_sb("task", "set", "docs", "--session", "s1", umask=0)
        self.assertEqual(root.stat().st_mode & 0o777, 0o700)
        self.assertEqual((root / "usage").stat().st_mode & 0o777, 0o700)
        self.state = self.root / "fresh2" / "state"
        self.run_sb("observe", "record", umask=0, stdin=json.dumps(
            {"session_id": "s1", "tool_name": "Read", "tool_input": {"file_path": "/r/a.py"}, "tool_response": "x"}))
        self.assertEqual(self.state.stat().st_mode & 0o777, 0o700)

    def test_write_task_refuses_a_category_or_session_outside_the_rules(self):
        for category in ("xpto", "", "Docs", "docs\n"):
            with self.subTest(category), self.assertRaises(ValueError):
                usage.write_task(self.state, "s1", category)
        with self.assertRaises(ValueError):
            usage.write_task(self.state, "../x", "docs")
        self.assertFalse(self.state.exists())

    def test_every_write_uses_its_own_temp_file_name(self):
        sources = []
        real_replace = os.replace
        self.addCleanup(setattr, usage.os, "replace", real_replace)
        usage.os.replace = lambda src, dst: (sources.append(Path(src).name), real_replace(src, dst))[1]
        for n in range(3):
            usage._write_atomic(self.state, usage.usage_dir(self.state) / f"s{n}.task", "docs\n")
        self.assertEqual(len(set(sources)), 3, sources)
        self.assertTrue(all(name.startswith("w-") and name.endswith(".tmp") for name in sources))

    def test_a_write_outside_the_state_directory_is_refused(self):
        with self.assertRaises(ValueError):
            usage._write_atomic(self.state, self.root / "outside.json", "x")
        self.assertFalse((self.root / "outside.json").exists())


class ReportTest(Fixture):
    def seed(self, name, date, category, eq, output, limit_at=()):
        directory = usage.usage_dir(self.state)
        directory.mkdir(parents=True, exist_ok=True)
        record = {"v": 1, "session": name, "date": date, "project": "p", "category": category, "eq": eq,
                  "output": output, "main_eq": eq, "main_output": output, "sub_eq": 0, "sub_output": 0,
                  "limit_hits": len(limit_at), "limit_at": list(limit_at)}
        (directory / f"{name}.json").write_text(json.dumps(record, sort_keys=True) + "\n")

    def report(self, days=30, today=TODAY):
        return usage.build_report(self.state, days, today)

    def test_the_text_has_the_fixed_layout_and_truncated_means(self):
        self.seed("a", "2026-10-28", "feature", 100, 10)
        self.seed("b", "2026-10-27", "feature", 51, 5)
        self.seed("c", "2026-10-27", "bugfix", 7, 1, ["2026-10-26T01:00:00Z"])
        self.seed("d", "2026-10-26", "docs", 0, 0, ["2026-10-24T05:00:00Z"])
        self.seed("e", "2026-10-26", None, 9, 9, ["2026-10-19T00:00:00Z", ""])
        done = self.run_sb("usage", "report", "--days", "7", "--today", "2026-10-29")
        self.assertEqual(done.returncode, 0)
        self.assertEqual(done.stdout, "\n".join([
            "uso por tarefa: 2026-10-23 a 2026-10-29, 5 sessoes",
            "categoria  sessoes  eq_total  eq_media  saida_total  saida_media",
            "feature  2  151  75  15  7",
            "bugfix  1  7  7  1  1",
            "pesquisa  0  0  0  0  0",
            "docs  1  0  0  0  0",
            "sem-categoria  1  9  9  9  9",
            "",
            "estouros por semana",
            "2026-W43  1",
            "2026-W44  2",
            "",
        ]))

    def test_json_carries_the_same_numbers(self):
        self.seed("a", "2026-10-28", "feature", 100, 10)
        self.seed("b", "2026-10-27", "feature", 51, 5, ["2026-10-28T00:00:00Z"])
        done = self.run_sb("usage", "report", "--days", "7", "--today", "2026-10-29", "--json")
        data = json.loads(done.stdout)
        self.assertEqual(data["sessions"], 2)
        self.assertEqual(data["categories"]["feature"],
                         {"sessions": 2, "eq_total": 151, "eq_mean": 75, "output_total": 15, "output_mean": 7})
        self.assertEqual(data["weeks"], [{"week": "2026-W43", "hits": 0}, {"week": "2026-W44", "hits": 1}])
        self.assertEqual((data["from"], data["to"], data["skipped"]), ("2026-10-23", "2026-10-29", 0))

    def test_the_window_boundary_is_one_day_exact(self):
        self.seed("in", "2026-10-23", "docs", 1, 1)
        self.seed("out", "2026-10-22", "docs", 1, 1)
        self.assertEqual(self.report(days=7)["categories"]["docs"]["sessions"], 1)

    def test_weeks_follow_iso_weeks_and_empty_weeks_show_zero(self):
        self.seed("sun", "2026-10-18", "docs", 1, 1, ["2026-10-18T10:00:00Z"])
        self.seed("mon", "2026-10-19", "docs", 1, 1, ["2026-10-19T10:00:00Z", "2026-10-19T11:00:00Z"])
        weeks = self.report(days=15, today=dt.date(2026, 10, 29))["weeks"]
        self.assertEqual(weeks, [{"week": "2026-W42", "hits": 1}, {"week": "2026-W43", "hits": 2},
                                 {"week": "2026-W44", "hits": 0}])

    def test_a_blank_limit_timestamp_uses_the_record_date_and_old_notices_do_not_count(self):
        self.seed("a", "2026-10-26", "docs", 1, 1, ["", "2026-09-01T00:00:00Z"])
        self.seed("old", "2026-09-01", "docs", 1, 1, [""])
        weeks = {w["week"]: w["hits"] for w in self.report(days=7)["weeks"]}
        self.assertEqual(weeks, {"2026-W43": 0, "2026-W44": 1})

    def test_a_notice_in_the_window_counts_even_when_the_session_started_before_it(self):
        self.seed("long", "2026-10-01", "docs", 1, 1, ["2026-10-28T00:00:00Z"])
        report = self.report(days=7)
        self.assertEqual(report["sessions"], 0)
        self.assertEqual({w["week"]: w["hits"] for w in report["weeks"]}["2026-W44"], 1)

    def test_an_empty_or_missing_state_reports_zeros(self):
        for _ in range(2):
            done = self.run_sb("usage", "report", "--today", "2026-10-29")
            self.assertEqual(done.returncode, 0)
            self.assertIn("0 sessoes", done.stdout)
            self.assertEqual(done.stdout.count("  0  0  0  0  0"), 5)
            usage.usage_dir(self.state).mkdir(parents=True, exist_ok=True)

    def test_unreadable_records_are_skipped_and_counted(self):
        self.seed("good", "2026-10-28", "docs", 3, 3)
        directory = usage.usage_dir(self.state)
        (directory / "garbled.json").write_text("{not json")
        (directory / "partial.json").write_text(json.dumps({"v": 1, "eq": 3}))
        extra = json.loads((directory / "good.json").read_text())
        extra["extra"] = 1
        (directory / "extra.json").write_text(json.dumps(extra))
        bool_field = json.loads((directory / "good.json").read_text())
        bool_field["eq"] = True
        (directory / "bool.json").write_text(json.dumps(bool_field))
        done = self.run_sb("usage", "report", "--today", "2026-10-29")
        self.assertTrue(done.stdout.endswith("ignorados: 4\n"), done.stdout)
        self.assertEqual(json.loads(self.run_sb("usage", "report", "--today", "2026-10-29", "--json").stdout)["skipped"], 4)
        self.assertIn("1 sessoes", done.stdout)

    def test_a_tampered_category_counts_as_uncategorized(self):
        self.seed("a", "2026-10-28", "xpto", 4, 4)
        self.assertEqual(self.report()["categories"][usage.UNCATEGORIZED]["sessions"], 1)

    def test_reporting_never_changes_the_state(self):
        self.seed("a", "2026-10-28", "docs", 4, 4)
        before = tree_hash(self.state)
        self.run_sb("usage", "report", "--today", "2026-10-29")
        self.run_sb("usage", "report", "--today", "2026-10-29", "--json")
        self.assertEqual(tree_hash(self.state), before)

    def test_bad_arguments_exit_2_without_a_traceback(self):
        for argv in (["--days", "0"], ["--days", "-3"], ["--days", "10000000"], ["--days", str(usage.MAX_DAYS + 1)],
                     ["--today", "2026-13-01"]):
            with self.subTest(argv):
                done = self.run_sb("usage", "report", *argv)
                self.assertEqual(done.returncode, 2)
                self.assertNotIn("Traceback", done.stderr)
        self.assertEqual(self.run_sb("usage", "report", "--days", str(usage.MAX_DAYS)).returncode, 0)
        for argv in (["--today", "0001-01-01", "--days", "2"], ["--today", "0001-01-01", "--days", "3660"]):
            with self.subTest(argv):
                done = self.run_sb("usage", "report", *argv)
                self.assertEqual(done.returncode, 2)
                self.assertNotIn("Traceback", done.stderr)
        self.assertEqual(self.run_sb("usage", "report", "--today", "9999-12-31", "--days", "2").returncode, 0)


class NonNegotiableTest(Fixture):
    def sentinel_transcript(self):
        rows = [
            {"type": "user", "timestamp": SENTINEL, "message": {"content": SENTINEL}},
            {"type": "assistant", "timestamp": SENTINEL, "uuid": SENTINEL,
             "message": {"id": SENTINEL, "model": SENTINEL, "usage": {"output_tokens": 3},
                         "content": [{"type": "text", "text": SENTINEL},
                                     {"type": "tool_result", "content": SENTINEL},
                                     {"type": "tool_use", "input": {"command": f"echo {SENTINEL}"}}]}},
            limit(text=f"Usage limit reached {SENTINEL}", ts=SENTINEL, uuid=SENTINEL),
        ]
        write_jsonl(self.transcript, rows)
        write_jsonl(self.root / "t1" / "subagents" / "agent-a.jsonl",
                    [{**rows[1], "message": {**rows[1]["message"], "id": "sub1"}}])

    def test_n1_no_tool_or_message_content_reaches_the_state(self):
        self.sentinel_transcript()
        shapes = [
            {"command": f"echo {SENTINEL}"}, {"file_path": "/r/a.py", "content": SENTINEL},
            {"file_path": "/r/b.py", "old_string": SENTINEL, "new_string": SENTINEL},
        ]
        for n, tool_input in enumerate(shapes):
            payload = {"session_id": "s1", "tool_name": "Bash" if n == 0 else "Edit", "tool_input": tool_input,
                       "tool_response": {"stdout": SENTINEL}}
            self.assertEqual(self.run_sb("observe", "record", stdin=json.dumps(payload)).returncode, 0)
        for _ in range(3):
            self.assertEqual(self.summarize("s1", self.transcript).returncode, 0)
        self.assertTrue(self.record()["limit_hits"])
        self.assertNotIn(SENTINEL.encode(), self.state_bytes())

    def test_n1_a_path_shaped_like_a_secret_is_not_logged_even_with_the_marker(self):
        for path in (f"/r/{FAKE_TOKEN}.py", f"/r/sb-allow-secret/{FAKE_TOKEN}.py"):  # sb-allow-secret
            payload = {"session_id": "s1", "tool_name": "Read", "tool_input": {"file_path": path}, "tool_response": "x"}
            self.assertFalse(observe.record(self.state, payload))
        self.assertFalse(observe.log_path(self.state, "s1").exists())
        self.assertTrue(observe.record(self.state, {"session_id": "s1", "tool_name": "Read",
                                                    "tool_input": {"file_path": "/r/a.py"}, "tool_response": "x"}))

    def test_n1_the_filter_ignores_the_marker_but_scan_text_keeps_honoring_it(self):
        self.assertTrue(secret_scan.contains_secret_shape(f"x {FAKE_TOKEN}"))  # sb-allow-secret
        self.assertTrue(secret_scan.contains_secret_shape(f"sb-allow-secret {FAKE_TOKEN}"))  # sb-allow-secret
        self.assertFalse(secret_scan.contains_secret_shape("/r/a.py"))
        self.assertEqual(secret_scan.scan_text(f"sb-allow-secret {FAKE_TOKEN}"), [])  # sb-allow-secret

    def test_n4_a_fake_credential_in_a_path_and_in_a_summary_never_reaches_the_state(self):
        write_jsonl(self.transcript, [reply("m1", out=1)])
        for _ in range(3):
            payload = {"session_id": "s1", "tool_name": "Read", "tool_input": {"file_path": f"/r/{FAKE_TOKEN}.py"},  # sb-allow-secret
                       "tool_response": "y" * 50_000}
            self.run_sb("observe", "record", stdin=json.dumps(payload))
        done = self.run_sb("candidate", "add", "--kind", "trap", "--title", "t", "--summary", f"usa {FAKE_TOKEN}")  # sb-allow-secret
        self.assertEqual(done.returncode, 2)
        self.summarize("s1", self.transcript, project=FAKE_TOKEN)
        blob = self.state_bytes() if self.state.exists() else b""
        self.assertNotIn(b"ghp_", blob)
        for path in self.state.rglob("*"):
            if path.is_file():
                self.assertEqual(secret_scan.scan_text(path.read_text(encoding="utf-8")), [], path.name)

    def test_n2_the_new_code_writes_only_through_one_atomic_helper(self):
        tree = ast.parse(Path(usage.__file__).read_text(encoding="utf-8"))
        imported = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
        imported |= {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
        self.assertFalse(imported & {"subprocess", "shutil"})
        writers, forbidden = set(), set()
        for func in (n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)):
            for call in (n for n in ast.walk(func) if isinstance(n, ast.Call)):
                name = call.func.attr if isinstance(call.func, ast.Attribute) else getattr(call.func, "id", "")
                if name in {"write_text", "write_bytes", "replace", "mkstemp", "fdopen", "rename", "write"}:
                    writers.add(func.name)
                if name in {"system", "popen", "run", "Popen", "check_output", "call"}:
                    forbidden.add(func.name)
        self.assertEqual(writers, {"_write_atomic"})
        self.assertEqual(forbidden, set())

    def test_n2_stop_leaves_the_project_untouched(self):
        project = self.root / "proj"
        (project / ".claude").mkdir(parents=True)
        for name in ("CLAUDE.md", "AGENTS.md", ".claude/settings.local.json"):
            (project / name).write_text("conteudo original\n")
        subprocess.run(["git", "init", "-q"], cwd=project, check=True)
        subprocess.run(["git", "add", "-A"], cwd=project, check=True)
        subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "init"], cwd=project,
                       check=True)

        def snapshot():
            sums = [hashlib.sha256((project / n).read_bytes()).hexdigest()
                    for n in ("CLAUDE.md", "AGENTS.md", ".claude/settings.local.json")]
            status = subprocess.run(["git", "status", "--porcelain"], cwd=project, capture_output=True, text=True).stdout
            return sums, status

        before = snapshot()
        for session in ("s1", "s2"):
            for _ in range(3):
                self.run_sb("observe", "record", cwd=project, stdin=json.dumps(
                    {"session_id": session, "tool_name": "Read", "tool_input": {"file_path": "/r/a.py"},
                     "tool_response": "x"}))
            self.run_sb("observe", "record", cwd=project, stdin=json.dumps(
                {"session_id": session, "tool_name": "Read", "tool_input": {"file_path": "/r/big.py"},
                 "tool_response": "y" * 45_000}))
            transcript = self.root / f"{session}.jsonl"
            write_jsonl(transcript, [reply(f"m-{session}", out=1)])
            for _ in range(3):
                self.run_sb("observe", "summarize", "--session", session, "--transcript", str(transcript), cwd=project)
        self.assertEqual(snapshot(), before)

    def test_n2_patch_apply_without_an_id_fails_and_changes_nothing(self):
        self.run_sb("task", "set", "docs", "--session", "s1")
        before = tree_hash(self.state)
        done = self.run_sb("patch", "apply")
        self.assertNotEqual(done.returncode, 0)
        self.assertEqual(tree_hash(self.state), before)


class RuntimeTest(Fixture):
    def big_inputs(self):
        rows = [reply(f"m{n}", out=n, read=1000 + n, create=10, inp=1, ts=f"2026-10-20T10:{n % 60:02d}:00Z",
                      uuid=f"u{n}") for n in range(20_000)]
        write_jsonl(self.transcript, rows)
        for n in range(15):
            write_jsonl(self.root / "t1" / "subagents" / f"agent-{n}.jsonl",
                        [reply(f"s{n}-{k}", out=1, read=100, inp=1, uuid=f"s{n}-{k}") for k in range(500)])
        log = observe.log_path(self.state, "s1")
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text("".join(json.dumps({"ts": 1, "tool": "Read", "path": f"/r/f{n % 50}.py", "size": 10}) + "\n"
                               for n in range(5000)))

    def test_stop_is_fast_with_a_big_log_and_a_big_transcript(self):
        self.big_inputs()
        self.assertGreater(self.transcript.stat().st_size, 4_000_000)
        times = []
        for _ in range(3):
            start = time.perf_counter()
            done = self.summarize("s1", self.transcript)
            times.append(time.perf_counter() - start)
            self.assertEqual(done.returncode, 0, done.stderr)
        self.assertLess(statistics.median(times), 2.0, times)
        self.assertEqual(self.record()["main_output"], sum(range(20_000)))

    def test_a_blocked_usage_directory_does_not_stop_the_candidates(self):
        write_jsonl(self.transcript, [reply("m1", out=1)])
        self.state.mkdir()
        for _ in range(3):
            self.run_sb("observe", "record", stdin=json.dumps(
                {"session_id": "s1", "tool_name": "Read", "tool_input": {"file_path": "/r/a.py"}, "tool_response": "x"}))
        (self.state / "usage").write_text("a file, not a directory")
        done = self.summarize("s1", self.transcript)
        self.assertEqual((done.returncode, done.stderr), (0, ""))
        self.assertEqual(len(candidates.load(self.state)[0]), 1)
        (self.state / "usage").unlink()
        self.lock_dir(0o500)
        done = self.summarize("s1", self.transcript)
        self.assertEqual((done.returncode, done.stderr), (0, ""))
        self.assertEqual(len(candidates.load(self.state)[0]), 1)


class FitTest(Fixture):
    def test_the_help_lists_the_new_commands(self):
        out = self.run_sb("--help").stdout
        self.assertIn("task", out)
        self.assertIn("usage", out)

    def test_the_new_module_imports_only_the_standard_library_and_this_directory(self):
        tree = ast.parse(Path(usage.__file__).read_text(encoding="utf-8"))
        names = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
        names |= {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
        self.assertLessEqual(names - {"lib"}, set(sys.stdlib_module_names))


if __name__ == "__main__":
    unittest.main()
