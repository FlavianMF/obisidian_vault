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
  - One sync at a time: an exclusive lock in `.git/` (waits up to
    SECOND_BRAIN_LOCK_TIMEOUT seconds, default 120) so two sessions cannot interleave
    pull, manifest regeneration and commit.
  - Update before create (RFC-001 §5): a NEW note whose title+tags already match an
    existing note (coverage >= SECOND_BRAIN_DUP_COVERAGE, default 0.5) is refused unless
    the caller states `--new-because "<why this is not an update>"`.
  - Every NEW note must be born with `confidence: low`, whoever writes it; the level only
    rises by evidence, never by declaration. Raising it on an existing note is checked:
    to medium needs a changed `verified:` line, to high needs 2+ projects in `seen_in`
    or a changed `verified:` that cites a test.
  - Two NEW notes in the same call are also compared with each other.
  - "New" means absent from HEAD (not `git status` says untracked), so `git add` or a local
    commit before the sync does not switch the checks off.
  - Derived manifest files never count as unrelated dirty files; a failed commit or push
    can be retried (the retry pushes commits that are still ahead of origin).
  - The lock lives in the git common dir, so it also works from a linked worktree.
  - Every run appends one line to ~/.local/state/second-brain/sync.jsonl (0600); an
    unexpected exception is logged as `crash`.

Write the note AFTER taking turns: two sessions that both have an unsynced note in the vault
refuse each other as "unrelated dirty files"; sync one, then write the next.

Usage:
    python3 vault_sync.py --vault-path docs/second_brain \
        --note "20_Permanent_Notes/New Pattern.md" \
        --project-name projetos_claude \
        --message "docs(vault): distill pattern from projetos_claude" \
        [--new-because "covers X, which the existing note does not"]
"""
from __future__ import annotations

import argparse
import datetime as dt
import fcntl
import json
import math
import os
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_manifests  # noqa: E402
from lib import frontmatter  # noqa: E402

MANIFEST_DIR_NAME = "00_META/manifests"
LOCK_NAME = "second-brain-sync.lock"
DEFAULT_LOCK_TIMEOUT_SECONDS = 120.0
LOCK_POLL_SECONDS = 0.1
DEFAULT_DUP_COVERAGE = 0.5
CANDIDATES_SCRIPT = Path(__file__).resolve().parent / "note_candidates.sh"


def run_git(vault_root: Path, args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(vault_root), *args],
        capture_output=True,
        text=True,
        check=check,
    )


def porcelain_entries(porcelain_output: str) -> list[tuple[str, str]]:
    """Parse `git status --porcelain -z` output into (status_code, path) pairs.

    -z is load-bearing, not cosmetic: plain --porcelain quote-escapes any
    non-ASCII byte in a path (core.quotePath, on by default) as octal
    sequences like '\\303\\241', which then fails to string-match a
    --note path containing the same character as literal UTF-8 - silently
    misclassifying a just-synced note as an "unrelated dirty file". -z
    disables quoting entirely and NUL-terminates each field instead, so
    paths come back as raw bytes regardless of the caller's git config.
    """
    entries = []
    tokens = porcelain_output.split("\0")
    i = 0
    while i < len(tokens):
        entry = tokens[i]
        i += 1
        if not entry:
            continue
        status_code = entry[:2]
        entries.append((status_code, entry[3:]))
        if status_code[0] in ("R", "C"):
            # Rename/copy entries carry a second NUL-terminated field (the
            # original path) that isn't a path of its own to report.
            i += 1
    return entries


def porcelain_paths(porcelain_output: str) -> list[str]:
    return [path for _, path in porcelain_entries(porcelain_output)]


def fail(message: str) -> int:
    print(f"error: {message}", file=sys.stderr)
    return 1


def state_dir() -> Path:
    return Path(os.environ.get("SECOND_BRAIN_STATE_DIR") or Path.home() / ".local/state/second-brain")


def log_event(event: dict) -> None:
    """Append one JSON line to the local sync log; never lets logging break the sync."""
    try:
        directory = state_dir()
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        entry = {"ts": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), **event}
        target = directory / "sync.jsonl"
        with open(os.open(target, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600), "a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except (OSError, ValueError):
        pass


def lock_timeout() -> float:
    try:
        value = float(os.environ.get("SECOND_BRAIN_LOCK_TIMEOUT", DEFAULT_LOCK_TIMEOUT_SECONDS))
    except ValueError:
        return DEFAULT_LOCK_TIMEOUT_SECONDS
    return value if math.isfinite(value) and value >= 0 else DEFAULT_LOCK_TIMEOUT_SECONDS


def git_common_dir(vault_root: Path) -> Path:
    done = run_git(vault_root, ["rev-parse", "--path-format=absolute", "--git-common-dir"], check=False)
    if done.returncode != 0 or not done.stdout.strip():
        raise RuntimeError(f"not a git repository: {vault_root}")
    return Path(done.stdout.strip())


@contextmanager
def sync_lock(vault_root: Path):
    """Exclusive inter-process lock in the git common dir (never a dirty file, shared by worktrees)."""
    timeout = lock_timeout()
    lock_path = git_common_dir(vault_root) / LOCK_NAME
    handle = open(lock_path, "w", encoding="utf-8")
    deadline = time.monotonic() + timeout
    try:
        while True:
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise TimeoutError(f"could not get the sync lock {lock_path} within {timeout:g}s")
                time.sleep(LOCK_POLL_SECONDS)
        yield
    finally:
        handle.close()


def dup_coverage() -> float:
    try:
        return float(os.environ.get("SECOND_BRAIN_DUP_COVERAGE", DEFAULT_DUP_COVERAGE))
    except ValueError:
        return DEFAULT_DUP_COVERAGE


def existing_candidates(
    vault_root: Path, note: str, manifest_dir: Path | None = None
) -> list[tuple[str, str, float]]:
    """Notes already in the manifests that match the new note's title+tags strongly enough to be an update."""
    data, _, _ = frontmatter.read_note(vault_root / note)
    title = str(data.get("title") or Path(note).stem)
    tags = data.get("tags")
    tags_text = ", ".join(tags) if isinstance(tags, list) else str(tags or "")
    env = {**os.environ, "SECOND_BRAIN_VAULT": str(vault_root), "SECOND_BRAIN_CANDIDATE_COVERAGE": str(dup_coverage())}
    if manifest_dir is not None:
        env["SECOND_BRAIN_MANIFEST_DIR"] = str(manifest_dir)
    done = subprocess.run(
        [str(CANDIDATES_SCRIPT), "-k", "5", "--", title, tags_text],
        capture_output=True, text=True, env=env, check=False, stdin=subprocess.DEVNULL
    )
    found = []
    for line in done.stdout.splitlines():
        path, row_title, coverage, *_ = line.split("\t")
        if path != note:
            found.append((path, row_title, float(coverage)))
    return found[:3]


def check_new_note(vault_root: Path, note: str, new_because: str | None) -> tuple[str, str] | None:
    """Return (outcome, message) when a NEW note breaks the F2 rules, else None."""
    data, _, _ = frontmatter.read_note(vault_root / note)
    if clean_value(data.get("confidence")) != "low":
        return "refused-confidence", (
            f"new note {note} must be born with `confidence: low` (every new note, manual or not, rises "
            "to medium/high by evidence, never by declaration; see Frontmatter-Schema)."
        )
    if new_because:
        return None
    candidates = existing_candidates(vault_root, note)
    if not candidates:
        return None
    listing = "\n  ".join(f"{path}  (coverage {cov:.2f})" for path, _, cov in candidates)
    return "refused-candidate", (
        f"new note {note} looks like an existing note; update it instead (dated entry, add the project "
        f"to `seen_in`):\n  {listing}\n"
        "If this really is a different subject, rerun with --new-because \"<one line why>\"."
    )


CONFIDENCE_RANK = {"low": 0, "medium": 1, "high": 2}


def clean_value(value: object) -> str:
    return str(value or "").strip().strip("\"'").lower()


def head_frontmatter(vault_root: Path, path: str) -> dict:
    done = run_git(vault_root, ["show", f"HEAD:{path}"], check=False)
    if done.returncode != 0:
        return {}
    fm_lines, _ = frontmatter.split_frontmatter(done.stdout)
    return frontmatter.parse_frontmatter(fm_lines)[0] if fm_lines else {}


def seen_count(data: dict) -> int:
    seen = data.get("seen_in")
    items = seen if isinstance(seen, list) else [str(seen or "")]
    return len({item.strip() for item in items if item.strip()})


def check_promotion(vault_root: Path, note: str) -> str | None:
    """Return an error message when an UPDATED note raises `confidence` without evidence."""
    new, _, _ = frontmatter.read_note(vault_root / note)
    old = head_frontmatter(vault_root, note)
    before = CONFIDENCE_RANK.get(clean_value(old.get("confidence")), 0)
    after = CONFIDENCE_RANK.get(clean_value(new.get("confidence")), before)
    if after <= before:
        return None
    verified_changed = bool(clean_value(new.get("verified"))) and new.get("verified") != old.get("verified")
    cites_test = verified_changed and any(w in clean_value(new.get("verified")) for w in ("test", "teste"))
    if after == CONFIDENCE_RANK["medium"] and verified_changed:
        return None
    if after == CONFIDENCE_RANK["high"] and (seen_count(new) >= 2 or cites_test):
        return None
    need = (
        "update `verified: <hoje> via <como foi reproduzido ou documentado>`"
        if after == CONFIDENCE_RANK["medium"]
        else "list 2+ projects in `seen_in`, or update `verified:` citing a test"
    )
    return (
        f"{note} raises confidence to {clean_value(new.get('confidence'))} without evidence; {need}, "
        "or keep the previous level (promotion is by evidence, never by declaration)."
    )


def sibling_duplicates(vault_root: Path, created: list[str]) -> str | None:
    """Compare NEW notes of the same call with each other (the committed manifests do not know them)."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        for rel, content in generate_manifests.build_manifest_files(vault_root).items():
            target = Path(tmp) / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        lines = []
        for note in created:
            for path, _, cov in existing_candidates(vault_root, note, Path(tmp) / "by_type"):
                if path in created:
                    lines.append(f"{note}  ~  {path}  (coverage {cov:.2f})")
    if not lines:
        return None
    return (
        "new notes in this call look like each other; merge them into one note:\n  " + "\n  ".join(lines) + "\n"
        "If they really cover different subjects, rerun with --new-because \"<one line why>\"."
    )


def in_head(vault_root: Path, path: str) -> bool:
    return run_git(vault_root, ["cat-file", "-e", f"HEAD:{path}"], check=False).returncode == 0


def ahead_of_origin(vault_root: Path) -> bool:
    done = run_git(vault_root, ["rev-list", "--count", "origin/master..HEAD"], check=False)
    return done.returncode == 0 and done.stdout.strip() not in ("", "0")


def is_manifest(path: str) -> bool:
    return path.startswith(MANIFEST_DIR_NAME + "/")


def sync(args: argparse.Namespace, vault_root: Path) -> tuple[int, dict]:
    event: dict = {"project": args.project_name, "created": [], "updated": [], "outcome": "error"}

    status = run_git(vault_root, ["status", "--porcelain", "--untracked-files=all", "-z"])
    entries = porcelain_entries(status.stdout)
    expected = set(args.note)
    unexpected = [path for _, path in entries if path not in expected and not is_manifest(path)]
    if unexpected:
        event["outcome"] = "refused-dirty"
        return fail("vault has unrelated dirty/untracked files, refusing to proceed:\n  " + "\n  ".join(unexpected)), event

    pull = run_git(vault_root, ["pull", "--ff-only", "origin", "master"], check=False)
    if pull.returncode != 0:
        return fail(f"git pull --ff-only failed (divergent history?):\n{pull.stderr}"), event

    for note in args.note:
        if not (vault_root / note).exists():
            return fail(f"--note path does not exist in vault: {note}"), event

    changed = {path for _, path in entries}
    event["created"] = sorted(n for n in args.note if n in changed and not in_head(vault_root, n))
    event["updated"] = sorted(n for n in args.note if n in changed and n not in event["created"])
    if args.new_because:
        event["new_because"] = args.new_because
    for note in event["created"]:
        problem = check_new_note(vault_root, note, args.new_because)
        if problem:
            event["outcome"], message = problem
            return fail(message), event

    if len(event["created"]) > 1 and not args.new_because:
        problem = sibling_duplicates(vault_root, event["created"])
        if problem:
            event["outcome"] = "refused-candidate"
            return fail(problem), event
    for note in event["updated"]:
        problem = check_promotion(vault_root, note)
        if problem:
            event["outcome"] = "refused-promotion"
            return fail(problem), event

    generate_manifests.write_manifests(vault_root)
    after_manifest_status = run_git(
        vault_root, ["status", "--porcelain", "--untracked-files=all", "-z", "--", MANIFEST_DIR_NAME]
    )
    stage_paths = sorted(
        {n for n in args.note if n in changed} | set(porcelain_paths(after_manifest_status.stdout))
    )
    if stage_paths:
        run_git(vault_root, ["add", "--", *stage_paths])
        message = args.message
        if args.project_name:
            message = f"{message}\n\nProvenance: {args.project_name}"
        commit = run_git(vault_root, ["commit", "-m", message], check=False)
        if commit.returncode != 0:
            run_git(vault_root, ["reset", "-q", "--", *stage_paths], check=False)
            event["outcome"] = "commit-failed"
            return fail(f"git commit failed (staged paths unstaged again; retry is safe):\n{commit.stderr}"), event
    elif not ahead_of_origin(vault_root):
        event["outcome"] = "nothing-to-sync"
        print("nothing to sync (no note changes, manifests already up to date)")
        return 0, event

    push = run_git(vault_root, ["push", "origin", "master"], check=False)
    if push.returncode != 0:
        event.update(outcome="push-failed", sha=run_git(vault_root, ["rev-parse", "HEAD"]).stdout.strip())
        return fail(f"git push failed (the commit stays local; rerun to push it):\n{push.stderr}"), event

    sha = run_git(vault_root, ["rev-parse", "HEAD"]).stdout.strip()
    event.update(outcome="synced", sha=sha)
    print(f"synced: {sha}")
    return 0, event


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--vault-path", required=True, type=Path)
    parser.add_argument("--note", action="append", default=[], help="Relative path of a new/changed note. Repeatable.")
    parser.add_argument("--project-name", required=True)
    parser.add_argument("--message", required=True)
    parser.add_argument(
        "--new-because", default=None,
        help="One line: why a new note that resembles an existing one is not an update of it.",
    )
    args = parser.parse_args()

    vault_root = args.vault_path.resolve()
    if not vault_root.is_dir():
        return fail(f"vault path not found: {vault_root}")

    try:
        with sync_lock(vault_root):
            code, event = sync(args, vault_root)
    except TimeoutError as exc:
        log_event({"project": args.project_name, "outcome": "lock-timeout"})
        return fail(str(exc))
    except Exception as exc:  # noqa: BLE001 - last resort: log it, never leave only a traceback
        log_event({"project": args.project_name, "outcome": "crash", "error": f"{type(exc).__name__}: {exc}"[:300]})
        return fail(f"{type(exc).__name__}: {exc}")
    log_event(event)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
