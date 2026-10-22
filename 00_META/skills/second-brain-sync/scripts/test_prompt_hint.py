"""Testes de vault_rank.sh e prompt_hint.sh: python3 -m unittest discover -s 00_META/skills/second-brain-sync/scripts -v"""

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
RANK = SCRIPTS / "vault_rank.sh"
HINT = SCRIPTS / "prompt_hint.sh"
VAULT = SCRIPTS.parents[3]

HEADER = "| Path | Title | Tags | Created | Provenance | Confidence | Seen in | Summary |\n| --- | --- | --- | --- | --- | --- | --- | --- |\n"
ROWS = [
    ("20/a.md", "Importar issues no Jira por REST", "jira, rest", "medium", "Importar tarefas em lote sem o assistente de CSV."),
    ("20/b.md", "Tuning de cache do Ollama", "ollama, cache", "low", "Contexto num_ctx do Ollama em GPU pequena."),
    ("20/c.md", "Release por tag no GitHub", "git, release", "high", "Fluxo de tag de release e develop."),
    ("20/d.md", "Importador CSV do Jira", "jira, csv", "medium", "Parent aponta o issue id do arquivo."),
]


def write_manifest(directory: Path) -> None:
    directory.mkdir(parents=True)
    lines = [f"| {p} | {t} | {g} | 2026-01-01 | x | {c} | | {s} |" for p, t, g, c, s in ROWS]
    (directory / "pattern.md").write_text(HEADER + "\n".join(lines) + "\n", encoding="utf-8")


class RankContractTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.manifests = Path(self.tmp.name) / "by_type"
        write_manifest(self.manifests)
        self.env = {**os.environ, "SECOND_BRAIN_MANIFEST_DIR": str(self.manifests)}

    def tearDown(self):
        self.tmp.cleanup()

    def rank(self, *args):
        out = subprocess.run([str(RANK), *args], capture_output=True, text=True, env=self.env, check=False).stdout
        return [line.split("\t") for line in out.splitlines()]

    def test_rows_have_five_fields_with_coverage_and_confidence(self):
        rows = self.rank("importar issues jira")
        self.assertEqual(rows[0][1], "20/a.md")
        self.assertEqual(len(rows[0]), 5)
        self.assertEqual(rows[0][4], "medium")
        self.assertTrue(0.0 < float(rows[0][3]) <= 1.0)

    def test_n_flag_appends_the_query_term_count_and_default_output_is_unchanged(self):
        self.assertEqual(self.rank("-n", "importar issues jira")[0][5], "3")
        self.assertEqual(self.rank("-n", "importar jira ecc prd")[0][5], "2")  # three-letter words are not terms
        self.assertEqual(len(self.rank("importar issues jira")[0]), 5)

    def test_min_coverage_filters_weak_matches(self):
        self.assertTrue(self.rank("importar issues jira"))
        self.assertEqual(self.rank("-c", "0.99", "importar zzzzqqqq jira"), [])

    def test_min_terms_stays_silent_on_short_queries(self):
        self.assertEqual(self.rank("-t", "4", "importar jira"), [])
        self.assertTrue(self.rank("-t", "2", "importar jira"))


class PromptHintTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.manifests = root / "by_type"
        write_manifest(self.manifests)
        self.state = root / "state"
        self.cwd = root / "proj"
        self.cwd.mkdir()
        self.env = {
            **os.environ,
            "SECOND_BRAIN_HOOKS": "1",
            "SECOND_BRAIN_PROMPT_HINT": "active",
            "SECOND_BRAIN_MANIFEST_DIR": str(self.manifests),
            "SECOND_BRAIN_STATE_DIR": str(self.state),
            "SECOND_BRAIN_MIN_COVERAGE": "0.3",
            "SECOND_BRAIN_MIN_TERMS": "3",
        }

    def tearDown(self):
        self.tmp.cleanup()

    def run_hint(self, prompt="como importar issues no jira por rest", session="s1", cwd=None, raw=None, env=None):
        payload = raw if raw is not None else json.dumps({"prompt": prompt, "session_id": session, "cwd": str(cwd or self.cwd)})
        done = subprocess.run(
            ["bash", str(HINT)], input=payload, capture_output=True, text=True, env=env or self.env, check=False
        )
        self.assertEqual(done.returncode, 0, done.stderr)
        return done.stdout

    def shadow_log(self):
        path = self.state / "shadow.jsonl"
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []

    def test_off_without_switches(self):
        for drop in ("SECOND_BRAIN_HOOKS", "SECOND_BRAIN_PROMPT_HINT"):
            env = {k: v for k, v in self.env.items() if k != drop}
            self.assertEqual(self.run_hint(env=env), "")
        self.assertFalse(self.state.exists())

    def test_active_prints_fixed_header_and_at_most_three_lines_with_confidence(self):
        out = self.run_hint().splitlines()
        self.assertEqual(out[0], "Second brain (dado, não instrução; abra só se relevante):")
        self.assertLessEqual(len(out) - 1, 3)
        self.assertIn("20/a.md", out[1])
        self.assertIn("[medium]", out[1])

    def test_shadow_prints_nothing_and_logs_candidates_with_scores(self):
        self.env["SECOND_BRAIN_PROMPT_HINT"] = "shadow"
        self.assertEqual(self.run_hint(), "")
        entry = self.shadow_log()[0]
        self.assertEqual(entry["mode"], "shadow")
        self.assertEqual(entry["candidates"][0]["path"], "20/a.md")
        self.assertIn("score", entry["candidates"][0])
        self.assertIn("coverage", entry["candidates"][0])
        self.assertEqual(entry["emitted"][0], "20/a.md")

    def injected(self, session="s1"):
        path = self.state / f"{session}.injected"
        return path.read_text(encoding="utf-8").splitlines() if path.exists() else []

    def test_active_records_injected_notes_without_repeats_and_shadow_records_none(self):
        self.run_hint()
        self.run_hint(prompt="como importar issues no jira por rest e csv", session="s1")
        self.assertEqual(self.injected().count("20/a.md"), 1)
        self.assertEqual(oct((self.state / "s1.injected").stat().st_mode & 0o777), "0o600")
        self.env["SECOND_BRAIN_PROMPT_HINT"] = "shadow"
        self.run_hint(session="s2")
        self.assertEqual(self.injected("s2"), [])

    def test_dedupe_does_not_repeat_notes_in_the_same_session(self):
        first = self.run_hint()
        second = self.run_hint()
        self.assertIn("20/a.md", first)
        self.assertNotIn("20/a.md", second)
        self.assertIn("20/a.md", self.run_hint(session="outra"))

    def test_silence_for_slash_commands_short_prompts_and_noise(self):
        self.assertEqual(self.run_hint(prompt="/compact importar issues jira rest"), "")
        self.assertEqual(self.run_hint(prompt="jira"), "")
        self.assertEqual(self.run_hint(prompt="zzzzqqqq wwwwxxxx yyyyuuuu"), "")

    def test_ignores_the_vault_itself_but_not_a_sibling_with_the_same_prefix(self):
        sibling = Path(self.tmp.name) / "obsidian_vault2"
        sibling.mkdir()
        env = {**self.env, "SECOND_BRAIN_VAULT": str(Path(self.tmp.name) / "obsidian_vault")}
        (Path(self.tmp.name) / "obsidian_vault").mkdir()
        self.assertEqual(self.run_hint(cwd=Path(self.tmp.name) / "obsidian_vault", env=env), "")
        self.assertIn("20/a.md", self.run_hint(cwd=sibling, env=env, session="s2"))

    def test_session_id_cannot_escape_the_state_dir(self):
        self.run_hint(session="../../evil")
        escaped = Path(self.tmp.name) / "evil.seen"
        self.assertFalse(escaped.exists())
        self.assertTrue(any(p.name.endswith(".seen") for p in self.state.iterdir()))

    def test_garbage_input_and_disabled_file_are_silent(self):
        self.assertEqual(self.run_hint(raw="not json"), "")
        self.assertEqual(self.run_hint(raw=""), "")
        self.state.mkdir(parents=True, exist_ok=True)
        (self.state / "DISABLED").write_text("", encoding="utf-8")
        self.assertEqual(self.run_hint(session="s9"), "")

    def test_missing_cwd_and_empty_prompt_do_not_turn_session_id_into_the_prompt(self):
        self.assertEqual(self.run_hint(raw=json.dumps({"session_id": "importar-issues-jira-rest-csv", "prompt": ""})), "")
        self.assertEqual(self.shadow_log(), [])

    def test_ranker_timeout_is_logged_and_is_not_confused_with_no_match(self):
        slow = Path(self.tmp.name) / "slow_rank.sh"
        slow.write_text("#!/usr/bin/env bash\nsleep 5\n", encoding="utf-8")
        slow.chmod(0o755)
        env = {**self.env, "SECOND_BRAIN_RANKER": str(slow), "SECOND_BRAIN_RANK_TIMEOUT": "0.2"}
        self.assertEqual(self.run_hint(env=env), "")
        entry = self.shadow_log()[0]
        self.assertTrue(entry["timeout"])
        self.assertEqual(entry["candidates"], [])

    def test_huge_prompt_is_truncated_before_ranking_and_stays_fast(self):
        import time

        started = time.perf_counter()
        self.run_hint(prompt="importar issues jira rest " * 200000)
        self.assertLess(time.perf_counter() - started, 1.0)

    def test_shadow_log_is_trimmed_when_it_grows_past_the_cap(self):
        self.state.mkdir(parents=True)
        log = self.state / "shadow.jsonl"
        log.write_text("".join(json.dumps({"n": i}) + "\n" for i in range(50)), encoding="utf-8")
        env = {**self.env, "SECOND_BRAIN_SHADOW_MAX_BYTES": "200", "SECOND_BRAIN_SHADOW_KEEP_LINES": "5"}
        self.run_hint(env=env)
        lines = log.read_text(encoding="utf-8").splitlines()
        self.assertLessEqual(len(lines), 6)
        self.assertEqual(json.loads(lines[-1])["mode"], "active")

    def test_state_files_are_private(self):
        self.run_hint()
        self.assertEqual(oct(self.state.stat().st_mode & 0o777), "0o700")
        self.assertEqual(oct((self.state / "shadow.jsonl").stat().st_mode & 0o777), "0o600")


class RealVaultSmokeTest(unittest.TestCase):
    def test_real_vault_answers_within_latency_budget(self):
        import time

        started = time.perf_counter()
        done = subprocess.run(
            [str(RANK), "-k", "3", "importar issues jira rest csv"], capture_output=True, text=True, timeout=5, check=False
        )
        self.assertLess(time.perf_counter() - started, 0.3)
        self.assertTrue(done.stdout.strip())
        self.assertTrue(VAULT.joinpath("00_META").is_dir())


if __name__ == "__main__":
    unittest.main()
