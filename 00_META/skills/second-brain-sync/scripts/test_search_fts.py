"""Tests of the SQLite FTS5 index and `sb search`: python3 -m pytest 00_META/skills/second-brain-sync/scripts/test_search_fts.py"""
from __future__ import annotations

import json
import os
import sqlite3
import statistics
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import generate_manifests as gm  # noqa: E402
import sb  # noqa: E402
import vault_index as vi  # noqa: E402

SB = HERE / "sb.py"


class IndexFixture(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.vault = Path(self._tmp.name) / "vault"
        (self.vault / "20_Permanent_Notes").mkdir(parents=True)
        env = {"SECOND_BRAIN_STATE_DIR": str(Path(self._tmp.name) / "state")}
        patcher = mock.patch.dict(os.environ, env)
        patcher.start()
        self.addCleanup(patcher.stop)
        for var in ("SECOND_BRAIN_INDEX", "SECOND_BRAIN_INDEX_PATH"):
            os.environ.pop(var, None)
        self.db = self.vault / vi.INDEX_RELPATH

    def note(self, name, *, title=None, type_="concept", tags="a", confidence="", body="Corpo da nota.\n"):
        path = self.vault / "20_Permanent_Notes" / f"{name}.md"
        conf = f"confidence: {confidence}\n" if confidence else ""
        path.write_text(f"---\ntitle: {title or name}\ntype: {type_}\ntags: [{tags}]\ncreated: 2026-10-01\n{conf}---\n\n{body}",
                        encoding="utf-8")
        return path

    def corpus(self):
        self.note("Subagentes Gastam Contexto", title="Subagentes Gastam Contexto", type_="trap", confidence="medium",
                  body="Subagentes gastam contexto quando usam a|b no shell.\n")
        self.note("Contexto de Agentes", title="Contexto de Agentes", type_="pattern", body="Agentes e contexto.\n")
        self.note("Receita de Pão", title="Receita de Pão", type_="concept", tags="culinaria",
                  body="Farinha, água e fermento para o pão.\n")
        self.note("Anotacao Qualquer", title="Anotação qualquer", body="Aqui se fala de subagentes de passagem, uma vez.\n")
        return vi.build_index(self.vault)


class BuildIndexTest(IndexFixture):
    def test_builds_the_index_from_notes_and_returns_the_count(self):
        self.assertEqual(self.corpus(), 4)
        self.assertTrue(self.db.is_file())
        with sqlite3.connect(self.db) as conn:
            self.assertEqual(conn.execute("SELECT count(*) FROM notes_fts").fetchone()[0], 4)

    def test_is_atomic_and_leaves_no_temp_file(self):
        self.corpus()
        self.assertEqual([p.name for p in self.db.parent.iterdir()], ["index.sqlite"])

    def test_rebuild_replaces_the_content_and_drops_deleted_notes(self):
        self.corpus()
        (self.vault / "20_Permanent_Notes" / "Receita de Pão.md").unlink()
        self.assertEqual(vi.build_index(self.vault), 3)
        self.assertEqual(vi.search_fts("farinha", self.db), [])

    def test_a_failed_build_keeps_the_previous_index(self):
        self.corpus()
        with mock.patch.object(gm.frontmatter, "read_note", side_effect=RuntimeError("boom")):
            with self.assertRaises(RuntimeError):
                vi.build_index(self.vault)
        self.assertEqual(vi.search_fts("farinha", self.db)[0]["title"], "Receita de Pão")
        self.assertFalse(self.db.with_name("index.sqlite.tmp").exists())

    def test_custom_db_path_by_argument_and_by_env(self):
        self.note("A")
        other = Path(self._tmp.name) / "x" / "custom.sqlite"
        vi.build_index(self.vault, other)
        self.assertTrue(other.is_file())
        with mock.patch.dict(os.environ, {"SECOND_BRAIN_INDEX_PATH": str(other)}):
            self.assertEqual(vi.default_db_path(self.vault), other)
        self.assertEqual(vi.default_db_path(self.vault), self.db)

    def test_empty_notes_are_skipped(self):
        (self.vault / "20_Permanent_Notes" / "vazia.md").write_text("")
        self.note("Cheia")
        self.assertEqual(vi.build_index(self.vault), 1)

    def test_write_manifests_builds_the_index(self):
        self.corpus()
        self.db.unlink()
        gm.write_manifests(self.vault)
        self.assertEqual(len(vi.search_fts("subagentes", self.db)), 2)

    def test_write_manifests_does_not_build_it_when_disabled(self):
        self.note("A")
        with mock.patch.dict(os.environ, {"SECOND_BRAIN_INDEX": "0"}):
            gm.write_manifests(self.vault)
        self.assertFalse(self.db.exists())

    def test_write_manifests_survives_an_index_failure(self):
        self.note("A")
        with mock.patch.object(vi, "build_index", side_effect=sqlite3.OperationalError("no such module: fts5")):
            self.assertTrue(gm.write_manifests(self.vault))
        self.assertTrue((self.vault / "00_META/manifests/INDEX.md").is_file())


class SearchFtsTest(IndexFixture):
    def setUp(self):
        super().setUp()
        self.corpus()

    def paths(self, query, **kw):
        return [h["path"].rsplit("/", 1)[-1][:-3] for h in vi.search_fts(query, self.db, **kw)]

    def test_exact_single_term(self):
        self.assertEqual(self.paths("farinha"), ["Receita de Pão"])

    def test_multiple_terms_require_all_of_them(self):
        self.assertEqual(self.paths("subagentes contexto"), ["Subagentes Gastam Contexto"])

    def test_falls_back_to_any_term_with_partial_coverage(self):
        hits = vi.search_fts("subagentes farinha", self.db)
        self.assertEqual({h["path"].rsplit("/", 1)[-1] for h in hits},
                         {"Subagentes Gastam Contexto.md", "Anotacao Qualquer.md", "Receita de Pão.md"})
        self.assertTrue(all(h["coverage"] == 0.5 and h["terms"] == 2 for h in hits))

    def test_title_and_tags_rank_above_a_body_mention(self):
        self.note("Sobre Pipelines", title="Pipelines de dados", body="Texto neutro.\n")
        self.note("Texto Longo", title="Outro assunto", body="Fala de pipelines uma vez no corpo.\n")
        self.note("Etiquetada", title="Sem relacao", tags="pipelines", body="Texto neutro.\n")
        vi.build_index(self.vault)
        order = self.paths("pipelines")
        self.assertEqual(order[0], "Sobre Pipelines")
        self.assertLess(order.index("Etiquetada"), order.index("Texto Longo"))

    def test_title_match_beats_body_only_match(self):
        self.assertEqual(self.paths("subagentes", limit=5)[:2], ["Subagentes Gastam Contexto", "Anotacao Qualquer"])

    def test_scores_are_non_negative_and_sorted_best_first(self):
        scores = [h["score"] for h in vi.search_fts("subagentes", self.db)]
        self.assertTrue(all(s >= 0 for s in scores))  # idf is floored near 0 in tiny corpora
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_accents_and_case_are_folded_and_prefix_matches(self):
        self.assertEqual(self.paths("PAO"), ["Receita de Pão"])
        self.assertEqual(self.paths("agente"), ["Contexto de Agentes"])

    def test_hit_has_the_search_fields(self):
        hit = vi.search_fts("subagentes contexto", self.db)[0]
        self.assertEqual(set(sb.SEARCH_FIELDS), set(hit) & set(sb.SEARCH_FIELDS))
        self.assertEqual((hit["type"], hit["confidence"], hit["coverage"], hit["terms"]), ("trap", "medium", 1.0, 2))
        self.assertIn("Subagentes gastam contexto", hit["summary"])

    def test_limit(self):
        self.assertEqual(len(vi.search_fts("subagentes", self.db, limit=1)), 1)
        self.assertEqual(vi.search_fts("subagentes", self.db, limit=0), [])

    def test_explicit_boolean_operators(self):
        self.assertEqual(sorted(self.paths("farinha OR contexto")),
                         ["Contexto de Agentes", "Receita de Pão", "Subagentes Gastam Contexto"])
        self.assertEqual(self.paths("subagentes AND contexto"), ["Subagentes Gastam Contexto"])

    def test_hostile_queries_never_raise(self):
        for query in ['"', "'", "(", "a OR", "AND", "NOT x", "foo*bar", "col:foo", "-x", "^y", 'a"b', "title:", "NEAR(a b)",
                      "\\", ";", "💥", "   ", ""]:
            with self.subTest(query=query):
                self.assertIsInstance(vi.search_fts(query, self.db), list)

    def test_no_match_returns_empty(self):
        self.assertEqual(vi.search_fts("zzzzzzzz", self.db), [])

    def test_missing_database_raises_a_sqlite_error(self):
        with self.assertRaises(sqlite3.Error):
            vi.search_fts("x", self.vault / "nope.sqlite")

    def test_build_match_quotes_everything(self):
        self.assertEqual(vi.build_match('foo"bar'), '"foo"* AND "bar"*')
        self.assertEqual(vi.build_match("a b", "or"), '"a" OR "b"')

    def test_latency_is_under_10ms(self):
        for i in range(400):  # a vault-sized index, not the 4 notes of the fixture
            self.note(f"Nota {i}", title=f"Nota numero {i} sobre agentes e contexto", tags="agentes, memoria",
                      body=("Texto de preenchimento sobre subagentes, tokens e economia de contexto. " * 40) + "\n")
        vi.build_index(self.vault)
        for query in ("contexto", "subagentes contexto", "economia de tokens memoria"):
            vi.search_fts(query, self.db)  # warm-up
            runs = []
            for _ in range(30):
                start = time.perf_counter()
                vi.search_fts(query, self.db, limit=5)
                runs.append((time.perf_counter() - start) * 1000)
            median = statistics.median(runs)
            print(f"\nbenchmark {query!r}: median {median:.2f} ms, max {max(runs):.2f} ms over {len(runs)} runs", end="")
            self.assertLess(median, 10, query)


class SbSearchTest(IndexFixture):
    def sb(self, *args, env=None):
        return subprocess.run([sys.executable, str(SB), "search", "--vault-path", str(self.vault), *args],
                              capture_output=True, text=True, env={**os.environ, **(env or {})})

    def test_uses_the_index_and_prints_tsv(self):
        self.corpus()
        result = self.sb("-k", "3", "subagentes", "contexto")
        self.assertEqual(result.returncode, 0)
        rows = [line.split("\t") for line in result.stdout.splitlines()]
        self.assertEqual([r[1] for r in rows], ["20_Permanent_Notes/Subagentes Gastam Contexto.md"])
        self.assertEqual(len(rows[0]), 5)
        self.assertEqual(rows[0][4], "medium")
        self.assertEqual(result.stdout, vi.format_tsv(vi.search_fts("subagentes contexto", self.db, 3)))

    def test_json_has_the_search_fields(self):
        self.corpus()
        hits = json.loads(self.sb("--json", "-k", "3", "subagentes", "contexto").stdout)
        self.assertEqual(list(hits[0]), list(sb.SEARCH_FIELDS))
        self.assertEqual((hits[0]["type"], hits[0]["terms"]), ("trap", 2))

    def test_falls_back_to_the_ranker_when_there_is_no_index(self):
        self.note("Subagentes Gastam Contexto", title="Subagentes Gastam Contexto", body="Subagentes e contexto.\n")
        with mock.patch.dict(os.environ, {"SECOND_BRAIN_INDEX": "0"}):
            gm.write_manifests(self.vault)
        self.assertFalse(self.db.exists())
        result = self.sb("-k", "3", "subagentes", "contexto")
        env = {**os.environ, "SECOND_BRAIN_MANIFEST_DIR": str(self.vault / "00_META/manifests/by_type")}
        rank = subprocess.run(["bash", str(HERE / "vault_rank.sh"), "-k", "3", "--", "subagentes contexto"],
                              capture_output=True, text=True, env=env, stdin=subprocess.DEVNULL)
        self.assertTrue(result.stdout)
        self.assertEqual((result.returncode, result.stdout), (0, rank.stdout))
        self.assertEqual(json.loads(self.sb("--json", "subagentes").stdout)[0]["title"], "Subagentes Gastam Contexto")

    def test_falls_back_when_the_index_is_corrupt(self):
        self.note("Subagentes Gastam Contexto", title="Subagentes Gastam Contexto", body="Subagentes e contexto.\n")
        with mock.patch.dict(os.environ, {"SECOND_BRAIN_INDEX": "0"}):
            gm.write_manifests(self.vault)
        self.db.write_bytes(b"not a sqlite database" * 100)
        result = self.sb("subagentes", "contexto")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Subagentes Gastam Contexto", result.stdout)

    def test_kill_switch_ignores_an_existing_index(self):
        self.corpus()
        self.assertEqual(self.sb("farinha", env={"SECOND_BRAIN_INDEX": "0"}).stdout, "")  # no manifests, no ranker rows
        self.assertTrue(self.sb("farinha").stdout)

    def test_reindex_builds_the_index_and_picks_up_new_notes(self):
        self.note("Antiga")
        self.assertFalse(self.db.exists())
        self.assertEqual(self.sb("--reindex", "zzzzzz").stdout, "")
        self.assertTrue(self.db.is_file())
        self.note("Nova", title="Marmelada caseira")
        self.assertEqual(self.sb("marmelada").stdout, "")  # stale index until reindexed
        self.assertIn("Marmelada caseira", self.sb("--reindex", "marmelada").stdout)

    def test_no_match_is_silent_and_exits_zero(self):
        self.corpus()
        result = self.sb("zzzzzzzz")
        self.assertEqual((result.returncode, result.stdout), (0, ""))

    def test_run_search_lazy_imports_vault_index(self):
        code = ("import sys; sys.path.insert(0, %r); import sb; assert 'vault_index' not in sys.modules; "
                "assert 'sqlite3' not in sys.modules" % str(HERE))
        self.assertEqual(subprocess.run([sys.executable, "-c", code]).returncode, 0)


if __name__ == "__main__":
    unittest.main()
