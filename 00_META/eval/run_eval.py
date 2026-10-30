#!/usr/bin/env python3
"""Harness do golden set de retrieval do second brain (RFC-001, etapa F0c).

Roda cada método de busca sobre `golden.jsonl` e imprime recall, MRR, nDCG, taxa de falso
positivo em queries negativas e **tokens por acerto**. Só biblioteca padrão; local-first.

    python3 00_META/eval/run_eval.py --methods rank,random,fixed --split dev --k 5

Métodos (adaptadores `search(query, k) -> [path, ...]`):
  rank    chama `vault_rank.sh` (o ranqueador de produção; nada reimplementado aqui)
  random  k notas aleatórias dos manifests (baseline degenerado; média de --draws sorteios)
  fixed   as k primeiras notas por ordem de path (baseline degenerado constante)
  rewrite query original + reformulações de rewrites.jsonl, cada uma pelo vault_rank.sh com o mesmo limiar, fundidas por RRF (k=60)

Custo em tokens (estimativa fixa, chars / 3,5; trocar por tokenizer real depois): saída do
método (linhas `título — path`) + corpo das notas que o agente abriria, em ordem de ranking,
até a primeira nota de grau 2 (ou todas as k, se nenhuma acerta). tokens_por_acerto =
tokens totais (todas as queries) / acertos@k.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import re
import statistics
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

VAULT = Path(__file__).resolve().parents[2]
GOLDEN = Path(__file__).resolve().parent / "golden.jsonl"
RUNS_DIR = Path(__file__).resolve().parent / "runs"
RANKER = VAULT / "00_META/skills/second-brain-sync/scripts/vault_rank.sh"
MANIFEST_DIR = VAULT / "00_META/manifests/by_type"
CHARS_PER_TOKEN = 3.5
KINDS = {"lexical", "paraphrase", "multihop", "negative"}
REQUIRED = {"id", "query", "kind", "relevant", "split", "status"}
BOOTSTRAP_RESAMPLES = 2000
REWRITES = Path(__file__).resolve().parent / "rewrites.jsonl"
RRF_K = 60
RRF_DEPTH = 10
REWRITES_MIN = 2
REWRITES_MAX = 3
REWRITE_REQUIRED = {"id", "query", "rewrites", "model", "created"}
TEST_LOCK = Path(__file__).resolve().parent / "test_run.json"
LOCKED_SPLITS = ("test", "all")


@dataclass(frozen=True)
class Query:
    id: str
    text: str
    kind: str
    grades: dict[str, int]  # path -> 1|2


def est_tokens(chars: int) -> float:
    return chars / CHARS_PER_TOKEN


def load_golden(path: Path = GOLDEN, split: str = "all", vault: Path = VAULT) -> list[Query]:
    """Carrega e valida o golden set; falha alto em rótulo quebrado."""
    queries: list[Query] = []
    seen: set[str] = set()
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        missing = REQUIRED - row.keys()
        if missing:
            raise ValueError(f"{path.name}:{lineno} faltam campos {sorted(missing)}")
        if row["id"] in seen:
            raise ValueError(f"{path.name}:{lineno} id duplicado {row['id']}")
        seen.add(row["id"])
        if row["kind"] not in KINDS:
            raise ValueError(f"{row['id']}: kind inválido {row['kind']!r}")
        if row["kind"] == "negative" and row["relevant"]:
            raise ValueError(f"{row['id']}: query negativa não pode ter notas relevantes")
        if row["kind"] != "negative" and not any(r["grade"] == 2 for r in row["relevant"]):
            raise ValueError(f"{row['id']}: precisa de ao menos uma nota de grau 2")
        for rel in row["relevant"]:
            if not (vault / rel["path"]).is_file():
                raise ValueError(f"{row['id']}: nota inexistente {rel['path']}")
        if row["status"] != "active" or split not in ("all", row["split"]):
            continue
        queries.append(Query(row["id"], row["query"], row["kind"], {r["path"]: r["grade"] for r in row["relevant"]}))
    return queries


def manifest_paths(manifest_dir: Path = MANIFEST_DIR) -> list[str]:
    paths: list[str] = []
    for file in sorted(manifest_dir.glob("*.md")):
        for line in file.read_text(encoding="utf-8").splitlines():
            if not line.startswith("| "):
                continue
            cell = line.split("|")[1].strip()
            if cell and cell != "Path" and set(cell) != {"-"}:
                paths.append(cell)
    return sorted(set(paths))


class RankAdapter:
    name = "rank"
    stochastic = False

    def __init__(self, min_coverage: float = 0.0, min_terms: int = 1) -> None:
        self._flags = ["-c", str(min_coverage), "-t", str(min_terms)]

    def search(self, query: str, k: int) -> list[str]:
        # the golden set measures the plain ranking; exporting SECOND_BRAIN_RANK_LEARN=1 measures it with the learning adjustment
        env = {**os.environ}
        env.setdefault("SECOND_BRAIN_RANK_LEARN", "0")
        result = subprocess.run(
            [str(RANKER), "-k", str(k), *self._flags, query], capture_output=True, text=True, timeout=10, check=False,
            env=env,
        )
        return [line.split("\t")[1] for line in result.stdout.splitlines() if line.count("\t") >= 2]


class RandomAdapter:
    name = "random"
    stochastic = True

    def __init__(self, paths: list[str], seed: int = 0) -> None:
        self._paths = paths
        self._rng = random.Random(seed)

    def search(self, query: str, k: int) -> list[str]:
        return self._rng.sample(self._paths, min(k, len(self._paths)))


class FixedAdapter:
    name = "fixed"
    stochastic = False

    def __init__(self, paths: list[str]) -> None:
        self._paths = paths

    def search(self, query: str, k: int) -> list[str]:
        return self._paths[:k]


def rrf_fuse(rankings: list[list[str]], k_rrf: int = RRF_K) -> list[str]:
    """Reciprocal rank fusion: score(d) = Σ 1/(k_rrf + posição), posição a partir de 1.

    Desempate determinístico: melhor posição em qualquer variante, depois a variante de menor
    índice (a query original é a 0), depois o path.
    """
    scores: dict[str, float] = {}
    best: dict[str, tuple[int, int]] = {}
    for variant, ranking in enumerate(rankings):
        for pos, path in enumerate(ranking, 1):
            scores[path] = scores.get(path, 0.0) + 1.0 / (k_rrf + pos)
            best[path] = min(best.get(path, (pos, variant)), (pos, variant))
    return sorted(scores, key=lambda p: (-scores[p], best[p], p))


def validate_rewrite_row(row: dict, where: str) -> None:
    """Falha alto em linha malformada de rewrites.jsonl (usado pelo eval e pelo gerador)."""
    missing = REWRITE_REQUIRED - row.keys()
    if missing:
        raise ValueError(f"{where} faltam campos {sorted(missing)}")
    rewrites = row["rewrites"]
    if not isinstance(rewrites, list) or not all(isinstance(r, str) and r.strip() for r in rewrites):
        raise ValueError(f"{where} rewrites inválidas: precisa ser lista de strings não vazias")
    folded = [r.strip().casefold() for r in rewrites]
    if not REWRITES_MIN <= len(rewrites) <= REWRITES_MAX:
        raise ValueError(f"{where} rewrites inválidas: {len(rewrites)} itens, esperado {REWRITES_MIN} a {REWRITES_MAX}")
    if len(set(folded)) != len(folded):
        raise ValueError(f"{where} rewrites inválidas: duplicatas")
    if str(row["query"]).strip().casefold() in folded:
        raise ValueError(f"{where} rewrites inválidas: reformulação igual à query")
    if not isinstance(row["model"], str) or not row["model"].strip():
        raise ValueError(f"{where} model vazio")
    if not isinstance(row["created"], str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", row["created"]):
        raise ValueError(f"{where} created inválido {row['created']!r}; esperado AAAA-MM-DD")


def load_rewrites(path: Path, queries: list[Query], known_ids: set[str]) -> dict[str, list[str]]:
    """Mapa texto da query -> reformulações. Falha alto se faltar linha ou se a query divergir."""
    rows: dict[str, dict] = {}
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        where = f"{path.name}:{lineno}"
        validate_rewrite_row(row, where)
        if row["id"] in rows:
            raise ValueError(f"{where} id duplicado {row['id']}")
        if row["id"] not in known_ids:
            raise ValueError(f"{where} id desconhecido {row['id']}")
        rows[row["id"]] = row
    out: dict[str, list[str]] = {}
    for q in queries:
        if q.id not in rows:
            raise ValueError(f"{q.id}: falta linha em {path.name}; rode gen_rewrites.py --split ...")
        if rows[q.id]["query"] != q.text:
            raise ValueError(f"{q.id}: query diverge do golden set")
        out[q.text] = rows[q.id]["rewrites"]
    return out


class RewriteAdapter:
    name = "rewrite"
    stochastic = False

    def __init__(
        self,
        rewrites: dict[str, list[str]],
        min_coverage: float = 0.0,
        min_terms: int = 1,
        search_fn=None,
        depth: int = RRF_DEPTH,
    ) -> None:
        self._rewrites = rewrites
        self._search = search_fn or RankAdapter(min_coverage, min_terms).search
        self._depth = depth

    def search(self, query: str, k: int) -> list[str]:
        if query not in self._rewrites:
            raise ValueError(f"sem reformulação para a query {query!r}")
        variants = [query, *self._rewrites[query]]
        return rrf_fuse([self._search(v, max(k, self._depth)) for v in variants])[:k]


def dcg(gains: list[int]) -> float:
    return sum(g / math.log2(i + 2) for i, g in enumerate(gains))


def score_query(query: Query, results: list[str], k: int, vault: Path = VAULT) -> dict[str, float]:
    """Métricas de uma query. Para query negativa só importa se o método devolveu algo."""
    top = results[:k]
    out_tokens = est_tokens(sum(len(f"{Path(p).stem} — {p}") for p in top))
    if query.kind == "negative":
        return {"neg": 1.0, "returned_any": float(bool(top)), "tokens": out_tokens + _open_cost(top, None, vault)}
    first_hit = next((i for i, p in enumerate(top) if query.grades.get(p) == 2), None)
    gains = [query.grades.get(p, 0) for p in top]
    ideal = sorted(query.grades.values(), reverse=True)[:k]
    relevant = [p for p, g in query.grades.items() if g >= 1]
    return {
        "neg": 0.0,
        "success": float(first_hit is not None),
        "recall": sum(p in top for p in relevant) / len(relevant),
        "mrr": 0.0 if first_hit is None else 1.0 / (first_hit + 1),
        "ndcg": dcg(gains) / dcg(ideal) if ideal else 0.0,
        "tokens": out_tokens + _open_cost(top, first_hit, vault),
    }


def _open_cost(top: list[str], first_hit: int | None, vault: Path) -> float:
    opened = top if first_hit is None else top[: first_hit + 1]
    chars = 0
    for path in opened:
        note = vault / path
        chars += len(note.read_text(encoding="utf-8")) if note.is_file() else 0
    return est_tokens(chars)


def bootstrap_ci(values: list[float], seed: int = 0) -> tuple[float, float]:
    """IC 95% percentil da média por bootstrap (determinístico)."""
    if not values:
        return (0.0, 0.0)
    rng = random.Random(seed)
    means = sorted(statistics.fmean(rng.choices(values, k=len(values))) for _ in range(BOOTSTRAP_RESAMPLES))
    return (means[int(0.025 * BOOTSTRAP_RESAMPLES)], means[int(0.975 * BOOTSTRAP_RESAMPLES) - 1])


def evaluate(adapter, queries: list[Query], k: int, draws: int = 1) -> dict:
    rounds = draws if adapter.stochastic else 1
    per_query: list[dict[str, float]] = []
    for query in queries:
        runs = [score_query(query, adapter.search(query.text, k), k) for _ in range(rounds)]
        per_query.append({key: statistics.fmean(r[key] for r in runs) for key in runs[0]})
    positives = [m for m in per_query if not m["neg"]]
    negatives = [m for m in per_query if m["neg"]]
    hits = sum(m["success"] for m in positives)
    total_tokens = sum(m["tokens"] for m in per_query)
    summary = {
        "n_pos": len(positives),
        "n_neg": len(negatives),
        f"success@{k}": statistics.fmean(m["success"] for m in positives) if positives else 0.0,
        f"recall@{k}": statistics.fmean(m["recall"] for m in positives) if positives else 0.0,
        "mrr": statistics.fmean(m["mrr"] for m in positives) if positives else 0.0,
        f"ndcg@{k}": statistics.fmean(m["ndcg"] for m in positives) if positives else 0.0,
        "neg_false_positive": statistics.fmean(m["returned_any"] for m in negatives) if negatives else None,
        "tokens_total": total_tokens,
        "tokens_per_hit": total_tokens / hits if hits else None,
        "ci95_success": bootstrap_ci([m["success"] for m in positives]),
    }
    return {"summary": summary, "per_query": {q.id: m for q, m in zip(queries, per_query)}}


def render(results: dict[str, dict], k: int) -> str:
    cols = [f"success@{k}", "IC95", f"recall@{k}", "MRR", f"nDCG@{k}", "FP neg", "tokens/acerto"]
    lines = ["| método | " + " | ".join(cols) + " |", "|---|" + "---|" * len(cols)]
    for name, res in results.items():
        s = res["summary"]
        lo, hi = s["ci95_success"]
        fp = "-" if s["neg_false_positive"] is None else f"{s['neg_false_positive']:.2f}"
        tph = "-" if s["tokens_per_hit"] is None else f"{s['tokens_per_hit']:.0f}"
        lines.append(
            f"| {name} | {s[f'success@{k}']:.2f} | {lo:.2f}–{hi:.2f} | {s[f'recall@{k}']:.2f} | {s['mrr']:.2f} "
            f"| {s[f'ndcg@{k}']:.2f} | {fp} | {tph} |"
        )
    return "\n".join(lines)


def _rewrites_for(path: Path, queries: list[Query]) -> dict[str, list[str]]:
    if not path.is_file():
        raise SystemExit(f"{path.name} não existe; rode 00_META/eval/gen_rewrites.py --split <split>")
    return load_rewrites(path, queries, {q.id for q in load_golden(split="all")})


def build_adapters(
    names: list[str],
    min_coverage: float = 0.0,
    min_terms: int = 1,
    queries: list[Query] | None = None,
    rewrites_path: Path = REWRITES,
) -> list:
    paths = manifest_paths()
    available = {
        "rank": lambda: RankAdapter(min_coverage, min_terms),
        "random": lambda: RandomAdapter(paths),
        "fixed": lambda: FixedAdapter(paths),
        "rewrite": lambda: RewriteAdapter(_rewrites_for(rewrites_path, queries or []), min_coverage, min_terms),
    }
    unknown = [n for n in names if n not in available]
    if unknown:
        raise SystemExit(f"método desconhecido: {unknown}; opções: {sorted(available)}")
    return [available[n]() for n in names]


def check_test_lock(split: str, confirmed: bool, lock_path: Path) -> None:
    """O split test roda uma vez só: exige confirmação e recusa se o lock já existe."""
    if split not in LOCKED_SPLITS:
        return
    if not confirmed:
        raise SystemExit("o split test roda uma vez só e exige --confirm-test-run, com aprovação do usuário")
    if lock_path.exists():
        try:
            date = json.loads(lock_path.read_text(encoding="utf-8")).get("date", "desconhecida")
        except (OSError, ValueError, AttributeError):
            date = "desconhecida"
        raise SystemExit(f"o split test já rodou em {date} ({lock_path.name}); não há segunda rodada")


def _vault_head() -> str | None:
    try:
        out = subprocess.run(["git", "-C", str(VAULT), "rev-parse", "HEAD"], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() or None if out.returncode == 0 else None


def write_test_lock(lock_path: Path, args, results: dict) -> None:
    """Grava o lock com criação exclusiva (modo "x"); falha se já existir."""
    payload = {
        "date": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "split": args.split,
        "methods": args.methods.split(","),
        "k": args.k,
        "min_coverage": args.min_coverage,
        "min_terms": args.min_terms,
        "head": _vault_head(),
        "summaries": {name: res["summary"] for name, res in results.items()},
    }
    with open(lock_path, "x", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=False, indent=1))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--methods", default="rank,random,fixed")
    parser.add_argument("--split", choices=["dev", "test", "all"], default="dev")
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--draws", type=int, default=200, help="sorteios por query para métodos aleatórios")
    parser.add_argument("--min-coverage", type=float, default=0.0, help="limiar de silêncio do rank e do rewrite (por variante, campo coverage)")
    parser.add_argument("--min-terms", type=int, default=1, help="mínimo de termos úteis na query do rank")
    parser.add_argument("--rewrites", type=Path, default=REWRITES, help="reformulações do adaptador rewrite")
    parser.add_argument("--no-save", action="store_true")
    parser.add_argument("--confirm-test-run", action="store_true", help="confirma a rodada única do split test (exige aprovação do usuário)")
    args = parser.parse_args(argv)
    check_test_lock(args.split, args.confirm_test_run, TEST_LOCK)

    queries = load_golden(split=args.split)
    if not queries:
        raise SystemExit("nenhuma query ativa neste split")
    results: dict[str, dict] = {}
    for adapter in build_adapters(args.methods.split(","), args.min_coverage, args.min_terms, queries, args.rewrites):
        started = time.perf_counter()
        results[adapter.name] = evaluate(adapter, queries, args.k, args.draws)
        results[adapter.name]["summary"]["seconds"] = round(time.perf_counter() - started, 2)
    if args.split in LOCKED_SPLITS:
        write_test_lock(TEST_LOCK, args, results)
    print(f"split={args.split} k={args.k} queries={len(queries)}\n")
    print(render(results, args.k))
    if not args.no_save:
        RUNS_DIR.mkdir(exist_ok=True)
        target = RUNS_DIR / f"{time.strftime('%Y%m%d-%H%M%S')}-{args.split}.json"
        target.write_text(json.dumps({"k": args.k, "split": args.split, "results": results}, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\nresultado salvo em {target.relative_to(VAULT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
