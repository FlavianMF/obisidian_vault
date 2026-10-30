"""Testes da fila de candidatos (I3): python3 -m unittest discover -s 00_META/skills/second-brain-sync/scripts -v

Credenciais abaixo são FALSAS e montadas em tempo de execução.
"""

import ast
import datetime as dt
import hashlib
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
import usage
from lib import secret_scan  # noqa: F401  (the scanner the queue relies on)

SB = Path(sb.__file__)
CLI_TIMEOUT = 30  # a hung subprocess fails the test instead of the whole run


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


class ReviewMemoryTest(QueueFixture):
    def review(self, cid, outcome):
        self.state.mkdir(parents=True, exist_ok=True)
        with (self.state / candidates.REVIEW_LOG).open("a") as log:
            log.write(json.dumps({"id": cid, "outcome": outcome}) + "\n")

    def test_a_temp_file_suffix_in_the_title_does_not_change_the_id(self):
        a = candidates.candidate_id("pattern", "Read grande de ecc-observer-analysis.jsonl.QT9hkj", "p")
        b = candidates.candidate_id("pattern", "Read grande de ecc-observer-analysis.jsonl.XJB6zi", "p")
        self.assertEqual(a, b)
        self.assertNotEqual(candidates.candidate_id("trap", "usar build.gradle", "p"),
                            candidates.candidate_id("trap", "usar build.groovy", "p"))

    def test_observer_noise_with_different_suffixes_is_queued_once(self):
        first = self.add("Releitura repetida de x.jsonl.QT9hkj", kind="trap", source="observer")
        second = self.add("Releitura repetida de x.jsonl.lAUVTH", kind="trap", source="observer")
        self.assertEqual((first[1], second[1]), (True, False))

    def test_a_decided_candidate_leaves_the_list_and_is_not_queued_again(self):
        cid, _ = self.add()
        self.review(cid, "rejected")
        self.assertEqual(candidates.load(self.state)[0], [])
        self.assertEqual(len(candidates.load(self.state, include_decided=True)[0]), 1)
        self.assertEqual(self.add(), (cid, False))
        self.assertTrue(candidates.was_decided(self.state, cid))
        self.assertEqual(candidates.summary_line(self.state), "0 pending")

    def test_applied_also_counts_as_decided(self):
        cid, _ = self.add()
        self.review(cid, "applied")
        self.assertEqual(candidates.load(self.state)[0], [])

    def test_refused_and_skipped_outcomes_keep_the_candidate_pending(self):
        cid, _ = self.add()
        self.review(cid, "refused")
        self.review(cid, "skipped")
        self.assertEqual([i.id for i in candidates.load(self.state)[0]], [cid])

    def test_a_garbled_review_log_line_is_ignored(self):
        cid, _ = self.add()
        (self.state / candidates.REVIEW_LOG).write_text("not json\n[]\n")
        self.assertEqual([i.id for i in candidates.load(self.state)[0]], [cid])


class DraftTest(QueueFixture):
    def test_draft_is_stored_with_mode_0600_in_a_0700_directory(self):
        cid, created = self.add(body="# Corpo\n\nTexto do rascunho.\n")
        path = candidates.draft_path(self.state, cid)
        self.assertEqual((created, candidates.read_draft(self.state, cid)), (True, "# Corpo\n\nTexto do rascunho.\n"))
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(path.parent.stat().st_mode), 0o700)

    def test_draft_with_a_secret_queues_nothing_and_never_echoes_it(self):
        token = fake_token()
        with self.assertRaises(candidates.QueueError) as raised:
            self.add(body=f"chave {token}")
        self.assertNotIn(token, str(raised.exception))
        self.assertEqual(candidates.load(self.state)[0], [])
        self.assertFalse((self.state / candidates.DRAFT_DIR).exists())

    def test_oversized_draft_is_refused(self):
        with self.assertRaises(candidates.QueueError):
            self.add(body="x" * (candidates.MAX_DRAFT_BYTES + 1))

    def test_a_duplicate_does_not_overwrite_the_first_draft(self):
        cid, _ = self.add(body="primeiro")
        self.add(body="segundo")
        self.assertEqual(candidates.read_draft(self.state, cid), "primeiro")

    def test_prune_apply_removes_the_draft_of_an_expired_candidate(self):
        entry = self.entry("Velho", 40)
        self.write_raw([entry])
        candidates.write_draft(self.state, entry["id"], "rascunho velho")
        candidates.prune(self.state, apply=False)
        self.assertIsNotNone(candidates.read_draft(self.state, entry["id"]))
        candidates.prune(self.state, apply=True)
        self.assertIsNone(candidates.read_draft(self.state, entry["id"]))


class CliTest(QueueFixture):
    def run_sb(self, *args, stdin=None):
        env = dict(os.environ, SECOND_BRAIN_STATE_DIR=str(self.state))
        return subprocess.run([sys.executable, str(SB), "candidate", *args], capture_output=True, text=True, env=env,
                              input=stdin)

    def test_body_file_from_stdin_is_kept_and_a_reviewed_candidate_says_so(self):
        done = self.run_sb("add", "--kind", "trap", "--title", "Com rascunho", "--project", "p", "--body-file", "-",
                           stdin="corpo vindo do stdin\n")
        self.assertEqual(done.returncode, 0)
        cid = done.stdout.split(": ")[1].strip()
        self.assertEqual(candidates.read_draft(self.state, cid), "corpo vindo do stdin\n")
        (self.state / candidates.REVIEW_LOG).write_text(json.dumps({"id": cid, "outcome": "rejected"}) + "\n")
        again = self.run_sb("add", "--kind", "trap", "--title", "Com rascunho", "--project", "p")
        self.assertIn("already reviewed", again.stdout)

    def test_body_file_with_a_secret_exits_two(self):
        token = fake_token()
        done = self.run_sb("add", "--kind", "trap", "--title", "t", "--body-file", "-", stdin=token)
        self.assertEqual(done.returncode, 2)
        self.assertNotIn(token, done.stdout + done.stderr)

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


FAKE_TOKEN = "ghp_" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8"  # sb-allow-secret
SENTINEL = "SENTINELA-NAO-GRAVAR"


def tree_hash(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if path.is_file():
            digest.update(str(path.relative_to(root)).encode() + oct(path.stat().st_mode).encode() + path.read_bytes())
    return digest.hexdigest()


class RecurrenceFixture(QueueFixture):
    TITLE = "Quoting do zsh quebra o hook"

    def recur(self, session, title=None, **kw):
        return self.add(title=title or self.TITLE, session=session, project=kw.pop("project", "p"), **kw)

    def raw(self) -> bytes:
        return candidates.queue_path(self.state).read_bytes()

    def objs(self):
        return [json.loads(line) for line in self.raw().split(b"\n") if line.strip()]

    def stamp(self):
        stat_ = candidates.queue_path(self.state).stat()
        return hashlib.sha256(self.raw()).hexdigest(), stat_.st_mtime_ns

    def seed_log(self, session, state=None):
        log = observe.log_path(state or self.state, session)
        log.parent.mkdir(parents=True, exist_ok=True)
        rows = [{"ts": 1, "tool": "Read", "path": "/r/a.py", "size": 10}] * 3
        rows.append({"ts": 2, "tool": "Read", "path": "/r/big.py", "size": 45_000})
        log.write_text("".join(json.dumps(r) + "\n" for r in rows))

    def run_sb(self, *args, env=None):
        base = {k: v for k, v in os.environ.items() if k != "CLAUDE_CODE_SESSION_ID"}
        base.update(SECOND_BRAIN_STATE_DIR=str(self.state), PYTHONDONTWRITEBYTECODE="1")
        base.update(env or {})
        return subprocess.run([sys.executable, str(SB), *args], capture_output=True, text=True, env=base,
                              timeout=CLI_TIMEOUT)

    def lock(self, path, mode):
        path.chmod(mode)
        self.addCleanup(lambda: path.exists() and path.chmod(0o700))


class NewLineTest(RecurrenceFixture):
    def test_a_new_line_has_the_old_keys_and_the_recurrence_keys(self):
        cid, created = self.recur("s1")
        (row,) = self.objs()
        self.assertEqual(list(row), ["id", "ts", "kind", "title", "summary", "project", "source", "count", "sessions",
                                     "session_ids"])
        self.assertEqual((row["id"], created, row["count"], row["sessions"], row["session_ids"]),
                         (cid, True, 1, 1, ["s1"]))
        self.assertEqual((row["kind"], row["title"], row["project"], row["source"]), ("trap", self.TITLE, "p", "agent"))
        self.assertEqual(stat.S_IMODE(candidates.queue_path(self.state).stat().st_mode), 0o600)

    def test_without_a_session_the_line_counts_once_and_has_no_session(self):
        self.recur(None)
        (row,) = self.objs()
        self.assertEqual((row["count"], row["sessions"], row["session_ids"]), (1, 0, []))

    def test_a_legacy_line_reads_as_count_one_and_no_sessions(self):
        self.write_raw([self.entry("Velho", 2)])
        (item,) = candidates.load(self.state)[0]
        self.assertEqual((item.count, item.sessions, item.session_ids), (1, 0, ()))

    def test_damaged_recurrence_fields_read_as_defaults(self):
        base = self.entry("Dano", 1)
        cases = [({"count": True}, 1, ()), ({"count": "3"}, 1, ()), ({"count": 2.5}, 1, ()), ({"count": -4}, 1, ()),
                 ({"count": 0}, 1, ()), ({"count": None}, 1, ()), ({"session_ids": "s1"}, 1, ()),
                 ({"session_ids": ["a", 3, None, "", "a", "b"]}, 2, ("a", "b")),
                 ({"count": 1, "sessions": 9, "session_ids": ["a", "b"]}, 2, ("a", "b"))]
        for extra, count, ids in cases:
            with self.subTest(extra=extra):
                self.write_raw([{**base, **extra}])
                (item,) = candidates.load(self.state)[0]
                self.assertEqual((item.count, item.sessions, item.session_ids), (count, len(ids), ids))

    def test_a_line_that_is_not_an_object_is_unreadable_not_fatal(self):
        self.write_raw(["[1, 2]", '"texto"', "7"])
        self.assertEqual(candidates.load(self.state), ([], 3))


class RecurrenceTest(RecurrenceFixture):
    def test_a_second_session_raises_count_and_sessions_in_place(self):
        cid, _ = self.recur("s1")
        again, created = self.recur("s2")
        (row,) = self.objs()
        self.assertEqual((again, created), (cid, False))
        self.assertEqual((row["count"], row["sessions"], row["session_ids"]), (2, 2, ["s1", "s2"]))

    def test_the_same_session_again_changes_nothing(self):
        self.recur("s1")
        first = self.stamp()
        for _ in range(3):
            self.recur("s1")
        self.assertEqual(self.stamp(), first)

    def test_a_sequence_counts_each_session_once(self):
        for session in ("s1", "s2", "s1", "s2", "s3"):
            self.recur(session)
        (row,) = self.objs()
        self.assertEqual((row["count"], row["sessions"], row["session_ids"]), (3, 3, ["s1", "s2", "s3"]))

    def test_a_duplicate_without_a_session_changes_nothing(self):
        self.recur("s1")
        first = self.stamp()
        self.recur(None)
        self.assertEqual(self.stamp(), first)
        self.state.joinpath(candidates.QUEUE_NAME).unlink()
        self.recur(None)
        first = self.stamp()
        self.recur(None)
        self.assertEqual(self.stamp(), first)

    def test_an_anonymous_line_takes_the_first_session_as_a_second_sighting(self):
        self.recur(None)
        self.recur("s1")
        self.assertEqual([(r["count"], r["sessions"]) for r in self.objs()], [(2, 1)])
        first = self.stamp()
        self.recur("s1")
        self.assertEqual(self.stamp(), first)

    def test_a_legacy_line_gets_the_recurrence_and_keeps_unknown_keys(self):
        legacy = {**self.entry(self.TITLE, 2), "extra": 1}
        self.write_raw([legacy])
        self.recur("s1")
        self.assertEqual([(r["count"], r["sessions"], r["extra"]) for r in self.objs()], [(2, 1, 1)])
        first = self.stamp()
        self.recur("s1")
        self.assertEqual(self.stamp(), first)
        self.recur("s2")
        self.assertEqual([(r["count"], r["sessions"]) for r in self.objs()], [(3, 2)])

    def test_a_duplicate_never_changes_the_text_the_first_one_set(self):
        cid, _ = self.recur("s1", summary="primeiro", body="rascunho 1")
        before = self.objs()[0]
        self.recur("s2", summary="segundo", body="rascunho 2", kind="trap")
        after = self.objs()[0]
        for key in ("id", "ts", "kind", "title", "summary", "project", "source"):
            self.assertEqual(after[key], before[key], key)
        self.assertEqual(candidates.read_draft(self.state, cid), "rascunho 1")

    def test_the_session_list_stops_at_the_cap_and_a_new_id_changes_nothing(self):
        for n in range(candidates.MAX_SESSION_IDS):
            self.recur(f"s{n}")
        (row,) = self.objs()
        self.assertEqual((row["sessions"], row["count"]), (100, 100))
        first = self.stamp()
        self.recur("novo")
        self.recur("s5")
        self.assertEqual(self.stamp(), first)

    def test_two_candidates_with_one_session_count_it_each(self):
        self.recur("s1", title="Primeiro achado")
        self.recur("s1", title="Segundo achado")
        self.assertEqual([r["sessions"] for r in self.objs()], [1, 1])

    def test_the_same_finding_in_another_project_is_another_candidate(self):
        self.recur("s1", project="A")
        self.recur("s2", project="B")
        self.assertEqual([(r["project"], r["sessions"], r["count"]) for r in self.objs()], [("A", 1, 1), ("B", 1, 1)])

    def test_two_live_lines_with_one_id_only_the_first_changes(self):
        first, second = self.entry(self.TITLE, 2), self.entry(self.TITLE, 1)
        second["session_ids"], second["count"] = ["s9"], 2
        self.write_raw([first, second])
        before_second = self.raw().split(b"\n")[1]
        self.recur("s9")
        rows = self.raw().split(b"\n")
        self.assertEqual(rows[1], before_second)
        self.assertEqual((json.loads(rows[0])["sessions"], json.loads(rows[0])["session_ids"]), (1, ["s9"]))

    def test_the_rewrite_keeps_the_mode_leaves_no_temp_file_and_ignores_the_umask(self):
        self.recur("s1")
        old = os.umask(0)
        try:
            self.recur("s2")
        finally:
            os.umask(old)
        self.assertEqual(stat.S_IMODE(candidates.queue_path(self.state).stat().st_mode), 0o600)
        self.assertEqual(sorted(p.name for p in self.state.iterdir()), ["queue.jsonl", "queue.lock"])

    def test_a_failed_rewrite_removes_its_temp_file(self):
        self.recur("s1")
        original = os.replace
        os.replace = lambda *a: (_ for _ in ()).throw(OSError(28, "No space left on device"))
        try:
            with self.assertRaises(OSError):
                self.recur("s2")
        finally:
            os.replace = original
        self.assertEqual(sorted(p.name for p in self.state.iterdir()), ["queue.jsonl", "queue.lock"])
        self.assertEqual(self.objs()[0]["sessions"], 1)


ODD = [b"\xff\xfe bad", b"", b'{"id":"zz","ts":"2026-10-20T00:00:00+00:00","kind":"trap","title":"crlf"}\r',
       "linha ilegivel \u2028 com separador".encode(), b"ultima sem quebra"]


class ByteExactTest(RecurrenceFixture):
    def target(self):
        return json.dumps(self.entry(RecurrenceFixture.TITLE, 2)).encode()

    def test_a_rewrite_keeps_every_other_line_byte_for_byte(self):
        self.state.mkdir(parents=True)
        rows = [ODD[0], self.target(), *ODD[1:]]
        candidates.queue_path(self.state).write_bytes(b"\n".join(rows))
        self.recur("s1")
        after = self.raw().split(b"\n")
        self.assertEqual([r for i, r in enumerate(after) if i != 1], [r for i, r in enumerate(rows) if i != 1])
        self.assertEqual(json.loads(after[1])["session_ids"], ["s1"])
        self.assertFalse(self.raw().endswith(b"\n"))

    def test_a_target_on_the_unterminated_last_line_stays_unterminated(self):
        self.state.mkdir(parents=True)
        candidates.queue_path(self.state).write_bytes(b"\n".join([*ODD[:3], self.target()]))
        self.recur("s1")
        self.assertFalse(self.raw().endswith(b"\n"))
        self.assertEqual(self.raw().split(b"\n")[:3], ODD[:3])

    def test_a_terminated_queue_stays_terminated(self):
        self.state.mkdir(parents=True)
        candidates.queue_path(self.state).write_bytes(self.target() + b"\n")
        self.recur("s1")
        self.assertTrue(self.raw().endswith(b"\n"))

    def test_invalid_utf8_in_the_queue_does_not_stop_add_list_or_prune(self):
        self.state.mkdir(parents=True)
        candidates.queue_path(self.state).write_bytes(b"\xff\xfe bad\n")
        done = self.run_sb("candidate", "add", "--kind", "trap", "--title", "novo", "--project", "p", "--session", "s1")
        self.assertEqual((done.returncode, done.stderr, done.stdout.startswith("queued: ")), (0, "", True))
        self.assertTrue(self.raw().startswith(b"\xff\xfe bad\n"))
        for args in (("list",), ("list", "--json"), ("prune",), ("prune", "--apply")):
            done = self.run_sb("candidate", *args)
            self.assertEqual((done.returncode, done.stderr), (0, ""), args)
        self.assertIn("1 unreadable line(s) kept", self.run_sb("candidate", "list").stdout)

    def test_a_new_line_is_never_glued_onto_an_unterminated_last_line(self):
        self.state.mkdir(parents=True)
        candidates.queue_path(self.state).write_bytes(b"lixo sem quebra")
        self.recur("s1")
        lines = self.raw().split(b"\n")
        self.assertEqual((lines[0], json.loads(lines[1])["sessions"]), (b"lixo sem quebra", 1))

    def test_prune_keeps_every_unexpired_and_unreadable_line_in_bytes(self):
        self.state.mkdir(parents=True)
        old = json.dumps(self.entry("velho", 40)).encode()
        rows = [ODD[0], old, self.target(), *ODD[1:]]
        candidates.queue_path(self.state).write_bytes(b"\n".join(rows))
        removed = candidates.prune(self.state, apply=True)
        self.assertEqual([r.title for r in removed], ["velho"])
        self.assertEqual(self.raw().split(b"\n"), [r for r in rows if r != old])

    def test_a_line_with_a_raw_0xff_inside_a_string_is_unreadable_and_never_the_target(self):
        self.state.mkdir(parents=True)
        cid = candidates.candidate_id("trap", self.TITLE, "p")
        bad = (b'{"id":"' + cid.encode() + b'","ts":"' + dt.datetime.now(dt.timezone.utc).isoformat().encode()
               + b'","kind":"trap","title":"x\xff"}')
        candidates.queue_path(self.state).write_bytes(bad + b"\n")
        self.recur("s2")
        rows = self.raw().split(b"\n")
        self.assertEqual((rows[0], json.loads(rows[1])["session_ids"]), (bad, ["s2"]))
        live = self.entry(self.TITLE, 1)
        candidates.queue_path(self.state).write_bytes(bad + b"\n" + json.dumps(live).encode() + b"\n")
        self.recur("s3")
        rows = self.raw().split(b"\n")
        self.assertEqual((rows[0], json.loads(rows[1])["session_ids"]), (bad, ["s3"]))

    def test_the_target_is_rewritten_as_utf8_json_with_the_same_values_and_order(self):
        self.state.mkdir(parents=True)
        cid = candidates.candidate_id("trap", "A\u00e7\u00e3o", "p")
        text = ('{"id": "%s",  "ts": "%s", "kind": "trap", "title": "A\\u00e7\\u00e3o", "summary": "", '
                '"project": "p", "source": "agent", "extra": [1]}\r') % (cid, candidates.utcnow().isoformat(timespec="seconds"))
        candidates.queue_path(self.state).write_bytes(text.encode() + b"\n")
        before = json.loads(text)
        self.recur("s1", title="A\u00e7\u00e3o")
        (line,) = [r for r in self.raw().split(b"\n") if r]
        after = json.loads(line)
        self.assertFalse(line.endswith(b"\r"))
        self.assertIn("Aç".encode(), line)
        self.assertEqual(list(after)[:len(before)], list(before))
        self.assertEqual({k: after[k] for k in before}, before)
        self.assertEqual(after["extra"], [1])


class TtlAndDecidedTest(RecurrenceFixture):
    def test_a_recurrence_does_not_renew_the_ts(self):
        self.write_raw([self.entry(self.TITLE, 20)])
        ts = self.objs()[0]["ts"]
        self.recur("s1")
        (item,) = candidates.load(self.state)[0]
        self.assertEqual((self.objs()[0]["ts"], item.days_left, item.age_days), (ts, 10, 20))

    def test_an_expired_line_is_left_alone_and_a_new_line_is_born(self):
        self.write_raw([self.entry(self.TITLE, 31)])
        before = self.raw()
        _, created = self.recur("s2")
        self.assertTrue(created)
        self.assertTrue(self.raw().startswith(before))
        items, _ = candidates.load(self.state)
        self.assertEqual(len(items), 2)
        (fresh,) = candidates.live(items)
        self.assertEqual((fresh.count, fresh.sessions, fresh.days_left), (1, 1, 30))

    def test_with_an_expired_and_a_live_line_only_the_live_one_changes(self):
        self.write_raw([self.entry(self.TITLE, 31), self.entry(self.TITLE, 3)])
        expired = self.raw().split(b"\n")[0]
        self.recur("s1")
        rows = self.raw().split(b"\n")
        self.assertEqual((rows[0], json.loads(rows[1])["sessions"]), (expired, 1))

    def test_a_decided_candidate_is_not_touched_by_a_new_session(self):
        for outcome in ("applied", "rejected"):
            with self.subTest(outcome=outcome):
                cid, _ = self.recur("s1", title=f"Decidido {outcome}")
                with (self.state / candidates.REVIEW_LOG).open("a") as log:
                    log.write(json.dumps({"id": cid, "outcome": outcome}) + "\n")
                first = self.stamp()
                self.assertEqual(self.recur("s2", title=f"Decidido {outcome}"), (cid, False))
                self.assertEqual(self.stamp(), first)
                self.assertNotIn(b"s2", self.raw())

    def test_refused_and_skipped_do_not_decide_so_the_recurrence_counts(self):
        cid, _ = self.recur("s1")
        with (self.state / candidates.REVIEW_LOG).open("a") as log:
            for outcome in ("refused", "skipped"):
                log.write(json.dumps({"id": cid, "outcome": outcome}) + "\n")
        self.recur("s2")
        self.assertEqual(self.objs()[0]["sessions"], 2)

    def test_prune_removes_the_expired_and_keeps_the_recurrent_counters(self):
        self.write_raw([self.entry("velho", 40)])
        self.recur("s1")
        self.recur("s2")
        removed = candidates.prune(self.state, apply=True)
        self.assertEqual([r.title for r in removed], ["velho"])
        (row,) = self.objs()
        self.assertEqual((row["count"], row["sessions"]), (2, 2))

    def test_list_summary_and_format_ignore_the_recurrence(self):
        self.write_raw([self.entry("a", 25), self.entry("b", 1)])
        text = candidates.format_list(candidates.live(candidates.load(self.state)[0]), 0, 0)
        self.recur("s1", title="a")
        self.recur("s2", title="a")
        self.assertEqual(candidates.format_list(candidates.live(candidates.load(self.state)[0]), 0, 0), text)
        self.assertEqual(candidates.summary_line(self.state), "2 pending, 1 expire within 7 days")


class SessionIdTest(RecurrenceFixture):
    def ids(self):
        return self.objs()[0]["session_ids"]

    def test_the_id_is_cleaned_cut_and_collapsed(self):
        cases = {"../../evil": "evil", "s_1-x": "s_1-x", "s1/": "s1", "sessão": "sesso", "x" * 100: "x" * 64,
                 "ab" * 32: "ab" * 32}
        for raw, expected in cases.items():
            with self.subTest(raw=raw[:20]):
                self.state_clean()
                self.recur(raw)
                self.assertEqual(self.ids(), [expected])
        self.state_clean()
        self.recur("s1")
        self.recur("s1/")
        self.assertEqual((self.ids(), self.objs()[0]["count"]), (["s1"], 1))
        self.assertEqual([p.name for p in self.state.iterdir() if p.is_dir()], [])

    def state_clean(self):
        for path in list(self.state.glob("*")):
            path.unlink()

    def test_an_empty_or_missing_id_is_anonymous_and_the_candidate_is_kept(self):
        for raw in ("", "///", "..", None):
            with self.subTest(raw=raw):
                self.state_clean()
                _, created = self.recur(raw)
                self.assertTrue(created)
                self.assertEqual(self.ids(), [])

    def test_an_id_shaped_like_a_secret_is_anonymous_in_every_form(self):
        gh = "ghp_" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8"  # sb-allow-secret
        spread = "/.".join([gh[:4], *[gh[i:i + 6] for i in range(4, len(gh), 6)]])  # sb-allow-secret
        cases = {"raw": gh, "marker": "sb-allow-secret" + gh, "cleaned": spread, "cut": "a" * 40 + gh,  # sb-allow-secret
                 "cut, separated": "a" * 40 + "-" + gh,  # sb-allow-secret
                 "past the cut": "b" * 70 + gh}  # sb-allow-secret
        for name, raw in cases.items():
            with self.subTest(name=name):
                self.state_clean()
                self.assertIsNone(candidates.safe_session(raw))
                _, created = self.recur(raw)
                self.assertTrue(created)
                self.assertEqual(self.ids(), [])
                self.assertEqual(secret_scan.scan_text(self.raw().decode()), [])
                self.assertNotIn(b"A1b2C3d4", self.raw())

    def test_an_id_that_only_the_cut_makes_secret_shaped_is_refused(self):
        head = "z" * 43 + "-" + "ghp_" + "A" * 16  # sb-allow-secret
        raw = head + "_" + "B" * 8  # the underscore hides the shape until the cut drops it
        self.assertEqual(len(head), 64)
        self.assertFalse(secret_scan.contains_secret_shape(raw))
        self.assertTrue(secret_scan.contains_secret_shape(head))
        self.assertIsNone(candidates.safe_session(raw))
        self.assertEqual(candidates.safe_session(raw, cut=False), raw)

    def test_a_long_id_is_refused_before_any_scan_and_stays_fast(self):
        self.assertEqual(candidates.safe_session("c" * 128), "c" * 64)
        for size in (129, 2000, 100_000):
            start = time.perf_counter()
            self.assertIsNone(candidates.safe_session("a" * size))
            self.assertIsNone(candidates.safe_session("a" * size, cut=False))
            self.assertLess(time.perf_counter() - start, 0.1, size)
        start = time.perf_counter()  # the worst id that is still scanned
        self.assertEqual(candidates.safe_session("a1" * 64, cut=False), "a1" * 64)
        self.assertLess(time.perf_counter() - start, 0.5)

    def test_a_long_session_creates_nothing_and_the_stop_stays_fast(self):
        for size in (200, 20_000):
            with self.subTest(size=size):
                start = time.perf_counter()
                result = observe.summarize(self.state, "z" * size, "repo")
                self.assertLess(time.perf_counter() - start, 1.0)
                self.assertEqual((result["calls"], result["queued"], result["usage"]), (0, 0, None))
                self.assertFalse(self.state.exists() and any(self.state.rglob("*")))
                with self.assertRaises(ValueError):
                    observe.log_path(self.state, "z" * size)

    def test_an_id_of_64_is_stored_and_one_of_65_is_cut(self):
        self.assertEqual(candidates.safe_session("c" * 64), "c" * 64)
        self.assertEqual(candidates.safe_session("c" * 65), "c" * 64)
        self.assertEqual(candidates.safe_session("c" * 65, cut=False), "c" * 65)


class SummarizeTest(RecurrenceFixture):
    def test_two_sessions_with_one_log_recur_and_queue_nothing_the_second_time(self):
        self.seed_log("s1")
        first = observe.summarize(self.state, "s1", "repo")
        self.seed_log("s2")
        second = observe.summarize(self.state, "s2", "repo")
        self.assertEqual((first["queued"], second["queued"]), (2, 0))
        self.assertEqual([(r["count"], r["sessions"]) for r in self.objs()], [(2, 2), (2, 2)])

    def test_five_stops_in_one_session_leave_the_same_state(self):
        self.seed_log("s1")
        observe.summarize(self.state, "s1", "repo")
        first = (tree_hash(self.state), self.stamp()[1])
        for _ in range(4):
            observe.summarize(self.state, "s1", "repo")
        self.assertEqual((tree_hash(self.state), self.stamp()[1]), first)
        self.assertEqual([(r["count"], r["sessions"]) for r in self.objs()], [(1, 1), (1, 1)])

    def test_a_growing_log_does_not_count_the_session_twice(self):
        self.seed_log("s1")
        observe.summarize(self.state, "s1", "repo")
        with observe.log_path(self.state, "s1").open("a") as log:
            log.write(json.dumps({"ts": 3, "tool": "Read", "path": "/r/a.py", "size": 10}) + "\n")
        observe.summarize(self.state, "s1", "repo")
        self.assertEqual([(r["count"], r["sessions"]) for r in self.objs()], [(1, 1), (1, 1)])

    def test_a_session_without_a_valid_id_has_no_log_and_creates_nothing(self):
        for session in ("", "///"):
            with self.subTest(session=session):
                result = observe.summarize(self.state, session, "repo")
                self.assertEqual((result["calls"], result["queued"], result["usage"]), (0, 0, None))
                self.assertFalse(self.state.exists() and any(self.state.rglob("*")))

    def state_clean(self):
        for path in list(self.state.rglob("*")):
            if path.is_file():
                path.unlink()

    def test_a_session_shaped_like_a_secret_is_refused_at_every_file_name(self):
        session = FAKE_TOKEN + SENTINEL.replace("-", "")
        transcript = Path(self._tmp.name) / "t.jsonl"
        transcript.write_text(json.dumps({"type": "assistant", "timestamp": "2026-10-20T10:00:00.000Z", "uuid": "u1",
                                          "message": {"id": "m1", "usage": {"output_tokens": 3}}}) + "\n")
        payload = {"session_id": session, "tool_name": "Read", "tool_input": {"file_path": "/r/a.py"},
                   "tool_response": "x"}
        for _ in range(3):
            self.assertFalse(observe.record(self.state, payload))
        result = observe.summarize(self.state, session, "repo", transcript)
        self.assertEqual((result["calls"], result["queued"], result["usage"]), (0, 0, None))
        self.assertFalse(self.state.exists() and any(self.state.rglob("*")))  # no file, no directory, under any name

    def test_a_refused_session_through_the_cli_exits_zero_and_writes_nothing(self):
        payload = json.dumps({"session_id": "q" * 300, "tool_name": "Read", "tool_input": {"file_path": "/r/a.py"},
                              "tool_response": "x"})
        secret = json.dumps({"session_id": FAKE_TOKEN, "tool_name": "Read", "tool_input": {"file_path": "/r/a.py"},
                             "tool_response": "x"})
        for body in (payload, secret):
            start = time.perf_counter()
            done = subprocess.run([sys.executable, str(SB), "observe", "record"], input=body, capture_output=True,
                                  text=True, env=dict(os.environ, SECOND_BRAIN_STATE_DIR=str(self.state)),
                                  timeout=CLI_TIMEOUT)
            self.assertEqual((done.returncode, done.stdout, done.stderr), (0, "", ""))
            self.assertLess(time.perf_counter() - start, 1.5)
        for session in ("q" * 20_000, FAKE_TOKEN):
            done = subprocess.run([sys.executable, str(SB), "observe", "summarize", "--session", session],
                                  capture_output=True, text=True, env=dict(os.environ, SECOND_BRAIN_STATE_DIR=str(self.state)),
                                  timeout=CLI_TIMEOUT)
            self.assertEqual((done.returncode, done.stderr), (0, ""))
        self.assertFalse(self.state.exists() and any(self.state.rglob("*")))

    def test_task_set_refuses_a_long_or_secret_shaped_id_with_exit_two(self):
        for session in ("q" * 300, FAKE_TOKEN, "a" * 40 + FAKE_TOKEN):
            done = self.run_sb("task", "set", "docs", "--session", session)
            self.assertEqual(done.returncode, 2)
            self.assertRegex(done.stderr, r"^sb task: session id refused \(over 128 characters or shaped like a credential\)\n$")
            self.assertNotIn(session, done.stdout + done.stderr)
        self.assertFalse(self.state.exists() and any(self.state.rglob("*")))
        self.assertEqual(self.run_sb("task", "set", "docs", "--session", "ok-1").returncode, 0)
        with self.assertRaises(ValueError):
            usage.write_task(self.state, "q" * 300, "docs")
        with self.assertRaises(ValueError):
            usage.write_task(self.state, FAKE_TOKEN, "docs")

    def test_no_file_name_in_the_state_carries_a_refused_id(self):
        for session in (FAKE_TOKEN, "q" * 150):
            self.run_sb("task", "set", "docs", "--session", session)
            self.run_sb("candidate", "add", "--kind", "trap", "--title", "t", "--session", session)
            observe.record(self.state, {"session_id": session, "tool_name": "Read", "tool_input": {"file_path": "/r/a"}})
        names = [p.name for p in self.state.rglob("*")] if self.state.exists() else []
        self.assertFalse([n for n in names if "ghp_" in n or "qqqq" in n], names)

    def test_a_blocked_queue_does_not_stop_the_usage_record(self):
        transcript = Path(self._tmp.name) / "t.jsonl"
        transcript.write_text(json.dumps({"type": "assistant", "timestamp": "2026-10-20T10:00:00.000Z", "uuid": "u1",
                                          "message": {"id": "m1", "usage": {"output_tokens": 3}}}) + "\n")
        self.seed_log("s1")
        self.add(title="primeiro")
        queue = candidates.queue_path(self.state)
        self.lock(queue, 0o400)  # file read-only, directory writable: new lines fail, recurrences swap the file
        result = observe.summarize(self.state, "s1", "repo", transcript)
        self.assertEqual((result["queued"], result["usage"]["output"]), (0, 3))
        queue.chmod(0o600)
        queue.unlink()
        queue.mkdir()  # a directory where the queue should be
        result = observe.summarize(self.state, "s1", "repo", transcript)
        self.assertEqual((result["queued"], result["usage"]["output"]), (0, 3))
        queue.rmdir()
        (self.state / "usage").mkdir(exist_ok=True)
        self.lock(self.state, 0o500)  # state directory read-only; usage/ and queue.lock already exist
        result = observe.summarize(self.state, "s1", "repo", transcript)
        self.assertEqual((result["queued"], result["usage"]["output"]), (0, 3))
        self.assertEqual(stat.S_IMODE(self.state.stat().st_mode), 0o500)

    def test_a_damaged_queue_does_not_stop_the_stop(self):
        self.state.mkdir(parents=True)
        candidates.queue_path(self.state).write_bytes(b"\xff\xfe bad\n")
        self.seed_log("s1")
        result = observe.summarize(self.state, "s1", "repo")
        self.assertEqual(result["queued"], 2)

    def test_concurrent_summaries_of_one_session_and_of_four_sessions(self):
        script = ("import sys; sys.path.insert(0, %r); import observe; from pathlib import Path; "
                  "observe.summarize(Path(sys.argv[1]), sys.argv[2], 'repo')") % str(Path(sb.__file__).parent)
        for round_ in range(5):
            for sessions, want in ((["s1"] * 4, 1), ([f"c{n}" for n in range(4)], 4)):
                state = Path(self._tmp.name) / f"state-{round_}-{want}"
                self.seed_log("x", state)
                for sid in set(sessions):
                    log = observe.log_path(state, sid)
                    log.write_bytes(observe.log_path(state, "x").read_bytes())
                procs = [subprocess.Popen([sys.executable, "-c", script, str(state), sid], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                         for sid in sessions]
                for proc in procs:
                    self.assertEqual((proc.wait(), proc.stderr.read()), (0, b""))
                    proc.stderr.close()
                rows = [json.loads(line) for line in (state / "queue.jsonl").read_bytes().splitlines()]
                self.assertEqual([(r["count"], r["sessions"], len(set(r["session_ids"]))) for r in rows],
                                 [(want, want, want)] * 2)
                self.assertFalse(list(state.glob(".queue-*")))

    def test_rewrites_race_without_losing_a_line(self):
        for _ in range(5):
            state = Path(self._tmp.name) / f"race-{_}"
            state.mkdir(parents=True)
            base = [self.entry(self.TITLE, 1), self.entry("vencida", 40)]
            (state / "queue.jsonl").write_text("".join(json.dumps(e) + "\n" for e in base))
            self.recur_in(state, "s1")
            self.seed_log("s2", state)
            procs = [
                subprocess.Popen([sys.executable, str(SB), "observe", "summarize", "--session", "s2", "--project", "p"],
                                 env=dict(os.environ, SECOND_BRAIN_STATE_DIR=str(state)), stdout=subprocess.DEVNULL, stderr=subprocess.PIPE),
                subprocess.Popen([sys.executable, str(SB), "candidate", "add", "--kind", "trap", "--title", self.TITLE,
                                  "--project", "p", "--session", "s3"],
                                 env=dict(os.environ, SECOND_BRAIN_STATE_DIR=str(state)), stdout=subprocess.DEVNULL, stderr=subprocess.PIPE),
                subprocess.Popen([sys.executable, str(SB), "candidate", "prune", "--apply"],
                                 env=dict(os.environ, SECOND_BRAIN_STATE_DIR=str(state)), stdout=subprocess.DEVNULL, stderr=subprocess.PIPE),
            ]
            for proc in procs:
                self.assertEqual((proc.wait(), proc.stderr.read()), (0, b""))
                proc.stderr.close()
            rows = [json.loads(line) for line in (state / "queue.jsonl").read_bytes().splitlines()]
            target = next(r for r in rows if r["title"] == self.TITLE)
            self.assertEqual((sorted(target["session_ids"]), target["count"]), (["s1", "s3"], 3))  # legacy base 1 plus two sessions
            self.assertNotIn("vencida", [r["title"] for r in rows])
            self.assertEqual(len(rows), 3)  # target plus the two findings of s2
            self.assertFalse(list(state.glob(".queue-*")))

    def recur_in(self, state, session):
        candidates.add(state, kind="trap", title=self.TITLE, summary="x", project="p", session=session)


class RecurrenceCliTest(RecurrenceFixture):
    def add_cli(self, *extra, env=None):
        return self.run_sb("candidate", "add", "--kind", "trap", "--title", "Hook sem aspas", "--project", "p", *extra,
                           env=env)

    def test_the_second_session_prints_the_recurrence(self):
        first = self.add_cli("--session", "s1")
        second = self.add_cli("--session", "s2")
        self.assertEqual((first.returncode, first.stdout.startswith("queued: ")), (0, True))
        cid = first.stdout.split(": ")[1].strip()
        self.assertEqual((second.returncode, second.stdout), (0, f"already queued: {cid} (seen 2x, 2 sessions)\n"))

    def test_the_same_session_prints_no_suffix_while_the_count_is_one_and_changes_nothing(self):
        self.add_cli("--session", "s1")
        first = self.stamp()
        again = self.add_cli("--session", "s1")
        self.assertRegex(again.stdout, r"^already queued: [0-9a-f]{8}\n$")
        self.assertEqual(self.stamp(), first)

    def test_the_flag_beats_the_environment_and_neither_means_anonymous(self):
        self.add_cli("--session", "flag", env={"CLAUDE_CODE_SESSION_ID": "env"})
        self.assertEqual(self.objs()[0]["session_ids"], ["flag"])
        self.add_cli(env={"CLAUDE_CODE_SESSION_ID": "env"})
        self.assertEqual(self.objs()[0]["session_ids"], ["flag", "env"])
        self.state_wipe()
        self.add_cli()
        self.assertEqual(self.objs()[0]["session_ids"], [])

    def state_wipe(self):
        for path in list(self.state.glob("*")):
            path.unlink()

    def test_a_secret_shaped_session_is_refused_with_exit_two_and_not_echoed(self):
        done = self.add_cli("--session", FAKE_TOKEN)
        self.assertEqual((done.returncode, done.stdout), (2, ""))
        self.assertRegex(done.stderr, r"^sb candidate: session id refused ")
        self.assertNotIn("ghp_", done.stdout + done.stderr)
        self.assertFalse(self.state.exists() and any(self.state.rglob("*")))
        self.assertEqual(self.add_cli("--session", "///").returncode, 0)  # empty after cleaning: no session, not a refusal
        self.assertEqual(self.objs()[0]["session_ids"], [])

    def test_a_huge_session_argument_answers_at_once_with_a_short_refusal(self):
        start = time.perf_counter()
        done = self.add_cli("--session", "q" * 100_000)
        self.assertLess(time.perf_counter() - start, 0.5 + 0.3)  # interpreter start included
        self.assertEqual((done.returncode, done.stdout), (2, ""))
        self.assertRegex(done.stderr, r"^sb candidate: session id refused \(over 128 characters or shaped like a credential\)\n$")
        self.assertFalse(self.state.exists() and any(self.state.rglob("*")))

    def test_a_secret_in_the_title_still_exits_two(self):
        done = self.run_sb("candidate", "add", "--kind", "trap", "--title", FAKE_TOKEN, "--session", "s1")
        self.assertEqual(done.returncode, 2)
        self.assertNotIn("ghp_", done.stdout + done.stderr)

    def test_a_decided_candidate_says_reviewed_and_changes_nothing(self):
        cid = self.add_cli("--session", "s1").stdout.split(": ")[1].strip()
        (self.state / candidates.REVIEW_LOG).write_text(json.dumps({"id": cid, "outcome": "rejected"}) + "\n")
        first = self.stamp()
        done = self.add_cli("--session", "s2")
        self.assertEqual(done.stdout, f"already reviewed: {cid}\n")
        self.assertEqual(self.stamp(), first)

    def test_list_json_keeps_the_old_keys_and_adds_the_recurrence(self):
        self.add_cli("--session", "s1")
        self.add_cli("--session", "s2")
        (item,) = json.loads(self.run_sb("candidate", "list", "--json").stdout)
        self.assertEqual((item["count"], item["sessions"], item["session_ids"], item["days_left"]), (2, 2, ["s1", "s2"], 30))
        for key in ("id", "ts", "kind", "title", "summary", "project", "source"):
            self.assertIn(key, item)

    def test_an_unwritable_queue_exits_two_with_one_clean_line(self):
        self.add_cli("--session", "s1")
        queue = candidates.queue_path(self.state)
        self.lock(queue, 0o400)
        done = self.add_cli("--session", "s2")  # recurrence swaps the file: the directory is writable
        self.assertEqual(done.returncode, 0)
        self.assertEqual(stat.S_IMODE(queue.stat().st_mode), 0o600)
        queue.chmod(0o400)
        new = self.run_sb("candidate", "add", "--kind", "trap", "--title", "Outro titulo qualquer", "--project", "p",
                          "--summary", "texto secreto de verdade", "--session", "s-confidencial")
        self.assertEqual(new.returncode, 2)
        self.assertRegex(new.stderr, r"^sb candidate: cannot write the queue \([^)]+\)\n$")
        for text in ("Outro titulo", "texto secreto", "s-confidencial", "Traceback"):
            self.assertNotIn(text, new.stderr + new.stdout)
        queue.chmod(0o600)
        queue.unlink()
        queue.mkdir()
        done = self.add_cli("--session", "s1")
        self.assertEqual(done.returncode, 2)
        self.assertNotIn("Traceback", done.stderr)
        self.assertRegex(done.stderr, r"^sb candidate: cannot write the queue")

    def test_a_read_only_state_directory_exits_two(self):
        self.add_cli("--session", "s1")
        self.lock(self.state, 0o500)
        done = self.add_cli("--session", "s2")
        self.assertEqual(done.returncode, 2)
        self.assertRegex(done.stderr, r"^sb candidate: cannot write the queue \([^)]+\)\n$")

    def test_list_text_is_unchanged_for_a_queue_of_old_lines(self):
        self.write_raw([self.entry("Antigo", 3)])
        text = self.run_sb("candidate", "list").stdout
        self.assertRegex(text, r"^[0-9a-f]{8}  trap      3d \(left 27d\)  p: Antigo\nqueue: 1 pending\n$")


class FitRecurrenceTest(unittest.TestCase):
    def test_candidates_gains_no_process_or_copy_call_and_one_atomic_writer(self):
        tree = ast.parse(Path(candidates.__file__).read_text(encoding="utf-8"))
        imported = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
        imported |= {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
        self.assertFalse(imported & {"subprocess", "shutil"})
        called = {c.func.attr if isinstance(c.func, ast.Attribute) else getattr(c.func, "id", "")
                  for c in ast.walk(tree) if isinstance(c, ast.Call)}
        self.assertFalse(called & {"system", "popen", "run", "Popen", "check_output", "call"})
        replacers = {f.name for f in ast.walk(tree) if isinstance(f, ast.FunctionDef)
                     for c in ast.walk(f) if isinstance(c, ast.Call) and getattr(c.func, "attr", "") == "replace"
                     and getattr(c.func.value, "id", "") == "os"}
        self.assertEqual(replacers, {"write_draft", "replace_file"})

    def test_observe_shares_the_session_pattern_with_candidates(self):
        self.assertIs(observe.SAFE_SESSION, candidates.SAFE_SESSION)


if __name__ == "__main__":
    unittest.main()
