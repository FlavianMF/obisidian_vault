#!/usr/bin/env python3
"""A/B cego do pacote de contexto (RFC-002 §5, etapa E3).

Uso:
  ab_ctxpack.py plan <tasks.tsv> [--reps N]
                                   sorteia a ordem dos braços em N pares por tarefa (2N sessões)
  ab_ctxpack.py launch             abre a próxima sessão pendente: claude --session-id <uuid> "<prompt>"
  ab_ctxpack.py run [--model M] [--budget USD]
                                   roda a próxima sessão pendente sem interação (claude -p, só leitura)
                                   e guarda a resposta final em out/<uuid>.txt para a nota
  ab_ctxpack.py requeue <uuid>     dá novo uuid a uma sessão que não terminou (mesmo braço)
  ab_ctxpack.py status             sessões e notas, sem revelar o braço
  ab_ctxpack.py grade <uuid> pass|fail
  ab_ctxpack.py report [--reveal]  revela os braços, soma usage_baseline.sh e aplica o critério de saída

tasks.tsv: uma tarefa por linha, "id<TAB>diretório<TAB>prompt" (prompt numa linha só, # comenta).
Braços: controle SB_CTXPACK=shadow (grava e não injeta), tratamento SB_CTXPACK=active.
O estado fica em ${SECOND_BRAIN_STATE_DIR:-~/.local/state/second-brain}/ab/ctxpack/, modo 0600.
O report lê só a usage numérica e a contagem de Read, nunca o conteúdo dos transcripts.
"""

import argparse
import csv
import os
import random
import subprocess
import sys
import uuid
from pathlib import Path

ARMS = ("shadow", "active")
RUNS = "runs.tsv"
GRADES = "grades.tsv"
FIELDS = ["task", "rep", "slot", "session", "arm", "cwd", "prompt"]
READ_ONLY_TOOLS = "Read Grep Glob Agent"
BASELINE = Path(__file__).with_name("usage_baseline.sh")
MIN_SUBAGENTS = 2
REREAD_DROP = 0.30
SUB_EQ_DROP = 0.10


def state_dir(env=os.environ) -> Path:
    base = env.get("SECOND_BRAIN_STATE_DIR") or str(Path.home() / ".local/state/second-brain")
    return Path(base) / "ab" / "ctxpack"


def write_private(path: Path, rows: list, fields: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def read_rows(path: Path) -> list:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def load_tasks(path: Path) -> list:
    tasks = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) != 3 or not all(p.strip() for p in parts):
            raise ValueError(f"{path}:{n}: esperado id<TAB>diretório<TAB>prompt")
        task, cwd, prompt = (p.strip() for p in parts)
        cwd = str(Path(cwd).expanduser())
        if not Path(cwd).is_dir():
            raise ValueError(f"{path}:{n}: diretório inexistente: {cwd}")
        tasks.append({"task": task, "cwd": cwd, "prompt": prompt})
    if len({t["task"] for t in tasks}) != len(tasks):
        raise ValueError(f"{path}: id de tarefa repetido")
    return tasks


def plan(tasks: list, rng: random.Random, reps: int = 1) -> list:
    """reps pares por tarefa, cada par com os dois braços em ordem sorteada."""
    runs = []
    for t in tasks:
        for rep in range(1, reps + 1):
            arms = list(ARMS)
            rng.shuffle(arms)
            for i, arm in enumerate(arms):
                slot = f"{2 * (rep - 1) + i + 1}/{2 * reps}"
                runs.append({**t, "rep": str(rep), "slot": slot, "session": str(uuid.uuid4()), "arm": arm})
    return runs


def transcript(session: str, projects: Path):
    hits = sorted(projects.glob(f"*/{session}.jsonl"))
    return hits[0] if hits else None


def pending(runs: list, projects: Path):
    return next((r for r in runs if transcript(r["session"], projects) is None), None)


def baseline(flag: str, path: Path) -> list:
    out = subprocess.run(["bash", str(BASELINE), flag, str(path)], capture_output=True, text=True, check=True)
    return [line.split("\t") for line in out.stdout.splitlines()]


def measure(path: Path) -> dict:
    main_eq = sub_eq = subs = 0
    for row in baseline("--sidechain", path):
        if len(row) == 10 and row[1] == "main":
            main_eq += int(row[9])
        elif len(row) == 10 and row[1] == "sub":
            sub_eq += int(row[9])
            subs += 1
    reads_sub = repeated = 0
    for row in baseline("--rereads", path):
        reads_sub += int(row[2])
        repeated += int(row[3])
    return {"main_eq": main_eq, "sub_eq": sub_eq, "subs": subs, "reads_sub": reads_sub, "repeated": repeated}


def drop(control: float, treatment: float):
    return None if control == 0 else (control - treatment) / control


def verdict(rows: list) -> dict:
    """rows: dicts com task, rep, arm, grade e as métricas de measure(). Só pares completos e válidos contam."""
    by_task = {}
    for r in rows:
        by_task.setdefault(f"{r['task']}#{r.get('rep') or 1}", {})[r["arm"]] = r
    valid, invalid = [], []
    for task, arms in sorted(by_task.items()):
        if set(arms) != set(ARMS) or any(a.get("subs") is None for a in arms.values()):
            invalid.append((task, "sessão faltando"))
        elif any(a["subs"] < MIN_SUBAGENTS for a in arms.values()):
            invalid.append((task, f"menos de {MIN_SUBAGENTS} subagentes"))
        else:
            valid.append(arms)
    total = {arm: {k: sum(v[arm][k] for v in valid) for k in ("main_eq", "sub_eq", "reads_sub", "repeated")} for arm in ARMS}
    regressions = [v["active"]["task"] for v in valid if v["active"]["grade"] == "fail" and v["shadow"]["grade"] == "pass"]
    ungraded = [v[a]["task"] for v in valid for a in ARMS if v[a]["grade"] not in ("pass", "fail")]
    reread = drop(total["shadow"]["repeated"], total["active"]["repeated"])
    sub_eq = drop(total["shadow"]["sub_eq"], total["active"]["sub_eq"])
    if not valid or ungraded:
        decision = "incompleto"
    elif regressions or reread is None or sub_eq is None or reread < REREAD_DROP or sub_eq < SUB_EQ_DROP:
        decision = "desliga: mude o padrão de SB_CTXPACK para shadow"
    else:
        decision = "mantém active"
    return {"valid": len(valid), "invalid": invalid, "total": total, "reread_drop": reread,
            "sub_eq_drop": sub_eq, "regressions": regressions, "ungraded": ungraded, "decision": decision}


def pct(value) -> str:
    return "n/a" if value is None else f"{value:+.1%}"


def cmd_plan(args, sd: Path) -> int:
    if read_rows(sd / RUNS) and not args.force:
        print(f"já existe {sd / RUNS}; use --force para sortear de novo", file=sys.stderr)
        return 1
    runs = plan(load_tasks(Path(args.tasks)), random.Random(args.seed), args.reps)
    write_private(sd / RUNS, runs, FIELDS)
    write_private(sd / GRADES, [], ["session", "grade"])
    print(f"{len(runs)} sessões planejadas em {sd / RUNS}. Rode: ab_ctxpack.py launch")
    return 0


def cmd_launch(args, sd: Path, projects: Path) -> int:
    run = pending(read_rows(sd / RUNS), projects)
    if run is None:
        print("nenhuma sessão pendente. Dê as notas e rode: ab_ctxpack.py report")
        return 0
    print(f"tarefa {run['task']} sessão {run['slot']} ({run['session']}). Sessão nova: não use /resume.")
    env = {**os.environ, "SB_CTXPACK": run["arm"]}
    os.chdir(run["cwd"])
    os.execvpe("claude", ["claude", "--session-id", run["session"], run["prompt"]], env)


def headless_argv(run: dict, model: str, budget: str) -> list:
    return ["claude", "-p", "--session-id", run["session"], "--output-format", "text",
            "--model", model, "--max-budget-usd", budget, f"--allowedTools={READ_ONLY_TOOLS}"]


def cmd_run(args, sd: Path, projects: Path) -> int:
    run = pending(read_rows(sd / RUNS), projects)
    if run is None:
        print("nenhuma sessão pendente. Dê as notas e rode: ab_ctxpack.py report")
        return 0
    print(f"tarefa {run['task']} sessão {run['slot']} ({run['session']})", flush=True)
    env = {**os.environ, "SB_CTXPACK": run["arm"]}
    # O prompt vai pelo stdin: --allowedTools aceita vários valores e engoliria um prompt posicional.
    done = subprocess.run(headless_argv(run, args.model, args.budget), cwd=run["cwd"], env=env, input=run["prompt"],
                          capture_output=True, text=True, timeout=args.timeout)
    out = sd / "out" / f"{run['session']}.txt"
    out.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    for path, text in ((out, done.stdout), (out.with_suffix(".err"), done.stderr)):
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
    print(f"exit {done.returncode}. Resposta em {out}" + (f", stderr em {out.with_suffix('.err')}" if done.returncode else ""))
    return done.returncode


def cmd_status(args, sd: Path, projects: Path) -> int:
    grades = {g["session"]: g["grade"] for g in read_rows(sd / GRADES)}
    for r in read_rows(sd / RUNS):
        done = "feita" if transcript(r["session"], projects) else "pendente"
        print(f"{r['task']}\t{r['slot']}\t{r['session']}\t{done}\t{grades.get(r['session'], '-')}")
    return 0


def cmd_grade(args, sd: Path) -> int:
    runs = [r for r in read_rows(sd / RUNS) if r["session"].startswith(args.session)]
    if len(runs) != 1:
        print(f"prefixo {args.session!r} casa com {len(runs)} sessões", file=sys.stderr)
        return 1
    grades = {g["session"]: g["grade"] for g in read_rows(sd / GRADES)}
    grades[runs[0]["session"]] = args.grade
    write_private(sd / GRADES, [{"session": s, "grade": g} for s, g in grades.items()], ["session", "grade"])
    print(f"{runs[0]['task']} sessão {runs[0]['slot']}: {args.grade}")
    return 0


def cmd_requeue(args, sd: Path) -> int:
    """Troca o uuid de uma sessão que não terminou (ex.: limite da conta). O braço fica o mesmo e oculto."""
    runs = read_rows(sd / RUNS)
    hits = [r for r in runs if r["session"].startswith(args.session)]
    if len(hits) != 1:
        print(f"prefixo {args.session!r} casa com {len(hits)} sessões", file=sys.stderr)
        return 1
    old = hits[0]["session"]
    hits[0]["session"] = str(uuid.uuid4())
    write_private(sd / RUNS, runs, FIELDS)
    grades = [g for g in read_rows(sd / GRADES) if g["session"] != old]
    write_private(sd / GRADES, grades, ["session", "grade"])
    print(f"{hits[0]['task']} sessão {hits[0]['slot']}: {old[:8]} -> {hits[0]['session']} (pendente)")
    return 0


def cmd_report(args, sd: Path, projects: Path) -> int:
    grades = {g["session"]: g["grade"] for g in read_rows(sd / GRADES)}
    runs = read_rows(sd / RUNS)
    if not args.reveal and any(r["session"] not in grades for r in runs):
        print("há sessão sem nota: o report revela os braços. Dê todas as notas ou use --reveal", file=sys.stderr)
        return 1
    rows = []
    for r in runs:
        path = transcript(r["session"], projects)
        metrics = measure(path) if path else {"subs": None}
        rows.append({**r, **metrics, "grade": grades.get(r["session"], "-")})
        if path:
            print(f"{r['task']}#{r.get('rep') or 1}\t{r['arm']}\t{rows[-1]['grade']}\t"
                  f"main_eq={metrics['main_eq']}\tsub_eq={metrics['sub_eq']}\tsubs={metrics['subs']}\t"
                  f"reads_sub={metrics['reads_sub']}\trepeated={metrics['repeated']}")
    v = verdict(rows)
    for arm in ARMS:
        print(f"total {arm}\t" + "\t".join(f"{k}={n}" for k, n in v["total"][arm].items()))
    print(f"tarefas válidas: {v['valid']}  inválidas: {v['invalid'] or '-'}")
    print(f"queda das releituras: {pct(v['reread_drop'])} (piso {REREAD_DROP:.0%})")
    print(f"queda do sub_eq: {pct(v['sub_eq_drop'])} (piso {SUB_EQ_DROP:.0%})")
    print(f"regressões (active falhou, shadow passou): {v['regressions'] or '-'}")
    if v["ungraded"]:
        print(f"sem nota: {sorted(set(v['ungraded']))}")
    print(f"decisão D1: {v['decision']}")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="ab_ctxpack", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--projects", default=str(Path.home() / ".claude/projects"), help=argparse.SUPPRESS)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan")
    p.add_argument("tasks")
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--force", action="store_true")
    p.add_argument("--reps", type=int, default=1)
    sub.add_parser("launch")
    r = sub.add_parser("run")
    r.add_argument("--model", default="sonnet")
    r.add_argument("--budget", default="3")
    r.add_argument("--timeout", type=int, default=1800)
    sub.add_parser("requeue").add_argument("session")
    sub.add_parser("status")
    g = sub.add_parser("grade")
    g.add_argument("session")
    g.add_argument("grade", choices=("pass", "fail"))
    sub.add_parser("report").add_argument("--reveal", action="store_true")
    args = parser.parse_args(argv)
    sd, projects = state_dir(), Path(args.projects)
    try:
        if args.cmd == "plan":
            return cmd_plan(args, sd)
        if args.cmd == "launch":
            return cmd_launch(args, sd, projects)
        if args.cmd == "run":
            return cmd_run(args, sd, projects)
        if args.cmd == "requeue":
            return cmd_requeue(args, sd)
        if args.cmd == "status":
            return cmd_status(args, sd, projects)
        if args.cmd == "grade":
            return cmd_grade(args, sd)
        return cmd_report(args, sd, projects)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
