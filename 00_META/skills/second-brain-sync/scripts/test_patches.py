"""Testes dos patches propostos (patches.py, patch_apply.py, sb patch).

python3 -m unittest discover -s 00_META/skills/second-brain-sync/scripts -v
Credenciais abaixo são FALSAS e montadas em tempo de execução.
"""

import ast
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import candidates
import observe
import patches
import sb

HERE = Path(__file__).resolve().parent
SB = Path(sb.__file__)
CLI_TIMEOUT = 30
SENTINEL = "SENTINELA-NAO-GRAVAR"
BIG = 45_000


def fake_token() -> str:
    return "".join(["ghp_", "A1b2C3d4E5f6G7h8I9j0", "K1l2M3n4O5p6Q7r8S9t0"])


def snapshot(root: Path) -> dict:
    """Name, kind, sha256, mode and mtime of everything under `root`, `.git` included."""
    seen = {}
    for path in sorted(root.rglob("*")):
        info = path.lstat()
        digest = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() and not path.is_symlink() else ""
        seen[str(path.relative_to(root))] = (stat.S_IFMT(info.st_mode), digest, stat.S_IMODE(info.st_mode), info.st_mtime_ns)
    return seen


def canon(obj) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


class Fixture(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        base = Path(os.path.realpath(self._tmp.name))
        self.base, self.state, self.root = base, base / "state", base / "proj"
        self.root.mkdir()

    # --- the project and its log
    def write(self, rel, data="x\n", root=None):
        path = (root or self.root) / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data if isinstance(data, bytes) else data.encode("utf-8"))
        return path

    def seed(self, session, reads, state=None):
        """`reads`: (path, size) pairs; one log row each."""
        log = observe.log_path(state or self.state, session)
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text("".join(json.dumps({"ts": 1, "tool": "Read", "path": str(p), "size": s}) + "\n" for p, s in reads))

    def thrice(self, rel="src/a.py", size=10, root=None):
        return [((root or self.root) / rel, size)] * 3

    def run_session(self, session, reads, root="default", project="proj"):
        self.seed(session, reads)
        return observe.summarize(self.state, session, project, None, root=self.root if root == "default" else root)

    def metas(self, rule=None):
        return [m for m in patches.list_patches(self.state) if rule in (None, m.rule)]

    def text(self, rule):
        (meta,) = self.metas(rule)
        return patches.read(self.state, meta.id).decode("utf-8")

    def files(self):
        return sorted(p.name for p in patches.patches_dir(self.state).glob("*")) if patches.patches_dir(self.state).exists() else []

    def state_hashes(self):
        return {str(p.relative_to(self.state)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(self.state.rglob("*")) if p.is_file()}

    def two_big(self, rel="src/big.py", root=None, sessions=("s1", "s2")):
        for sid in sessions:
            self.run_session(sid, [((root or self.root) / rel, BIG)], root=root or "default")

    # --- the CLI
    def run_sb(self, *args, cwd=None, env=None, stdin=None):
        base = {k: v for k, v in os.environ.items() if k not in ("CLAUDE_CODE_SESSION_ID",)}
        base.update(SECOND_BRAIN_STATE_DIR=str(self.state), PYTHONDONTWRITEBYTECODE="1")
        base.update(env or {})
        return subprocess.run([sys.executable, str(SB), *args], capture_output=True, text=True, env=base, input=stdin,
                              cwd=cwd or self.root, timeout=CLI_TIMEOUT)

    def git_checks(self, patch_text: str, old: dict | None = None, with_git=True) -> tuple[int, int]:
        """(`git apply --check`, `patch -p1 --dry-run`) return codes over a scratch copy holding the old files."""
        with tempfile.TemporaryDirectory() as scratch:
            work = Path(scratch) / "w"
            work.mkdir()
            for name, data in (old or {}).items():
                (work / name).parent.mkdir(parents=True, exist_ok=True)
                (work / name).write_bytes(data if isinstance(data, bytes) else data.encode("utf-8"))
            patch_file = Path(scratch) / "p.patch"
            patch_file.write_text(patch_text, encoding="utf-8")
            if with_git:
                subprocess.run(["git", "init", "-q", str(work)], check=True, timeout=CLI_TIMEOUT)
            git = subprocess.run(["git", "apply", "--check", str(patch_file)], cwd=work, capture_output=True, timeout=CLI_TIMEOUT)
            plain = subprocess.run(["patch", "-p1", "--dry-run", "-i", str(patch_file)], cwd=work, capture_output=True, timeout=CLI_TIMEOUT)
            return git.returncode, plain.returncode

    def applied(self, patch_text: str, old: dict | None = None) -> Path:
        scratch = Path(tempfile.mkdtemp(dir=self.base))
        for name, data in (old or {}).items():
            (scratch / name).parent.mkdir(parents=True, exist_ok=True)
            (scratch / name).write_bytes(data if isinstance(data, bytes) else data.encode("utf-8"))
        patch_file = scratch.parent / (scratch.name + ".patch")
        patch_file.write_text(patch_text, encoding="utf-8")
        subprocess.run(["patch", "-p1", "-i", str(patch_file)], cwd=scratch, check=True, capture_output=True, timeout=CLI_TIMEOUT)
        return scratch


class RulesTest(Fixture):
    def test_two_reads_make_no_patch_and_three_make_one(self):
        self.run_session("s1", self.thrice()[:2])
        self.assertEqual(self.files(), [])
        self.run_session("s1", self.thrice())
        self.assertEqual([m.rule for m in self.metas()], ["reread"])

    def test_big_read_boundary(self):
        self.run_session("s1", [(self.root / "a.py", 39_999)])
        self.assertEqual(self.metas(), [])
        self.run_session("s1", [(self.root / "a.py", 40_000)])
        self.assertEqual([m.rule for m in self.metas()], ["big"])

    def test_reads_of_different_paths_are_not_summed(self):
        reads = [(self.root / "a.py", 10), (self.root / "b.py", 10), (self.root / "c.py", 10)] * 1
        self.run_session("s1", reads + reads[:1])
        self.assertEqual(self.metas(), [])

    def test_expensive_turns_alone_make_no_patch_and_no_candidate(self):
        transcript = self.base / "t.jsonl"
        rows = [{"type": "assistant", "message": {"usage": {"cache_creation_input_tokens": 90_000}}}] * 5
        transcript.write_text("".join(json.dumps(r) + "\n" for r in rows))
        result = observe.summarize(self.state, "s1", "proj", transcript, root=self.root)
        self.assertEqual((result["expensive_turns"], result["patches"], self.metas()), (5, 0, []))
        self.assertEqual(candidates.load(self.state)[0], [])

    def test_only_the_first_three_findings_make_patches(self):
        reads = [(self.root / f"f{i}.py", 10) for i in range(5) for _ in range(3)]
        self.run_session("s1", reads)
        self.assertEqual(len(self.metas()), observe.MAX_CANDIDATES)

    def test_the_patch_names_rule_file_count_and_sessions(self):
        self.run_session("s1", self.thrice() + [(self.root / "src/a.py", 10)])
        self.run_session("s2", self.thrice() + [(self.root / "src/a.py", 10)])
        text = self.text("reread")
        for needle in ("# rule: reread", "# file: src/a.py", "# count: 4", "# sessions: 2", "REREAD_MIN",
                       "+- Leia `src/a.py` com offset/limit: 4 releituras em 2 sessões"):
            self.assertIn(needle, text)
        self.assertNotIn("TODO", text)

    def test_ineligible_paths_make_no_patch(self):
        top = str(self.root)
        bad = [str(self.base / "outside.py"), "rel/a.py", top + "/a`b.py", top + "/a(1).py", top + "/a\nb.py",
               top + "/../x.py", top + "/a//b.py", top + "/" + "x" * 201, top + "/a\x07b.py", top + "/./c.py", top + "/d/", top + "//x.py"]
        for path in bad:
            with self.subTest(repr(path)):
                self.run_session("s1", [(path, 10)] * 3)
                self.assertEqual(self.metas(), [])
        self.assertFalse(patches.patches_dir(self.state).exists())

    def test_root_home_or_slash_makes_no_patch(self):
        with mock.patch.dict(os.environ, {"HOME": str(self.root)}):
            self.run_session("s1", self.thrice())
        self.assertEqual(self.metas(), [])
        self.run_session("s1", [(Path("/etc/passwd"), 10)] * 3, root=Path("/"))
        self.assertEqual(self.metas(), [])

    def test_without_a_root_the_old_behaviour_holds(self):
        result = self.run_session("s1", self.thrice(), root=None)
        self.assertEqual((result["patches"], self.files(), result["queued"]), (0, [], 1))
        titles = [c.title for c in candidates.load(self.state)[0]]
        self.assertEqual(titles, ["Releitura repetida de a.py"])
        self.assertNotIn("patches", observe.format_summary(result))

    def test_a_root_given_through_a_link_matches_the_real_root(self):
        link = self.base / "link"
        link.symlink_to(self.root)
        self.seed("s1", self.thrice())
        observe.summarize(self.state, "s1", "proj", None, root=link)
        self.assertEqual(len(self.metas()), 1)
        self.assertEqual(self.metas()[0].root, str(self.root))

    def test_secret_shaped_root_file_or_project_make_no_patch(self):
        marked = "sb-allow-secret " + fake_token()
        hidden = self.base / marked
        hidden.mkdir()
        for root, rel, project in ((hidden, "a.py", "proj"), (self.root, marked + ".py", "proj"), (self.root, "a.py", fake_token())):
            with self.subTest(rel=rel[:6], project=project[:6]):
                self.seed("sx", [(root / rel, 10)] * 3)
                observe.summarize(self.state, "sx", project, None, root=root)
                self.assertEqual(self.metas(), [])
        if self.state.exists():
            from lib import secret_scan
            for path in self.state.rglob("*"):
                if path.is_file():
                    self.assertEqual(secret_scan.scan_text(path.read_text(errors="replace")), [], path.name)

    def test_a_session_without_a_usable_id_makes_no_patch(self):
        self.seed("s1", self.thrice())
        for session in ("", fake_token(), "!!!"):
            observe.summarize(self.state, session, "proj", None, root=self.root)
        self.assertEqual(self.metas(), [])


class UnitTest(unittest.TestCase):
    def test_eligible_rel(self):
        for good in ("a/b.py", "ação.py", "dir with space/x.md", "x" * 200):
            self.assertTrue(patches.eligible_rel(good), good)
        for bad in ("/x", "../x", "a/../b", "a//b", "./a", "a/", "", " a", "a ", "a`b", "a(b", "a)b", "x" * 201, "a\nb",
                    ".", "..", "a/.."):
            self.assertFalse(patches.eligible_rel(bad), repr(bad))

    def meta(self, **kw):
        base = dict(id="", rule="reread", project="proj", root="/r", target="CLAUDE.md", file="a.py", count=3,
                    session_ids=("s1",), created="2026-10-29")
        base.update(kw)
        meta = patches.Meta(**base)
        return meta._replace(id=patches.patch_id(meta.rule, meta.root, meta.file))

    def test_the_patch_text_uses_the_singular_for_one(self):
        reread = patches.line_text(self.meta(count=3))
        self.assertIn("3 releituras em 1 sessão (", reread)
        big = self.meta(rule="big", count=1, size=45000, target="CLAUDE.md")
        self.assertIn("1 leitura de ~45 mil caracteres em 1 sessão;", patches.line_text(big))
        self.assertIn("1 leitura)", patches._why(big))
        self.assertIn("1 sessão repetiu", patches._why(big))
        self.assertIn("2 sessões repetiram", patches._why(big._replace(session_ids=("a", "b"))))

    def test_validate_refuses_secret_shapes_even_with_the_allow_marker(self):
        token = fake_token()
        for variant in (token, f"sb-allow-secret {token}", f"{token} sb-allow-secret"):
            for field in ("root", "file", "project"):
                value = "/" + variant if field == "root" else variant
                with self.subTest(field=field, variant=variant[:14]):
                    with self.assertRaises(patches.PatchError):
                        patches.validate(self.meta(**{field: value}))
        patches.validate(self.meta())

    def test_validate_refuses_a_target_that_does_not_fit_the_rule(self):
        for kw in ({"rule": "big", "target": "README.md"}, {"rule": "reread", "target": ".claude/settings.local.json"},
                   {"rule": "deny", "target": "CLAUDE.md"}, {"rule": "deny", "target": "AGENTS.md"},
                   {"rule": "deny", "target": patches.SETTINGS_REL, "file": "src/*.py"},
                   {"rule": "deny", "target": patches.SETTINGS_REL, "file": "CLAUDE.md"},
                   {"rule": "nope", "target": "CLAUDE.md"}):
            with self.subTest(kw), self.assertRaises(patches.PatchError):
                patches.validate(self.meta(**kw))
        patches.validate(self.meta(rule="deny", target=patches.SETTINGS_REL, size=45000))
        patches.validate(self.meta(rule="big", target="AGENTS.md", size=45000))

    def test_render_scans_the_whole_text_on_its_own(self):
        for root in ("/" + fake_token(), "/sb-allow-secret " + fake_token()):  # the marker must not excuse it
            with self.subTest(root[:14]), mock.patch.object(patches, "validate"):
                with self.assertRaises(patches.PatchError):
                    patches.render(self.meta(root=root), b"a\nb\n")

    def test_deny_new_refuses_what_is_not_the_canonical_shape(self):
        good = canon({"permissions": {"allow": ["a"]}})
        self.assertIn(b"Read(./x)", patches.deny_new(good.encode(), "x"))
        for label, old in (("indent 4", json.dumps({"permissions": {"allow": ["a"]}}, indent=4).encode() + b"\n"),
                           ("no final newline", good.rstrip("\n").encode()), ("trailing space", good.encode() + b" "),
                           ("empty deny", canon({"permissions": {"deny": []}}).encode()),
                           ("deny not a list", canon({"permissions": {"deny": "x"}}).encode()),
                           ("non-ascii escaped", b'{\n  "permissions": {\n    "allow": [\n      "\\u00e9"\n    ]\n  }\n}\n')):
            with self.subTest(label), self.assertRaises(patches.PatchError):
                patches.deny_new(old, "x")

    def test_insertion_accepts_only_pure_insertions(self):
        old = b"a\nb\nc\n"
        self.assertEqual(patches.insertion(old, b"a\nb\nc\nd\n"), (3, [b"d\n"]))
        self.assertEqual(patches.insertion(old, b"a\nX\nY\nb\nc\n"), (1, [b"X\n", b"Y\n"])) if patches.git_safe(1, 3) else None
        self.assertEqual(patches.insertion(old, b"a\nb\nX\nc\n"), (2, [b"X\n"]))
        for new in (b"a\nX\nc\nd\n", b"a\nb\n", b"a\nb\nc\n", b"X\nb\nc\nd\n", b"a\nb\nc\nd"):
            with self.assertRaises(patches.PatchError, msg=new):
                patches.insertion(old, new)
        with self.assertRaises(patches.PatchError):  # a replacement after line 2 that only looks like an insertion
            patches.insertion(b"a\nb\nc\nd\n", b"a\nb\nX\nd\ne\n")
        with self.assertRaises(patches.PatchError):  # a one-line target: git apply would refuse the hunk
            patches.insertion(b"a\n", b"a\nb\n")

    def test_a_header_with_an_unsafe_session_id_is_not_parsed(self):
        meta = patches.Meta("0" * 8, "reread", "p", "/r", "CLAUDE.md", "a.py", 3, ("s1",), "2026-10-29")
        text = "\n".join(patches._header(meta)) + "\n"
        self.assertIsNotNone(patches.parse(text.encode()))
        for ids in (fake_token(), "s1,s/2", "s1,,s2", "s1, s2"):
            bad = text.replace("# session_ids: s1", f"# session_ids: {ids}").replace("# sessions: 1", f"# sessions: {len(ids.split(','))}")
            self.assertIsNone(patches.parse(bad.encode()), ids)

    def test_a_patch_file_over_the_size_limit_is_not_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp)
            patches.patches_dir(state).mkdir()
            patches.patch_file(state, "abcdef12").write_bytes(b"#" * (patches.MAX_PATCH_BYTES + 1))
            self.assertIsNone(patches.read(state, "abcdef12"))
            patches.patch_file(state, "abcdef12").write_bytes(b"#" * patches.MAX_PATCH_BYTES)
            self.assertIsNotNone(patches.read(state, "abcdef12"))

    def test_write_target_makes_its_temp_file_beside_the_target_and_removes_it_on_failure(self):
        import patch_apply
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "sub" / "CLAUDE.md"
            target.parent.mkdir()
            seen = []
            real = tempfile.mkstemp

            def spy(*args, **kw):
                seen.append(kw.get("dir"))
                return real(*args, **kw)

            with mock.patch.object(patch_apply.tempfile, "mkstemp", side_effect=spy):
                patch_apply.write_target(target, b"one\n")
            self.assertEqual(seen, [target.parent])
            with mock.patch.object(patch_apply.os, "replace", side_effect=OSError("boom")):
                with self.assertRaises(OSError):
                    patch_apply.write_target(target, b"two\n")
            self.assertEqual(sorted(p.name for p in target.parent.iterdir()), ["CLAUDE.md"])
            self.assertEqual(target.read_bytes(), b"one\n")
            fresh = Path(tmp) / "new" / ".claude" / "settings.local.json"
            fresh.parent.parent.mkdir()
            with mock.patch.object(patch_apply.os, "replace", side_effect=OSError("boom")):
                with self.assertRaises(OSError):
                    patch_apply.write_target(fresh, b"{}\n")
            self.assertFalse(fresh.parent.exists())

    def test_propose_survives_a_directory_where_a_patch_should_be(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(os.path.realpath(tmp))
            root, state = base / "p", base / "state"
            root.mkdir()
            (root / "CLAUDE.md").write_text("a\nb\n")
            finding = observe.analyze([{"tool": "Read", "path": str(root / "a.py"), "size": 10}] * 3)[0]
            patches.patches_dir(state).mkdir(parents=True)
            patches.patch_file(state, patches.patch_id("reread", str(root), "a.py")).mkdir()
            self.assertEqual(patches.propose(state, [finding], root=root, project="p", session="s1"), 0)


class TargetTest(Fixture):
    def line_of(self):
        return self.metas()[0]

    def test_target_choice(self):
        cases = [
            ({"CLAUDE.md": "a\nb\n"}, "CLAUDE.md"),
            ({"AGENTS.md": "a\nb\n"}, "AGENTS.md"),
            ({"CLAUDE.md": "a\nb\n", "AGENTS.md": "a\nb\n"}, "CLAUDE.md"),
            ({}, "CLAUDE.md"),
        ]
        for files, want in cases:
            with self.subTest(files=sorted(files)):
                shutil.rmtree(self.state, ignore_errors=True)
                for name in ("CLAUDE.md", "AGENTS.md"):
                    (self.root / name).unlink(missing_ok=True)
                for name, data in files.items():
                    self.write(name, data)
                self.run_session("s1", self.thrice())
                self.assertEqual(self.line_of().target, want)
        text = self.text("reread")
        self.assertIn("--- /dev/null", text)
        self.assertIn("@@ -0,0 +1 @@", text)

    def test_claude_md_as_a_link_to_agents_md_picks_agents_md(self):
        self.write("AGENTS.md", "a\nb\n")
        (self.root / "CLAUDE.md").symlink_to("AGENTS.md")
        self.run_session("s1", self.thrice())
        self.assertEqual(self.line_of().target, "AGENTS.md")

    def test_broken_link_or_directory_makes_no_patch_and_creates_nothing(self):
        (self.root / "CLAUDE.md").symlink_to("nowhere.md")
        self.run_session("s1", self.thrice())
        self.assertEqual(self.metas(), [])
        (self.root / "CLAUDE.md").unlink()
        (self.root / "CLAUDE.md").mkdir()
        self.run_session("s1", self.thrice())
        self.assertEqual(self.metas(), [])

    def test_unusable_target_makes_no_patch_and_does_not_fall_back(self):
        bad = {"no newline": b"a\nb", "no newline, 3 lines": b"a\nb\nc", "not utf-8": b"a\n\xff\xfe\n",
               "over 256 KB": b"h\n" + b"x" * (patches.MAX_TARGET_BYTES - 2) + b"\n"}
        for label, data in bad.items():
            with self.subTest(label):
                shutil.rmtree(self.state, ignore_errors=True)
                self.write("CLAUDE.md", data)
                self.write("AGENTS.md", "fine\nfile\n")
                self.run_session("s1", self.thrice())
                self.assertEqual(self.metas(), [])

    def test_one_line_target_makes_no_patch_and_two_lines_do(self):
        for body, count in (("one\n", 0), ("one\ntwo\n", 1), ("\n", 0)):
            with self.subTest(body=body):
                shutil.rmtree(self.state, ignore_errors=True)
                self.write("CLAUDE.md", body)
                self.run_session("s1", self.thrice())
                self.assertEqual(len(self.metas()), count)

    def test_empty_target(self):
        self.write("CLAUDE.md", "")
        self.run_session("s1", self.thrice())
        self.assertIn("@@ -0,0 +1 @@", self.text("reread"))

    def test_crlf_target_keeps_old_lines_and_counts_a_crlf_line_as_present(self):
        self.write("CLAUDE.md", "a\r\nb\r\nc\r\n")
        self.run_session("s1", self.thrice())
        text = self.text("reread")
        self.assertNotIn("\r", text)
        self.assertEqual(self.git_checks(text, {"CLAUDE.md": "a\r\nb\r\nc\r\n"}), (0, 0))
        done = self.applied(text, {"CLAUDE.md": "a\r\nb\r\nc\r\n"})
        self.assertTrue((done / "CLAUDE.md").read_bytes().startswith(b"a\r\nb\r\nc\r\n- Leia"))
        present = "a\r\nb\r\n- Leia `src/a.py` com offset/limit: 2 releituras\r\n"
        self.write("CLAUDE.md", present)
        self.run_session("s1", self.thrice())
        self.assertEqual(self.metas(), [])

    def test_accented_names_work_with_and_without_git(self):
        root = self.base / "projeto ação"
        root.mkdir()
        self.write("CLAUDE.md", "a\nb\n", root=root)
        reads = [(root / "src" / "leitura é.py", 10)] * 3
        self.seed("s1", reads)
        observe.summarize(self.state, "s1", "projeto", None, root=root)
        text = self.text("reread")
        self.assertIn("leitura é.py", text)
        for with_git in (True, False):
            self.assertEqual(self.git_checks(text, {"CLAUDE.md": "a\nb\n"}, with_git=with_git), (0, 0))

    def test_sentinel_in_the_target_never_reaches_the_state(self):
        body = f"linha um\n{SENTINEL} meio\nultima {SENTINEL}\n"
        self.write("CLAUDE.md", body)
        self.write("AGENTS.md", f"{SENTINEL}\nx\n")
        self.write(".claude/settings.local.json", canon({"permissions": {"allow": [f"Bash({SENTINEL})"], "x": SENTINEL}}))
        self.two_big()
        self.run_session("s3", self.thrice())
        self.assertGreaterEqual(len(self.metas()), 2)
        for path in self.state.rglob("*"):
            if path.is_file():
                self.assertNotIn(SENTINEL.encode(), path.read_bytes(), path.name)


class DenyTest(Fixture):
    def settings(self, obj):
        self.write(".claude/settings.local.json", canon(obj) if not isinstance(obj, (str, bytes)) else obj)

    def test_two_distinct_sessions_make_a_deny_patch_next_to_the_line(self):
        self.write("CLAUDE.md", "a\nb\n")
        self.run_session("s1", [(self.root / "src/big.py", BIG)])
        self.assertEqual([m.rule for m in self.metas()], ["big"])
        self.run_session("s1", [(self.root / "src/big.py", BIG)])
        self.assertEqual([m.rule for m in self.metas()], ["big"])
        self.run_session("s2", [(self.root / "src/big.py", BIG)])
        self.assertEqual(sorted(m.rule for m in self.metas()), ["big", "deny"])

    def test_an_anonymous_session_does_not_count(self):
        self.run_session("s1", [(self.root / "big.py", BIG)])
        finding = observe.analyze([{"tool": "Read", "path": str(self.root / "big.py"), "size": BIG}])[0]
        before = self.state_hashes()
        for session in (None, "", fake_token()):
            self.assertEqual(patches.propose(self.state, [finding], root=self.root, project="proj", session=session), 0)
        self.assertEqual(self.state_hashes(), before)
        self.assertEqual([m.rule for m in self.metas()], ["big"])

    def test_the_same_file_name_in_two_roots_does_not_pool_sessions(self):
        a, b = self.base / "a" / "app", self.base / "b" / "app"
        for root in (a, b):
            root.mkdir(parents=True)
            self.write("CLAUDE.md", "a\nb\n", root=root)
        self.run_session("s1", [(a / "src/x.py", BIG)], root=a)
        self.run_session("s2", [(b / "src/x.py", BIG)], root=b)
        found = self.metas()
        self.assertEqual(sorted(m.rule for m in found), ["big", "big"])
        self.assertEqual(len({m.id for m in found}), 2)

    def test_reread_never_makes_a_deny(self):
        for sid in ("s1", "s2", "s3"):
            self.run_session(sid, self.thrice())
        self.assertEqual([m.rule for m in self.metas()], ["reread"])
        self.assertEqual(self.metas("reread")[0].sessions, 3)

    def test_gate_candidate_must_be_alive_and_undecided(self):
        self.run_session("s1", [(self.root / "big.py", BIG)])
        cid = candidates.get(self.state, candidates.candidate_id("pattern", "Read grande de big.py", "proj")).id
        queue = candidates.queue_path(self.state)
        original = queue.read_bytes()
        for label in ("decided", "expired", "absent"):
            with self.subTest(label):
                shutil.rmtree(patches.patches_dir(self.state))
                queue.write_bytes(original)
                (self.state / "review.jsonl").unlink(missing_ok=True)
                if label == "decided":
                    (self.state / "review.jsonl").write_text(json.dumps({"id": cid, "outcome": "rejected"}) + "\n")
                elif label == "expired":
                    obj = json.loads(original.decode().splitlines()[0])
                    obj["ts"] = "2020-01-01T00:00:00+00:00"
                    queue.write_text(json.dumps(obj) + "\n")
                else:
                    queue.unlink()
                self.run_session("s2", [(self.root / "big.py", BIG)])
                self.assertEqual([m.rule for m in self.metas()], ["big"], label)

    def test_gate_candidate_with_one_session_is_not_enough(self):
        self.write("CLAUDE.md", "a\nb\n")
        finding = observe.analyze([{"tool": "Read", "path": str(self.root / "big.py"), "size": BIG}])[0]
        candidates.add(self.state, kind=finding.kind, title=finding.title, summary=finding.summary, project="proj",
                       source="observer", session="a")
        for sid in ("a", "b"):
            patches.propose(self.state, [finding], root=self.root, project="proj", session=sid)
        (line,) = self.metas("big")
        self.assertEqual(line.sessions, 2)
        self.assertEqual(candidates.get(self.state, candidates.candidate_id(finding.kind, finding.title, "proj")).sessions, 1)
        self.assertEqual([m.rule for m in self.metas()], ["big"])

    def test_a_deny_entry_that_appears_later_drops_the_deny_patch(self):
        self.write("CLAUDE.md", "a\nb\n")
        self.two_big()
        self.assertEqual(len(self.metas("deny")), 1)
        self.settings({"permissions": {"deny": ["Read(./src/big.py)"]}})
        self.run_session("s3", [(self.root / "src/big.py", BIG)])
        self.assertEqual([m.rule for m in self.metas()], ["big"])

    def test_no_line_patch_means_no_deny(self):
        self.write("CLAUDE.md", "a\nb")  # no newline: the line patch cannot be born
        self.two_big()
        self.assertEqual(self.metas(), [])

    def test_the_cap_of_fifty_stops_new_patches(self):
        directory = patches.patches_dir(self.state)
        directory.mkdir(parents=True)
        for i in range(patches.MAX_PATCHES):
            (directory / f"{i:08x}.patch").write_text("junk")
        self.two_big()
        self.assertEqual(len(patches.live_files(self.state)), patches.MAX_PATCHES)
        self.assertEqual(self.metas(), [])

    def test_shapes_of_the_deny_patch(self):
        shapes = {
            "absent": None,
            "deny first item": {"permissions": {"allow": ["Bash(ls)"], "deny": ["Read(./other)"]}},
            "permissions without deny": {"permissions": {"allow": ["Bash(ls)"], "ask": []}, "model": "x"},
            "deny first of permissions": {"model": "x", "permissions": {"deny": ["Read(./other)", "Bash(rm)"], "allow": []}},
        }
        for label, obj in shapes.items():
            with self.subTest(label):
                shutil.rmtree(self.state, ignore_errors=True)
                (self.root / ".claude").exists() and shutil.rmtree(self.root / ".claude")
                self.write("CLAUDE.md", "a\nb\n")
                old = {}
                if obj is not None:
                    self.settings(obj)
                    old = {".claude/settings.local.json": canon(obj)}
                self.two_big()
                text = self.text("deny")
                body = text.split("\n--- ", 1)[1]
                self.assertFalse([l for l in body.splitlines()[1:] if l.startswith("-") and not l.startswith("---")])
                self.assertEqual(self.git_checks(text, old), (0, 0))
                done = self.applied(text, old) / ".claude/settings.local.json"
                new = json.loads(done.read_text())
                self.assertIn("Read(./src/big.py)", new["permissions"]["deny"])
                if obj is not None:
                    for key, value in obj.items():
                        if key != "permissions":
                            self.assertEqual(new[key], value)
                    self.assertEqual([k for k in new if k in obj], list(obj))
                    self.assertEqual({k: v for k, v in new["permissions"].items() if k != "deny"},
                                     {k: v for k, v in obj["permissions"].items() if k != "deny"})
                    self.assertEqual(new["permissions"]["deny"][1:], obj["permissions"].get("deny", []))

    def test_sentinel_in_settings_positions_never_reaches_the_state(self):
        obj = {"model": SENTINEL, "permissions": {"allow": [f"Bash({SENTINEL})"], "deny": [SENTINEL], "zz": SENTINEL}, "zzz": SENTINEL}
        self.write("CLAUDE.md", f"a\n{SENTINEL}\n")
        self.settings(obj)
        self.two_big()
        self.assertEqual(len(self.metas("deny")), 1)
        for path in self.state.rglob("*"):
            if path.is_file():
                self.assertNotIn(SENTINEL.encode(), path.read_bytes())

    def test_settings_that_cannot_be_patched_make_no_deny(self):
        cases = {
            "invalid json": "{nope", "root list": "[]\n", "permissions not object": canon({"permissions": 3}),
            "deny not list": canon({"permissions": {"deny": "x"}}), "empty deny": canon({"permissions": {"deny": []}}),
            "empty permissions": canon({"permissions": {}}), "empty object": "{}\n",
            "no permissions key": canon({"model": "x"}), "no final newline": canon({"permissions": {"allow": ["a"]}}).rstrip("\n"),
            "canonical plus a space": canon({"permissions": {"allow": ["a"], "ask": ["b"]}}) + " ",
            "indent 4": json.dumps({"permissions": {"allow": ["a"]}}, indent=4) + "\n", "not utf-8": b"\xff\n",
            "entry present": canon({"permissions": {"deny": ["Read(./src/big.py)"]}}),
            "deep": "[" * 100_000 + "]" * 100_000 + "\n", "duplicate keys": '{"permissions": {"allow": [1], "allow": [2]}}\n',
        }
        for label, content in cases.items():
            with self.subTest(label):
                shutil.rmtree(self.state, ignore_errors=True)
                self.write("CLAUDE.md", "a\nb\n")
                self.settings(content)
                self.two_big()
                self.assertEqual([m.rule for m in self.metas()], ["big"], label)

    def test_settings_dir_that_is_a_link_makes_no_deny(self):
        self.write("CLAUDE.md", "a\nb\n")
        elsewhere = self.base / "elsewhere"
        elsewhere.mkdir()
        (self.root / ".claude").symlink_to(elsewhere)
        self.two_big()
        self.assertEqual([m.rule for m in self.metas()], ["big"])
        self.assertEqual(list(elsewhere.iterdir()), [])

    def test_files_that_cannot_be_denied(self):
        self.write("CLAUDE.md", "a\nb\n")
        for rel in ("CLAUDE.md", "AGENTS.md", ".claude/settings.local.json", ".claude/other.json", "src/*.py", "a[1].py", "a{b}.py", "a!b.py"):
            with self.subTest(rel):
                shutil.rmtree(self.state, ignore_errors=True)
                shutil.rmtree(self.root / ".claude", ignore_errors=True)
                self.write(rel, "z\n") if rel != "CLAUDE.md" else None
                self.two_big(rel=rel)
                self.assertNotIn("deny", [m.rule for m in self.metas()])
                self.assertIn("big", [m.rule for m in self.metas()] + ["big"] * (rel == "CLAUDE.md"))
        shutil.rmtree(self.state)
        shutil.rmtree(self.root / ".claude", ignore_errors=True)
        self.two_big(rel="src/fine.py")  # the same fixture does make a deny for an ordinary file
        self.assertIn("deny", [m.rule for m in self.metas()])

    def test_deny_survives_the_line_being_applied(self):
        """E3: the gate held when the patch was born; the apply does not look at the line patch."""
        self.write("CLAUDE.md", "a\nb\n")
        self.two_big()
        (deny,) = self.metas("deny")
        (line,) = self.metas("big")
        before = patches.read(self.state, deny.id)
        done = self.run_sb("patch", "apply", line.id, "--apply")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.run_session("s3", [(self.root / "src/big.py", BIG)])
        self.assertEqual(patches.read(self.state, deny.id), before)
        self.assertEqual(self.run_sb("patch", "apply", deny.id, "--apply").returncode, 0)
        self.assertEqual(json.loads((self.root / ".claude/settings.local.json").read_text())["permissions"]["deny"],
                         ["Read(./src/big.py)"])

    def test_why_says_the_entry_blocks_every_read(self):
        self.write("CLAUDE.md", "a\nb\n")
        self.two_big()
        self.assertIn("bloqueia todo Read, offset/limit incluído", self.text("deny"))

    def test_session_ids_pass_the_guard_cut_and_cap(self):
        self.write("CLAUDE.md", "a\nb\n")
        long_id = "x" * 100
        self.two_big(sessions=(long_id, "s2"))
        finding = observe.analyze([{"tool": "Read", "path": str(self.root / "src/big.py"), "size": BIG}])[0]
        patches.propose(self.state, [finding], root=self.root, project="proj", session=fake_token())
        (line,) = self.metas("big")
        self.assertEqual(line.session_ids, ("x" * 64, "s2"))
        self.assertEqual(self.run_sb("patch", "list").returncode, 0)
        needle = fake_token().encode()
        for path in self.state.rglob("*"):
            if path.is_file():
                self.assertNotIn(needle, path.read_bytes())
        shutil.rmtree(self.state)
        self.two_big(sessions=[f"s{i}" for i in range(105)])
        self.assertEqual(self.metas("big")[0].sessions, candidates.MAX_SESSION_IDS)

    def test_fake_credential_with_the_allow_marker_in_root_or_file_makes_no_patch(self):
        marker = f"sb-allow-secret {fake_token()}"
        root = self.base / marker
        root.mkdir()
        self.two_big(root=root)
        self.two_big(rel=f"{marker}.py")
        self.assertEqual(self.metas(), [])


class ProjectNameTest(Fixture):
    def test_a_project_name_shaped_like_a_credential_reaches_neither_queue_nor_patch(self):
        for project in (fake_token(), f"sb-allow-secret {fake_token()}"):
            with self.subTest(project[:12]):
                self.seed("s1", self.thrice())
                result = observe.summarize(self.state, "s1", project, None, root=self.root)
                self.assertEqual((result["queued"], result["patches"]), (0, 0))
        for path in self.state.rglob("*"):
            if path.is_file():
                self.assertNotIn(b"ghp_", path.read_bytes(), path.name)


class StoreTest(Fixture):
    def test_three_summaries_leave_the_state_byte_identical(self):
        self.write("CLAUDE.md", "a\nb\n")
        self.two_big()
        self.run_session("s3", self.thrice())
        first = self.state_hashes()
        for _ in range(2):
            self.run_session("s3", self.thrice())
        self.assertEqual(first, self.state_hashes())

    def test_two_sessions_one_file_per_rule(self):
        self.run_session("s1", self.thrice())
        created = self.metas("reread")[0].created
        with mock.patch.object(candidates, "utcnow", return_value=candidates.utcnow().replace(year=2026, month=11, day=2)):
            self.run_session("s2", self.thrice() + [(self.root / "src/a.py", 10)])
        (meta,) = self.metas("reread")
        self.assertEqual((meta.sessions, meta.created, meta.count), (2, created, 4))
        self.assertEqual(self.files(), [f"{meta.id}.patch"])

    def test_count_grows_and_never_shrinks(self):
        self.run_session("s1", self.thrice() + [(self.root / "src/a.py", 10)])
        self.assertEqual(self.metas("reread")[0].count, 4)
        self.run_session("s1", self.thrice())
        self.assertEqual(self.metas("reread")[0].count, 4)
        self.run_session("s1", self.thrice() * 2)
        self.assertEqual(self.metas("reread")[0].count, 6)

    def test_a_target_that_already_has_the_line_drops_the_patch(self):
        self.write("CLAUDE.md", "a\nb\n")
        self.run_session("s1", self.thrice())
        self.assertEqual(len(self.metas()), 1)
        self.write("CLAUDE.md", "a\nb\n- Leia `src/a.py` com offset/limit: já feito\n")
        self.run_session("s1", self.thrice())
        self.assertEqual(self.metas(), [])
        self.write("CLAUDE.md", "a\nb\n- Evite ler `src/a.py` inteiro: x\n")
        self.run_session("s1", self.thrice())
        self.assertEqual(self.metas(), [])

    def test_a_target_swap_rewrites_the_same_patch_file(self):
        self.write("AGENTS.md", "a\nb\n")
        self.run_session("s1", self.thrice())
        (first,) = self.metas()
        self.write("CLAUDE.md", "a\nb\n")
        self.run_session("s1", self.thrice())
        (second,) = self.metas()
        self.assertEqual((first.id, first.target, second.target), (second.id, "AGENTS.md", "CLAUDE.md"))
        self.assertEqual(len(self.files()), 1)

    def test_bytes_do_not_depend_on_the_hour(self):
        self.run_session("s1", self.thrice())
        first = self.state_hashes()
        later = candidates.utcnow().replace(hour=3, minute=1)
        with mock.patch.object(candidates, "utcnow", return_value=later):
            self.run_session("s1", self.thrice())
        self.assertEqual(first, self.state_hashes())

    def test_modes_of_the_patch_store(self):
        self.run_session("s1", self.thrice())
        self.assertEqual(stat.S_IMODE(patches.patches_dir(self.state).stat().st_mode), 0o700)
        for path in patches.patches_dir(self.state).iterdir():
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)

    def test_patches_expire_after_the_candidate_ttl(self):
        self.run_session("s1", self.thrice())
        (meta,) = self.metas()
        future = candidates.utcnow() + candidates.dt.timedelta(days=candidates.TTL_DAYS)
        with mock.patch.object(candidates, "utcnow", return_value=future):
            self.assertEqual(self.metas(), [])
            self.assertEqual(patches.expire(self.state), 1)
        self.assertEqual(self.files(), [])
        self.assertEqual(meta.days_left, candidates.TTL_DAYS)

    def test_summarize_expires_old_patches(self):
        self.run_session("s1", self.thrice())
        (meta,) = self.metas()
        path = patches.patch_file(self.state, meta.id)
        path.write_bytes(path.read_bytes().replace(f"# created: {meta.created}".encode(), b"# created: 2020-01-01"))
        self.assertEqual(self.files(), [path.name])
        self.run_session("s2", [(self.root / "other.py", 10)])
        self.assertEqual(self.files(), [])

    def test_summarize_runs_git_once(self):
        subprocess.run(["git", "init", "-q", str(self.root)], check=True, timeout=CLI_TIMEOUT)
        self.seed("s1", self.thrice())
        calls = []
        real = subprocess.run

        def spy(*args, **kw):
            calls.append(args[0])
            return real(*args, **kw)

        here = os.getcwd()
        self.addCleanup(os.chdir, here)
        os.chdir(self.root)
        with mock.patch.dict(os.environ, {"SECOND_BRAIN_STATE_DIR": str(self.state)}), \
                mock.patch.object(sb.subprocess, "run", side_effect=spy):
            self.assertEqual(sb.main(["observe", "summarize", "--session", "s1"]), 0)
        self.assertEqual([c for c in calls if c[:2] == ["git", "rev-parse"]], [["git", "rev-parse", "--show-toplevel"]])
        self.assertEqual(len(calls), 1)
        self.assertEqual(len(self.metas()), 1)

    def test_no_lock_file_is_left_in_the_state_by_the_patches_and_the_queue_lock_is_private(self):
        self.write("CLAUDE.md", "a\nb\n")
        old = os.umask(0o002)
        try:
            self.two_big()
            self.run_sb("patch", "list")
            self.run_sb("patch", "apply", self.metas("big")[0].id, "--apply")
            shell = self.run_sb("observe", "summarize", "--session", "s2")
            self.assertEqual(shell.returncode, 0)
        finally:
            os.umask(old)
        names = sorted(p.name for p in self.state.iterdir())
        self.assertNotIn("patches.lock", names)
        self.assertEqual(stat.S_IMODE((self.state / "queue.lock").stat().st_mode), 0o600)
        self.assertEqual([p for p in self.state.rglob("*.lock") if p.name != "queue.lock"], [])

    def test_the_cli_takes_the_git_root_from_a_subfolder(self):
        subprocess.run(["git", "init", "-q", str(self.root)], check=True, timeout=CLI_TIMEOUT)
        (self.root / "src").mkdir()
        self.seed("s1", self.thrice())
        self.assertEqual(self.run_sb("observe", "summarize", "--session", "s1", cwd=self.root / "src").returncode, 0)
        (meta,) = self.metas()
        self.assertEqual((meta.root, meta.project), (str(self.root), "proj"))

    def test_the_header_round_trips_and_a_damaged_one_is_refused(self):
        self.run_session("s1", self.thrice())
        data = patches.read(self.state, self.metas()[0].id)
        self.assertIsNotNone(patches.parse(data))
        for bad in (data.replace(b"# count: 3", b"# count: x"), data.replace(b"# sessions: 1", b"# sessions: 2"),
                    data.replace(b"# rule: reread", b"# rule: nope"), data + b"\xff", b"",
                    data.replace(b"# created: ", b"# created: x"), data.replace(b"# why:", b"# why2:")):
            self.assertIsNone(patches.parse(bad))


class EdgeTest(Fixture):
    def test_missing_malformed_and_unwritable_inputs_exit_zero(self):
        shell = self.run_sb("observe", "summarize", "--session", "nolog")
        self.assertEqual(shell.returncode, 0, shell.stderr)
        log = observe.log_path(self.state, "s1")
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text("not json\n{\"tool\": 1}\n" + json.dumps({"tool": "Read", "path": str(self.root / "a.py"), "size": 1}) + "\n")
        self.assertEqual(self.run_sb("observe", "summarize", "--session", "s1").returncode, 0)

    @unittest.skipIf(os.geteuid() == 0, "root ignores file modes")
    def test_a_read_only_state_still_exits_zero_and_writes_the_usage_record_when_it_can(self):
        self.seed("s1", self.thrice())
        os.chmod(self.state, 0o500)
        self.addCleanup(os.chmod, self.state, 0o700)
        shell = self.run_sb("observe", "summarize", "--session", "s1", cwd=self.root)
        self.assertEqual(shell.returncode, 0, shell.stderr)
        self.assertNotIn("Traceback", shell.stderr)

    @unittest.skipIf(os.geteuid() == 0, "root ignores file modes")
    def test_a_read_only_patch_file_and_a_directory_in_its_place(self):
        self.write("CLAUDE.md", "a\nb\n")
        self.run_session("s1", self.thrice())
        (meta,) = self.metas()
        path = patches.patch_file(self.state, meta.id)
        path.chmod(0o400)
        self.run_session("s2", self.thrice())
        self.assertEqual(self.metas()[0].sessions, 2)
        path.unlink()
        path.mkdir()
        self.run_session("s3", self.thrice())  # must not raise
        self.assertEqual(self.run_sb("patch", "list").returncode, 0)

    def test_an_unreadable_patch_is_ignored_by_list(self):
        directory = patches.patches_dir(self.state)
        directory.mkdir(parents=True)
        (directory / "deadbeef.patch").write_bytes(b"\xff\xfe")
        self.run_session("s1", self.thrice())
        out = self.run_sb("patch", "list")
        self.assertEqual(out.returncode, 0)
        self.assertIn("1 pending", out.stdout)

    def test_the_summary_waits_for_the_patches_lock(self):
        import time
        self.write("CLAUDE.md", "a\nb\n")
        self.seed("s1", self.thrice())
        env = dict(os.environ, SECOND_BRAIN_STATE_DIR=str(self.state), PYTHONDONTWRITEBYTECODE="1")
        with patches.locked(self.state):
            proc = subprocess.Popen([sys.executable, str(SB), "observe", "summarize", "--session", "s1"], cwd=self.root,
                                    env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(1.5)
            self.assertIsNone(proc.poll(), "the summary wrote patches while the lock was held")
            self.assertEqual(self.metas(), [])
        self.assertEqual(proc.wait(timeout=CLI_TIMEOUT), 0)
        self.assertEqual(len(self.metas()), 1)

    def test_expire_waits_for_the_patches_lock(self):
        import time
        self.run_session("s1", self.thrice())
        (meta,) = self.metas()
        path = patches.patch_file(self.state, meta.id)
        path.write_bytes(path.read_bytes().replace(f"# created: {meta.created}".encode(), b"# created: 2020-01-01"))
        code = f"import pathlib, patches; patches.expire(pathlib.Path({str(self.state)!r}))"
        with patches.locked(self.state):
            proc = subprocess.Popen([sys.executable, "-c", code], cwd=HERE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                    env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
            time.sleep(1.5)
            self.assertIsNone(proc.poll(), "expire ran while the lock was held")
            self.assertTrue(path.exists())
        self.assertEqual(proc.wait(timeout=CLI_TIMEOUT), 0)
        self.assertFalse(path.exists())

    def test_parallel_summaries_of_distinct_sessions_keep_every_session_id(self):
        self.write("CLAUDE.md", "a\nb\n")
        env = dict(os.environ, SECOND_BRAIN_STATE_DIR=str(self.state), PYTHONDONTWRITEBYTECODE="1")
        for round_ in range(3):
            shutil.rmtree(self.state, ignore_errors=True)
            names = [f"p{round_}{i}" for i in range(4)]
            for name in names:
                self.seed(name, self.thrice())
            procs = [subprocess.Popen([sys.executable, str(SB), "observe", "summarize", "--session", name], cwd=self.root,
                                      env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) for name in names]
            for proc in procs:
                self.assertEqual(proc.wait(timeout=CLI_TIMEOUT), 0)
            self.assertEqual(sorted(self.metas("reread")[0].session_ids), sorted(names))

    def test_two_simultaneous_summaries_leave_one_file_with_one_run_bytes(self):
        self.write("CLAUDE.md", "a\nb\n")
        self.seed("s1", self.thrice())
        env = dict(os.environ, SECOND_BRAIN_STATE_DIR=str(self.state), PYTHONDONTWRITEBYTECODE="1")
        procs = [subprocess.Popen([sys.executable, str(SB), "observe", "summarize", "--session", "s1"], cwd=self.root, env=env,
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) for _ in range(2)]
        for proc in procs:
            self.assertEqual(proc.wait(timeout=CLI_TIMEOUT), 0)
        after = self.state_hashes()
        solo = self.base / "solo"
        env["SECOND_BRAIN_STATE_DIR"] = str(solo)
        self.seed("s1", self.thrice(), state=solo)
        subprocess.run([sys.executable, str(SB), "observe", "summarize", "--session", "s1"], cwd=self.root, env=env, check=True, timeout=CLI_TIMEOUT)
        again = {k: v for k, v in after.items() if k.startswith("patches/")}
        self.assertEqual(again, {str(p.relative_to(solo)): hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in sorted(solo.rglob("*.patch"))})
        self.assertEqual(len(again), 1)


class ApplyTest(Fixture):
    def setUp(self):
        super().setUp()
        self.write("CLAUDE.md", "um\ndois\ntres\n")
        self.write("AGENTS.md", "agentes\n")
        self.write(".claude/settings.local.json", canon({"permissions": {"allow": ["Bash(ls)"]}}))
        subprocess.run(["git", "init", "-q", str(self.root)], check=True, timeout=CLI_TIMEOUT)
        self.two_big()
        self.run_session("s1", self.thrice())
        self.ids = {m.rule: m.id for m in self.metas()}

    def test_no_id_is_a_usage_error(self):
        before = snapshot(self.root)
        out = self.run_sb("patch", "apply")
        self.assertEqual(out.returncode, 2)
        self.assertEqual(snapshot(self.root), before)

    def test_read_only_commands_and_the_dry_run_change_nothing(self):
        before, state_before = snapshot(self.root), self.state_hashes()
        for args in (("patch", "list"), ("patch", "list", "--json"), ("patch", "show", self.ids["big"]),
                     ("patch", "apply", self.ids["big"]), ("patch", "apply", self.ids["deny"])):
            out = self.run_sb(*args)
            self.assertEqual(out.returncode, 0, (args, out.stderr))
        self.assertEqual(snapshot(self.root), before)
        self.assertEqual(self.state_hashes(), state_before)
        dry = self.run_sb("patch", "apply", self.ids["big"]).stdout
        self.assertIn(f"target: {self.root / 'CLAUDE.md'}", dry)
        self.assertIn("would apply (dry run, add --apply)", dry)
        self.assertIn("+- Evite ler `src/big.py` inteiro", dry)

    def test_apply_writes_only_the_target_of_the_header_from_any_cwd(self):
        other = self.base / "elsewhere"
        other.mkdir()
        before = snapshot(self.root)
        out = self.run_sb("patch", "apply", self.ids["big"], "--apply", cwd=other)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(out.stdout.strip(), f"applied: {self.ids['big']} -> {self.root / 'CLAUDE.md'}")
        after = snapshot(self.root)
        changed = {k for k in after if before.get(k) != after[k] and after[k][0] != stat.S_IFDIR}
        self.assertEqual(changed - {".git"}, {"CLAUDE.md"})
        self.assertEqual(list(other.iterdir()), [])
        text = (self.root / "CLAUDE.md").read_text()
        self.assertTrue(text.startswith("um\ndois\ntres\n- Evite ler `src/big.py` inteiro"))
        self.assertEqual(text.count("src/big.py"), 1)
        self.assertEqual(patches.read(self.state, self.ids["big"]), None)
        self.assertEqual(self.run_sb("patch", "apply", self.ids["big"], "--apply").returncode, 2)

    def test_a_summary_after_the_apply_does_not_bring_the_patch_back(self):
        self.run_sb("patch", "apply", self.ids["big"], "--apply")
        self.run_session("s1", [(self.root / "src/big.py", BIG)])
        self.run_session("s2", [(self.root / "src/big.py", BIG)])
        self.assertNotIn(self.ids["big"], [m.id for m in self.metas()])
        self.assertEqual((self.root / "CLAUDE.md").read_text().count("src/big.py"), 1)

    def test_apply_and_summary_at_the_same_time(self):
        env = dict(os.environ, SECOND_BRAIN_STATE_DIR=str(self.state), PYTHONDONTWRITEBYTECODE="1")
        one = subprocess.Popen([sys.executable, str(SB), "patch", "apply", self.ids["big"], "--apply"], cwd=self.root, env=env,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        two = subprocess.Popen([sys.executable, str(SB), "observe", "summarize", "--session", "s2"], cwd=self.root, env=env,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.assertEqual((one.wait(timeout=CLI_TIMEOUT), two.wait(timeout=CLI_TIMEOUT)), (0, 0))
        self.assertEqual((self.root / "CLAUDE.md").read_text().count("src/big.py"), 1)
        self.assertNotIn(self.ids["big"], [m.id for m in self.metas()])

    def test_the_deny_apply_writes_the_settings_only(self):
        before = snapshot(self.root)
        out = self.run_sb("patch", "apply", self.ids["deny"], "--apply")
        self.assertEqual(out.returncode, 0, out.stderr)
        after = snapshot(self.root)
        changed = {k for k in after if before.get(k) != after[k] and after[k][0] != stat.S_IFDIR}
        self.assertEqual(changed - {".git"}, {".claude/settings.local.json"})
        self.assertEqual(json.loads((self.root / ".claude/settings.local.json").read_text()),
                         {"permissions": {"deny": ["Read(./src/big.py)"], "allow": ["Bash(ls)"]}})

    def refused(self, pid, label):
        before = snapshot(self.root)
        for flag in ((), ("--apply",)):
            out = self.run_sb("patch", "apply", pid, *flag)
            self.assertEqual(out.returncode, 1, (label, out.stdout, out.stderr))
            self.assertIn("refused:", out.stderr)
            self.assertNotIn("Traceback", out.stderr)
            self.assertEqual(snapshot(self.root), before, label)
        self.assertEqual(sorted(p.name for p in self.root.iterdir() if p.name.startswith(".sb-patch")), [])

    def rewrite(self, pid, old, new, count=1):
        path = patches.patch_file(self.state, pid)
        path.write_bytes(path.read_bytes().replace(old, new, count))

    def test_refusals_on_the_target(self):
        pid = self.ids["big"]
        outside = self.base / "outside.md"
        outside.write_text("fora\nfora\n")
        cases = {
            "line appended": lambda: self.write("CLAUDE.md", "um\ndois\ntres\nquatro\n"),
            "target removed": lambda: (self.root / "CLAUDE.md").unlink(),
            "target is a link out": lambda: ((self.root / "CLAUDE.md").unlink(), (self.root / "CLAUDE.md").symlink_to(outside)),
            "target lost its newline": lambda: self.write("CLAUDE.md", "um\ndois\ntres"),
            "target is now a directory": lambda: ((self.root / "CLAUDE.md").unlink(), (self.root / "CLAUDE.md").mkdir()),
        }
        original = (self.root / "CLAUDE.md").read_bytes()
        for label, change in cases.items():
            with self.subTest(label):
                (self.root / "CLAUDE.md").is_dir() and (self.root / "CLAUDE.md").rmdir()
                (self.root / "CLAUDE.md").unlink(missing_ok=True)
                (self.root / "CLAUDE.md").write_bytes(original)
                change()
                self.refused(pid, label)
        self.assertEqual(outside.read_text(), "fora\nfora\n")

    def test_refusals_on_the_patch(self):
        pid = self.ids["big"]
        original = patches.read(self.state, pid)
        edits = {
            "one byte of the line": (b"caracteres em 2", b"caracteres em 3"), "target path": (b"# target: CLAUDE.md", b"# target: ../x"),
            "rel with ..": (b"# file: src/big.py", b"# file: ../big.py"), "unknown rule": (b"# rule: big", b"# rule: nope"),
            "root missing": (b"# root: " + str(self.root).encode(), b"# root: " + str(self.base / "gone").encode()),
            "id in the header": (b"# sb-patch: " + pid.encode(), b"# sb-patch: 00000000"),
            "created past ttl": (b"# created: " + patches.parse(original).created.encode(), b"# created: 2020-01-01"),
            "diff position": (b"@@ -3,0 +4 @@", b"@@ -2,0 +3 @@"),
        }
        for label, (old, new) in edits.items():
            with self.subTest(label):
                patches.patch_file(self.state, pid).write_bytes(original)
                self.rewrite(pid, old, new)
                self.refused(pid, label)

    def test_a_patch_with_another_file_name_is_refused(self):
        pid = self.ids["big"]
        data = patches.read(self.state, pid)
        patches.patch_file(self.state, "00000001").write_bytes(data)
        self.refused("00000001", "renamed")

    def test_forged_headers_with_a_matching_id(self):
        """The id binds rule, root and file, so a forger must recompute it: the other checks still stop them."""
        home = self.base / "home"
        home.mkdir()
        self.write("CLAUDE.md", "a\nb\n", root=home)
        meta = patches.parse(patches.read(self.state, self.ids["big"]))
        forged = {
            "root is $HOME": (str(home), meta.rule, meta.target, meta.file),
            "other project": (str(self.base), meta.rule, meta.target, meta.file),
            "deny on a markdown": (str(self.root), "deny", "CLAUDE.md", meta.file),
            "line on settings": (str(self.root), "big", ".claude/settings.local.json", meta.file),
            "target not allowed": (str(self.root), "big", "README.md", meta.file),
        }
        for label, (root, rule, target, rel) in forged.items():
            with self.subTest(label), mock.patch.dict(os.environ, {"HOME": str(home)}):
                pid = patches.patch_id(rule, root, rel)
                candidate = meta._replace(id=pid, rule=rule, root=root, target=target, file=rel)
                old = (Path(root) / "CLAUDE.md").read_bytes() if (Path(root) / "CLAUDE.md").exists() else b"x\ny\n"
                try:
                    built = patches.render(candidate, old).text
                except patches.PatchError:
                    # the renderer already refuses; write the header by hand so the apply sees it
                    built = patches.read(self.state, self.ids["big"]).replace(
                        b"# sb-patch: " + self.ids["big"].encode(), b"# sb-patch: " + pid.encode()).replace(
                        str(self.root).encode(), root.encode()).replace(b"# target: CLAUDE.md", f"# target: {target}".encode()
                        ).replace(b"# rule: big", f"# rule: {rule}".encode())
                patches.patch_file(self.state, pid).write_bytes(built)
                before = snapshot(self.root)
                out = self.run_sb("patch", "apply", pid, "--apply", env={"HOME": str(home)})
                self.assertEqual(out.returncode, 1, (label, out.stdout, out.stderr))
                self.assertEqual(snapshot(self.root), before)
                self.assertEqual((home / "CLAUDE.md").read_text(), "a\nb\n")

    def test_a_root_edited_to_a_twin_project_is_refused(self):
        twin = self.base / "twin"
        twin.mkdir()
        self.write("CLAUDE.md", "um\ndois\ntres\n", root=twin)
        pid = self.ids["big"]
        self.rewrite(pid, f"# root: {self.root}".encode(), f"# root: {twin}".encode())
        out = self.run_sb("patch", "apply", pid, "--apply")
        self.assertEqual(out.returncode, 1, out.stdout)
        self.assertEqual((twin / "CLAUDE.md").read_text(), "um\ndois\ntres\n")

    def test_a_deny_patch_retargeted_to_a_markdown_file_is_refused(self):
        pid = self.ids["deny"]
        for old, new in ((b"# target: .claude/settings.local.json", b"# target: CLAUDE.md"),
                         (b"a/.claude/settings.local.json", b"a/CLAUDE.md"), (b"b/.claude/settings.local.json", b"b/CLAUDE.md")):
            self.rewrite(pid, old, new)
        before = snapshot(self.root)
        out = self.run_sb("patch", "apply", pid, "--apply")
        self.assertEqual(out.returncode, 1, out.stdout)
        self.assertEqual(snapshot(self.root), before)

    def test_the_apply_waits_for_the_patches_lock(self):
        import time
        env = dict(os.environ, SECOND_BRAIN_STATE_DIR=str(self.state), PYTHONDONTWRITEBYTECODE="1")
        with patches.locked(self.state):
            proc = subprocess.Popen([sys.executable, str(SB), "patch", "apply", self.ids["big"], "--apply"], cwd=self.root,
                                    env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(1.5)
            self.assertIsNone(proc.poll(), "the apply ran while the lock was held")
            self.assertEqual((self.root / "CLAUDE.md").read_text(), "um\ndois\ntres\n")
        self.assertEqual(proc.wait(timeout=CLI_TIMEOUT), 0)

    def test_deny_entry_that_appeared_is_refused(self):
        self.write(".claude/settings.local.json", canon({"permissions": {"deny": ["Read(./src/big.py)"]}}))
        self.refused(self.ids["deny"], "entry appeared")

    def test_deny_settings_that_changed_are_refused(self):
        self.write(".claude/settings.local.json", canon({"model": "x", "permissions": {"allow": ["Bash(ls)"]}}))
        self.refused(self.ids["deny"], "settings changed before the insertion point")

    def test_modes_of_existing_and_new_files(self):
        (self.root / "CLAUDE.md").chmod(0o640)
        self.assertEqual(self.run_sb("patch", "apply", self.ids["big"], "--apply").returncode, 0)
        self.assertEqual(stat.S_IMODE((self.root / "CLAUDE.md").stat().st_mode), 0o640)
        (self.root / ".claude/settings.local.json").chmod(0o600)
        self.assertEqual(self.run_sb("patch", "apply", self.ids["deny"], "--apply").returncode, 0)
        self.assertEqual(stat.S_IMODE((self.root / ".claude/settings.local.json").stat().st_mode), 0o600)

    def test_new_files_get_default_modes_whatever_the_umask(self):
        fresh = self.base / "fresh"
        fresh.mkdir()
        self.seed("n1", [(fresh / "src/big.py", BIG)] * 1)
        self.seed("n2", [(fresh / "src/big.py", BIG)] * 1)
        for sid in ("n1", "n2"):
            observe.summarize(self.state, sid, "fresh", None, root=fresh)
        ids = {m.rule: m.id for m in self.metas() if m.root == str(fresh)}
        old = os.umask(0o077)
        try:
            for pid in ids.values():
                out = self.run_sb("patch", "apply", pid, "--apply")
                self.assertEqual(out.returncode, 0, out.stderr)
        finally:
            os.umask(old)
        self.assertEqual(stat.S_IMODE((fresh / "CLAUDE.md").stat().st_mode), 0o644)
        self.assertEqual(stat.S_IMODE((fresh / ".claude/settings.local.json").stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE((fresh / ".claude").stat().st_mode), 0o755)

    @unittest.skipIf(os.geteuid() == 0, "root ignores directory modes")
    def test_an_unwritable_folder_exits_one_without_a_trace_or_temp_file(self):
        fresh = self.base / "fresh2"
        fresh.mkdir()
        self.seed("n1", [(fresh / "big.py", BIG)])
        observe.summarize(self.state, "n1", "fresh2", None, root=fresh)
        (meta,) = [m for m in self.metas() if m.root == str(fresh)]
        fresh.chmod(0o555)
        self.addCleanup(fresh.chmod, 0o755)
        out = self.run_sb("patch", "apply", meta.id, "--apply")
        self.assertEqual(out.returncode, 1)
        self.assertNotIn("Traceback", out.stderr)
        self.assertEqual(list(fresh.iterdir()), [])
        self.assertIsNotNone(patches.read(self.state, meta.id))

    def test_show_and_unknown_ids(self):
        shown = self.run_sb("patch", "show", self.ids["big"])
        self.assertEqual(shown.stdout.encode(), patches.read(self.state, self.ids["big"]))
        for bad in ("../x", "zzzzzzzz", "00000000", "ABCDEF12", ""):
            self.assertEqual(self.run_sb("patch", "show", bad).returncode, 2, bad)
        self.assertEqual(self.run_sb("patch", "apply", "../x", "--apply").returncode, 2)

    def test_list_shows_the_columns_and_json(self):
        out = self.run_sb("patch", "list").stdout
        for needle in (self.ids["big"], "reread", "big", "deny", "CLAUDE.md", "proj", "left 30d", "3 pending"):
            self.assertIn(needle, out)
        rows = json.loads(self.run_sb("patch", "list", "--json").stdout)
        self.assertEqual(sorted(r["rule"] for r in rows), ["big", "deny", "reread"])
        self.assertTrue(all({"id", "count", "sessions", "days_left", "target"} <= set(r) for r in rows))


class ProjectTreeTest(Fixture):
    """N2: the observer and the hook never touch a project."""

    def hook(self, args, payload, project, session):
        script = Path.home() / "dotfiles/claude/hooks/second-brain-observe.sh"
        if not script.exists():
            self.skipTest("hook not installed")
        env = dict(os.environ, SECOND_BRAIN_HOOKS="1", SECOND_BRAIN_VAULT=str(HERE.parents[3]),
                   SECOND_BRAIN_STATE_DIR=str(self.state), PYTHONDONTWRITEBYTECODE="1")
        return subprocess.run(["bash", str(script), *args], input=json.dumps(payload), text=True, cwd=project, env=env,
                              capture_output=True, timeout=CLI_TIMEOUT)

    def drive(self, project, with_git):
        if with_git:
            subprocess.run(["git", "init", "-q", str(project)], check=True, timeout=CLI_TIMEOUT)
            subprocess.run(["git", "-C", str(project), "add", "-A"], check=True, timeout=CLI_TIMEOUT)
            subprocess.run(["git", "-C", str(project), "-c", "user.email=a@b", "-c", "user.name=n", "commit", "-qm", "x",
                            "--allow-empty"], check=True, timeout=CLI_TIMEOUT)
        before = snapshot(project)
        for sid in ("h1", "h2"):
            for _ in range(3):
                for name, size in (("src/a.py", 10), ("src/big.py", BIG)):
                    self.hook([], {"session_id": sid, "tool_name": "Read", "tool_input": {"file_path": str(project / name)},
                                   "tool_response": "x" * size}, project, sid)
            for _ in range(3):
                self.hook(["stop"], {"session_id": sid, "transcript_path": ""}, project, sid)
        self.assertEqual(snapshot(project), before)
        return len(self.metas())

    def test_the_hook_leaves_a_full_project_untouched(self):
        self.write("CLAUDE.md", "a\nb\n")
        self.write("AGENTS.md", "a\nb\n")
        self.write(".claude/settings.local.json", canon({"permissions": {"allow": ["x"]}}))
        self.assertGreaterEqual(self.drive(self.root, True), 3)

    def test_the_hook_leaves_a_project_without_instructions_untouched(self):
        self.assertGreaterEqual(self.drive(self.root, True), 2)

    def test_the_hook_leaves_a_project_without_git_untouched(self):
        self.write("CLAUDE.md", "a\nb\n")
        self.assertGreaterEqual(self.drive(self.root, False), 2)

    def test_library_summaries_leave_the_tree_byte_for_byte(self):
        self.write("CLAUDE.md", "a\nb\n")
        self.write(".claude/settings.local.json", canon({"permissions": {"allow": ["x"]}}))
        before = snapshot(self.root)
        self.two_big()
        self.run_session("s3", self.thrice())
        self.assertEqual(snapshot(self.root), before)


class ReachTest(unittest.TestCase):
    def source(self, name):
        return (HERE / name).read_text()

    def test_patch_apply_is_imported_once_and_only_inside_run_patch(self):
        tree = ast.parse(self.source("sb.py"))
        top = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
        self.assertFalse([n for n in top if "patch_apply" in ast.dump(n)])
        inside = []
        for func in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
            for node in ast.walk(func):
                if isinstance(node, (ast.Import, ast.ImportFrom)) and "patch_apply" in ast.dump(node):
                    inside.append(func.name)
        self.assertEqual(inside, ["run_patch"])
        self.assertEqual(self.source("sb.py").count("patch_apply."), 1)

    def test_no_other_module_or_script_reaches_the_writer(self):
        for path in HERE.iterdir():
            if path.suffix in (".py", ".sh") and not path.name.startswith("test_") and path.name not in ("sb.py", "patch_apply.py"):
                self.assertNotIn("patch_apply", path.read_text(), path.name)
                self.assertNotIn("apply_patch", path.read_text(), path.name)

    def test_observer_modules_have_no_subprocess_shutil_or_project_writes(self):
        for name in ("patches.py", "observe.py"):
            tree = ast.parse(self.source(name))
            modules = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
            modules |= {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
            self.assertFalse(modules & {"subprocess", "shutil", "tempfile"}, name)
            for token in ("write_text", "write_bytes", "os.rename", "os.replace", "os.chmod", "'w'", '"w"', "'wb'", '"wb"'):
                self.assertNotIn(token, self.source(name), (name, token))

    def test_only_stdlib_and_local_modules(self):
        local = {p.stem for p in HERE.glob("*.py")} | {"lib"}
        for name in ("patches.py", "patch_apply.py"):
            tree = ast.parse(self.source(name))
            for node in ast.walk(tree):
                mods = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or ""] if isinstance(node, ast.ImportFrom) else []
                for mod in mods:
                    root = mod.split(".")[0]
                    self.assertTrue(root in local or root in sys.stdlib_module_names or root == "__future__", (name, mod))

    def test_constants_and_named_tuples(self):
        self.assertEqual((patches.MAX_PATCHES, patches.MAX_TARGET_BYTES, patches.DENY_MIN_SESSIONS), (50, 262144, 2))
        for cls in (patches.Meta, patches.Built, observe.Finding):
            self.assertTrue(issubclass(cls, tuple))
        import patch_apply
        self.assertTrue(issubclass(patch_apply.Result, tuple))

    def test_the_vault_diff_stays_inside_the_skill(self):
        out = subprocess.run(["git", "diff", "--name-only", "master...HEAD"], capture_output=True, text=True, cwd=HERE, timeout=CLI_TIMEOUT)
        if out.returncode != 0:
            self.skipTest("no master branch here")
        for name in out.stdout.split():
            self.assertTrue(name.startswith("00_META/skills/second-brain-sync/"), name)


class GitApplyTableTest(Fixture):
    """R6: `git apply --check` and `patch -p1 --dry-run` take every form the code generates."""

    def make(self, body, with_git=True):
        shutil.rmtree(self.state, ignore_errors=True)
        for name in ("CLAUDE.md", "AGENTS.md"):
            (self.root / name).unlink(missing_ok=True)
        if body is not None:
            self.write("CLAUDE.md", body)
        self.run_session("s1", self.thrice())
        return self.text("reread") if self.metas() else ""

    def test_line_forms(self):
        cases = {"two lines": "a\nb\n", "many lines": "a\n" * 40, "empty": "", "new file": None, "crlf": "a\r\nb\r\n"}
        for label, body in cases.items():
            for with_git in (True, False):
                with self.subTest(label, git=with_git):
                    text = self.make(body)
                    old = {} if body is None else {"CLAUDE.md": body}
                    self.assertEqual(self.git_checks(text, old, with_git=with_git), (0, 0))

    def test_position_table(self):
        for lines in range(0, 6):
            with self.subTest(lines=lines):
                text = self.make("x\n" * lines) if lines else self.make("")
                made = bool(self.metas())
                self.assertEqual(made, lines != 1)
                if made:
                    self.assertEqual(self.git_checks(text, {"CLAUDE.md": "x\n" * lines}), (0, 0))
        self.assertTrue(patches.git_safe(0, 0) and patches.git_safe(2, 2) and patches.git_safe(3, 40))
        self.assertFalse(patches.git_safe(0, 1) or patches.git_safe(1, 1) or patches.git_safe(1, 5))

    def test_settings_forms(self):
        cases = {"new": None, "first deny item": {"permissions": {"deny": ["Read(./o)"]}},
                 "deny first of permissions": {"permissions": {"allow": ["a"]}}}
        for label, obj in cases.items():
            for with_git in (True, False):
                with self.subTest(label, git=with_git):
                    shutil.rmtree(self.state, ignore_errors=True)
                    shutil.rmtree(self.root / ".claude", ignore_errors=True)
                    self.write("CLAUDE.md", "a\nb\n")
                    old = {}
                    if obj is not None:
                        self.write(".claude/settings.local.json", canon(obj))
                        old = {".claude/settings.local.json": canon(obj)}
                    self.two_big()
                    self.assertEqual(self.git_checks(self.text("deny"), old, with_git=with_git), (0, 0))

    def test_permissions_in_first_position_makes_no_deny(self):
        self.write("CLAUDE.md", "a\nb\n")
        self.write(".claude/settings.local.json", canon({"model": "x"}))
        self.two_big()
        self.assertEqual([m.rule for m in self.metas()], ["big"])

    def test_git_safe_is_enforced(self):
        with mock.patch.object(patches, "git_safe", return_value=True):
            self.write("CLAUDE.md", "one\n")
            self.run_session("s1", self.thrice())
            self.assertEqual(len(self.metas()), 1)  # the mutation lets the unsafe patch through...
        shutil.rmtree(self.state)
        self.run_session("s1", self.thrice())
        self.assertEqual(self.metas(), [])  # ...and the real rule stops it


class WorstCaseTest(Fixture):
    def test_the_stop_hook_stays_under_a_second(self):
        import statistics
        import time
        self.write("CLAUDE.md", "h\n" + "x" * (patches.MAX_TARGET_BYTES - 3) + "\n")
        settings = canon({"permissions": {"allow": [f"Bash(cmd{i})" for i in range(9000)]}})
        self.write(".claude/settings.local.json", settings)
        self.assertGreater(len(settings), 190_000)
        directory = patches.patches_dir(self.state)
        directory.mkdir(parents=True)
        for i in range(patches.MAX_PATCHES - 6):
            (directory / f"{i:08x}.patch").write_text("# not ours\n")
        reads = [(self.root / f"src/big{i}.py", BIG) for i in range(3)]  # three big reads, none read twice
        reads += [(self.root / f"src/noise{i}.py", 10) for i in range(4997)]  # a 5000-line log with no reread
        script = Path.home() / "dotfiles/claude/hooks/second-brain-observe.sh"
        env = dict(os.environ, SECOND_BRAIN_HOOKS="1", SECOND_BRAIN_VAULT=str(HERE.parents[3]),
                   SECOND_BRAIN_STATE_DIR=str(self.state), PYTHONDONTWRITEBYTECODE="1")
        times = []
        for sid in ("w1", "w2", "w2"):
            self.seed(sid, reads)
            began = time.monotonic()
            if script.exists():
                subprocess.run(["bash", str(script), "stop"], input=json.dumps({"session_id": sid}), text=True, cwd=self.root,
                               env=env, capture_output=True, timeout=CLI_TIMEOUT)
            else:
                self.run_sb("observe", "summarize", "--session", sid)
            times.append(time.monotonic() - began)
        self.assertLess(statistics.median(times), 1.0, times)
        self.assertEqual(sorted(m.rule for m in self.metas()), ["big"] * 3 + ["deny"] * 3)


if __name__ == "__main__":
    unittest.main()
