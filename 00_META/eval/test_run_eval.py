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


if __name__ == "__main__":
    unittest.main()
