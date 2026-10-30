"""Start the review web app on a throwaway vault and state dir, for browser smoke tests.

    python3 dev_sandbox.py [--port 8765] [--count 6]

Never touches the real vault or queue. Prints the URL, then serves until interrupted.
"""
from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path

import candidates
import web_service

HERE = Path(__file__).resolve().parent
NOTE = """---
title: {title}
type: concept
tags: [jira, rest]
created: 2026-10-14
provenance: manual
confidence: medium
---

# {title}

Corpo da nota.
"""
BODY = "Contexto e receita.\n\n## O que NÃO funcionou\n\nNada falhou no teste.\n"


def git(vault: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(vault), *args], check=True, capture_output=True, text=True)


def build(root: Path, count: int = 6) -> tuple[Path, Path]:
    vault, state, remote = root / "vault", root / "state", root / "remote.git"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "master", str(remote)], check=True)
    subprocess.run(["git", "init", "-q", "-b", "master", str(vault)], check=True)
    git(vault, "config", "user.email", "sandbox@example.com")
    git(vault, "config", "user.name", "sandbox")
    git(vault, "remote", "add", "origin", str(remote))
    notes = vault / "20_Permanent_Notes"
    notes.mkdir()
    (notes / "Importar Issues no Jira por REST.md").write_text(NOTE.format(title="Importar Issues no Jira por REST"), encoding="utf-8")
    subprocess.run(["python3", str(HERE / "generate_manifests.py"), "--vault-path", str(vault)], check=True, capture_output=True)
    git(vault, "add", "-A")
    git(vault, "commit", "-q", "-m", "init")
    git(vault, "push", "-q", "origin", "master")
    state.mkdir()
    kinds = ["trap", "pattern", "decision", "concept"]
    for n in range(count):
        candidates.add(state, kind=kinds[n % 4], title=f"Candidato de teste número {n} distinto", summary=f"Resumo {n} do candidato",
                       project="projeto_x", body=BODY if n % 2 == 0 else None)
    candidates.add(state, kind="concept", title="Importar Issues no Jira por REST", summary="duplicata", project="projeto_x")
    return vault, state


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--count", type=int, default=6)
    args = parser.parse_args()
    import uvicorn

    with tempfile.TemporaryDirectory() as tmp:
        vault, state = build(Path(tmp), args.count)
        print(f"sandbox: http://127.0.0.1:{args.port}/  (vault {vault})", flush=True)
        uvicorn.run(web_service.create_app(vault, state), host="127.0.0.1", port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
