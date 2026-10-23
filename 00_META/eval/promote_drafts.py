#!/usr/bin/env python3
"""Aprovação registrada e promoção de rascunhos para o golden set (PRD-004, B1).

    python3 00_META/eval/promote_drafts.py review                       # tabela dos pendentes, para o usuário
    python3 00_META/eval/promote_drafts.py decide --file d.json --date 2026-10-23
    python3 00_META/eval/promote_drafts.py promote --seed 20261023 --dry-run
    python3 00_META/eval/promote_drafts.py promote --seed 20261023

`decide` grava só o que o usuário decidiu (nada é inferido). `promote` é um lote único: monta as queries
novas dos rascunhos aprovados, divide dev/test por semente com cotas, roda os pisos 1 a 6 em memória e só
então escreve o golden.jsonl (arquivo temporário + os.replace). Nada aqui depende de resultado de busca.
"""

from __future__ import annotations

import argparse
import copy
import datetime
import json
import os
import re
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import gen_drafts as gd
import run_eval as ev
import validate_golden as vg

FIRST_NEW_ID = 43
DEFAULT_KIND = "paraphrase"
LANGS = ("pt", "en")


def git_commit() -> str:
    out = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], cwd=ev.VAULT, capture_output=True, text=True, check=True
    )  # fmt: skip
    return out.stdout.strip()


def atomic_write(path: Path, text: str) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def cell(text: object) -> str:
    return str(text if text is not None else "").replace("|", "\\|").replace("\n", " ")


def review(drafts: list[dict], titles: dict[str, str], status: str = "pending") -> str:
    lines = [
        "| draft_id | origin | polarity | flavor | query | from_path (título) | title_hits |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for d in drafts:
        if d.get("status") != status:
            continue
        src = d.get("from_path")
        origin_note = f"{src} ({titles.get(src, '?')})" if src else ""
        lines.append(
            "| " + " | ".join(cell(x) for x in (d["draft_id"], d["origin"], d["polarity"], d.get("flavor"), d["query"], origin_note, d.get("title_hits"))) + " |"
        )  # fmt: skip
    return "\n".join(lines)


def check_relevant(rel: list, vault: Path, where: str) -> list[dict]:
    out = []
    for item in rel:
        if not isinstance(item, dict) or item.get("grade") not in (1, 2):
            raise ValueError(f"{where}: relevant inválido {item!r}")
        if not isinstance(item.get("path"), str) or not (vault / item["path"]).is_file():
            raise ValueError(f"{where}: nota inexistente {item.get('path')!r}")
        out.append({"path": item["path"], "grade": item["grade"]})
    return out


def resolve(d: dict, dec: dict, date: str, vault: Path, titles: dict[str, str]) -> dict:
    where = d["draft_id"]
    origin = d["origin"]
    text = dec.get("query", d["query"]).strip()
    edited = text != d["query"].strip()
    if not text:
        raise ValueError(f"{where}: query vazia")
    kind = dec.get("kind") or d.get("kind")
    if origin == "shadow":
        if not kind:
            raise ValueError(f"{where}: shadow aprovado exige kind")
        negative = kind == "negative"
    elif origin == "manual":
        negative = kind == "negative"
    else:
        negative = d.get("polarity") == "negative"
        if not negative and kind == "negative":
            raise ValueError(f"{where}: positiva não pode ter kind negative")
        kind = "negative" if negative else (kind or DEFAULT_KIND)
    if kind not in ev.KINDS:
        raise ValueError(f"{where}: kind inválido {kind!r}")
    if negative:
        kind, relevant = "negative", []
    elif origin == "llm":
        if not d.get("from_path"):
            raise ValueError(f"{where}: positiva sem from_path")
        extra = check_relevant(dec.get("relevant") or [], vault, where)
        if any(x["grade"] != 1 for x in extra):
            raise ValueError(f"{where}: relevant extra de rascunho llm só pode ser de grau 1")
        relevant = check_relevant([{"path": d["from_path"], "grade": 2}], vault, where) + [
            x for x in extra if x["path"] != d["from_path"]
        ]
        if edited:
            hits = vg.title_hits(text, titles.get(d["from_path"], ""))
            if hits > gd.MAX_TITLE_HITS:
                raise ValueError(f"{where}: query editada com title_hits={hits}")
    else:
        relevant = check_relevant(dec.get("relevant") or d.get("relevant") or [], vault, where)
        if not any(x["grade"] == 2 for x in relevant):
            raise ValueError(f"{where}: positiva exige ao menos uma nota de grau 2")
    out = copy.deepcopy(d)
    out["status"] = "approved"
    out["polarity"] = "negative" if negative else "positive"
    out["decision"] = {"by": "user", "date": date, "edited": edited, "kind": kind, "relevant": relevant, "query": text}
    return out


def apply_decisions(drafts: list[dict], decisions: list[dict], date: str, vault: Path, titles: dict[str, str]) -> list[dict]:
    """Aplica as decisões do usuário numa cópia dos rascunhos; tudo ou nada."""
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        raise ValueError(f"data inválida {date!r}")
    by_id = {d["draft_id"]: i for i, d in enumerate(drafts)}
    out = copy.deepcopy(drafts)
    for dec in decisions:
        did = dec.get("draft_id")
        if did not in by_id:
            raise ValueError(f"rascunho inexistente {did}")
        d = out[by_id[did]]
        if d["status"] != "pending":
            raise ValueError(f"{did}: status {d['status']}, só pending é decidível")
        verdict = dec.get("decision")
        if verdict == "approve":
            out[by_id[did]] = resolve(d, dec, date, vault, titles)
        elif verdict == "reject":
            d["status"] = "rejected"
            d["decision"] = {"by": "user", "date": date, "edited": False}
        else:
            raise ValueError(f"{did}: decision deve ser approve ou reject, veio {verdict!r}")
    return out


def build_new_rows(approved: list[dict], first_num: int, seed: int, today: str, commit: str) -> list[dict]:
    rows = []
    for i, d in enumerate(sorted(approved, key=lambda x: x["draft_id"])):
        dec = d["decision"]
        rows.append(
            {
                "id": f"q{first_num + i:03d}", "query": dec["query"], "lang": d["lang"] if d.get("lang") in LANGS else "pt",
                "kind": dec["kind"], "source": d["origin"], "validated": True, "repo": None, "relevant": dec["relevant"],
                "split": "dev", "split_seed": seed, "vault_commit": commit, "status": "active", "created": today, "notes": "",
                "approval": {"by": "user", "date": dec["date"], "draft": d["draft_id"], "edited": dec["edited"]},
            }
        )  # fmt: skip
    return rows


def promote(
    *, golden_path: Path, drafts_path: Path, seed: int, vault: Path, today: str,
    commit_fn: Callable[[], str] = git_commit, dry_run: bool = False,
) -> str:  # fmt: skip
    rows, errors = vg.read_jsonl(golden_path)
    if errors:
        raise ValueError(errors[0][1])
    if any("split_seed" in r for r in rows):
        raise ValueError("golden.jsonl já tem split_seed: a divisão é um lote único")
    drafts = gd.read_drafts(drafts_path)
    approved = [d for d in drafts if d.get("status") == "approved"]
    if not approved:
        raise ValueError("nenhum rascunho aprovado")
    nums = [int(m.group(1)) for r in rows if (m := re.fullmatch(r"q(\d+)", str(r.get("id"))))]
    new = build_new_rows(approved, max([FIRST_NEW_ID - 1, *nums]) + 1, seed, today, commit_fn())
    test = [r for r in rows if r.get("status") == "active" and r.get("split") == "test"]
    base_neg = sum(vg.is_negative(r) for r in test)
    splits = vg.assign_splits(new, seed, len(test) - base_neg, base_neg)
    for r in new:
        r["split"] = splits[r["id"]]
    fails = vg.check([*rows, *new], drafts, vault)
    if fails:
        raise ValueError("pisos falharam, nada escrito: " + "; ".join(f"piso {n}: {m}" for n, m in fails))
    lines = ["| id | split | kind | query |", "| --- | --- | --- | --- |"]
    lines += [f"| {r['id']} | {r['split']} | {r['kind']} | {cell(r['query'])} |" for r in new]
    n_test = sum(r["split"] == "test" for r in new)
    lines.append(f"\n{len(new)} novas ({n_test} test, {len(new) - n_test} dev); total {len(rows) + len(new)}")
    if not dry_run:
        text = golden_path.read_text(encoding="utf-8")
        if text and not text.endswith("\n"):
            text += "\n"
        atomic_write(golden_path, text + "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in new))
    return "\n".join(lines)


def load_titles(manifests: Path) -> dict[str, str]:
    return {r["path"]: r["title"] for r in gd.manifest_rows(manifests)}


def main(argv: list[str] | None = None) -> int:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--drafts", type=Path, default=vg.DRAFTS)
    common.add_argument("--vault", type=Path, default=ev.VAULT)
    common.add_argument("--manifests", type=Path, default=ev.MANIFEST_DIR)
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    rev = sub.add_parser("review", parents=[common])
    rev.add_argument("--status", default="pending")
    dec = sub.add_parser("decide", parents=[common])
    dec.add_argument("--file", type=Path, required=True)
    dec.add_argument("--date", required=True)
    pro = sub.add_parser("promote", parents=[common])
    pro.add_argument("--golden", type=Path, default=ev.GOLDEN)
    pro.add_argument("--seed", type=int, required=True)
    pro.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    if args.cmd == "review":
        print(review(gd.read_drafts(args.drafts), load_titles(args.manifests), args.status))
    elif args.cmd == "decide":
        decisions = json.loads(args.file.read_text(encoding="utf-8"))
        if not isinstance(decisions, list):
            raise SystemExit("o arquivo de decisões deve ser uma lista JSON")
        drafts = gd.read_drafts(args.drafts)
        done = apply_decisions(drafts, decisions, args.date, args.vault, load_titles(args.manifests))
        atomic_write(args.drafts, "".join(json.dumps(d, ensure_ascii=False) + "\n" for d in done))
        print(f"{len(decisions)} decisões gravadas em {args.drafts.name}")
    else:
        print(
            promote(
                golden_path=args.golden, drafts_path=args.drafts, seed=args.seed, vault=args.vault,
                today=datetime.date.today().isoformat(), commit_fn=git_commit, dry_run=args.dry_run,
            )
        )  # fmt: skip
    return 0


if __name__ == "__main__":
    sys.exit(main())
