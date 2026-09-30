#!/usr/bin/env python3
"""Generate frontmatter-only manifests for the second-brain vault.

Reads every note's frontmatter (never its body) and writes lightweight,
grep-friendly markdown tables under 00_META/manifests/ — the replacement
for MOC entry points that depend on Dataview (inert to filesystem-only
agents). Partitioned by `type`, since that's the axis the old Dataview
`WHERE type = "..."` blocks were filtering on.

Read-only w.r.t. note content: a note still missing frontmatter is bucketed
as `unclassified` for this run only — this script never writes back into a
note (that's backfill_frontmatter.py's job).

Optional fields `confidence` and `seen_in` become manifest columns (blank when
absent). `--stale-report` lists pattern/trap notes whose `verified` date (or
`created`, when `verified` is missing) is older than `--stale-days`; it only
prints, never writes.

Usage:
    python3 generate_manifests.py                      # vault = repo containing this script
    python3 generate_manifests.py --vault-path docs/second_brain
    python3 generate_manifests.py --vault-path docs/second_brain --check
    python3 generate_manifests.py --stale-report [--stale-days 180]
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import frontmatter  # noqa: E402

MANIFEST_DIR_NAME = "00_META/manifests"
SKILL_DIR_NAME = "00_META/skills"
SHARD_THRESHOLD = 150
EXCLUDE_DIR_PARTS = {".obsidian", ".git"}
DEFAULT_VAULT_ROOT = Path(__file__).resolve().parents[4]
STALE_TYPES = ("pattern", "trap")
DEFAULT_STALE_DAYS = 180
DATE_PREFIX = re.compile(r"^\s*(\d{4}-\d{2}-\d{2})")


def as_list_str(value) -> str:
    if isinstance(value, list):
        return ", ".join(v for v in value if v)
    return str(value or "")


def iter_notes(vault_root: Path):
    for path in sorted(vault_root.rglob("*.md")):
        rel = path.relative_to(vault_root)
        if any(part in EXCLUDE_DIR_PARTS for part in rel.parts):
            continue
        if str(rel).startswith(MANIFEST_DIR_NAME) or str(rel).startswith(SKILL_DIR_NAME):
            continue
        yield path, rel


def collect_rows(vault_root: Path) -> dict[str, list[dict[str, str]]]:
    by_type: dict[str, list[dict[str, str]]] = {}
    for path, rel in iter_notes(vault_root):
        if path.stat().st_size == 0:
            continue
        data, _, _ = frontmatter.read_note(path)
        note_type = str(data.get("type") or "unclassified").strip() or "unclassified"
        title = str(data.get("title") or path.stem)
        tags_str = as_list_str(data.get("tags"))
        created = str(data.get("created") or "")
        provenance = str(data.get("provenance") or "")
        by_type.setdefault(note_type, []).append(
            {
                "path": str(rel).replace("\\", "/"),
                "title": title,
                "tags": tags_str,
                "created": created,
                "provenance": provenance,
                "confidence": str(data.get("confidence") or ""),
                "seen_in": as_list_str(data.get("seen_in")),
                "verified": str(data.get("verified") or ""),
            }
        )
    for rows in by_type.values():
        rows.sort(key=lambda r: r["path"])
    return by_type


def semester_key(created: str) -> str:
    if len(created) >= 7 and created[4] == "-":
        year = created[:4]
        try:
            month = int(created[5:7])
        except ValueError:
            return "unknown"
        half = "H1" if month <= 6 else "H2"
        return f"{year}{half}"
    return "unknown"


def shard_rows(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    """Split rows into semester shards if the type exceeds SHARD_THRESHOLD, else one shard.

    A semester itself can still exceed the threshold (e.g. a bulk import that
    stamps the same `created` date on hundreds of notes) — semester grouping
    alone doesn't bound shard size, so oversized semesters get further split
    into fixed-size chunks.
    """
    if len(rows) <= SHARD_THRESHOLD:
        return {"": rows}
    by_semester: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        key = semester_key(row["created"])
        by_semester.setdefault(key, []).append(row)

    shards: dict[str, list[dict[str, str]]] = {}
    for key, semester_rows in sorted(by_semester.items(), reverse=True):
        if len(semester_rows) <= SHARD_THRESHOLD:
            shards[key] = semester_rows
            continue
        for i in range(0, len(semester_rows), SHARD_THRESHOLD):
            chunk_num = i // SHARD_THRESHOLD + 1
            suffix = key if chunk_num == 1 else f"{key}-{chunk_num}"
            shards[suffix] = semester_rows[i : i + SHARD_THRESHOLD]
    return shards


def render_table(rows: list[dict[str, str]]) -> str:
    lines = [
        "| Path | Title | Tags | Created | Provenance | Confidence | Seen in |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['path']} | {row['title']} | {row['tags']} | {row['created']} "
            f"| {row['provenance']} | {row['confidence']} | {row['seen_in']} |"
        )
    return "\n".join(lines) + "\n"


def sanitize_type_name(note_type: str) -> str:
    safe = note_type.strip().lower()
    for char in (" ", "/", "\\"):
        safe = safe.replace(char, "-")
    return safe or "unclassified"


def build_manifest_files(vault_root: Path) -> dict[str, str]:
    """Return {relative_path_under_manifest_dir: content} for every file that should exist."""
    by_type = collect_rows(vault_root)
    files: dict[str, str] = {}
    index_lines = [
        "# Second-Brain Vault — Agent Manifest Index",
        "",
        "Generated by `second-brain-sync`'s `generate_manifests.py`. Read this file first, then "
        "`grep` (never `Read` in full) the relevant `by_type/*.md` file(s) below — glob covers "
        "shards automatically if a type has grown past the shard threshold.",
        "",
        "## Notes by type",
        "",
        "| Type | Count | Files |",
        "| --- | --- | --- |",
    ]
    for note_type in sorted(by_type):
        rows = by_type[note_type]
        safe_type = sanitize_type_name(note_type)
        shards = shard_rows(rows)
        shard_files = []
        for suffix, shard_rows_list in shards.items():
            fname = f"{safe_type}.md" if suffix == "" else f"{safe_type}_{suffix}.md"
            files[f"by_type/{fname}"] = render_table(shard_rows_list)
            shard_files.append(f"by_type/{fname}")
        index_lines.append(
            f"| {note_type} | {len(rows)} | {', '.join(shard_files)} |"
        )

    folder_counts: dict[str, int] = {}
    for _, rel in iter_notes(vault_root):
        top = rel.parts[0] if len(rel.parts) > 1 else "(root)"
        folder_counts[top] = folder_counts.get(top, 0) + 1
    index_lines += ["", "## Notes by folder (orientation only)", "", "| Folder | Count |", "| --- | --- |"]
    for folder in sorted(folder_counts):
        index_lines.append(f"| {folder} | {folder_counts[folder]} |")

    files["INDEX.md"] = "\n".join(index_lines) + "\n"
    return files


def write_manifests(vault_root: Path) -> bool:
    """Write manifest files. Returns True if anything on disk changed."""
    manifest_dir = vault_root / MANIFEST_DIR_NAME
    desired = build_manifest_files(vault_root)
    changed = False

    existing_by_type_files: set[Path] = set()
    by_type_dir = manifest_dir / "by_type"
    if by_type_dir.is_dir():
        existing_by_type_files = {p for p in by_type_dir.rglob("*.md")}

    desired_paths: set[Path] = set()
    for rel_name, content in desired.items():
        target = manifest_dir / rel_name
        desired_paths.add(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists() or target.read_text(encoding="utf-8") != content:
            target.write_text(content, encoding="utf-8")
            changed = True

    # Remove stale shard/type files that no longer have any notes (e.g. type renamed away).
    for stale in existing_by_type_files - desired_paths:
        stale.unlink()
        changed = True
        for parent in stale.parents:
            if parent == by_type_dir or by_type_dir not in parent.parents:
                break
            try:
                parent.rmdir()
            except OSError:
                break

    return changed


def check_manifests(vault_root: Path) -> bool:
    """Return True if on-disk manifests match a fresh regeneration (no drift)."""
    manifest_dir = vault_root / MANIFEST_DIR_NAME
    desired = build_manifest_files(vault_root)
    on_disk: dict[str, str] = {}
    if manifest_dir.is_dir():
        for path in manifest_dir.rglob("*.md"):
            rel = str(path.relative_to(manifest_dir))
            on_disk[rel] = path.read_text(encoding="utf-8")
    return on_disk == desired


def parse_date(value: str) -> dt.date | None:
    match = DATE_PREFIX.match(value or "")
    if not match:
        return None
    try:
        return dt.date.fromisoformat(match.group(1))
    except ValueError:
        return None


def stale_report(vault_root: Path, stale_days: int, today: dt.date) -> str:
    """Markdown table of pattern/trap notes whose verified (else created) date is older than stale_days."""
    by_type = collect_rows(vault_root)
    cutoff = today - dt.timedelta(days=stale_days)
    stale = []
    for note_type in STALE_TYPES:
        for row in by_type.get(note_type, []):
            source = "verified" if parse_date(row["verified"]) else "created"
            date = parse_date(row[source])
            if date is None or date < cutoff:
                stale.append((date.isoformat() if date else "", source, note_type, row))
    stale.sort(key=lambda item: (item[0], item[3]["path"]))
    lines = [
        f"# Stale report — {', '.join(STALE_TYPES)} older than {stale_days} days (cutoff {cutoff.isoformat()})",
        "",
        f"{len(stale)} note(s).",
        "",
        "| Date | Source | Type | Path | Seen in |",
        "| --- | --- | --- | --- | --- |",
    ]
    for date, source, note_type, row in stale:
        lines.append(f"| {date or '?'} | {source} | {note_type} | {row['path']} | {row['seen_in']} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--vault-path", type=Path, default=DEFAULT_VAULT_ROOT,
        help="Vault root (default: the repo this script lives in).",
    )
    parser.add_argument("--check", action="store_true", help="Exit 1 if manifests would change; never writes.")
    parser.add_argument("--stale-report", action="store_true", help="Print stale pattern/trap notes; never writes.")
    parser.add_argument("--stale-days", type=int, default=DEFAULT_STALE_DAYS)
    parser.add_argument("--today", type=dt.date.fromisoformat, default=None, help="Override today (YYYY-MM-DD).")
    args = parser.parse_args()

    vault_root = args.vault_path.resolve()
    if not vault_root.is_dir():
        print(f"error: vault path not found: {vault_root}", file=sys.stderr)
        return 2

    if args.stale_report:
        print(stale_report(vault_root, args.stale_days, args.today or dt.date.today()), end="")
        return 0

    if args.check:
        if check_manifests(vault_root):
            print("manifests up to date")
            return 0
        print("manifests are stale — run without --check to regenerate", file=sys.stderr)
        return 1

    changed = write_manifests(vault_root)
    print("manifests updated" if changed else "manifests already up to date (no changes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
