#!/usr/bin/env python3
"""Valida o golden set contra os pisos 1 a 6 do PRD-004 (B1).

    python3 00_META/eval/validate_golden.py              # todos os pisos
    python3 00_META/eval/validate_golden.py --only 4,5,6 # só alguns

Coleta todas as falhas (não para na primeira) e sai com 1 se algum piso pedido falhou.
Lê o JSONL cru: uma linha inválida vira falha do piso 5, não traceback.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
import unicodedata
from pathlib import Path

import run_eval as ev

DRAFTS = Path(__file__).resolve().parent / "drafts.jsonl"
BASELINE_IDS = {f"q{i:03d}" for i in range(1, 43)}
BASELINE_TEST = {"q003", "q006", "q009", "q012", "q015", "q018", "q021", "q024", "q027", "q030"}
NEW_SOURCES = {"llm", "shadow", "manual"}
LEGACY_SOURCE = "llm-draft+user-approved"
MIN_TOTAL = 60
MIN_NEW = 18
MIN_TEST = 24
MIN_TEST_POS = 16
MIN_TEST_NEG = 8
MIN_NEG_SHARE = 0.30
MIN_TERM_LEN = 4
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def fold(s: str) -> str:
    """NFKD, sem combinantes, casefold."""
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)).casefold()


def norm_query(s: str) -> str:
    return " ".join(re.sub(r"[^0-9a-z]+", " ", fold(s)).split())


def stoplist() -> frozenset[str]:
    """Stoplist do ranqueador, lida do próprio script para não duplicar a lista."""
    match = re.search(r'stoplist = "([^"]*)"', ev.RANKER.read_text(encoding="utf-8"))
    if not match:
        raise RuntimeError(f"stoplist não encontrada em {ev.RANKER}")
    return frozenset(match.group(1).split())


def rank_terms(s: str) -> list[str]:
    """Termos que o ranqueador usa: >= 4 caracteres, fora da stoplist, sem repetição."""
    stop = stoplist()
    seen: dict[str, None] = {}
    for tok in re.split(r"[^0-9a-z]+", fold(s)):
        if len(tok) >= MIN_TERM_LEN and tok not in stop:
            seen.setdefault(tok)
    return list(seen)


def title_hits(query: str, title: str) -> int:
    """Termos da query que casam como substring no título (peso 3 no ranqueador)."""
    folded = fold(title)
    return sum(term in folded for term in rank_terms(query))


def is_negative(row: dict) -> bool:
    return row.get("kind") == "negative"


def assign_splits(
    new_rows: list[dict], seed: int, base_test_pos: int, base_test_neg: int,
    test_pos: int = MIN_TEST_POS, test_neg: int = MIN_TEST_NEG,
) -> dict[str, str]:  # fmt: skip
    """Divide as queries novas em dev/test por semente, preenchendo só o déficit do test."""
    dpos = max(0, test_pos - base_test_pos)
    dneg = max(0, test_neg - base_test_neg)
    out: dict[str, str] = {}
    for offset, neg, deficit in ((0, False, dpos), (1, True, dneg)):
        ids = sorted(r["id"] for r in new_rows if is_negative(r) == neg)
        if len(ids) < deficit:
            kind = "negativas" if neg else "positivas"
            raise ValueError(f"faltam {kind} novas: {len(ids)} para um déficit de {deficit} no test")
        random.Random(seed + offset).shuffle(ids)
        for i, qid in enumerate(ids):
            out[qid] = "test" if i < deficit else "dev"
    return out


def read_jsonl(path: Path) -> tuple[list[dict], list[tuple[int, str]]]:
    rows: list[dict] = []
    errors: list[tuple[int, str]] = []
    if not path.is_file():
        return rows, errors
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            errors.append((5, f"{path.name}:{lineno} linha não é JSON"))
            continue
        if not isinstance(row, dict):
            errors.append((5, f"{path.name}:{lineno} linha não é objeto JSON"))
            continue
        rows.append(row)
    return rows, errors


def check(rows: list[dict], drafts: list[dict], vault: Path, parse_errors=()) -> list[tuple[int, str]]:
    fails: list[tuple[int, str]] = []
    for item in parse_errors:
        fails.append((5, item[1]) if isinstance(item, tuple) else (5, str(item)))
    active = [r for r in rows if r.get("status") == "active"]
    new = [r for r in active if r.get("id") not in BASELINE_IDS]
    test = [r for r in active if r.get("split") == "test"]
    base_neg_test = sum(is_negative(r) for r in test if r.get("id") in BASELINE_IDS)
    base_pos_test = sum(not is_negative(r) for r in test if r.get("id") in BASELINE_IDS)

    # piso 1
    if len(active) < MIN_TOTAL:
        fails.append((1, f"{len(active)} queries ativas; mínimo {MIN_TOTAL}"))
    if len(new) < MIN_NEW:
        fails.append((1, f"{len(new)} queries novas; mínimo {MIN_NEW}"))
    # piso 2
    tpos = sum(not is_negative(r) for r in test)
    tneg = len(test) - tpos
    if len(test) < MIN_TEST:
        fails.append((2, f"test com {len(test)} queries; mínimo {MIN_TEST}"))
    if tpos < MIN_TEST_POS:
        fails.append((2, f"test com {tpos} positivas; mínimo {MIN_TEST_POS}"))
    if tneg < MIN_TEST_NEG:
        fails.append((2, f"test com {tneg} negativas; mínimo {MIN_TEST_NEG}"))
    # piso 3
    if active:
        share = sum(is_negative(r) for r in active) / len(active)
        if share < MIN_NEG_SHARE:
            fails.append((3, f"negativas são {share:.1%} do total; mínimo {MIN_NEG_SHARE:.0%}"))
    # piso 4
    by_id = {r.get("id"): r for r in rows}
    for qid in sorted(BASELINE_IDS):
        row = by_id.get(qid)
        if row is None:
            fails.append((4, f"{qid} do baseline ausente"))
        elif (row.get("split") == "test") != (qid in BASELINE_TEST):
            fails.append((4, f"{qid} mudou de split ({row.get('split')})"))
    seeds = set()
    for r in new:
        if not isinstance(r.get("split_seed"), int) or isinstance(r.get("split_seed"), bool):
            fails.append((4, f"{r.get('id')} sem split_seed inteiro"))
        else:
            seeds.add(r["split_seed"])
        if r.get("split") not in ("dev", "test"):
            fails.append((4, f"{r.get('id')} com split inválido {r.get('split')!r}"))
    if len(seeds) > 1:
        fails.append((4, f"mais de uma semente nas queries novas: {sorted(seeds)}"))
    if len(seeds) == 1 and not any(f[0] == 4 for f in fails):
        try:
            expected = assign_splits(new, next(iter(seeds)), base_pos_test, base_neg_test)
        except ValueError as exc:
            fails.append((4, str(exc)))
        else:
            wrong = sorted(r["id"] for r in new if expected[r["id"]] != r["split"])
            if wrong:
                fails.append((4, f"split diverge do recalculado pela semente em {wrong}"))
    # piso 5
    seen_ids: set = set()
    seen_q: dict[str, str] = {}
    for r in rows:
        qid = r.get("id")
        missing = ev.REQUIRED - r.keys()
        if missing:
            fails.append((5, f"{qid}: faltam campos {sorted(missing)}"))
            continue
        if qid in seen_ids:
            fails.append((5, f"id duplicado {qid}"))
        seen_ids.add(qid)
        if r["kind"] not in ev.KINDS:
            fails.append((5, f"{qid}: kind inválido {r['kind']!r}"))
        rel = r["relevant"] if isinstance(r["relevant"], list) else []
        if is_negative(r) and rel:
            fails.append((5, f"{qid}: negativa com relevant"))
        if r["kind"] in ev.KINDS and not is_negative(r) and not any(isinstance(x, dict) and x.get("grade") == 2 for x in rel):
            fails.append((5, f"{qid}: positiva sem nota de grau 2"))
        for x in rel:
            path = x.get("path") if isinstance(x, dict) else None
            if not isinstance(path, str) or not (vault / path).is_file():
                fails.append((5, f"{qid}: nota inexistente {path}"))
        if r["status"] == "active" and isinstance(r["query"], str):
            key = norm_query(r["query"])
            if key in seen_q:
                fails.append((5, f"{qid}: query duplicada de {seen_q[key]}"))
            seen_q.setdefault(key, qid)
    # piso 6
    approved = {d.get("draft_id") for d in drafts if d.get("status") == "approved"}
    for r in active:
        qid = r.get("id")
        if qid in BASELINE_IDS:
            if r.get("source") != LEGACY_SOURCE:
                fails.append((6, f"{qid}: source do baseline deveria ser {LEGACY_SOURCE!r}"))
            continue
        if r.get("source") not in NEW_SOURCES:
            fails.append((6, f"{qid}: source inválido {r.get('source')!r}"))
        ap = r.get("approval")
        if not isinstance(ap, dict) or ap.get("by") != "user" or not isinstance(ap.get("draft"), str) or not (
            isinstance(ap.get("date"), str) and DATE.match(ap["date"])
        ):
            fails.append((6, f"{qid}: approval ausente ou inválido"))
            continue
        if r.get("source") in ("llm", "shadow") and ap["draft"] not in approved:
            fails.append((6, f"{qid}: rascunho {ap['draft']} não está approved em drafts.jsonl"))
    return fails


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--golden", type=Path, default=ev.GOLDEN)
    parser.add_argument("--drafts", type=Path, default=DRAFTS)
    parser.add_argument("--vault", type=Path, default=ev.VAULT)
    parser.add_argument("--only", default="", help="pisos separados por vírgula, ex.: 4,5,6")
    args = parser.parse_args(argv)
    try:
        wanted = {int(x) for x in args.only.split(",") if x.strip()} or set(range(1, 7))
    except ValueError:
        raise SystemExit(f"--only inválido: {args.only!r}") from None
    rows, errors = read_jsonl(args.golden)
    drafts, _ = read_jsonl(args.drafts)
    fails = check(rows, drafts, args.vault, errors)
    failed = 0
    for n in sorted(wanted):
        msgs = [m for f, m in fails if f == n]
        if msgs:
            failed += 1
            print(f"piso {n}: FAIL — " + "; ".join(msgs))
        else:
            print(f"piso {n}: PASS")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
