"""Testes da F2 (note_candidates.sh e guardas do vault_sync.py).

    python3 -m unittest discover -s 00_META/skills/second-brain-sync/scripts -v
"""

import importlib
import json
import os
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
SYNC = SCRIPTS / "vault_sync.py"
CANDIDATES = SCRIPTS / "note_candidates.sh"
GEN = SCRIPTS / "generate_manifests.py"
SB = SCRIPTS / "sb.py"

NOTE = """---
title: {title}
type: pattern
tags: [{tags}]
created: 2026-10-14
provenance: {provenance}
{extra}---

# {title}

Corpo da nota sobre {title}.

## O que NÃO funcionou

Nada falhou neste teste.
"""


def make_note(title, tags="jira, rest", provenance="projeto_x", confidence="low"):
    extra = f"confidence: {confidence}\n" if confidence else ""
    return NOTE.format(title=title, tags=tags, provenance=provenance, extra=extra)


def git(cwd, *args):
    subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True)


class VaultFixture(unittest.TestCase):
    """Vault git real com remoto bare local; nada toca a rede nem o vault do usuário."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.remote = root / "remote.git"
        subprocess.run(["git", "init", "-q", "--bare", "-b", "master", str(self.remote)], check=True)
        self.vault = root / "vault"
        subprocess.run(["git", "init", "-q", "-b", "master", str(self.vault)], check=True)
        git(self.vault, "config", "user.email", "t@example.com")
        git(self.vault, "config", "user.name", "t")
        git(self.vault, "remote", "add", "origin", str(self.remote))
        (self.vault / "20_Permanent_Notes").mkdir()
        self.write("Importar Issues no Jira por REST", tags="jira, rest, csv", provenance="manual", confidence="medium")
        subprocess.run(["python3", str(GEN), "--vault-path", str(self.vault)], check=True, capture_output=True)
        git(self.vault, "add", "-A")
        git(self.vault, "commit", "-q", "-m", "init")
        git(self.vault, "push", "-q", "origin", "master")
        self.state = root / "state"
        self.env = {**os.environ, "SECOND_BRAIN_STATE_DIR": str(self.state)}

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, title, **kwargs):
        rel = f"20_Permanent_Notes/{title}.md"
        (self.vault / rel).write_text(make_note(title, **kwargs), encoding="utf-8")
        return rel

    def sync(self, *notes, new_because=None, extra_env=None, verdict=None, reason=None):
        cmd = ["python3", str(SYNC), "--vault-path", str(self.vault), "--project-name", "projeto_x", "--message", "docs: t"]
        for note in notes:
            cmd += ["--note", note]
        if new_because:
            cmd += ["--new-because", new_because]
        if verdict:
            cmd += ["--verdict", verdict]
        if reason:
            cmd += ["--reason", reason]
        return subprocess.run(cmd, capture_output=True, text=True, env={**self.env, **(extra_env or {})}, check=False)

    def log(self, name):
        path = self.state / name
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []


class NoteCandidatesTest(VaultFixture):
    def run_candidates(self, *args):
        env = {**self.env, "SECOND_BRAIN_VAULT": str(self.vault)}
        return subprocess.run([str(CANDIDATES), *args], capture_output=True, text=True, env=env, check=False)

    def test_lists_existing_note_with_coverage_and_confidence_and_logs_the_call(self):
        done = self.run_candidates("Importar issues no Jira via REST", "jira, rest")
        self.assertEqual(done.returncode, 0)
        path, title, coverage, confidence = done.stdout.splitlines()[0].split("\t")
        self.assertEqual(path, "20_Permanent_Notes/Importar Issues no Jira por REST.md")
        self.assertEqual(confidence, "medium")
        self.assertGreater(float(coverage), 0.5)
        entry = self.log("note_candidates.jsonl")[0]
        self.assertEqual(entry["title"], "Importar issues no Jira via REST")
        self.assertEqual(entry["candidates"][0]["path"], path)

    def test_silent_and_logged_when_nothing_matches(self):
        done = self.run_candidates("receita de pão de queijo mineiro")
        self.assertEqual((done.returncode, done.stdout), (0, ""))
        self.assertEqual(self.log("note_candidates.jsonl")[0]["candidates"], [])

    def test_at_most_three_candidates(self):
        for i in range(5):
            self.write(f"Importar issues Jira variante {i}", tags="jira, rest")
        done = self.run_candidates("Importar issues Jira variante", "jira rest")
        self.assertLessEqual(len(done.stdout.splitlines()), 3)


class SyncGuardsTest(VaultFixture):
    def test_new_note_with_strong_candidate_is_refused_without_justification(self):
        rel = self.write("Importar Issues no Jira via REST", tags="jira, rest, csv")
        done = self.sync(rel)
        self.assertEqual(done.returncode, 1)
        self.assertIn("Importar Issues no Jira por REST.md", done.stderr)
        self.assertIn("--new-because", done.stderr)
        self.assertEqual(self.log("sync.jsonl")[-1]["outcome"], "refused-candidate")

    def test_new_note_with_justification_syncs_and_logs_it(self):
        rel = self.write("Importar Issues no Jira via REST", tags="jira, rest, csv")
        done = self.sync(rel, new_because="cobre o limite de 100 mil linhas, que a nota existente não trata")
        self.assertEqual(done.returncode, 0, done.stderr)
        entry = self.log("sync.jsonl")[-1]
        self.assertEqual(entry["outcome"], "synced")
        self.assertEqual(entry["created"], [rel])
        self.assertIn("100 mil", entry["new_because"])

    def test_unrelated_new_note_syncs_without_justification(self):
        rel = self.write("Calibração de Câmera Estéreo", tags="visao, opencv")
        self.assertEqual(self.sync(rel).returncode, 0)

    def test_updating_an_existing_note_never_asks_for_justification(self):
        rel = "20_Permanent_Notes/Importar Issues no Jira por REST.md"
        path = self.vault / rel
        path.write_text(path.read_text(encoding="utf-8") + "\n- 2026-10-14: confirmado em projeto_x.\n", encoding="utf-8")
        done = self.sync(rel)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(self.log("sync.jsonl")[-1]["updated"], [rel])

    def test_new_agent_note_must_be_born_low_confidence(self):
        for confidence in ("medium", "high", ""):
            rel = self.write("Calibração de Câmera Estéreo", tags="visao, opencv", confidence=confidence)
            done = self.sync(rel)
            self.assertEqual(done.returncode, 1, f"confidence={confidence!r}")
            self.assertIn("confidence: low", done.stderr)
            (self.vault / rel).unlink()

    def test_manual_provenance_does_not_exempt_a_new_note_from_low_confidence(self):
        rel = self.write("Calibração de Câmera Estéreo", tags="visao, opencv", provenance="manual", confidence="high")
        done = self.sync(rel)
        self.assertEqual(done.returncode, 1)
        self.assertEqual(self.log("sync.jsonl")[-1]["outcome"], "refused-confidence")
        (self.vault / rel).write_text(make_note("Calibração de Câmera Estéreo", tags="visao, opencv", provenance="manual"), encoding="utf-8")
        self.assertEqual(self.sync(rel).returncode, 0)

    def test_second_sync_waits_for_the_lock_instead_of_racing(self):
        lock_dir = self.vault / ".git"
        holder = subprocess.Popen(
            ["python3", "-c", "import fcntl,sys,time;f=open(sys.argv[1],'w');fcntl.flock(f,fcntl.LOCK_EX);print('held',flush=True);time.sleep(1.5)",
             str(lock_dir / "second-brain-sync.lock")],
            stdout=subprocess.PIPE, text=True,
        )
        try:
            self.assertEqual(holder.stdout.readline().strip(), "held")
            rel = self.write("Calibração de Câmera Estéreo", tags="visao, opencv")
            started = time.perf_counter()
            done = self.sync(rel)
            self.assertEqual(done.returncode, 0, done.stderr)
            self.assertGreaterEqual(time.perf_counter() - started, 1.0)
        finally:
            holder.wait()
            holder.stdout.close()

    def test_lock_timeout_fails_loudly(self):
        lock_dir = self.vault / ".git"
        holder = subprocess.Popen(
            ["python3", "-c", "import fcntl,sys,time;f=open(sys.argv[1],'w');fcntl.flock(f,fcntl.LOCK_EX);print('held',flush=True);time.sleep(3)",
             str(lock_dir / "second-brain-sync.lock")],
            stdout=subprocess.PIPE, text=True,
        )
        try:
            holder.stdout.readline()
            rel = self.write("Calibração de Câmera Estéreo", tags="visao, opencv")
            done = self.sync(rel, extra_env={"SECOND_BRAIN_LOCK_TIMEOUT": "0.5"})
            self.assertEqual(done.returncode, 1)
            self.assertIn("lock", done.stderr.lower())
            self.assertEqual(self.log("sync.jsonl")[-1]["outcome"], "lock-timeout")
        finally:
            holder.wait()
            holder.stdout.close()

    def test_never_uses_force_and_still_refuses_unrelated_dirty_files(self):
        rel = self.write("Calibração de Câmera Estéreo", tags="visao, opencv")
        (self.vault / "20_Permanent_Notes" / "sujo.md").write_text("x", encoding="utf-8")
        done = self.sync(rel)
        self.assertEqual(done.returncode, 1)
        self.assertIn("unrelated dirty", done.stderr)


class ReviewRegressionTest(VaultFixture):
    """Achados da revisão independente da F2 (2026-10-15)."""

    def duplicate(self, **kwargs):
        return self.write("Importar Issues no Jira via REST", tags="jira, rest, csv", **kwargs)

    def test_staging_the_new_note_first_does_not_switch_the_checks_off(self):
        rel = self.duplicate(confidence="high")
        git(self.vault, "add", rel)
        done = self.sync(rel)
        self.assertEqual(done.returncode, 1)
        self.assertEqual(self.log("sync.jsonl")[-1]["created"], [rel])

    def test_title_starting_with_a_dash_still_finds_the_candidate(self):
        (self.vault / "20_Permanent_Notes" / "Importar Issues no Jira via REST.md").write_text(
            make_note("- Importar Issues no Jira via REST", tags="jira, rest, csv"), encoding="utf-8"
        )
        rel = "20_Permanent_Notes/Importar Issues no Jira via REST.md"
        done = self.sync(rel)
        self.assertEqual(done.returncode, 1, done.stdout)
        self.assertEqual(self.log("sync.jsonl")[-1]["outcome"], "refused-candidate")

    def test_sync_works_from_a_linked_worktree(self):
        worktree = Path(self.tmp.name) / "wt"
        git(self.vault, "worktree", "add", "-q", "-b", "wtb", str(worktree))
        rel = "20_Permanent_Notes/Calibração de Câmera Estéreo.md"
        (worktree / rel).write_text(make_note("Calibração de Câmera Estéreo", tags="visao, opencv"), encoding="utf-8")
        cmd = ["python3", str(SYNC), "--vault-path", str(worktree), "--project-name", "projeto_x", "--message", "docs: t", "--note", rel]
        done = subprocess.run(cmd, capture_output=True, text=True, env=self.env, check=False)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertFalse((worktree / "second-brain-sync.lock").exists())

    def test_failed_commit_unstages_and_the_retry_succeeds(self):
        hook = self.vault / ".git" / "hooks" / "pre-commit"
        hook.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        hook.chmod(0o755)
        rel = self.write("Calibração de Câmera Estéreo", tags="visao, opencv")
        self.assertEqual(self.sync(rel).returncode, 1)
        self.assertEqual(self.log("sync.jsonl")[-1]["outcome"], "commit-failed")
        staged = subprocess.run(["git", "-C", str(self.vault), "diff", "--cached", "--name-only"], capture_output=True, text=True).stdout
        self.assertEqual(staged, "")
        hook.unlink()
        self.assertEqual(self.sync(rel).returncode, 0)

    def test_failed_push_keeps_the_commit_and_the_retry_pushes_it(self):
        hook = self.remote / "hooks" / "pre-receive"
        hook.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        hook.chmod(0o755)
        rel = self.write("Calibração de Câmera Estéreo", tags="visao, opencv")
        self.assertEqual(self.sync(rel).returncode, 1)
        self.assertEqual(self.log("sync.jsonl")[-1]["outcome"], "push-failed")
        hook.unlink()
        retry = self.sync(rel)
        self.assertEqual(retry.returncode, 0, retry.stderr)
        remote_head = subprocess.run(["git", "-C", str(self.remote), "rev-parse", "master"], capture_output=True, text=True).stdout
        local_head = subprocess.run(["git", "-C", str(self.vault), "rev-parse", "HEAD"], capture_output=True, text=True).stdout
        self.assertEqual(remote_head, local_head)

    def test_not_a_repository_fails_cleanly_without_litter_and_is_logged(self):
        plain = Path(self.tmp.name) / "plain"
        plain.mkdir()
        cmd = ["python3", str(SYNC), "--vault-path", str(plain), "--project-name", "p", "--message", "m"]
        done = subprocess.run(cmd, capture_output=True, text=True, env=self.env, check=False)
        self.assertEqual(done.returncode, 1)
        self.assertNotIn("Traceback", done.stderr)
        self.assertEqual(list(plain.iterdir()), [])
        self.assertEqual(self.log("sync.jsonl")[-1]["outcome"], "crash")

    def test_undecodable_argument_does_not_break_the_exit_code_after_the_push(self):
        rel = self.write("Calibração de Câmera Estéreo", tags="visao, opencv")
        done = self.sync(rel, new_because="motivo \udcff")
        self.assertEqual(done.returncode, 0, done.stderr)

    def test_lock_timeout_is_logged_and_non_finite_timeouts_are_rejected(self):
        sys_path = str(SCRIPTS)
        import sys

        sys.path.insert(0, sys_path)
        try:
            module = importlib.import_module("vault_sync")
        finally:
            sys.path.remove(sys_path)
        for bad in ("nan", "inf", "-1", "abc"):
            os.environ["SECOND_BRAIN_LOCK_TIMEOUT"] = bad
            try:
                self.assertEqual(module.lock_timeout(), module.DEFAULT_LOCK_TIMEOUT_SECONDS, bad)
            finally:
                del os.environ["SECOND_BRAIN_LOCK_TIMEOUT"]


class PromotionAndSiblingTest(VaultFixture):
    LOW = "20_Permanent_Notes/Calibração de Câmera Estéreo.md"
    MEDIUM = "20_Permanent_Notes/Importar Issues no Jira por REST.md"

    def commit_low_note(self):
        (self.vault / self.LOW).write_text(make_note("Calibração de Câmera Estéreo", tags="visao, opencv"), encoding="utf-8")
        self.assertEqual(self.sync(self.LOW).returncode, 0)

    def edit(self, rel, *pairs):
        path = self.vault / rel
        text = path.read_text(encoding="utf-8")
        for old, new in pairs:
            self.assertIn(old, text)
            text = text.replace(old, new, 1)
        path.write_text(text, encoding="utf-8")

    def test_low_to_medium_needs_a_new_verified_line(self):
        self.commit_low_note()
        self.edit(self.LOW, ("confidence: low", "confidence: medium"))
        done = self.sync(self.LOW)
        self.assertEqual(done.returncode, 1)
        self.assertEqual(self.log("sync.jsonl")[-1]["outcome"], "refused-promotion")
        self.edit(self.LOW, ("confidence: medium\n", "confidence: medium\nverified: 2026-10-15 via teste manual\n"))
        self.assertEqual(self.sync(self.LOW).returncode, 0)

    def test_declaring_the_same_verified_line_again_is_not_new_evidence(self):
        self.commit_low_note()
        self.edit(self.LOW, ("confidence: low\n", "confidence: low\nverified: 2026-10-15 via git log\n"))
        self.assertEqual(self.sync(self.LOW).returncode, 0)
        self.edit(self.LOW, ("confidence: low", "confidence: medium"))
        self.assertEqual(self.sync(self.LOW).returncode, 1)

    def test_to_high_needs_two_projects_or_a_test(self):
        self.edit(self.MEDIUM, ("confidence: medium", "confidence: high"))
        self.assertEqual(self.sync(self.MEDIUM).returncode, 1)
        self.edit(self.MEDIUM, ("confidence: high\n", "confidence: high\nseen_in: [projeto_x]\n"))
        self.assertEqual(self.sync(self.MEDIUM).returncode, 1, "one project is not enough")
        self.edit(self.MEDIUM, ("seen_in: [projeto_x]", "seen_in: [projeto_x, projeto_y]"))
        self.assertEqual(self.sync(self.MEDIUM).returncode, 0)

    def test_quoted_or_capitalised_confidence_cannot_dodge_the_check(self):
        self.edit(self.MEDIUM, ("confidence: medium", 'confidence: "High"'))
        self.assertEqual(self.sync(self.MEDIUM).returncode, 1)

    def test_demotion_and_unchanged_confidence_never_ask_for_evidence(self):
        self.edit(self.MEDIUM, ("confidence: medium", "confidence: low"))
        self.assertEqual(self.sync(self.MEDIUM).returncode, 0)

    def two_siblings(self):
        a = "20_Permanent_Notes/Calibração Estéreo A.md"
        b = "20_Permanent_Notes/Calibração Estéreo B.md"
        for rel, title in ((a, "Calibração de Câmera Estéreo com OpenCV"), (b, "Calibração de Câmera Estéreo no OpenCV")):
            (self.vault / rel).write_text(make_note(title, tags="visao, opencv, calibracao"), encoding="utf-8")
        return a, b

    def test_two_near_identical_new_notes_in_one_call_are_refused(self):
        a, b = self.two_siblings()
        done = self.sync(a, b)
        self.assertEqual(done.returncode, 1)
        self.assertIn("look like each other", done.stderr)
        self.assertEqual(self.log("sync.jsonl")[-1]["outcome"], "refused-candidate")
        self.assertFalse(any(p.suffix == ".tmp" for p in self.vault.rglob("*")))

    def test_siblings_pass_with_a_justification(self):
        a, b = self.two_siblings()
        self.assertEqual(self.sync(a, b, new_because="A cobre intrínsecos, B cobre extrínsecos").returncode, 0)

    def test_two_unrelated_new_notes_in_one_call_pass(self):
        a = self.write("Calibração de Câmera Estéreo", tags="visao, opencv")
        b = self.write("Receita de Pão de Queijo Mineiro", tags="culinaria, receita")
        self.assertEqual(self.sync(a, b).returncode, 0)


class VerdictAndNegativeSectionTest(VaultFixture):
    def new_note(self, title="Calibração de Câmera Estéreo", type_="pattern", section=True):
        rel = f"20_Permanent_Notes/{title}.md"
        text = make_note(title, tags="visao, opencv").replace("type: pattern", f"type: {type_}")
        if not section:
            text = text.split("## O que NÃO funcionou")[0]
        (self.vault / rel).write_text(text, encoding="utf-8")
        return rel

    def touch_existing(self):
        rel = "20_Permanent_Notes/Importar Issues no Jira por REST.md"
        path = self.vault / rel
        path.write_text(path.read_text(encoding="utf-8") + "\nMais uma observação.\n", encoding="utf-8")
        return rel

    def last(self):
        return self.log("sync.jsonl")[-1]

    def test_verdict_is_inferred_and_logged_when_omitted(self):
        self.assertEqual(self.sync(self.new_note()).returncode, 0)
        self.assertEqual((self.last()["verdict"], self.last()["verdict_source"]), ("save", "inferred"))
        self.assertEqual(self.sync(self.touch_existing()).returncode, 0)
        self.assertEqual((self.last()["verdict"], self.last()["verdict_source"]), ("absorb", "inferred"))

    def test_declared_verdicts_that_match_the_git_facts_are_logged(self):
        self.assertEqual(self.sync(self.new_note(), verdict="improve-then-save").returncode, 0)
        self.assertEqual((self.last()["verdict"], self.last()["verdict_source"]), ("improve-then-save", "declared"))
        self.assertEqual(self.sync(self.touch_existing(), verdict="absorb").returncode, 0)
        self.assertEqual(self.last()["verdict"], "absorb")

    def test_save_without_a_new_note_is_refused(self):
        done = self.sync(self.touch_existing(), verdict="save")
        self.assertEqual(done.returncode, 1)
        self.assertIn("needs a new note", done.stderr)
        self.assertEqual(self.last()["outcome"], "refused-verdict")

    def test_absorb_that_creates_a_note_is_refused(self):
        done = self.sync(self.new_note(), verdict="absorb")
        self.assertEqual(done.returncode, 1)
        self.assertIn("updating existing notes", done.stderr)
        self.assertEqual(self.last()["outcome"], "refused-verdict")

    def test_drop_writes_nothing_and_records_the_reason(self):
        head = subprocess.run(["git", "-C", str(self.vault), "rev-parse", "HEAD"], capture_output=True, text=True).stdout
        done = self.sync(verdict="drop", reason="já coberto pela nota de Jira")
        self.assertEqual(done.returncode, 0)
        self.assertEqual((self.last()["outcome"], self.last()["verdict"]), ("dropped", "drop"))
        self.assertEqual(self.last()["reason"], "já coberto pela nota de Jira")
        self.assertEqual(
            subprocess.run(["git", "-C", str(self.vault), "rev-parse", "HEAD"], capture_output=True, text=True).stdout, head
        )

    def test_drop_needs_a_reason_and_refuses_notes(self):
        self.assertEqual(self.sync(verdict="drop").returncode, 1)
        self.assertEqual(self.sync(self.new_note(), verdict="drop", reason="x").returncode, 1)
        self.assertEqual(self.last()["outcome"], "refused-verdict")

    def test_drop_ignores_a_dirty_vault(self):
        self.new_note()
        self.assertEqual(self.sync(verdict="drop", reason="rascunho descartado").returncode, 0)

    def test_new_pattern_or_trap_without_the_section_is_refused(self):
        for type_ in ("pattern", "trap"):
            with self.subTest(type_):
                done = self.sync(self.new_note(title=f"Nota {type_} sem seção", type_=type_, section=False))
                self.assertEqual(done.returncode, 1)
                self.assertIn("O que NÃO funcionou", done.stderr)
                self.assertEqual(self.last()["outcome"], "refused-section")
                (self.vault / f"20_Permanent_Notes/Nota {type_} sem seção.md").unlink()

    def test_sb_sync_forwards_to_vault_sync_with_the_vault_preset(self):
        rel = self.new_note()
        env = {**self.env, "SECOND_BRAIN_VAULT": str(self.vault)}
        done = subprocess.run(
            ["python3", str(SB), "sync", "--note", rel, "--project-name", "projeto_x", "--message", "docs: via sb",
             "--verdict", "save"],
            capture_output=True, text=True, env=env, check=False,
        )
        self.assertEqual((done.returncode, done.stdout.startswith("synced: ")), (0, True))
        self.assertEqual((self.last()["outcome"], self.last()["verdict"]), ("synced", "save"))
        refused = subprocess.run(
            ["python3", str(SB), "sync", "--project-name", "projeto_x", "--message", "m", "--verdict", "drop"],
            capture_output=True, text=True, env=env, check=False,
        )
        self.assertEqual(refused.returncode, 1)
        self.assertIn("--reason", refused.stderr)

    def test_other_types_and_updates_do_not_need_the_section(self):
        self.assertEqual(self.sync(self.new_note(type_="concept", section=False)).returncode, 0)
        existing = self.vault / "20_Permanent_Notes/Importar Issues no Jira por REST.md"
        existing.write_text(existing.read_text(encoding="utf-8").split("## O que NÃO funcionou")[0], encoding="utf-8")
        git(self.vault, "add", "-A")
        git(self.vault, "commit", "-q", "-m", "note without the section")
        git(self.vault, "push", "-q", "origin", "master")
        self.assertEqual(self.sync(self.touch_existing()).returncode, 0)


if __name__ == "__main__":
    unittest.main()
