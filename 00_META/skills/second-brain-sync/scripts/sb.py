#!/usr/bin/env python3
"""sb: single entry point of the second-brain runtime (RFC-001; Estudo S5, step I1).

Subcommands over the scripts that already exist. status, doctor and search only read; `sync` is the
single writer and delegates every guard to vault_sync.py.

  sb status                 vault, notes by type, git state, hook switches, last sync
  sb doctor [--json]        unresolved wikilinks, duplicate titles, frontmatter, secrets, stale notes
  sb search [-k N] <query>  the L1 ranker (vault_rank.sh), same TSV output
  sb candidate add|list|prune
                            queue of note candidates (local state, 30-day TTL); never writes the vault
  sb sync --note ... --project-name P --message M [--verdict V] [--reason R]
                            vault_sync.py with the vault path preset; the guards live there

Short-lived process, no daemon, stdlib only. `doctor` exits 1 when it finds an error-level issue.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import NamedTuple

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import candidates  # noqa: E402
import generate_manifests as gm  # noqa: E402
from lib import frontmatter, secret_scan  # noqa: E402

REQUIRED_FIELDS = ("title", "type", "tags", "created")
NOTE_TYPES = {
    "meta", "pattern", "decision", "concept", "trap", "project", "literature", "moc", "inbox", "template",
    "unclassified", "article", "literature-note", "permanent",
}
CONFIDENCE_LEVELS = {"low", "medium", "high"}
SCOPES = {"global", "project"}
STATUSES = {"active", "superseded", "completed", "archived"}
TEMPLATE_DIR = "90_Assets/"  # placeholders such as `type: article/book/paper` are not real values
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SKIP_DIRS = {".git", ".obsidian"}
ERROR, WARN = "error", "warn"


class Issue(NamedTuple):
    check: str
    severity: str
    path: str
    detail: str


# ---------------------------------------------------------------- shared helpers

def strip_code(text: str) -> str:
    """Remove fenced blocks and inline code, so `[[x]]` shown as an example is not a link."""
    kept: list[str] = []
    fence: str | None = None
    for line in text.splitlines():
        marker = line.lstrip()[:3]
        if fence is None and marker in ("```", "~~~"):
            fence = marker
            continue
        if fence is not None:
            if marker == fence:
                fence = None
            continue
        kept.append(re.sub(r"`[^`\n]*`", "", line))
    return "\n".join(kept)


def clean_link_target(raw: str) -> str:
    target = raw.split("#", 1)[0].split("^", 1)[0]
    return target.strip().rstrip("\\").strip()


class LinkIndex(NamedTuple):
    stems: dict[str, list[str]]
    paths: set[str]
    files: set[str]


def build_index(vault: Path) -> LinkIndex:
    stems: dict[str, list[str]] = defaultdict(list)
    paths: set[str] = set()
    files: set[str] = set()
    for root, dirs, names in os.walk(vault):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in names:
            path = Path(root) / name
            rel = path.relative_to(vault)
            files.add(name.casefold())
            if path.suffix.lower() == ".md":
                stems[path.stem.casefold()].append(str(rel))
                paths.add(str(rel.with_suffix("")).casefold())
    return LinkIndex(dict(stems), paths, files)


def link_resolves(target: str, index: LinkIndex) -> bool:
    key = target.casefold()
    if key.endswith(".md"):
        key = key[:-3]
    if key in index.stems or key in index.paths:
        return True
    if "/" in key and any(p.endswith("/" + key) for p in index.paths):
        return True
    return "." in key.rsplit("/", 1)[-1] and key.rsplit("/", 1)[-1] in index.files


def normalize_supersedes(value) -> list[str]:
    """`supersedes` is a title, a wikilink, or a list of them; the flat parser keeps the brackets."""
    items = value if isinstance(value, list) else [value]
    cleaned = []
    for item in items:
        text = str(item).strip().strip("\"'").strip("[]").split("|", 1)[0].strip()
        if text:
            cleaned.append(text)
    return cleaned


# ---------------------------------------------------------------- doctor

def check_note(vault: Path, rel: Path, text: str, index: LinkIndex) -> tuple[list[Issue], dict]:
    issues: list[Issue] = []
    path = str(rel)
    if not text.strip():
        return [Issue("empty-note", WARN, path, "0 bytes; Obsidian creates these when a pending link is clicked")], {}
    if path.startswith(TEMPLATE_DIR):
        return [Issue("secret", ERROR, path, f"{f.label} (line {f.line})") for f in secret_scan.scan_text(text)], {}
    fm_lines, body = frontmatter.split_frontmatter(text)
    if fm_lines is None:
        issues.append(Issue("frontmatter", ERROR, path, "no frontmatter block"))
        data: dict = {}
    else:
        data, _ = frontmatter.parse_frontmatter(fm_lines)
        for field in REQUIRED_FIELDS:
            if field not in data or data[field] in ("", []) and field != "tags":
                issues.append(Issue("frontmatter", ERROR, path, f"missing `{field}`"))
        if data.get("type") and data["type"] not in NOTE_TYPES:
            issues.append(Issue("frontmatter", ERROR, path, f"unknown type `{data['type']}`"))
        if data.get("created") and not DATE_RE.match(str(data["created"])):
            issues.append(Issue("frontmatter", ERROR, path, f"`created` is not YYYY-MM-DD: {data['created']}"))
        for field, allowed in (("confidence", CONFIDENCE_LEVELS), ("scope", SCOPES), ("status", STATUSES)):
            if data.get(field) and data[field] not in allowed:
                issues.append(Issue("frontmatter", ERROR, path, f"`{field}: {data[field]}` not in {sorted(allowed)}"))
        for target in normalize_supersedes(data.get("supersedes", [])):
            if not link_resolves(target, index):
                issues.append(Issue("supersedes", ERROR, path, f"supersedes `{target}`, which does not exist"))
    reported: set[str] = set()
    for match in gm.WIKILINK.finditer(strip_code(body)):
        if "\n" in match.group(1):
            continue  # Obsidian does not render a link that spans lines
        target = clean_link_target(match.group(1))
        if target and target not in reported and not link_resolves(target, index):
            reported.add(target)
            # A link to a note that does not exist yet is normal Obsidian practice (a pending note).
            issues.append(Issue("unresolved-link", WARN, path, f"[[{target}]]"))
    for finding in secret_scan.scan_text(text):
        issues.append(Issue("secret", ERROR, path, f"{finding.label} (line {finding.line})"))
    return issues, data


def bare_link_targets(body: str) -> set[str]:
    """Stems that a note points at by name only (no folder), which is where duplicates become ambiguous."""
    targets = set()
    for match in gm.WIKILINK.finditer(strip_code(body)):
        if "\n" not in match.group(1):
            target = clean_link_target(match.group(1))
            if target and "/" not in target:
                targets.add(target.casefold())
    return targets


def run_doctor(vault: Path, stale_days: int, today: dt.date) -> list[Issue]:
    index = build_index(vault)
    issues: list[Issue] = []
    by_title: dict[str, list[str]] = defaultdict(list)
    by_stem: dict[str, list[str]] = defaultdict(list)
    superseded_targets: set[str] = set()
    bare_targets: set[str] = set()
    superseded_notes: list[tuple[str, str]] = []
    cutoff = today - dt.timedelta(days=stale_days)
    for path, rel in gm.iter_notes(vault):
        text = path.read_text(encoding="utf-8", errors="replace")
        note_issues, data = check_note(vault, rel, text, index)
        issues.extend(note_issues)
        bare_targets |= bare_link_targets(text)
        if data.get("title"):
            by_title[data["title"].casefold()].append(str(rel))
        by_stem[path.stem.casefold()].append(str(rel))
        for target in normalize_supersedes(data.get("supersedes", [])):
            superseded_targets.add(target.casefold())
        if data.get("status") == "superseded":
            superseded_notes.append((str(rel), path.stem.casefold()))
        if data.get("type") in gm.STALE_TYPES:
            source = "verified" if gm.parse_date(str(data.get("verified", ""))) else "created"
            date = gm.parse_date(str(data.get(source, "")))
            if date is None or date < cutoff:
                issues.append(Issue("stale", WARN, str(rel), f"{source} {date or '?'}"))
    for label, groups in (("duplicate-title", by_title), ("duplicate-name", by_stem)):
        for key, paths in sorted(groups.items()):
            # Same file name in two folders only misleads a `[[name]]` link, so skip names nobody links by name.
            if len(paths) > 1 and (label == "duplicate-title" or key in bare_targets):
                issues.append(Issue(label, WARN, paths[0], f"`{key}` also in: {', '.join(paths[1:])}"))
    for rel, stem in superseded_notes:
        if stem not in superseded_targets:
            issues.append(Issue("supersedes", WARN, rel, "status is superseded but no note says `supersedes` it"))
    if not gm.check_manifests(vault):
        issues.append(Issue("manifest-drift", WARN, "00_META/manifests", "manifests differ from a fresh regeneration"))
    return issues


def format_doctor(issues: list[Issue], limit: int) -> str:
    if not issues:
        return "doctor: ok, no issues\n"
    grouped: dict[tuple[str, str], list[Issue]] = defaultdict(list)
    for issue in issues:
        grouped[(issue.severity, issue.check)].append(issue)
    lines = []
    for (severity, check), items in sorted(grouped.items(), key=lambda kv: (kv[0][0] != ERROR, kv[0][1])):
        lines.append(f"{severity} {check}: {len(items)}")
        for issue in items[:limit]:
            lines.append(f"  {issue.path}: {issue.detail}")
        if len(items) > limit:
            lines.append(f"  ... +{len(items) - limit} more (--limit)")
    errors = sum(1 for i in issues if i.severity == ERROR)
    lines.append(f"doctor: {errors} error(s), {len(issues) - errors} warning(s)")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- status

def git_summary(vault: Path) -> str:
    try:
        out = subprocess.run(
            ["git", "-C", str(vault), "status", "--porcelain=v1", "-b"],
            capture_output=True, text=True, timeout=15, check=True,
        ).stdout.splitlines()
    except (OSError, subprocess.SubprocessError):
        return "not a git repo (or git unavailable)"
    if not out:
        return "unknown"
    return f"{out[0][3:]}, {len(out) - 1} changed file(s)"


def last_sync(state_dir: Path) -> str:
    log = state_dir / "sync.jsonl"
    try:
        last = log.read_text(encoding="utf-8").strip().splitlines()[-1]
        entry = json.loads(last)
        return f"{entry.get('ts', '?')} {entry.get('outcome', '?')} {str(entry.get('sha', ''))[:7]}".strip()
    except (OSError, IndexError, ValueError):
        return "none"


def run_status(vault: Path, state_dir: Path, env) -> str:
    counts: dict[str, int] = defaultdict(int)
    total = 0
    for path, _ in gm.iter_notes(vault):
        data, _, _ = frontmatter.read_note(path)
        counts[str(data.get("type") or "no-type")] += 1
        total += 1
    by_type = ", ".join(f"{t} {n}" for t, n in sorted(counts.items()))
    drift = "ok" if gm.check_manifests(vault) else "DRIFT (run generate_manifests.py)"
    lines = [
        f"vault: {vault}",
        f"notes: {total} ({by_type})",
        f"git: {git_summary(vault)}",
        f"manifests: {drift}",
        f"hooks: SECOND_BRAIN_HOOKS={env.get('SECOND_BRAIN_HOOKS', 'unset')} "
        f"SECOND_BRAIN_PROMPT_HINT={env.get('SECOND_BRAIN_PROMPT_HINT', 'unset')} "
        f"kill-switch={'ON' if (state_dir / 'DISABLED').exists() else 'off'}",
        f"last sync: {last_sync(state_dir)}",
        f"candidates: {candidates.summary_line(state_dir)}",
    ]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- search

def run_search(vault: Path, query: str, k: int) -> int:
    env = dict(os.environ, SECOND_BRAIN_MANIFEST_DIR=str(vault / "00_META/manifests/by_type"))
    subprocess.run(["bash", str(HERE / "vault_rank.sh"), "-k", str(k), "--", query], env=env, check=False)
    return 0  # vault_rank.sh contract: silent, always exit 0


# ---------------------------------------------------------------- cli

def run_candidate(args, state_dir: Path) -> int:
    if args.action == "add":
        project = args.project or detect_project()
        try:
            cid, created = candidates.add(state_dir, kind=args.kind, title=args.title, summary=args.summary,
                                          project=project, source=args.source)
        except candidates.QueueError as err:
            sys.stderr.write(f"sb candidate: {err}\n")
            return 2
        sys.stdout.write(f"{'queued' if created else 'already queued'}: {cid}\n")
        return 0
    if args.action == "list":
        items, bad = candidates.load(state_dir)
        pending = candidates.live(items)
        if args.json:
            json.dump([{**i._asdict(), "ts": i.ts.isoformat(), "days_left": i.days_left} for i in pending],
                      sys.stdout, ensure_ascii=False, indent=2)
            sys.stdout.write("\n")
        else:
            sys.stdout.write(candidates.format_list(pending, len(items) - len(pending), bad))
        return 0
    removed = candidates.prune(state_dir, apply=args.apply)
    verb = "removed" if args.apply else "would remove (dry run, add --apply)"
    for item in removed:
        sys.stdout.write(f"{verb}: {item.id} {item.kind} {item.age_days}d {item.title}\n")
    if not removed:
        sys.stdout.write("nothing expired\n")
    return 0


def detect_project() -> str:
    """Name of the git repo the agent is working in; the folder name outside a repo."""
    try:
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, timeout=5)
        if top.returncode == 0 and top.stdout.strip():
            return Path(top.stdout.strip()).name
    except (OSError, subprocess.SubprocessError):
        pass
    return Path.cwd().name


def run_sync(rest: list[str]) -> int:
    """`sb sync ...` is vault_sync.py with --vault-path preset; every guard stays in vault_sync.py."""
    import vault_sync

    vault = Path(os.environ.get("SECOND_BRAIN_VAULT") or gm.DEFAULT_VAULT_ROOT)
    sys.argv = ["sb sync", "--vault-path", str(vault), *rest]  # a later --vault-path in `rest` wins
    code = vault_sync.main()
    if code == 0:
        report_note_issues(vault, synced_notes(rest))
    return code


def synced_notes(rest: list[str]) -> set[str]:
    """Paths passed with --note / --note=, relative to the vault, as `doctor` prints them."""
    notes: set[str] = set()
    for i, arg in enumerate(rest):
        if arg == "--note" and i + 1 < len(rest):
            notes.add(rest[i + 1])
        elif arg.startswith("--note="):
            notes.add(arg.split("=", 1)[1])
    return notes


def report_note_issues(vault: Path, notes: set[str]) -> None:
    """Run `doctor` after a successful sync and print only the findings on the notes just synced."""
    if not notes:
        return
    try:
        issues = run_doctor(vault, gm.DEFAULT_STALE_DAYS, dt.date.today())
    except Exception as exc:  # the sync already succeeded; a doctor failure must not turn it into an error
        sys.stderr.write(f"sb sync: doctor skipped ({exc})\n")
        return
    mine = [i for i in issues if i.path in notes]
    if not mine:
        sys.stdout.write("doctor: no issues on the synced notes\n")
        return
    sys.stdout.write(f"doctor: {len(mine)} issue(s) on the synced notes, fix and sync again:\n")
    for i in mine:
        sys.stdout.write(f"  {i.severity} {i.check} {i.path}: {i.detail}\n")


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--vault-path", type=Path, default=Path(os.environ.get("SECOND_BRAIN_VAULT") or gm.DEFAULT_VAULT_ROOT))
    parser = argparse.ArgumentParser(prog="sb", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status", parents=[common], help="vault, git, hooks, last sync")
    doctor = sub.add_parser("doctor", parents=[common], help="read-only vault health check")
    doctor.add_argument("--json", action="store_true")
    doctor.add_argument("--limit", type=int, default=15, help="lines per check (default 15)")
    doctor.add_argument("--stale-days", type=int, default=gm.DEFAULT_STALE_DAYS)
    doctor.add_argument("--today", type=dt.date.fromisoformat, default=None, help=argparse.SUPPRESS)
    search = sub.add_parser("search", parents=[common], help="L1 ranker over the manifests")
    search.add_argument("-k", type=int, default=5)
    search.add_argument("query", nargs="+")
    cand = sub.add_parser("candidate", parents=[common], help="queue of note candidates (30-day TTL)")
    cand_sub = cand.add_subparsers(dest="action", required=True)
    cand_add = cand_sub.add_parser("add", help="queue one candidate; the vault is not touched")
    cand_add.add_argument("--kind", required=True, choices=candidates.KINDS)
    cand_add.add_argument("--title", required=True, help=f"up to {candidates.MAX_TITLE} characters")
    cand_add.add_argument("--summary", default="", help=f"up to {candidates.MAX_SUMMARY} characters, no secrets")
    cand_add.add_argument("--project", default="", help="default: the git repo name")
    cand_add.add_argument("--source", default="agent", choices=("agent", "user", "ecc"))
    cand_list = cand_sub.add_parser("list", help="pending candidates, oldest first")
    cand_list.add_argument("--json", action="store_true")
    cand_prune = cand_sub.add_parser("prune", help="drop candidates older than 30 days (dry run by default)")
    cand_prune.add_argument("--apply", action="store_true")
    sub.add_parser("sync", add_help=False, help="vault_sync.py with the vault preset (sb sync --help)")
    return parser


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "sync":
        return run_sync(argv[1:])
    args = build_parser().parse_args(argv)
    vault = args.vault_path.resolve()
    state_dir = Path(os.environ.get("SECOND_BRAIN_STATE_DIR") or Path.home() / ".local/state/second-brain")
    if args.command == "status":
        sys.stdout.write(run_status(vault, state_dir, os.environ))
        return 0
    if args.command == "candidate":
        return run_candidate(args, state_dir)
    if args.command == "search":
        return run_search(vault, " ".join(args.query), args.k)
    issues = run_doctor(vault, args.stale_days, args.today or dt.date.today())
    if args.json:
        json.dump([i._asdict() for i in issues], sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    else:
        sys.stdout.write(format_doctor(issues, args.limit))
    return 1 if any(i.severity == ERROR for i in issues) else 0


if __name__ == "__main__":
    sys.exit(main())
