#!/usr/bin/env python3
"""Gera rascunhos de queries para o golden set (PRD-004, B1). Nunca escreve no golden.jsonl.

    python3 00_META/eval/gen_drafts.py positives --n 24 --dry-run   # mostra os prompts, não chama nada
    python3 00_META/eval/gen_drafts.py positives --n 24 --limit 1   # uma chamada (Haiku)
    python3 00_META/eval/gen_drafts.py negatives                    # 4 áreas, 5 perguntas por chamada
    python3 00_META/eval/gen_drafts.py shadow                       # filtro local do log do shadow, sem LLM
    python3 00_META/eval/gen_drafts.py manual --query "..." --kind negative

Cada rascunho vai para drafts.jsonl com status `pending` (ou `auto_rejected`, com `reason`). Quem aprova é
o usuário, depois, por promote_drafts.py. Este módulo não importa ranqueador nem lê resultado de busca: o
rótulo de uma positiva vem da nota de origem, nunca de um rank (piso 7). Do log do shadow só se lê o texto
da pergunta e o carimbo de tempo.
"""

from __future__ import annotations

import argparse
import collections
import datetime
import hashlib
import json
import os
import random
import re
import shlex
import shutil
import sys
from pathlib import Path

import gen_rewrites as gr
import run_eval as ev
import validate_golden as vg

SEED = 20261023
SYSTEM_PROMPT = "Você escreve perguntas de busca realistas. Responda só com JSON válido."
POOL_TYPES = ("pattern", "trap", "decision", "concept", "permanent", "article")
NEG_AREAS = (
    "frontend e CSS",
    "bancos de dados e SQL",
    "infraestrutura, Docker e CI",
    "linguagens, testes e ferramentas de linha de comando",
)
NEG_PER_CALL = 5
TOP_TAGS = 40
MAX_TITLE_HITS = 1
MIN_SHADOW_WORDS = 6
SHADOW_LOG_LIMIT = 300
SHADOW_DEFAULT = Path.home() / ".local/state/second-brain/shadow.jsonl"
MANIFEST_CELLS = 8
FLAVORS = ("near", "far")


def build_positive_prompt(title: str, summary: str, forbidden: list[str]) -> str:
    return (
        "Um desenvolvedor tem um problema que a nota abaixo resolve, mas ainda não conhece a nota. "
        "Escreva **uma** pergunta que ele digitaria num buscador de notas pessoais, descrevendo o sintoma "
        "ou a situação, não o nome da solução. Máximo de 15 palavras. "
        f"Não use nenhuma destas palavras nem variações: {', '.join(forbidden) or '(nenhuma)'}. "
        "Pode usar no máximo um nome de ferramenta. Português, com termos técnicos em inglês quando for natural.\n"
        'Responda só com JSON: {"query": "...", "lang": "pt|en"}\n'
        f"Título: {title}\n"
        f"Resumo: {summary}"
    )


def build_negative_prompt(area: str, top_tags: list[str]) -> str:
    return (
        f"Uma base de notas técnicas pessoais cobre estes temas: {', '.join(top_tags)}.\n"
        f"Escreva {NEG_PER_CALL} perguntas de desenvolvedor sobre {area} que essa base provavelmente **não** "
        "responde: 2 ou 3 `near` (mesma stack dos temas, problema específico diferente) e o resto `far`. "
        "Máximo de 15 palavras cada.\n"
        'Responda só com JSON: {"queries": [{"query": "...", "flavor": "near|far", "lang": "pt|en"}]}'
    )


def manifest_rows(manifest_dir: Path) -> list[dict]:
    """Linhas dos manifests por tipo; linha com número de células diferente de 8 é ignorada."""
    out: list[dict] = []
    for file in sorted(manifest_dir.glob("*.md")):
        for line in file.read_text(encoding="utf-8").splitlines():
            if not line.startswith("| "):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) != MANIFEST_CELLS or cells[0] in ("Path", "") or set(cells[0]) == {"-"}:
                continue
            tags = [t.strip() for t in cells[2].split(",") if t.strip()]
            out.append({"path": cells[0], "title": cells[1], "tags": tags, "type": file.stem, "summary": cells[7]})
    return out


def positive_pool(rows: list[dict], used_paths: set[str], drafted: set[str]) -> list[dict]:
    pool: dict[str, dict] = {}
    for r in rows:
        if r["type"] not in POOL_TYPES or not r["summary"] or r["path"].startswith("00_META/"):
            continue
        if r["path"] in used_paths or r["path"] in drafted:
            continue
        pool.setdefault(r["path"], r)
    return [pool[p] for p in sorted(pool)]


def top_tags(rows: list[dict], n: int = TOP_TAGS) -> list[str]:
    counts = collections.Counter(t for r in rows for t in r["tags"])
    return [t for t, _ in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:n]]


def filter_shadow(rows: list[dict]) -> list[tuple[str, str]]:
    """Pares (ts, prompt) que passam o filtro determinístico. Só lê `prompt` e `ts`."""
    out: list[tuple[str, str]] = []
    seen: set[str] = set()
    for row in rows:
        raw, ts = row.get("prompt"), row.get("ts")
        if not isinstance(raw, str) or not isinstance(ts, str):
            continue
        text = raw.strip()
        if text.startswith("<") or len(text.split()) < MIN_SHADOW_WORDS:
            continue
        if re.match(r"^q\d+\.", text, re.IGNORECASE) or len(raw) >= SHADOW_LOG_LIMIT:
            continue
        key = vg.norm_query(text)
        if key in seen:
            continue
        seen.add(key)
        out.append((ts, text))
    return out


def read_drafts(path: Path) -> list[dict]:
    rows: list[dict] = []
    if not path.is_file():
        return rows
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path.name}:{lineno} linha não é JSON") from exc
    return rows


def read_golden(path: Path) -> list[dict]:
    rows, errors = vg.read_jsonl(path)
    if errors:
        raise ValueError(errors[0][1])
    return rows


def next_id(drafts: list[dict]) -> str:
    nums = [int(m.group(1)) for d in drafts if (m := re.fullmatch(r"d(\d+)", str(d.get("draft_id", ""))))]
    return f"d{max(nums, default=0) + 1:03d}"


def new_draft(drafts: list[dict], **fields) -> dict:
    row = {
        "draft_id": next_id(drafts), "origin": None, "polarity": None, "query": None, "lang": None,
        "from_path": None, "title_hits": None, "flavor": None, "shadow_ts": None, "model": None,
        "created": datetime.date.today().isoformat(), "status": "pending", "reason": "", "decision": None,
    }  # fmt: skip
    row.update(fields)
    return row


def append_draft(path: Path, drafts: list[dict], row: dict) -> None:
    drafts.append(row)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        fh.flush()


def parse_payload(result: str) -> dict:
    try:
        payload = json.loads(result)
    except json.JSONDecodeError as exc:
        raise ValueError("result não é JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError("result não é objeto JSON")
    return payload


def query_text(item: object) -> str:
    text = item.get("query") if isinstance(item, dict) else None
    if not isinstance(text, str) or not text.strip():
        raise ValueError("resposta sem campo query")
    return text.strip()


def print_header(binary: str, count: int, label: str) -> None:
    dropped = sorted(k for k in os.environ if gr._dropped(k))
    print(f"# binário: {binary}")
    print(f"# comando: {shlex.join(gr.build_command(binary, SYSTEM_PROMPT))}  (prompt via stdin, cwd temporário fora do vault)")
    print(f"# env removido: {', '.join(dropped) or '(nenhum)'}; definido: SECOND_BRAIN_HOOKS, JEV_TOOL_E")
    print(f"# system prompt: {SYSTEM_PROMPT}")
    print(f"# {count} chamadas ({label}); nenhuma feita")


def known_queries(golden: list[dict], drafts: list[dict]) -> set[str]:
    return {vg.norm_query(r["query"]) for r in [*golden, *drafts] if isinstance(r.get("query"), str)}


def find_binary(name: str) -> str:
    binary = shutil.which(name)
    if not binary:
        raise SystemExit(f"executável não encontrado: {name}")
    return binary


def call(prompt: str, binary: str, timeout: int) -> tuple[dict, str]:
    stdout = gr.run_claude(prompt, binary=binary, timeout=timeout, system_prompt=SYSTEM_PROMPT)
    result, model = gr.parse_envelope(stdout)
    return parse_payload(result), model


def cmd_positives(args: argparse.Namespace) -> int:
    rows = manifest_rows(args.manifests)
    golden = read_golden(args.golden)
    drafts = read_drafts(args.drafts)
    used = {rel["path"] for g in golden for rel in g.get("relevant", [])}
    pool = positive_pool(rows, used, {d["from_path"] for d in drafts if d.get("from_path")})
    chosen = random.Random(args.seed).sample(pool, min(args.n, len(pool)))
    if args.limit is not None:
        chosen = chosen[: args.limit]
    prompts = [(r, build_positive_prompt(r["title"], r["summary"], vg.rank_terms(r["title"]))) for r in chosen]
    binary = find_binary(args.claude)
    if args.dry_run:
        print_header(binary, len(prompts), "positivas")
        for r, prompt in prompts:
            print(f"### {r['path']}")
            print(prompt)
        return 0
    seen = known_queries(golden, drafts)
    for r, prompt in prompts:
        payload, model = call(prompt, binary, args.timeout)
        text = query_text(payload)
        hits = vg.title_hits(text, r["title"])
        status, reason = "pending", ""
        if vg.norm_query(text) in seen:
            status, reason = "auto_rejected", "duplicata"
        elif hits > MAX_TITLE_HITS:
            status, reason = "auto_rejected", f"title_hits={hits}"
        seen.add(vg.norm_query(text))
        row = new_draft(
            drafts, origin="llm", polarity="positive", query=text, lang=payload.get("lang"), from_path=r["path"],
            title_hits=hits, model=model, status=status, reason=reason,
        )  # fmt: skip
        append_draft(args.drafts, drafts, row)
        print(f"{row['draft_id']}  {row['status']:<13} {row['from_path']}")
    return 0


def cmd_negatives(args: argparse.Namespace) -> int:
    tags = top_tags(manifest_rows(args.manifests))
    golden = read_golden(args.golden)
    drafts = read_drafts(args.drafts)
    done = {d["area"] for d in drafts if d.get("area")}
    areas = [a for a in args.areas if a not in done]
    if args.limit is not None:
        areas = areas[: args.limit]
    binary = find_binary(args.claude)
    if args.dry_run:
        print_header(binary, len(areas), "negativas")
        for area in areas:
            print(f"### neg:{area}")
            print(build_negative_prompt(area, tags))
        return 0
    seen = known_queries(golden, drafts)
    for area in areas:
        payload, model = call(build_negative_prompt(area, tags), binary, args.timeout)
        items = payload.get("queries")
        if not isinstance(items, list) or not items:
            raise ValueError("resposta sem lista queries")
        for item in items[:NEG_PER_CALL]:
            text = query_text(item)
            flavor = item.get("flavor")
            if flavor not in FLAVORS:
                raise ValueError(f"flavor inválido {flavor!r}")
            dup = vg.norm_query(text) in seen
            seen.add(vg.norm_query(text))
            row = new_draft(
                drafts, origin="llm", polarity="negative", query=text, lang=item.get("lang"), flavor=flavor, model=model,
                status="auto_rejected" if dup else "pending", reason="duplicata" if dup else "", area=area,
            )  # fmt: skip
            append_draft(args.drafts, drafts, row)
            print(f"{row['draft_id']}  {row['status']:<13} neg:{area}")
    return 0


def cmd_shadow(args: argparse.Namespace) -> int:
    if not args.shadow.is_file():
        raise SystemExit(f"log do shadow não encontrado: {args.shadow}")
    log_rows = []
    for line in args.shadow.read_text(encoding="utf-8").splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            log_rows.append(row)
    golden = read_golden(args.golden)
    drafts = read_drafts(args.drafts)
    have = {d["shadow_ts"] + ":" + hashlib.sha1(d["query"].encode()).hexdigest() for d in drafts if d.get("shadow_ts")}
    seen = known_queries(golden, drafts)
    todo = []
    for ts, text in filter_shadow(log_rows):
        key = ts + ":" + hashlib.sha1(text.encode()).hexdigest()
        if key not in have and vg.norm_query(text) not in seen:
            todo.append((ts, text))
    if args.limit is not None:
        todo = todo[: args.limit]
    if args.dry_run:
        print(f"# {len(todo)} candidatos do shadow; nada gravado")
        for ts, text in todo:
            print(f"- {ts}  {text}")
        return 0
    for ts, text in todo:
        row = new_draft(drafts, origin="shadow", query=text, shadow_ts=ts)
        append_draft(args.drafts, drafts, row)
        print(f"{row['draft_id']}  pending        shadow {ts}")
    return 0


def cmd_manual(args: argparse.Namespace) -> int:
    if args.kind not in ev.KINDS:
        raise SystemExit(f"--kind inválido: {args.kind}")
    relevant = []
    for spec in args.relevant or []:
        path, _, grade = spec.rpartition(":")
        if not path or grade not in ("1", "2"):
            raise SystemExit(f"--relevant espera PATH:GRADE (1 ou 2): {spec!r}")
        relevant.append({"path": path, "grade": int(grade)})
    drafts = read_drafts(args.drafts)
    if vg.norm_query(args.query) in known_queries(read_golden(args.golden), drafts):
        print("query já existe no golden ou nos rascunhos; nada gravado")
        return 0
    neg = args.kind == "negative"
    row = new_draft(
        drafts, origin="manual", polarity="negative" if neg else "positive", query=args.query.strip(),
        kind=args.kind, relevant=[] if neg else relevant,
    )  # fmt: skip
    if args.dry_run:
        print(json.dumps(row, ensure_ascii=False))
        return 0
    append_draft(args.drafts, drafts, row)
    print(f"{row['draft_id']}  pending        manual")
    return 0


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--drafts", type=Path, default=vg.DRAFTS)
    common.add_argument("--golden", type=Path, default=ev.GOLDEN)
    common.add_argument("--manifests", type=Path, default=ev.MANIFEST_DIR)
    common.add_argument("--dry-run", action="store_true", help="mostra prompts/candidatos, não chama nem grava")
    common.add_argument("--limit", type=int, default=None, help="só as N primeiras chamadas/linhas")
    common.add_argument("--claude", default="claude", help="executável (resolvido com shutil.which)")
    common.add_argument("--timeout", type=int, default=gr.TIMEOUT)
    common.add_argument("--seed", type=int, default=SEED)
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    pos = sub.add_parser("positives", parents=[common])
    pos.add_argument("--n", type=int, default=24)
    pos.set_defaults(func=cmd_positives)
    neg = sub.add_parser("negatives", parents=[common])
    neg.add_argument("--areas", nargs="+", default=list(NEG_AREAS))
    neg.set_defaults(func=cmd_negatives)
    sh = sub.add_parser("shadow", parents=[common])
    sh.add_argument("--shadow", type=Path, default=SHADOW_DEFAULT)
    sh.set_defaults(func=cmd_shadow)
    man = sub.add_parser("manual", parents=[common])
    man.add_argument("--query", required=True)
    man.add_argument("--kind", required=True)
    man.add_argument("--relevant", action="append", metavar="PATH:GRADE")
    man.set_defaults(func=cmd_manual)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
