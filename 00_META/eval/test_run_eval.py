"""Testes do harness: python3 -m unittest discover -s 00_META/eval -v"""

import json
import math
import tempfile
import unittest
from pathlib import Path

import run_eval as ev


class ScoreQueryTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.vault = Path(self.tmp.name)
        for name in ("a.md", "b.md", "c.md"):
            (self.vault / name).write_text("x" * 350, encoding="utf-8")  # 100 tokens cada

    def tearDown(self):
        self.tmp.cleanup()

    def test_hit_at_rank_two_gives_half_mrr_and_opens_two_notes(self):
        query = ev.Query("q", "t", "lexical", {"b.md": 2})
        m = ev.score_query(query, ["a.md", "b.md", "c.md"], 3, self.vault)
        self.assertEqual(m["success"], 1.0)
        self.assertEqual(m["mrr"], 0.5)
        self.assertGreaterEqual(m["tokens"], 200)  # abriu a.md e b.md
        self.assertLess(m["tokens"], 300)

    def test_miss_opens_all_k_notes(self):
        query = ev.Query("q", "t", "lexical", {"z.md": 2})
        m = ev.score_query(query, ["a.md", "b.md"], 2, self.vault)
        self.assertEqual((m["success"], m["mrr"], m["recall"]), (0.0, 0.0, 0.0))
        self.assertGreaterEqual(m["tokens"], 200)

    def test_ndcg_perfect_when_grade2_first(self):
        query = ev.Query("q", "t", "multihop", {"a.md": 2, "b.md": 1})
        self.assertAlmostEqual(ev.score_query(query, ["a.md", "b.md"], 2, self.vault)["ndcg"], 1.0)

    def test_ndcg_penalizes_swapped_order(self):
        query = ev.Query("q", "t", "multihop", {"a.md": 2, "b.md": 1})
        got = ev.score_query(query, ["b.md", "a.md"], 2, self.vault)["ndcg"]
        want = ev.dcg([1, 2]) / ev.dcg([2, 1])
        self.assertAlmostEqual(got, want)
        self.assertLess(got, 1.0)

    def test_negative_query_flags_any_result_as_false_positive(self):
        query = ev.Query("q", "t", "negative", {})
        self.assertEqual(ev.score_query(query, ["a.md"], 3, self.vault)["returned_any"], 1.0)
        self.assertEqual(ev.score_query(query, [], 3, self.vault)["returned_any"], 0.0)


class BootstrapTest(unittest.TestCase):
    def test_ci_bounds_contain_mean_and_stay_in_unit_interval(self):
        values = [1.0] * 8 + [0.0] * 2
        lo, hi = ev.bootstrap_ci(values)
        self.assertLessEqual(lo, 0.8)
        self.assertGreaterEqual(hi, 0.8)
        self.assertTrue(0.0 <= lo <= hi <= 1.0)

    def test_ci_is_deterministic(self):
        values = [1.0, 0.0, 1.0, 1.0, 0.0]
        self.assertEqual(ev.bootstrap_ci(values), ev.bootstrap_ci(values))

    def test_empty_values(self):
        self.assertEqual(ev.bootstrap_ci([]), (0.0, 0.0))


class GoldenFileTest(unittest.TestCase):
    def test_real_golden_is_valid_and_labels_exist(self):
        queries = ev.load_golden(split="all")
        self.assertGreaterEqual(len(queries), 30)
        self.assertTrue(any(q.kind == "negative" for q in queries))

    def test_split_dev_and_test_partition_the_active_queries(self):
        dev = {q.id for q in ev.load_golden(split="dev")}
        test = {q.id for q in ev.load_golden(split="test")}
        self.assertFalse(dev & test)
        self.assertEqual(dev | test, {q.id for q in ev.load_golden(split="all")})

    def test_missing_label_path_fails_loudly(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "g.jsonl"
            row = {"id": "q1", "query": "x", "kind": "lexical", "split": "dev", "status": "active",
                   "relevant": [{"path": "nao/existe.md", "grade": 2}]}
            bad.write_text(json.dumps(row) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "inexistente"):
                ev.load_golden(bad)

    def test_duplicate_id_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "g.jsonl"
            row = {"id": "q1", "query": "x", "kind": "negative", "split": "dev", "status": "active", "relevant": []}
            bad.write_text((json.dumps(row) + "\n") * 2, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicado"):
                ev.load_golden(bad)


class RankerContractTest(unittest.TestCase):
    def test_ranker_returns_at_most_k_tsv_lines_and_silence_on_noise(self):
        adapter = ev.RankAdapter()
        self.assertLessEqual(len(adapter.search("jira importar issues csv", 3)), 3)
        self.assertEqual(adapter.search("zzzzqqqq xxxxwwww", 3), [])

    def test_ranker_survives_backslashes_and_quotes(self):
        self.assertIsInstance(ev.RankAdapter().search('regex \\d+ "quote" $x', 3), list)

    def test_fixed_adapter_is_constant_and_random_varies(self):
        paths = [f"p{i}.md" for i in range(50)]
        fixed = ev.FixedAdapter(paths)
        self.assertEqual(fixed.search("a", 5), fixed.search("b", 5))
        rnd = ev.RandomAdapter(paths)
        self.assertNotEqual(rnd.search("a", 5), rnd.search("a", 5))

class RrfTest(unittest.TestCase):
    def test_fuse_orders_by_summed_reciprocal_rank(self):
        out = ev.rrf_fuse([["a", "b", "c"], ["b", "a", "d"], ["b", "e"]])
        self.assertEqual(out, ["b", "a", "e", "c", "d"])
        self.assertAlmostEqual(1 / 61 + 1 / 62 + 1 / 61, 2 / 61 + 1 / 62)

    def test_tie_breaks_by_lowest_variant_index(self):
        self.assertEqual(ev.rrf_fuse([["x"], ["y"]]), ["x", "y"])
        self.assertEqual(ev.rrf_fuse([["y"], ["x"]]), ["y", "x"])

    def test_empty_inputs(self):
        self.assertEqual(ev.rrf_fuse([]), [])
        self.assertEqual(ev.rrf_fuse([[], []]), [])


class RewriteAdapterTest(unittest.TestCase):
    def test_calls_original_and_each_rewrite_with_depth(self):
        calls = []

        def fake(query, k):
            calls.append((query, k))
            return ["a.md", "b.md", "c.md"]

        adapter = ev.RewriteAdapter({"q": ["r1", "r2"]}, search_fn=fake)
        out = adapter.search("q", 2)
        self.assertEqual(calls, [("q", 10), ("r1", 10), ("r2", 10)])
        self.assertLessEqual(len(out), 2)

    def test_silence_when_all_variants_empty(self):
        adapter = ev.RewriteAdapter({"q": ["r1", "r2"]}, search_fn=lambda q, k: [])
        self.assertEqual(adapter.search("q", 5), [])

    def test_threshold_goes_to_inner_rank_adapter(self):
        adapter = ev.RewriteAdapter({"q": ["r"]}, min_coverage=0.35, min_terms=2)
        self.assertEqual(adapter._search.__self__._flags, ["-c", "0.35", "-t", "2"])

    def test_unknown_query_fails_loudly(self):
        adapter = ev.RewriteAdapter({"q": ["r"]}, search_fn=lambda q, k: [])
        with self.assertRaisesRegex(ValueError, "sem reformulação"):
            adapter.search("outra", 5)


def _rw_row(id_, query, rewrites=("r1", "r2", "r3"), created="2026-10-22"):
    return {"id": id_, "query": query, "rewrites": list(rewrites), "model": "claude-haiku-x", "created": created}


class LoadRewritesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "rewrites.jsonl"
        self.queries = [ev.Query("q1", "texto q1", "lexical", {"a.md": 2}), ev.Query("q2", "texto q2", "lexical", {"a.md": 2})]
        self.known = {"q1", "q2", "q3"}

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, *rows):
        self.path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")

    def load(self, queries=None):
        return ev.load_rewrites(self.path, self.queries if queries is None else queries, self.known)

    def test_valid_file_returns_map_by_text(self):
        self.write(_rw_row("q1", "texto q1"), _rw_row("q2", "texto q2"))
        self.assertEqual(self.load()["texto q1"], ["r1", "r2", "r3"])

    def test_extra_row_from_other_split_is_accepted(self):
        self.write(_rw_row("q1", "texto q1"), _rw_row("q3", "texto q3"))
        self.assertEqual(self.load(self.queries[:1]), {"texto q1": ["r1", "r2", "r3"]})

    def test_missing_line(self):
        self.write(_rw_row("q1", "texto q1"))
        with self.assertRaisesRegex(ValueError, "falta linha"):
            self.load()

    def test_query_diverges(self):
        self.write(_rw_row("q1", "outro texto"), _rw_row("q2", "texto q2"))
        with self.assertRaisesRegex(ValueError, "diverge"):
            self.load()

    def test_duplicate_id(self):
        self.write(_rw_row("q1", "texto q1"), _rw_row("q1", "texto q1"))
        with self.assertRaisesRegex(ValueError, "duplicado"):
            self.load()

    def test_unknown_id(self):
        self.write(_rw_row("q1", "texto q1"), _rw_row("q2", "texto q2"), _rw_row("q99", "x"))
        with self.assertRaisesRegex(ValueError, "desconhecido"):
            self.load()

    def test_bad_rewrite_counts_and_content(self):
        for bad in (["r1"], ["r1", "r2", "r3", "r4"], ["r1", "R1"], ["r1", "texto q1"], ["r1", " "]):
            self.write(_rw_row("q1", "texto q1", bad), _rw_row("q2", "texto q2"))
            with self.assertRaisesRegex(ValueError, "rewrites inválidas"):
                self.load()

    def test_bad_created_and_missing_fields(self):
        self.write(_rw_row("q1", "texto q1", created="22/10/2026"), _rw_row("q2", "texto q2"))
        with self.assertRaisesRegex(ValueError, "created"):
            self.load()
        self.write({"id": "q1"})
        with self.assertRaisesRegex(ValueError, "faltam campos"):
            self.load()


class BuildAdaptersRewriteTest(unittest.TestCase):
    def test_missing_file_exits_with_hint(self):
        with self.assertRaisesRegex(SystemExit, "gen_rewrites.py"):
            ev.build_adapters(["rewrite"], rewrites_path=Path("/nonexistent/rewrites.jsonl"), queries=[])

    def test_rank_does_not_need_file(self):
        self.assertEqual([a.name for a in ev.build_adapters(["rank"])], ["rank"])


@unittest.skipUnless(ev.REWRITES.is_file(), "rewrites.jsonl ainda não gerado")
class RealRewritesTest(unittest.TestCase):
    def test_real_file_valid_for_dev(self):
        ids = {q.id for q in ev.load_golden(split="all")}
        ev.load_rewrites(ev.REWRITES, ev.load_golden(split="dev"), ids)


if __name__ == "__main__":
    unittest.main()
