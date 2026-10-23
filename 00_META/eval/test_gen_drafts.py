"""Testes do gerador de rascunhos, sem rede: python3 -m unittest discover -s 00_META/eval -v"""

import contextlib
import io
import json
import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import gen_drafts as gd
import gen_rewrites as gr
import run_eval as ev
import validate_golden as vg

FAKE = r'''#!/usr/bin/env python3
import json, os, sys
mode = os.environ.get("FAKE_MODE", "positive")
stdin = sys.stdin.read()
cap = os.environ.get("FAKE_CAPTURE")
if cap:
    json.dump({"argv": sys.argv, "cwd": os.getcwd(), "stdin": stdin, "env_keys": sorted(os.environ)}, open(cap, "w"))
counter = os.environ.get("FAKE_COUNTER")
n = 1
if counter:
    with open(counter, "a") as fh:
        fh.write("x\n")
    n = len(open(counter).read().splitlines())
if mode == "fail_if_called":
    sys.exit(3)
if mode == "fail_second" and n >= 2:
    sys.exit(3)
haiku = {"claude-haiku-4-5-20251001": {"inputTokens": 1}}
pos = {"query": "meu modelo local esquece o começo da conversa caso%d" % n, "lang": "pt"}
if mode == "same":
    pos = {"query": "meu modelo local esquece o começo da conversa", "lang": "pt"}
if mode == "golden_dup":
    pos = {"query": "Pergunta já existente no golden!", "lang": "pt"}
neg = {"queries": [
    {"query": "como configurar um cluster Kubernetes multi-região", "flavor": "far", "lang": "pt"},
    {"query": "como tunar índices no PostgreSQL com muitas escritas", "flavor": "near", "lang": "pt"},
    {"query": "por que meu grid CSS quebra no Safari", "flavor": "far", "lang": "pt"},
]}
if mode == "title_copy":
    body = {"query": "Ollama contexto grande demais", "lang": "pt"}
elif mode in ("negative", "neg_dup"):
    body = neg
else:
    body = pos
text = json.dumps(body)
if mode == "fenced":
    text = "```json\n" + text + "\n```"
env = {"type": "result", "subtype": "success", "is_error": False, "result": text, "modelUsage": haiku}
if mode == "sonnet":
    env["modelUsage"] = {"claude-sonnet-4-5": {"inputTokens": 1}}
print(json.dumps(env))
'''

HEADER = "| Path | Title | Tags | Created | Provenance | Confidence | Seen in | Summary |\n| --- | --- | --- | --- | --- | --- | --- | --- |\n"


def mrow(path, title, tags="docker, ollama", summary="Resumo da nota."):
    return f"| {path} | {title} | {tags} | 2026-01-01 | x |  |  | {summary} |\n"


def build_vault(root: Path) -> Path:
    mdir = root / "manifests"
    mdir.mkdir()
    pattern = HEADER
    for name in ("Alpha", "Beta", "Gamma", "Delta"):
        pattern += mrow(f"20_Permanent_Notes/{name}.md", f"Ollama Ignora Contexto Variante {name}")
    pattern += mrow("20_Permanent_Notes/SemResumo.md", "Ollama Sem Resumo", summary="")
    pattern += mrow("00_META/Interna.md", "Ollama Interna")
    pattern += "| 20_Permanent_Notes/Pipe.md | Ollama Pipe | docker | 2026-01-01 | x |  |  | resumo com | pipe dentro |\n"
    (mdir / "pattern.md").write_text(pattern, encoding="utf-8")
    (mdir / "project.md").write_text(HEADER + mrow("40_Projects/P.md", "Ollama Projeto"), encoding="utf-8")
    golden = root / "golden.jsonl"
    golden.write_text(
        json.dumps({"id": "q001", "query": "pergunta já existente no golden", "kind": "paraphrase", "split": "dev", "status": "active",
                    "relevant": [{"path": "20_Permanent_Notes/Delta.md", "grade": 2}]}) + "\n",
        encoding="utf-8",
    )  # fmt: skip
    return mdir


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.mdir = build_vault(self.root)
        self.golden = self.root / "golden.jsonl"
        self.drafts = self.root / "drafts.jsonl"
        fake = self.root / "fakeclaude"
        fake.write_text(FAKE, encoding="utf-8")
        fake.chmod(fake.stat().st_mode | stat.S_IXUSR | 0o755)
        self.fake = str(fake)
        self.cap = str(self.root / "cap.json")
        self.counter = str(self.root / "counter.txt")

    def calls(self):
        p = Path(self.counter)
        return len(p.read_text().splitlines()) if p.exists() else 0

    def run_main(self, args, mode="positive", **env):
        full = {"FAKE_MODE": mode, "FAKE_CAPTURE": self.cap, "FAKE_COUNTER": self.counter, **env}
        argv = [args[0], "--manifests", str(self.mdir), "--golden", str(self.golden), "--drafts", str(self.drafts),
                "--claude", self.fake, *args[1:]]  # fmt: skip
        buf = io.StringIO()
        with mock.patch.dict(os.environ, full), contextlib.redirect_stdout(buf):
            gd.main(argv)
        return buf.getvalue()

    def rows(self):
        if not self.drafts.exists():
            return []
        return [json.loads(x) for x in self.drafts.read_text(encoding="utf-8").splitlines() if x.strip()]


class TermsTest(unittest.TestCase):
    def test_rank_terms_uses_stoplist_from_ranker(self):
        self.assertIn("para", vg.stoplist())
        terms = vg.rank_terms("Para que serve o Ollama com GPU? Ação rápida")
        self.assertNotIn("para", terms)
        self.assertNotIn("gpu", terms)
        self.assertIn("ollama", terms)
        self.assertIn("acao", terms)

    def test_title_hits(self):
        self.assertEqual(vg.title_hits("Ollama ignora contexto", "Ollama Ignora Tamanho de Contexto"), 3)
        self.assertEqual(vg.title_hits("o agente falha", "Agentes Autônomos"), 1)
        self.assertEqual(vg.title_hits("nada a ver", "Ollama"), 0)


class PromptTest(Base):
    def test_positive_prompt_scope(self):
        forbidden = vg.rank_terms("Ollama Ignora Contexto Variante Alpha")
        prompt = gd.build_positive_prompt("Ollama Ignora Contexto Variante Alpha", "Resumo da nota.", forbidden)
        self.assertIn("Ollama Ignora Contexto Variante Alpha", prompt)
        self.assertIn("Resumo da nota.", prompt)
        for term in forbidden:
            self.assertIn(term, prompt)
        self.assertNotIn("Beta", prompt)
        self.assertNotIn(".md", prompt)
        self.assertNotIn("vault_rank", prompt)

    def test_negative_prompt_has_area_and_tags(self):
        prompt = gd.build_negative_prompt("frontend e CSS", ["docker", "ollama"])
        self.assertIn("frontend e CSS", prompt)
        self.assertIn("docker", prompt)
        self.assertIn("near", prompt)

    def test_static_no_ranker_or_shadow_internals(self):
        here = Path(__file__).parent
        for name in ("gen_drafts.py", "promote_drafts.py"):
            text = (here / name).read_text(encoding="utf-8")
            for bad in ("vault_rank", "RankAdapter", "RANKER", "prompt_hint", "candidates", "emitted"):
                self.assertNotIn(bad, text, f"{name} contém {bad}")


class ManifestTest(Base):
    def test_manifest_rows_skip_malformed(self):
        rows = gd.manifest_rows(self.mdir)
        paths = {r["path"] for r in rows}
        self.assertIn("20_Permanent_Notes/Alpha.md", paths)
        self.assertNotIn("20_Permanent_Notes/Pipe.md", paths)
        row = next(r for r in rows if r["path"].endswith("Alpha.md"))
        self.assertEqual(row["type"], "pattern")
        self.assertEqual(row["tags"], ["docker", "ollama"])

    def test_pool_filters(self):
        rows = gd.manifest_rows(self.mdir)
        pool = gd.positive_pool(rows, used_paths={"20_Permanent_Notes/Delta.md"}, drafted=set())
        self.assertEqual(sorted(r["path"] for r in pool), [f"20_Permanent_Notes/{n}.md" for n in ("Alpha", "Beta", "Gamma")])

    def test_top_tags(self):
        self.assertEqual(gd.top_tags(gd.manifest_rows(self.mdir), 1), ["docker"])


class ShadowFilterTest(unittest.TestCase):
    def test_filters(self):
        rows = [
            {"ts": "t1", "prompt": "<task-notification>quase tudo aqui dentro vira ruido</task-notification>"},
            {"ts": "t2", "prompt": "só cinco palavras aqui sim"},
            {"ts": "t3", "prompt": "q1. responda a pergunta sobre o assunto do projeto agora"},
            {"ts": "t4", "prompt": "a" * 300},
            {"ts": "t5", "prompt": "Como faço para reduzir o custo das chamadas do Haiku no eval?"},
            {"ts": "t6", "prompt": "como faco para reduzir o custo das chamadas do haiku no eval"},
            {"ts": "t7", "prompt": "  Por que o Ollama ignora o tamanho do contexto no modelo?  "},
            {"ts": "t8"},
        ]
        got = gd.filter_shadow(rows)
        self.assertEqual([ts for ts, _ in got], ["t5", "t7"])
        self.assertEqual(got[1][1], "Por que o Ollama ignora o tamanho do contexto no modelo?")


class ShadowCliTest(Base):
    def test_only_prompt_and_ts_are_read(self):
        sentinel = "SENTINELA-SECRETA"
        shadow = self.root / "shadow.jsonl"
        shadow.write_text(
            json.dumps({"ts": "t1", "prompt": "Como faço para reduzir o custo das chamadas do Haiku no eval?",
                        "candidates": [sentinel], "emitted": sentinel, "cwd": sentinel}) + "\n",
            encoding="utf-8",
        )  # fmt: skip
        self.run_main(["shadow", "--shadow", str(shadow)], mode="fail_if_called")
        text = self.drafts.read_text(encoding="utf-8")
        self.assertNotIn(sentinel, text)
        row = self.rows()[0]
        self.assertEqual((row["origin"], row["polarity"], row["status"], row["shadow_ts"]), ("shadow", None, "pending", "t1"))
        self.run_main(["shadow", "--shadow", str(shadow)], mode="fail_if_called")
        self.assertEqual(len(self.rows()), 1)

    def test_dry_run_lists_without_writing(self):
        shadow = self.root / "shadow.jsonl"
        shadow.write_text(json.dumps({"ts": "t1", "prompt": "Como faço para reduzir o custo das chamadas do Haiku?"}) + "\n", encoding="utf-8")
        out = self.run_main(["shadow", "--shadow", str(shadow), "--dry-run"])
        self.assertIn("reduzir o custo", out)
        self.assertFalse(self.drafts.exists())


class PositivesTest(Base):
    def test_generates_pending_rows_with_metadata(self):
        self.run_main(["positives", "--n", "2"], mode="fenced")
        rows = self.rows()
        self.assertEqual(len(rows), 2)
        self.assertEqual([r["draft_id"] for r in rows], ["d001", "d002"])
        for r in rows:
            self.assertEqual((r["origin"], r["polarity"], r["status"]), ("llm", "positive", "pending"))
            self.assertIn("haiku", r["model"])
            self.assertEqual(r["title_hits"], 0)
            self.assertTrue(r["from_path"].startswith("20_Permanent_Notes/"))
            self.assertNotEqual(r["from_path"], "20_Permanent_Notes/Delta.md")

    def test_same_seed_same_sample(self):
        self.run_main(["positives", "--n", "2"])
        first = [r["from_path"] for r in self.rows()]
        self.drafts.unlink()
        self.run_main(["positives", "--n", "2"])
        self.assertEqual(first, [r["from_path"] for r in self.rows()])

    def test_title_copy_is_auto_rejected(self):
        self.run_main(["positives", "--n", "1"], mode="title_copy")
        row = self.rows()[0]
        self.assertEqual(row["status"], "auto_rejected")
        self.assertEqual(row["reason"], "title_hits=2")

    def test_duplicate_of_golden_or_draft_is_auto_rejected(self):
        self.run_main(["positives", "--n", "1"], mode="golden_dup")
        self.assertEqual((self.rows()[0]["status"], self.rows()[0]["reason"]), ("auto_rejected", "duplicata"))
        self.drafts.unlink()
        self.run_main(["positives", "--n", "2"], mode="same")
        rows = self.rows()
        self.assertEqual(rows[0]["status"], "pending")
        self.assertEqual((rows[1]["status"], rows[1]["reason"]), ("auto_rejected", "duplicata"))

    def test_idempotent_no_call_for_drafted_notes(self):
        self.run_main(["positives", "--n", "3"])
        Path(self.counter).unlink()
        self.run_main(["positives", "--n", "3"], mode="fail_if_called")
        self.assertEqual(self.calls(), 0)
        self.assertEqual(len(self.rows()), 3)

    def test_dry_run_calls_nothing_and_writes_nothing(self):
        out = self.run_main(["positives", "--n", "2", "--dry-run"], mode="fail_if_called")
        self.assertEqual(self.calls(), 0)
        self.assertFalse(self.drafts.exists())
        self.assertIn("### 20_Permanent_Notes/", out)
        self.assertIn(gd.SYSTEM_PROMPT, out)

    def test_limit_one_makes_one_call(self):
        self.run_main(["positives", "--n", "3", "--limit", "1"])
        self.assertEqual(self.calls(), 1)
        self.assertEqual(len(self.rows()), 1)

    def test_failure_midway_keeps_first_row(self):
        with self.assertRaises(RuntimeError):
            self.run_main(["positives", "--n", "3"], mode="fail_second")
        self.assertEqual(len(self.rows()), 1)

    def test_wrong_model_fails_loudly(self):
        with self.assertRaisesRegex(ValueError, "modelo inesperado"):
            self.run_main(["positives", "--n", "1"], mode="sonnet")
        self.assertEqual(self.rows(), [])

    def test_isolation(self):
        self.run_main(["positives", "--n", "1"], CLAUDECODE="1", CLAUDE_CODE_SESSION_ID="x")
        cap = json.loads(Path(self.cap).read_text())
        self.assertFalse([a for a in cap["argv"] if str(ev.VAULT) in a])
        self.assertNotIn(str(ev.VAULT), str(Path(cap["cwd"]).resolve()))
        self.assertNotIn("CLAUDECODE", cap["env_keys"])
        self.assertNotIn("CLAUDE_CODE_SESSION_ID", cap["env_keys"])
        system = cap["argv"][cap["argv"].index("--system-prompt") + 1]
        self.assertEqual(system, gd.SYSTEM_PROMPT)
        self.assertNotEqual(system, gr.SYSTEM_PROMPT)
        self.assertEqual(cap["argv"][-2:], ["--tools", ""])


class NegativesTest(Base):
    def test_negatives_rows(self):
        self.run_main(["negatives", "--areas", "frontend e CSS", "bancos de dados"], mode="negative")
        rows = self.rows()
        self.assertEqual(self.calls(), 2)
        first = [r for r in rows if r["area"] == "frontend e CSS"]
        self.assertEqual(len(first), 3)
        self.assertEqual({r["flavor"] for r in first}, {"near", "far"})
        for r in first:
            self.assertEqual((r["polarity"], r["origin"], r["from_path"]), ("negative", "llm", None))
        # segunda área devolve as mesmas perguntas: duplicata dentro do lote
        second = [r for r in rows if r["area"] == "bancos de dados"]
        self.assertTrue(all(r["status"] == "auto_rejected" and r["reason"] == "duplicata" for r in second))

    def test_area_idempotent(self):
        self.run_main(["negatives", "--areas", "frontend e CSS"], mode="negative")
        Path(self.counter).unlink()
        self.run_main(["negatives", "--areas", "frontend e CSS"], mode="fail_if_called")
        self.assertEqual(self.calls(), 0)

    def test_dry_run_default_areas(self):
        out = self.run_main(["negatives", "--dry-run"], mode="fail_if_called")
        self.assertEqual(self.calls(), 0)
        for area in gd.NEG_AREAS:
            self.assertIn(area, out)


class ManualTest(Base):
    def test_manual_row(self):
        self.run_main(["manual", "--query", "Como migrar o banco sem downtime nenhum?", "--kind", "negative"])
        row = self.rows()[0]
        self.assertEqual((row["origin"], row["polarity"], row["status"], row["kind"]), ("manual", "negative", "pending", "negative"))
        self.run_main(["manual", "--query", "como migrar o banco sem downtime nenhum", "--kind", "negative"])
        self.assertEqual(len(self.rows()), 1)


if __name__ == "__main__":
    unittest.main()
