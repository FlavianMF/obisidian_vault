"""Testes do `sb` (I1) e do scanner de segredos: python3 -m unittest discover -s 00_META/skills/second-brain-sync/scripts -v

Credenciais abaixo são FALSAS e montadas em tempo de execução, para não existirem como literais no repositório.
"""

import datetime as dt
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

import generate_manifests as gm
import sb
from lib import secret_scan

SB = Path(sb.__file__)
TODAY = dt.date(2026, 10, 15)


def fake(*parts: str) -> str:
    return "".join(parts)


class SecretScanTest(unittest.TestCase):
    SHAPES = {
        "provider API key": fake("sk-", "A1b2C3d4E5f6G7h8I9j0"),
        "GitHub token": fake("gh", "p_", "A1b2C3d4E5f6G7h8I9j0K1l2"),
        "AWS access key id": fake("AK", "IA", "ABCDEFGHIJKLMNOP"),
        "Slack token": fake("xo", "xb-", "0000000000-ABCDEFGH"),
        "private key": fake("-----BEGIN RSA PRIV", "ATE KEY-----"),
        "JSON web token": fake("ey", "JhbGciOiJIUzI1NiJ9.ey", "JmYWtlIjoiZmFrZSJ9.", "FAKEsig0123456789"),
        "URL with credentials": fake("postgres://app:", "Fake9876pw", "@db.local/app"),
        "bearer token": fake("Authorization: Bear", "er ", "FAKEbearer0123456789ABCD"),
        "credential assignment": fake("aws_secret", "_access_key=", "FAKEaws0123SecretKey456"),
    }

    def test_detects_each_shape_the_ecc_observer_redactor_misses(self):
        for label, text in self.SHAPES.items():
            with self.subTest(label):
                self.assertIn(label, [f.label for f in secret_scan.scan_text(f"x {text} y")])

    def test_ordinary_prose_and_placeholders_are_clean(self):
        clean = (
            "O token expira em 5000 ms e a senha fica no cofre.\n"
            "password: <redigido>\n"
            "tokens: 5000\n"
            "Veja [[Nota Alvo]] e o `sk-` curto.\n"
        )
        self.assertEqual(secret_scan.scan_text(clean), [])

    def test_allow_marker_skips_the_line(self):
        line = fake("DB_PASS", "WORD=", "Fake0123456789abc") + "  # sb-allow-secret"
        self.assertEqual(secret_scan.scan_text(line), [])

    def test_finding_carries_label_and_line_never_the_secret(self):
        secret = self.SHAPES["GitHub token"]
        findings = secret_scan.scan_text(f"a\n{secret}\n")
        self.assertEqual([(f.label, f.line) for f in findings], [("GitHub token", 2)])
        self.assertNotIn(secret, repr(findings))


class VaultFixture(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.vault = Path(self._tmp.name) / "vault"
        self.state = Path(self._tmp.name) / "state"
        self.state.mkdir()
        # the ranker reads <state>/*.injected: never the real state dir of the machine
        patcher = mock.patch.dict(os.environ, {"SECOND_BRAIN_STATE_DIR": str(self.state)})
        patcher.start()
        self.addCleanup(patcher.stop)
        (self.vault / "20_Permanent_Notes").mkdir(parents=True)

    def note(self, name, *, title=None, type_="concept", created="2026-10-01", extra="", body="Corpo da nota.\n",
             folder="20_Permanent_Notes", frontmatter=True):
        path = self.vault / folder / f"{name}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        if frontmatter:
            fm = f"---\ntitle: {title or name}\ntype: {type_}\ntags: [a]\ncreated: {created}\n{extra}---\n\n"
        else:
            fm = ""
        path.write_text(fm + body, encoding="utf-8")
        return path

    def doctor(self, **kwargs):
        gm.write_manifests(self.vault)
        return sb.run_doctor(self.vault, kwargs.get("stale_days", 180), TODAY)

    def checks(self, issues, check):
        return [i for i in issues if i.check == check]


class DoctorTest(VaultFixture):
    def test_clean_vault_has_no_issues(self):
        self.note("Alpha", body="Veja [[Beta]] e [[Beta|apelido]] e [[Beta#Seção]].\n")
        self.note("Beta")
        self.assertEqual(self.doctor(), [])

    def test_reports_unresolved_link_as_a_warning_but_not_links_shown_in_code(self):
        self.note("Alpha", body="Real [[Fantasma]].\n\n```\n[[Exemplo Em Bloco]]\n```\n\nInline `[[Exemplo Inline]]`.\n")
        issues = self.checks(self.doctor(), "unresolved-link")
        self.assertEqual([(i.detail, i.severity) for i in issues], [("[[Fantasma]]", sb.WARN)])

    def test_ignores_a_wikilink_that_spans_lines(self):
        self.note("Alpha", body="Texto [[Skill - Sincronização de\nConhecimento Recursiva]] fim.\n")
        self.assertEqual(self.checks(self.doctor(), "unresolved-link"), [])

    def test_resolves_folder_path_and_case_insensitive_links(self):
        self.note("Alpha", body="[[20_Permanent_Notes/Beta]] e [[beta]] e [[Beta.md]].\n")
        self.note("Beta")
        self.assertEqual(self.checks(self.doctor(), "unresolved-link"), [])

    def test_accepts_the_vault_note_types_and_project_statuses(self):
        self.note("Artigo", type_="article")
        self.note("Ficha", type_="literature-note")
        self.note("Conceito", type_="permanent")
        self.note("Feito", type_="project", extra="status: completed\n")
        self.note("Guardado", type_="project", extra="status: archived\n")
        self.assertEqual(self.checks(self.doctor(), "frontmatter"), [])

    def test_empty_note_is_a_warning_and_skips_the_other_checks(self):
        (self.vault / "Vazia.md").write_text("")
        issues = [i for i in self.doctor() if i.path == "Vazia.md"]
        self.assertEqual([(i.check, i.severity) for i in issues], [("empty-note", sb.WARN)])

    def test_template_placeholders_are_not_checked_but_secrets_still_are(self):
        self.note("Modelo", type_="article/book/paper", body="[[Alvo Inexistente]]\n", folder="90_Assets")
        self.assertEqual([i for i in self.doctor() if i.path.startswith("90_Assets/")], [])
        secret = SecretScanTest.SHAPES["GitHub token"]
        self.note("Modelo", folder="90_Assets", body=f"{secret}\n")
        self.assertEqual([i.check for i in self.doctor() if i.path.startswith("90_Assets/")], ["secret"])

    def test_reports_duplicate_titles_across_notes(self):
        self.note("Alpha", title="Mesmo Título")
        self.note("Beta", title="mesmo título")
        issues = self.checks(self.doctor(), "duplicate-title")
        self.assertEqual(len(issues), 1)
        self.assertIn("Beta.md", issues[0].detail)

    def test_duplicate_file_name_warns_only_when_a_bare_link_targets_it(self):
        self.note("indice", folder="40_Projects/a")
        self.note("indice", folder="40_Projects/b", body="[[a/indice]]\n")
        self.assertEqual(self.checks(self.doctor(), "duplicate-name"), [])
        self.note("Ref", body="Veja [[indice]].\n")
        issues = self.checks(self.doctor(), "duplicate-name")
        self.assertEqual(len(issues), 1)

    def test_reports_secret_without_echoing_it(self):
        secret = SecretScanTest.SHAPES["GitHub token"]
        self.note("Alpha", body=f"chave {secret}\n")
        issues = self.checks(self.doctor(), "secret")
        self.assertEqual(len(issues), 1)
        self.assertNotIn(secret, issues[0].detail)

    def test_reports_missing_frontmatter_and_bad_values(self):
        self.note("Sem", frontmatter=False)
        self.note("Tipo", type_="coisa", extra="confidence: certa\n")
        details = " | ".join(i.detail for i in self.checks(self.doctor(), "frontmatter"))
        self.assertIn("no frontmatter block", details)
        self.assertIn("unknown type `coisa`", details)
        self.assertIn("`confidence: certa`", details)

    def test_supersedes_must_point_to_an_existing_note(self):
        self.note("Novo", extra="supersedes: [[Antigo]]\n")
        self.note("Orfa", extra="supersedes: [[Inexistente]]\n")
        self.note("Antigo", extra="status: superseded\n")
        errors = [i for i in self.checks(self.doctor(), "supersedes") if i.severity == sb.ERROR]
        self.assertEqual([i.path.endswith("Orfa.md") for i in errors], [True])

    def test_superseded_note_without_a_successor_is_a_warning(self):
        self.note("Antigo", extra="status: superseded\n")
        issues = self.checks(self.doctor(), "supersedes")
        self.assertEqual([i.severity for i in issues], [sb.WARN])

    def test_stale_uses_verified_then_created(self):
        self.note("Velha", type_="pattern", created="2025-01-01")
        self.note("Verificada", type_="trap", created="2025-01-01", extra="verified: 2026-10-01 via teste\n")
        stale = self.checks(self.doctor(), "stale")
        self.assertEqual([i.path for i in stale], ["20_Permanent_Notes/Velha.md"])

    def test_manifest_drift_is_a_warning(self):
        self.note("Alpha")
        gm.write_manifests(self.vault)
        self.note("Beta")
        drift = self.checks(sb.run_doctor(self.vault, 180, TODAY), "manifest-drift")
        self.assertEqual([i.severity for i in drift], [sb.WARN])

    def test_cli_exit_code_and_json(self):
        self.note("Alpha", type_="coisa")
        gm.write_manifests(self.vault)
        result = subprocess.run(
            [sys.executable, str(SB), "doctor", "--vault-path", str(self.vault), "--json"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 1)
        self.assertEqual([i["check"] for i in json.loads(result.stdout)], ["frontmatter"])

    def test_cli_exit_zero_when_only_warnings(self):
        self.note("Velha", type_="pattern", created="2020-01-01")
        gm.write_manifests(self.vault)
        result = subprocess.run(
            [sys.executable, str(SB), "doctor", "--vault-path", str(self.vault)], capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("warn stale: 1", result.stdout)

    def test_report_is_capped_per_check(self):
        for i in range(5):
            self.note(f"N{i}", body=f"[[Falta{i}]]\n")
        text = sb.format_doctor(self.doctor(), limit=2)
        self.assertIn("... +3 more", text)


class StatusAndSearchTest(VaultFixture):
    def test_status_reports_counts_kill_switch_and_last_sync(self):
        self.note("Alpha")
        self.note("Padrao", type_="pattern")
        gm.write_manifests(self.vault)
        (self.state / "DISABLED").write_text("")
        (self.state / "sync.jsonl").write_text(
            json.dumps({"ts": "2026-10-15T14:00:00Z", "outcome": "synced", "sha": "abcdef1234567"}) + "\n"
        )
        text = sb.run_status(self.vault, self.state, {"SECOND_BRAIN_HOOKS": "1"})
        self.assertIn("notes: 2 (concept 1, pattern 1)", text)
        self.assertIn("manifests: ok", text)
        self.assertIn("SECOND_BRAIN_HOOKS=1", text)
        self.assertIn("kill-switch=ON", text)
        self.assertIn("last sync: 2026-10-15T14:00:00Z synced abcdef1", text)

    def test_status_with_no_state_and_no_git(self):
        self.note("Alpha")
        text = sb.run_status(self.vault, self.state, {})
        self.assertIn("kill-switch=off", text)
        self.assertIn("last sync: none", text)
        self.assertIn("SECOND_BRAIN_HOOKS=unset", text)

    def test_search_prints_the_same_tsv_as_the_ranker(self):
        self.note("Subagentes Gastam Contexto", title="Subagentes Gastam Contexto", body="Subagentes e contexto.\n")
        self.note("Outra Coisa", title="Receita de Pão")
        gm.write_manifests(self.vault)
        result = subprocess.run(
            [sys.executable, str(SB), "search", "--vault-path", str(self.vault), "-k", "3", "subagentes", "contexto"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0)
        rows = [line.split("\t") for line in result.stdout.splitlines()]
        self.assertEqual([r[1] for r in rows], ["20_Permanent_Notes/Subagentes Gastam Contexto.md"])

    def test_search_with_no_match_is_silent_and_exits_zero(self):
        self.note("Alpha")
        gm.write_manifests(self.vault)
        result = subprocess.run(
            [sys.executable, str(SB), "search", "--vault-path", str(self.vault), "zzzzzzzz"],
            capture_output=True, text=True,
        )
        self.assertEqual((result.returncode, result.stdout), (0, ""))


class SearchJsonTest(VaultFixture):
    EXPECTED_TSV = b'4.352\t20_Permanent_Notes/Subagentes Gastam Contexto.md\tSubagentes Gastam Contexto\t1.000\tmedium\n1.410\t20_Permanent_Notes/Contexto de Agentes.md\tContexto de Agentes\t0.324\t\n'

    def _corpus(self):
        self.note("Subagentes Gastam Contexto", title="Subagentes Gastam Contexto", type_="trap",
                  extra="confidence: medium\n", body="Subagentes gastam contexto quando usam a|b no shell.\n")
        self.note("Contexto de Agentes", title="Contexto de Agentes", type_="pattern", body="Agentes e contexto.\n")
        self.note("Receita de Pão", title="Receita de Pão", type_="concept")
        gm.write_manifests(self.vault)

    def _sb(self, *args, vault=None, text=False):
        vault = vault if vault is not None else self.vault
        return subprocess.run([sys.executable, str(SB), "search", "--vault-path", str(vault), *args],
                              capture_output=True, text=text)

    def _json(self, *query, k="3", vault=None):
        result = self._sb("--json", "-k", k, *query, vault=vault, text=True)
        self.assertEqual(result.returncode, 0)
        return json.loads(result.stdout)

    def _ranker(self, query, k="3"):
        env = {**os.environ, "SECOND_BRAIN_MANIFEST_DIR": str(self.vault / "00_META/manifests/by_type")}
        return subprocess.run(["bash", str(SB.parent / "vault_rank.sh"), "-k", k, "--", query],
                              capture_output=True, env=env, stdin=subprocess.DEVNULL)

    def test_tsv_is_byte_identical_to_the_ranker(self):
        self._corpus()
        result = self._sb("-k", "3", "subagentes", "contexto")
        rank = self._ranker("subagentes contexto")
        self.assertEqual(result.returncode, 0)
        self.assertTrue(result.stdout)
        self.assertEqual(result.stdout, rank.stdout)

    def test_tsv_snapshot_is_unchanged(self):
        self._corpus()
        self.assertEqual(self._sb("-k", "3", "subagentes", "contexto").stdout, self.EXPECTED_TSV)

    def test_tsv_without_vault_is_silent(self):
        result = self._sb("zzzzzzzz", vault=Path(self._tmp.name) / "nope")
        self.assertEqual((result.returncode, result.stdout), (0, b""))

    def test_json_fields_order_and_types(self):
        self._corpus()
        first = self._json("subagentes", "contexto")[0]
        self.assertEqual(list(first), ["path", "title", "type", "summary", "coverage", "confidence", "score", "terms"])
        self.assertEqual([type(v) for v in first.values()], [str, str, str, str, float, str, float, int])
        self.assertTrue(0 <= first["coverage"] <= 1)
        self.assertEqual(first["terms"], 2)

    def test_json_matches_the_tsv_rows(self):
        self._corpus()
        rows = [line.split("\t") for line in self._ranker("subagentes contexto").stdout.decode().splitlines()]
        hits = self._json("subagentes", "contexto")
        self.assertEqual([h["path"] for h in hits], [r[1] for r in rows])
        self.assertEqual([h["score"] for h in hits], [float(r[0]) for r in rows])
        self.assertEqual([h["coverage"] for h in hits], [float(r[3]) for r in rows])
        self.assertEqual([h["confidence"] for h in hits], [r[4] for r in rows])

    def test_json_joins_type_and_summary_from_the_manifest(self):
        self._corpus()
        by_title = {h["title"]: h for h in self._json("subagentes", "contexto")}
        trap = by_title["Subagentes Gastam Contexto"]
        self.assertEqual((trap["type"], trap["confidence"]), ("trap", "medium"))
        self.assertIn("a¦b", trap["summary"])
        self.assertEqual(by_title["Contexto de Agentes"]["confidence"], "")

    def test_json_no_match_prints_empty_list(self):
        self._corpus()
        result = self._sb("--json", "zzzzzzzz", text=True)
        self.assertEqual((result.returncode, result.stdout), (0, "[]\n"))

    def test_json_query_without_useful_terms_prints_empty_list(self):
        self._corpus()
        self.assertEqual(self._json("de uma com"), [])

    def test_json_missing_vault_prints_empty_list(self):
        result = self._sb("--json", "zzzzzzzz", vault=Path(self._tmp.name) / "nope", text=True)
        self.assertEqual((result.returncode, result.stdout), (0, "[]\n"))

    def test_json_respects_k(self):
        self._corpus()
        self.assertEqual(len(self._json("subagentes", "contexto", k="1")), 1)

    def test_rank_json_keeps_a_hit_missing_from_the_manifest(self):
        self.assertEqual(
            sb.rank_json("1.500\tX.md\tX\t0.500\tlow\t2\n", {}),
            [{"path": "X.md", "title": "X", "type": "", "summary": "", "coverage": 0.5, "confidence": "low",
              "score": 1.5, "terms": 2}],
        )

    def test_rank_json_skips_malformed_lines(self):
        self.assertEqual(sb.rank_json("lixo\n1.0\tA.md\tA\n", {}), [])

    def test_read_manifest_rows_round_trip(self):
        self._corpus()
        rows = gm.read_manifest_rows(self.vault / "00_META/manifests/by_type")
        self.assertEqual(len(rows), 3)
        trap = rows["20_Permanent_Notes/Subagentes Gastam Contexto.md"]
        body = "Subagentes gastam contexto quando usam a|b no shell.\n"
        self.assertEqual((trap["type"], trap["confidence"]), ("trap", "medium"))
        self.assertEqual(trap["summary"], gm.extract_summary(body).replace("|", "¦"))

    def test_read_manifest_rows_strips_shard_suffix(self):
        header = "| Path | Title | Tags | Created | Provenance | Confidence | Seen_in | Summary |\n"
        sep = "|---|---|---|---|---|---|---|---|\n"
        out = Path(self._tmp.name) / "by_type"
        (out / "sub").mkdir(parents=True)
        for name in ("pattern_2026H2.md", "pattern_unknown-2.md", "article-book-paper.md", "sub/other.md"):
            stem = name.replace("/", "_")
            (out / name).write_text(header + sep + f"| {stem} | T | a | 2026-10-01 | | | | S |\n", encoding="utf-8")
        (out / "ignored.txt").write_text(header + sep + "| ignored.txt | T | a | 2026-10-01 | | | | S |\n")
        rows = gm.read_manifest_rows(out)
        self.assertEqual({p: r["type"] for p, r in rows.items()},
                         {"pattern_2026H2.md": "pattern", "pattern_unknown-2.md": "pattern",
                          "article-book-paper.md": "article-book-paper"})


class SyncDoctorReportTest(VaultFixture):
    def run_report(self, notes):
        import contextlib
        import io
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            sb.report_note_issues(self.vault, notes)
        return out.getvalue()

    def test_synced_notes_reads_both_note_spellings(self):
        rest = ["--note", "a.md", "--project-name", "p", "--note=b.md"]
        self.assertEqual(sb.synced_notes(rest), {"a.md", "b.md"})

    def test_reports_only_issues_on_the_synced_notes(self):
        self.note("Alpha", body="Real [[Fantasma]].\n")
        self.note("Beta", body="Outro [[Sumido]].\n")
        text = self.run_report({"20_Permanent_Notes/Alpha.md"})
        self.assertIn("Fantasma", text)
        self.assertNotIn("Sumido", text)

    def test_clean_synced_note_says_so(self):
        self.note("Alpha")
        self.assertIn("no issues", self.run_report({"20_Permanent_Notes/Alpha.md"}))


if __name__ == "__main__":
    unittest.main()
