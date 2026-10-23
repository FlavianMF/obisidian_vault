#!/usr/bin/env python3
"""Gera reformulações das queries do golden set com Haiku, uma vez (PRD-003, fase A3).

    python3 00_META/eval/gen_rewrites.py --split dev --dry-run     # mostra os prompts, não chama nada
    python3 00_META/eval/gen_rewrites.py --split dev --limit 1     # uma chamada, confere o modelo
    python3 00_META/eval/gen_rewrites.py --split dev               # completa o que faltar

Idempotente: só chama o modelo para ids sem linha em rewrites.jsonl e nunca reescreve linha
existente. O prompt leva só o texto da query (nunca paths, títulos ou notas do vault), senão o
eval vaza o gabarito. O `claude` roda pelo binário do PATH (nunca pela função do zsh), em cwd
temporário fora do vault, com --safe-mode, sem ferramentas e sem as variáveis da sessão pai.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable, Mapping
from pathlib import Path

import run_eval as ev

MODEL = "haiku"
TIMEOUT = 120
BUDGET_USD = "0.05"

SYSTEM_PROMPT = "Você reformula consultas de busca. Responda só com JSON válido."

PROMPT_HEAD = (
    "Você vai reformular uma consulta de busca. Uma pessoa vai procurar esta consulta numa base de "
    "notas técnicas pessoais, escritas em português e em inglês, com um buscador por palavras-chave.\n"
    "\n"
    "Escreva 3 reformulações da consulta que usem o vocabulário que uma nota sobre o assunto "
    "provavelmente usaria: termos técnicos, nomes de ferramentas e sinônimos. Pelo menos uma "
    "reformulação em português e pelo menos uma em inglês. Cada reformulação tem no máximo 12 "
    "palavras. Não responda à consulta e não invente fatos.\n"
    "\n"
    "Responda só com JSON, sem texto antes ou depois, neste formato:\n"
    '{"rewrites": ["...", "...", "..."]}\n'
    "\n"
    "Consulta: "
)

DROP_ENV = ("CLAUDECODE", "CLAUDE_PID", "CLAUDE_EFFORT")
DROP_ENV_PREFIX = "CLAUDE_CODE_"
FENCE = re.compile(r"^```(?:json)?\s*|\s*```$")


def build_prompt(query: str) -> str:
    return PROMPT_HEAD + query.strip()


def build_command(binary: str, system_prompt: str = SYSTEM_PROMPT, budget: str = BUDGET_USD) -> list[str]:
    # `--tools ""` é variádica: fica por último, e o prompt vai pelo stdin.
    return [
        binary, "-p", "--model", MODEL, "--output-format", "json", "--safe-mode", "--strict-mcp-config",
        "--disable-slash-commands", "--no-session-persistence", "--max-budget-usd", budget,
        "--system-prompt", system_prompt, "--tools", "",
    ]  # fmt: skip


def _dropped(key: str) -> bool:
    return key in DROP_ENV or key.startswith(DROP_ENV_PREFIX)


def child_env(base: Mapping[str, str]) -> dict[str, str]:
    env = {k: v for k, v in base.items() if not _dropped(k)}
    env["SECOND_BRAIN_HOOKS"] = "0"
    env["JEV_TOOL_E"] = "0"
    return env


def parse_envelope(stdout: str) -> tuple[str, str]:
    """Valida o envelope do `claude -p`; devolve (result sem fence, modelos separados por vírgula)."""
    try:
        envelope = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise ValueError("envelope não é JSON") from exc
    if not isinstance(envelope, dict):
        raise ValueError("envelope não é JSON")
    if envelope.get("is_error") or not isinstance(envelope.get("result"), str):
        raise ValueError(f"resposta com erro: subtype={envelope.get('subtype')!r}")
    usage = envelope.get("modelUsage")
    if not isinstance(usage, dict) or not usage:
        raise ValueError("envelope sem modelUsage")
    keys = sorted(usage)
    if not all("haiku" in k.casefold() for k in keys):
        raise ValueError(f"modelo inesperado: {keys}")
    return FENCE.sub("", envelope["result"].strip()), ",".join(keys)


def parse_response(stdout: str, query: str) -> tuple[list[str], str]:
    result, model = parse_envelope(stdout)
    try:
        payload = json.loads(result)
    except json.JSONDecodeError as exc:
        raise ValueError("result não é JSON") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("rewrites"), list):
        raise ValueError("result sem lista rewrites")
    seen = {query.strip().casefold()}
    rewrites: list[str] = []
    for item in payload["rewrites"]:
        if not isinstance(item, str) or not item.strip() or item.strip().casefold() in seen:
            continue
        seen.add(item.strip().casefold())
        rewrites.append(item.strip())
    if len(rewrites) > ev.REWRITES_MAX:
        raise ValueError(f"{len(rewrites)} reformulações; máximo {ev.REWRITES_MAX}")
    if len(rewrites) < ev.REWRITES_MIN:
        raise ValueError(f"{len(rewrites)} reformulações válidas; mínimo {ev.REWRITES_MIN}")
    return rewrites, model


def run_claude(prompt: str, *, binary: str, timeout: int, system_prompt: str = SYSTEM_PROMPT) -> str:
    """Roda o `claude -p` isolado (cwd fora do vault, env limpo) e devolve o stdout."""
    with tempfile.TemporaryDirectory(prefix="gen_rewrites-") as tmp:
        if Path(tmp).resolve().is_relative_to(ev.VAULT):
            raise SystemExit(f"diretório temporário dentro do vault: {tmp}")
        try:
            result = subprocess.run(
                build_command(binary, system_prompt), input=prompt, capture_output=True, text=True,
                timeout=timeout, cwd=tmp, env=child_env(os.environ), check=False,
            )  # fmt: skip
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(f"timeout de {timeout}s") from exc
    if result.returncode != 0:
        raise RuntimeError(f"claude saiu com {result.returncode}: {result.stderr[-300:]}")
    return result.stdout


def call_claude(prompt: str, *, binary: str, timeout: int, query: str | None = None) -> tuple[list[str], str]:
    stdout = run_claude(prompt, binary=binary, timeout=timeout)
    original = query if query is not None else prompt.removeprefix(PROMPT_HEAD)
    return parse_response(stdout, original)


def read_existing(path: Path) -> dict[str, dict]:
    rows: dict[str, dict] = {}
    if not path.is_file():
        return rows
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        where = f"{path.name}:{lineno}"
        ev.validate_rewrite_row(row, where)
        if row["id"] in rows:
            raise ValueError(f"{where} id duplicado {row['id']}")
        rows[row["id"]] = row
    return rows


def pending(queries: list[ev.Query], existing: dict[str, dict]) -> list[ev.Query]:
    todo = []
    for q in queries:
        row = existing.get(q.id)
        if row is None:
            todo.append(q)
        elif row["query"] != q.text:
            raise ValueError(f"{q.id}: query diverge do golden set")
    return todo


def generate(
    queries: list[ev.Query],
    out_path: Path,
    call: Callable[[ev.Query], tuple[list[str], str]],
    today: str,
    existing: dict[str, dict] | None = None,
    on_row: Callable[[dict], None] | None = None,
) -> int:
    existing = read_existing(out_path) if existing is None else existing
    written = 0
    for q in pending(queries, existing):
        rewrites, model = call(q)
        row = {"id": q.id, "query": q.text, "rewrites": rewrites, "model": model, "created": today}
        ev.validate_rewrite_row(row, q.id)
        with out_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            fh.flush()
        written += 1
        if on_row:
            on_row(row)
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--split", choices=["dev", "test", "all"], default="dev")
    parser.add_argument("--dry-run", action="store_true", help="mostra comando e prompts, não chama o claude")
    parser.add_argument("--limit", type=int, default=None, help="só as N primeiras pendentes")
    parser.add_argument("--out", type=Path, default=ev.REWRITES)
    parser.add_argument("--claude", default="claude", help="executável (resolvido com shutil.which)")
    parser.add_argument("--timeout", type=int, default=TIMEOUT)
    args = parser.parse_args(argv)

    binary = shutil.which(args.claude)
    if not binary:
        raise SystemExit(f"executável não encontrado: {args.claude}")
    queries = ev.load_golden(split=args.split)
    todo = pending(queries, read_existing(args.out))
    if args.limit is not None:
        todo = todo[: args.limit]

    if args.dry_run:
        dropped = sorted(k for k in os.environ if _dropped(k))
        print(f"# binário: {binary}")
        print(f"# comando: {shlex.join(build_command(binary))}  (prompt via stdin, cwd temporário fora do vault)")
        print(f"# env removido: {', '.join(dropped) or '(nenhum)'}; definido: SECOND_BRAIN_HOOKS, JEV_TOOL_E")
        print(f"# system prompt: {SYSTEM_PROMPT}")
        print(f"# {len(todo)} queries sem linha em {args.out.name} (split {args.split}); nenhuma chamada feita")
        for q in todo:
            print(f"### {q.id}")
            print(build_prompt(q.text))
        return 0

    def call(q: ev.Query) -> tuple[list[str], str]:
        return call_claude(build_prompt(q.text), binary=binary, timeout=args.timeout, query=q.text)

    def report(row: dict) -> None:
        print(f"{row['id']}  {len(row['rewrites'])} reformulações  {row['model']}")

    total = generate(todo, args.out, call, datetime.date.today().isoformat(), on_row=report)
    print(f"{total} linhas novas em {args.out.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
