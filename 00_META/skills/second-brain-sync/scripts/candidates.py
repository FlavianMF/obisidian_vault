"""Candidate queue of the second-brain runtime (Estudo S5, step I3).

An agent that was corrected, or that found a trap, appends one line here instead of writing to the vault.
The queue never touches the vault: a person turns a candidate into a note later (`sb review`, step I4).
Each line lives 30 days; the last 7 days are flagged. The file is local state, mode 0600, one JSON object per line.

Recurrence: adding a live duplicate from a session the line has not seen raises `count` and `sessions` in place and
appends the session id to `session_ids`. The same session again changes nothing, byte for byte, so the observer can
run on every Stop. A duplicate without a session id changes nothing either: it cannot prove another session. The
recurrence never renews `ts`, so a line still dies 30 days after it was first seen.
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
from lib.session_id import MAX_SESSION_LEN, MAX_SESSION_RAW, SAFE_SESSION, safe_session  # noqa: F401  (re-exported)

QUEUE_NAME = "queue.jsonl"
KINDS = ("trap", "pattern", "decision", "concept")
TTL_DAYS = 30
WARN_DAYS = 7
MAX_TITLE = 120
MAX_SUMMARY = 500
REVIEW_LOG = "review.jsonl"  # written by review.py; read here so a reviewed candidate never comes back
DRAFT_DIR = "drafts"  # optional note body that travels with a candidate
MAX_DRAFT_BYTES = 16 * 1024
MAX_SESSION_IDS = 100  # per line; `sessions` saturates here, and the gates only ask for >= 2
UNREADABLE = "\ufffd"  # what read_lines returns for a line that is not UTF-8: parse_line refuses it
DECIDED_OUTCOMES = ("applied", "rejected")
# mktemp-style suffix (`.QT9hkj`): six letters/digits with mixed case or a digit, so `.gradle` and `.json` stay.
TEMP_SUFFIX = re.compile(r"\.(?=[A-Za-z0-9]*[A-Z0-9])(?=[A-Za-z0-9]*[a-z])[A-Za-z0-9]{6}\b")


class Candidate(NamedTuple):
    id: str
    ts: dt.datetime
    kind: str
    title: str
    summary: str
    project: str
    source: str
    count: int = 1  # sessions that recorded it, plus one when the line came without a session id
    sessions: int = 0  # distinct session ids; always len(session_ids)
    session_ids: tuple[str, ...] = ()

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
    """Stable id; a random temp-file suffix in the title does not change it."""
    key = f"{kind}|{TEMP_SUFFIX.sub('', normalize(title)).casefold()}|{project.casefold()}"
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:8]


def decided_ids(state_dir: Path) -> set[str]:
    """Ids the review already turned into a note or rejected (review.jsonl is append-only)."""
    decided: set[str] = set()
    for line in read_lines(state_dir / REVIEW_LOG):
        try:
            raw = json.loads(line)
        except ValueError:
            continue
        if isinstance(raw, dict) and raw.get("outcome") in DECIDED_OUTCOMES and isinstance(raw.get("id"), str):
            decided.add(raw["id"])
    return decided


def was_decided(state_dir: Path, cid: str) -> bool:
    return cid in decided_ids(state_dir)


def draft_path(state_dir: Path, cid: str) -> Path:
    return state_dir / DRAFT_DIR / f"{re.sub(r'[^A-Za-z0-9]', '', cid)}.md"


def read_draft(state_dir: Path, cid: str) -> str | None:
    try:
        return draft_path(state_dir, cid).read_text(encoding="utf-8")
    except OSError:
        return None


def remove_draft(state_dir: Path, cid: str) -> None:
    draft_path(state_dir, cid).unlink(missing_ok=True)


def write_draft(state_dir: Path, cid: str, body: str) -> None:
    target = draft_path(state_dir, cid)
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, tmp = tempfile.mkstemp(dir=target.parent, prefix=".draft-")
    with os.fdopen(fd, "w", encoding="utf-8") as out:
        out.write(body)
    os.chmod(tmp, 0o600)
    os.replace(tmp, target)


@contextmanager
def locked(path: Path) -> Iterator[None]:
    """Serialise writers (two sessions can add at once); the lock file is the queue's sibling."""
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(path.with_suffix(".lock"), os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)  # private, whatever the umask
    with os.fdopen(fd, "a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def recurrence(raw: dict) -> tuple[int, tuple[str, ...]]:
    """`count` and `session_ids` of a line; a legacy or damaged line reads as count 1 with no ids."""
    ids: list[str] = []
    if isinstance(raw.get("session_ids"), list):
        ids = list(dict.fromkeys(i for i in raw["session_ids"] if isinstance(i, str) and i))
    count = raw.get("count")
    count = count if type(count) is int and count >= 1 else 1
    return max(count, len(ids)), tuple(ids)


def parse_line(line: str) -> Candidate | None:
    try:
        raw = json.loads(line)
        count, ids = recurrence(raw)
        return Candidate(
            id=str(raw["id"]), ts=dt.datetime.fromisoformat(raw["ts"]), kind=str(raw["kind"]),
            title=str(raw["title"]), summary=str(raw.get("summary", "")), project=str(raw.get("project", "")),
            source=str(raw.get("source", "agent")), count=count, sessions=len(ids), session_ids=ids,
        )
    except (ValueError, KeyError, TypeError, AttributeError):
        return None


def parse_bytes(line: bytes) -> tuple[dict, Candidate] | None:
    """A line as (its JSON object, its candidate), or None unless it is strict UTF-8 and a candidate."""
    try:
        text = line.decode("utf-8")
    except UnicodeDecodeError:
        return None
    item = parse_line(text)
    return None if item is None else (json.loads(text), item)


def read_lines(path: Path) -> list[str]:
    """Non-blank lines, split on newline only. A line that is not UTF-8 comes back as UNREADABLE, never raises."""
    try:
        data = path.read_bytes()
    except OSError:
        return []
    lines = []
    for raw in data.split(b"\n"):
        try:
            line = raw.decode("utf-8")
        except UnicodeDecodeError:
            line = UNREADABLE
        if line.strip():
            lines.append(line)
    return lines


def replace_file(path: Path, data: bytes) -> None:
    """Swap the queue for `data` in one step, mode 0600; the temp file is removed if anything fails."""
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".queue-")
    try:
        with os.fdopen(fd, "wb") as out:
            out.write(data)
        os.chmod(tmp, 0o600)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def load(state_dir: Path, include_decided: bool = False) -> tuple[list[Candidate], int]:
    """Parsable candidates that no review has decided yet, plus how many lines could not be parsed."""
    items, bad = [], 0
    decided = set() if include_decided else decided_ids(state_dir)
    for line in read_lines(queue_path(state_dir)):
        item = parse_line(line)
        if item is None:
            bad += 1
        elif item.id not in decided:
            items.append(item)
    return items, bad


def live(items: list[Candidate]) -> list[Candidate]:
    return [i for i in items if i.days_left > 0]


def add(state_dir: Path, *, kind: str, title: str, summary: str, project: str, source: str = "agent",
        body: str | None = None, session: str | None = None) -> tuple[str, bool]:
    """Append a candidate. Returns (id, created).

    Not queued again: an identical live candidate, or one the review already decided (`was_decided`). A live
    duplicate from a new `session` raises `count` and `sessions` in the first live line; the same session, or no
    session, changes nothing. `body` is an optional note draft that travels with the candidate (stored 0600, same
    lifetime). An unusable session id (empty, or shaped like a credential) is the same as none.
    """
    title, summary, project = normalize(title), normalize(summary), normalize(project)
    if kind not in KINDS:
        raise QueueError(f"kind must be one of {', '.join(KINDS)}")
    if not title:
        raise QueueError("title is empty")
    if len(title) > MAX_TITLE:
        raise QueueError(f"title is over {MAX_TITLE} characters")
    if len(summary) > MAX_SUMMARY:
        raise QueueError(f"summary is over {MAX_SUMMARY} characters")
    if body is not None and len(body.encode("utf-8")) > MAX_DRAFT_BYTES:
        raise QueueError(f"draft is over {MAX_DRAFT_BYTES // 1024} KB")
    findings = secret_scan.scan_text(f"{title}\n{summary}\n{body or ''}")
    if secret_scan.contains_secret_shape(project):  # a folder name can carry a token; the marker does not excuse it
        raise QueueError("project looks like a secret; nothing was queued")
    if findings:
        labels = ", ".join(sorted({f.label for f in findings}))
        raise QueueError(f"looks like a secret ({labels}); nothing was queued")
    cid = candidate_id(kind, title, project)
    sid = safe_session(session)
    path = queue_path(state_dir)
    with locked(path):
        if cid in decided_ids(state_dir):
            return cid, False
        try:
            data = path.read_bytes()
        except OSError:
            data = b""
        rows = data.split(b"\n") if data else []
        for index, row in enumerate(rows):
            parsed = parse_bytes(row)
            if parsed is None or parsed[1].id != cid or parsed[1].days_left <= 0:
                continue
            obj, item = parsed
            ids = list(item.session_ids)
            if sid is not None and sid not in ids and len(ids) < MAX_SESSION_IDS:
                ids.append(sid)
                obj.update(count=item.count + 1, sessions=len(ids), session_ids=ids)
                try:
                    rows[index] = json.dumps(obj, ensure_ascii=False).encode("utf-8")
                except UnicodeEncodeError:  # a lone surrogate that json.loads accepted
                    rows[index] = json.dumps(obj).encode("utf-8")
                replace_file(path, b"\n".join(rows))
            return cid, False
        if body:
            write_draft(state_dir, cid, body)
        entry = {"id": cid, "ts": utcnow().isoformat(timespec="seconds"), "kind": kind, "title": title,
                 "summary": summary, "project": project, "source": source, "count": 1,
                 "sessions": 1 if sid else 0, "session_ids": [sid] if sid else []}
        gap = b"\n" if data and not data.endswith(b"\n") else b""  # never glue onto an unterminated last line
        fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
        with os.fdopen(fd, "ab") as out:
            out.write(gap + (json.dumps(entry, ensure_ascii=False) + "\n").encode("utf-8"))
    return cid, True


def get(state_dir: Path, cid: str) -> Candidate | None:
    """The first live, undecided candidate with this id."""
    return next((i for i in live(load(state_dir)[0]) if i.id == cid), None)


def prune(state_dir: Path, *, apply: bool) -> list[Candidate]:
    """Drop expired candidates (every other line, readable or not, is kept byte for byte). Dry run unless `apply`."""
    path = queue_path(state_dir)
    with locked(path):
        try:
            rows = path.read_bytes().split(b"\n")
        except OSError:
            return []
        kept, expired = [], []
        for row in rows:
            parsed = parse_bytes(row)
            if parsed is not None and parsed[1].days_left <= 0:
                expired.append(parsed[1])
            else:
                kept.append(row)
        if apply and expired:
            replace_file(path, b"\n".join(kept))
            for item in expired:
                remove_draft(state_dir, item.id)
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
