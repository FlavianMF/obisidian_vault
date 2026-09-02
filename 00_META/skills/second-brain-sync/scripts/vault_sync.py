#!/usr/bin/env python3
"""End-of-task autonomous sync of the second-brain vault.

Called by the second-brain-sync skill without asking for confirmation
(explicit user decision — see docs/PRD.md RQ-03 in the pilot project).
Guardrails live here in code, not in prose the agent has to remember:
  - `git pull --ff-only` only — never merges/rebases, fails loud on divergence.
  - Stages only the note path(s) explicitly passed in, plus manifest files
    that actually changed — never `git add -A`.
  - No code path here ever passes `--force` to git.
  - Aborts if the vault has unrelated dirty/untracked files before starting,
    rather than silently sweeping them into the commit.

Usage:
    python3 vault_sync.py --vault-path docs/second_brain \
        --note "20_Permanent_Notes/New Pattern.md" \
        --project-name projetos_claude \
        --message "docs(vault): distill pattern from projetos_claude"
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_manifests  # noqa: E402

MANIFEST_DIR_NAME = "00_META/manifests"


def run_git(vault_root: Path, args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(vault_root), *args],
        capture_output=True,
        text=True,
        check=check,
    )


def porcelain_paths(porcelain_output: str) -> list[str]:
    """Parse `git status --porcelain -z` output.

    -z is load-bearing, not cosmetic: plain --porcelain quote-escapes any
    non-ASCII byte in a path (core.quotePath, on by default) as octal
    sequences like '\\303\\241', which then fails to string-match a
    --note path containing the same character as literal UTF-8 - silently
    misclassifying a just-synced note as an "unrelated dirty file". -z
    disables quoting entirely and NUL-terminates each field instead, so
    paths come back as raw bytes regardless of the caller's git config.
    """
    paths = []
    tokens = porcelain_output.split("\0")
    i = 0
    while i < len(tokens):
        entry = tokens[i]
        i += 1
        if not entry:
            continue
        status_code = entry[:2]
        paths.append(entry[3:])
        if status_code[0] in ("R", "C"):
            # Rename/copy entries carry a second NUL-terminated field (the
            # original path) that isn't a path of its own to report.
            i += 1
    return paths


def fail(message: str) -> int:
    print(f"error: {message}", file=sys.stderr)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vault-path", required=True, type=Path)
    parser.add_argument("--note", action="append", default=[], help="Relative path of a new/changed note. Repeatable.")
    parser.add_argument("--project-name", required=True)
    parser.add_argument("--message", required=True)
    args = parser.parse_args()

    vault_root = args.vault_path.resolve()
    if not vault_root.is_dir():
        return fail(f"vault path not found: {vault_root}")

    status = run_git(vault_root, ["status", "--porcelain", "--untracked-files=all", "-z"])
    dirty = porcelain_paths(status.stdout)
    expected = set(args.note)
    unexpected = [p for p in dirty if p not in expected]
    if unexpected:
        return fail(
            "vault has unrelated dirty/untracked files, refusing to proceed:\n  "
            + "\n  ".join(unexpected)
        )

    pull = run_git(vault_root, ["pull", "--ff-only", "origin", "master"], check=False)
    if pull.returncode != 0:
        return fail(f"git pull --ff-only failed (divergent history?):\n{pull.stderr}")

    generate_manifests.write_manifests(vault_root)
    after_manifest_status = run_git(
        vault_root, ["status", "--porcelain", "--untracked-files=all", "-z", "--", MANIFEST_DIR_NAME]
    )
    manifest_changed_paths = porcelain_paths(after_manifest_status.stdout)

    stage_paths = sorted(set(args.note) | set(manifest_changed_paths))
    if not stage_paths:
        print("nothing to sync (no note changes, manifests already up to date)")
        return 0

    for note in args.note:
        if not (vault_root / note).exists():
            return fail(f"--note path does not exist in vault: {note}")

    run_git(vault_root, ["add", "--", *stage_paths])

    message = args.message
    if args.project_name:
        message = f"{message}\n\nProvenance: {args.project_name}"
    commit = run_git(vault_root, ["commit", "-m", message], check=False)
    if commit.returncode != 0:
        return fail(f"git commit failed:\n{commit.stderr}")

    push = run_git(vault_root, ["push", "origin", "master"], check=False)
    if push.returncode != 0:
        return fail(f"git push failed:\n{push.stderr}")

    sha = run_git(vault_root, ["rev-parse", "HEAD"]).stdout.strip()
    print(f"synced: {sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
