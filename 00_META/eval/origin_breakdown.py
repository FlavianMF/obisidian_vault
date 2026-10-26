"""Quebra um run do run_eval.py por origem das queries (antiga x nova).

Uso: python3 00_META/eval/origin_breakdown.py <run.json> [--golden PATH]
Antiga = linha do golden sem `approval`; nova = com `approval`.
"""

import argparse
import json
import sys
from pathlib import Path

GOLDEN = Path(__file__).resolve().parent / "golden.jsonl"
GROUPS = ("pos_antiga", "pos_nova", "neg_antiga", "neg_nova")


def origin(row: dict) -> str:
    return "nova" if "approval" in row else "antiga"


def breakdown(run: dict, golden_rows: list[dict]) -> dict[str, dict[str, tuple[float, int]]]:
    by_id = {row["id"]: row for row in golden_rows}
    out: dict[str, dict[str, tuple[float, int]]] = {}
    for method, result in run["results"].items():
        sums = {g: 0.0 for g in GROUPS}
        counts = {g: 0 for g in GROUPS}
        for qid, metrics in result["per_query"].items():
            row = by_id.get(qid)
            if row is None:
                raise ValueError(f"{method}: id {qid} do run não existe no golden")
            is_neg = bool(metrics.get("neg"))
            if is_neg != (row.get("kind") == "negative"):
                raise ValueError(f"{method}: {qid} tem kind={row.get('kind')} mas neg={metrics.get('neg')} no run")
            group = ("neg_" if is_neg else "pos_") + origin(row)
            sums[group] += float(metrics["returned_any" if is_neg else "success"])
            counts[group] += 1
        out[method] = {g: (sums[g], counts[g]) for g in GROUPS}
    return out


def fmt(cell: tuple[float, int]) -> str:
    total, n = cell
    shown = str(int(total)) if float(total).is_integer() else f"{total:.1f}"
    return f"{shown}/{n}"


def render(table: dict[str, dict[str, tuple[float, int]]]) -> str:
    lines = [
        "| método | positivas antigas | positivas novas | negativas antigas (FP) | negativas novas (FP) |",
        "|---|---|---|---|---|",
    ]
    for method, groups in table.items():
        lines.append(f"| {method} | " + " | ".join(fmt(groups[g]) for g in GROUPS) + " |")
    return "\n".join(lines)


def load_golden(path: Path) -> list[dict]:
    rows = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{number} JSON inválido: {exc}") from exc
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path, help="runs/*.json gerado pelo run_eval.py")
    parser.add_argument("--golden", type=Path, default=GOLDEN)
    args = parser.parse_args(argv)
    if not args.run.is_file():
        raise SystemExit(f"run não encontrado: {args.run}; gere com run_eval.py")
    run = json.loads(args.run.read_text(encoding="utf-8"))
    table = breakdown(run, load_golden(args.golden))
    print(f"split={run.get('split')} k={run.get('k')}\n")
    print(render(table))
    return 0


if __name__ == "__main__":
    sys.exit(main())
