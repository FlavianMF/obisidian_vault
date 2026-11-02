from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import projects


def bootstrap(
    vault: Path,
    state_dir: Path,
    slug: str | None = None,
    all_projects: bool = False,
    apply: bool = False,
) -> int:
    issues = projects.validate(vault)
    errors = [i for i in issues if i.severity == "ERROR"]
    if errors:
        sys.stderr.write("sb projects bootstrap: manifesto com erros de validação, abortando:\n")
        for e in errors:
            sys.stderr.write(f"  {e.severity} {e.check} {e.path}: {e.detail}\n")
        return 1

    try:
        manifest = projects.load_manifest(vault)
    except Exception as exc:
        sys.stderr.write(f"sb projects bootstrap: erro ao carregar manifesto: {exc}\n")
        return 1

    if not slug and not all_projects:
        sys.stderr.write("sb projects bootstrap: especifique um slug ou use --all\n")
        return 1

    if all_projects:
        targets = manifest.projects
    else:
        targets = [p for p in manifest.projects if p.get("slug") == slug]
        if not targets:
            valid = ", ".join(sorted(p.get("slug", "") for p in manifest.projects))
            sys.stderr.write(f"sb projects bootstrap: slug desconhecido '{slug}'. Slugs válidos: {valid}\n")
            return 1

    if not apply:
        sys.stdout.write("Plano de bootstrap (dry run, use --apply para executar):\n")
        for p in targets:
            s = p.get("slug", "")
            repo = p.get("repo", "")
            chk = p.get("checkout", "")
            branch = p.get("branch", "master")
            setup_cmds = p.get("setup", [])
            envs = p.get("env", [])
            chk_path = Path(os.path.expanduser(chk))

            sys.stdout.write(f"\nProjeto: {s}\n")
            if not chk_path.exists():
                sys.stdout.write(f"  [clone] git clone {repo} {chk}\n")
            else:
                sys.stdout.write(f"  [checkout] já existe em {chk}\n")
            sys.stdout.write(f"  [branch] git checkout {branch} (se working tree estiver limpo)\n")
            if setup_cmds:
                for c in setup_cmds:
                    sys.stdout.write(f"  [setup] {c}\n")
            if envs:
                for e in envs:
                    st = "presente" if e in os.environ else "ausente"
                    sys.stdout.write(f"  [env] {e}: {st}\n")
        return 0

    results = {}
    now = dt.datetime.now().isoformat()

    for p in targets:
        s = p.get("slug", "")
        repo = p.get("repo", "")
        chk = p.get("checkout", "")
        branch = p.get("branch", "master")
        setup_cmds = p.get("setup", [])
        envs = p.get("env", [])
        chk_path = Path(os.path.expanduser(chk))

        sys.stdout.write(f"== Executando bootstrap para {s}\n")
        p_res: dict[str, Any] = {
            "slug": s,
            "ts": now,
            "clone": "skipped",
            "branch": "skipped",
            "setup": [],
            "env": {},
        }

        # 1. Clone se checkout não existir
        if not chk_path.exists():
            chk_path.parent.mkdir(parents=True, exist_ok=True)
            sys.stdout.write(f"  Clonando {repo} para {chk_path}...\n")
            c_proc = subprocess.run(
                ["git", "clone", repo, str(chk_path)],
                capture_output=True,
                text=True,
                check=False,
            )
            if c_proc.returncode != 0:
                sys.stderr.write(f"  Erro ao clonar {repo}: {c_proc.stderr}\n")
                p_res["clone"] = "failed"
                results[s] = p_res
                continue
            p_res["clone"] = "ok"
        else:
            p_res["clone"] = "already_exists"

        # 2. Confere branch (só muda se limpa, se suja só avisa)
        try:
            status_out = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=chk_path,
                capture_output=True,
                text=True,
                check=False,
            ).stdout.strip()
            if status_out:
                sys.stdout.write(f"  Aviso: working tree de {s} está sujo. Não trocando de branch.\n")
                p_res["branch"] = "dirty_skipped"
            else:
                b_proc = subprocess.run(
                    ["git", "checkout", branch],
                    cwd=chk_path,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                p_res["branch"] = "ok" if b_proc.returncode == 0 else "failed"
        except Exception as exc:
            p_res["branch"] = f"error: {exc}"

        # 3. Setup commands (timeout 900s)
        for cmd in setup_cmds:
            sys.stdout.write(f"  Rodando setup: {cmd}\n")
            try:
                s_proc = subprocess.run(
                    cmd,
                    shell=True,
                    cwd=chk_path,
                    timeout=900,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                p_res["setup"].append({
                    "command": cmd,
                    "status": "ok" if s_proc.returncode == 0 else "failed",
                    "code": s_proc.returncode,
                })
            except subprocess.TimeoutExpired:
                sys.stderr.write(f"  Timeout de 900s excedido em: {cmd}\n")
                p_res["setup"].append({"command": cmd, "status": "timeout"})
            except Exception as exc:
                p_res["setup"].append({"command": cmd, "status": f"error: {exc}"})

        # 4. Check env vars (NUNCA mostrar valor)
        for e in envs:
            st = "presente" if e in os.environ else "ausente"
            sys.stdout.write(f"  Variável de ambiente {e}: {st}\n")
            p_res["env"][e] = st

        results[s] = p_res

    # 3. Grava o resultado no snapshot projects.json, campo bootstrap
    state_dir.mkdir(parents=True, exist_ok=True)
    snap_file = state_dir / "projects.json"
    snap_data = {"ts": now, "quota": {}, "projects": []}
    if snap_file.exists():
        try:
            snap_data = json.loads(snap_file.read_text(encoding="utf-8"))
        except Exception:
            pass

    if "bootstrap" not in snap_data:
        snap_data["bootstrap"] = {}
    snap_data["bootstrap"].update(results)

    fd, tmp = tempfile.mkstemp(dir=str(state_dir), prefix="tmp_snap_")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(snap_data, f, ensure_ascii=False, indent=2)
    os.chmod(tmp, 0o600)
    os.replace(tmp, str(snap_file))

    sys.stdout.write("Bootstrap finalizado com sucesso.\n")
    return 0
