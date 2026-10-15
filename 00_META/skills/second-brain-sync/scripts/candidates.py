"""Candidate queue of the second-brain runtime (Estudo S5, step I3).

An agent that was corrected, or that found a trap, appends one line here instead of writing to the vault.
The queue never touches the vault: a person turns a candidate into a note later (`sb review`, step I4).
Each line lives 30 days; the last 7 days are flagged. The file is local state, mode 0600, one JSON object per line.
"""
from __future__ import annotations

import datetime as dt
import fcntl
import hashlib
import json
import os
import re
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, NamedTuple

from lib import secret_scan

QUEUE_NAME = "queue.jsonl"
KINDS = ("trap", "pattern", "decision", "concept")
TTL_DAYS = 30
WARN_DAYS = 7
MAX_TITLE = 120
MAX_SUMMARY = 500


class Candidate(NamedTuple):
    id: str
    ts: dt.datetime
    kind: str
    title: str
    summary: str
    project: str
    source: str

    @property
    def age_days(self) -> int:
        return (utcnow() - self.ts).days

    @property
    def days_left(self) -> int:
        return TTL_DAYS - self.age_days


class QueueError(ValueError):
    """The candidate is refused; the message never contains the offending value."""


def utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def queue_path(state_dir: Path) -> Path:
    return state_dir / QUEUE_NAME


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def candidate_id(kind: str, title: str, project: str) -> str:
    key = f"{kind}|{normalize(title).casefold()}|{project.casefold()}"
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:8]


@contextmanager
def locked(path: Path) -> Iterator[None]:
    """Serialise writers (two sessions can add at once); the lock file is the queue's sibling."""
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with open(path.with_suffix(".lock"), "a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def parse_line(line: str) -> Candidate | None:
    try:
        raw = json.loads(line)
        return Candidate(
            id=str(raw["id"]), ts=dt.datetime.fromisoformat(raw["ts"]), kind=str(raw["kind"]),
            title=str(raw["title"]), summary=str(raw.get("summary", "")), project=str(raw.get("project", "")),
            source=str(raw.get("source", "agent")),
        )
    except (ValueError, KeyError, TypeError):
        return None


def read_lines(path: Path) -> list[str]:
    try:
        return [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    except OSError:
        return []


def load(state_dir: Path) -> tuple[list[Candidate], int]:
    """All parsable candidates, plus how many lines could not be parsed."""
    items, bad = [], 0
    for line in read_lines(queue_path(state_dir)):
        item = parse_line(line)
        if item is None:
            bad += 1
        else:
            items.append(item)
    return items, bad


def live(items: list[Candidate]) -> list[Candidate]:
    return [i for i in items if i.days_left > 0]


def add(state_dir: Path, *, kind: str, title: str, summary: str, project: str, source: str = "agent") -> tuple[str, bool]:
    """Append a candidate. Returns (id, created); an identical live candidate is not queued twice."""
    title, summary, project = normalize(title), normalize(summary), normalize(project)
    if kind not in KINDS:
        raise QueueError(f"kind must be one of {', '.join(KINDS)}")
    if not title:
        raise QueueError("title is empty")
    if len(title) > MAX_TITLE:
        raise QueueError(f"title is over {MAX_TITLE} characters")
    if len(summary) > MAX_SUMMARY:
        raise QueueError(f"summary is over {MAX_SUMMARY} characters")
    findings = secret_scan.scan_text(f"{title}\n{summary}")
    if findings:
        labels = ", ".join(sorted({f.label for f in findings}))
        raise QueueError(f"looks like a secret ({labels}); nothing was queued")
    cid = candidate_id(kind, title, project)
    path = queue_path(state_dir)
    with locked(path):
        items, _ = load(state_dir)
        if any(i.id == cid and i.days_left > 0 for i in items):
            return cid, False
        entry = {"id": cid, "ts": utcnow().isoformat(timespec="seconds"), "kind": kind, "title": title,
                 "summary": summary, "project": project, "source": source}
        fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
        with os.fdopen(fd, "a", encoding="utf-8") as out:
            out.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return cid, True


def prune(state_dir: Path, *, apply: bool) -> list[Candidate]:
    """Drop expired candidates (unparsable lines are kept: they are not ours to delete). Dry run unless `apply`."""
    path = queue_path(state_dir)
    with locked(path):
        kept, expired = [], []
        for line in read_lines(path):
            item = parse_line(line)
            if item is not None and item.days_left <= 0:
                expired.append(item)
            else:
                kept.append(line)
        if apply and expired:
            fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".queue-")
            with os.fdopen(fd, "w", encoding="utf-8") as out:
                out.write("".join(line + "\n" for line in kept))
            os.chmod(tmp, 0o600)
            os.replace(tmp, path)
    return expired


def format_list(items: list[Candidate], expired: int, bad: int) -> str:
    if not items:
        tail = f" ({expired} expired, run `sb candidate prune --apply`)" if expired else ""
        return f"queue: empty{tail}\n"
    lines = []
    for item in sorted(items, key=lambda i: i.ts):
        soon = "  expires soon" if item.days_left <= WARN_DAYS else ""
        lines.append(f"{item.id}  {item.kind:<8} {item.age_days:>2}d (left {item.days_left:>2}d)  "
                     f"{item.project or '-'}: {item.title}{soon}")
    footer = f"queue: {len(items)} pending"
    if expired:
        footer += f", {expired} expired (run `sb candidate prune --apply`)"
    if bad:
        footer += f", {bad} unreadable line(s) kept"
    return "\n".join(lines) + "\n" + footer + "\n"


def summary_line(state_dir: Path) -> str:
    items, bad = load(state_dir)
    pending = live(items)
    soon = sum(1 for i in pending if i.days_left <= WARN_DAYS)
    expired = len(items) - len(pending)
    text = f"{len(pending)} pending"
    if soon:
        text += f", {soon} expire within {WARN_DAYS} days"
    if expired:
        text += f", {expired} expired"
    if bad:
        text += f", {bad} unreadable"
    return text
