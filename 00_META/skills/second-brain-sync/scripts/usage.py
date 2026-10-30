"""Token usage per session, in numbers only (Estudo S5, step A: measurement).

`update` runs inside the Stop hook (`observe summarize`): it reads the numeric `usage` fields of the transcript
and of its subagent files, counts the usage-limit notices, and writes one record per session to
`<state>/usage/<session>.json`. It never stores a message, a command or the text of a notice. The record is a
function of the transcript, so a second run on the same transcript leaves the same bytes. `sb task set` keeps the
category of the session in `<state>/usage/<session>.task`. `build_report` and `format_report` back `sb usage report`.
Files are mode 0600 in a 0700 directory and expire after USAGE_TTL_DAYS.
"""
from __future__ import annotations

import datetime as dt
import json
import math
import os
import re
import tempfile
import time
import unicodedata
from pathlib import Path
from typing import Iterator, NamedTuple

from lib import secret_scan
from lib.session_id import safe_session

USAGE_DIR = "usage"
USAGE_TTL_DAYS = 90
TMP_TTL_SECONDS = 3600
CATEGORIES = ("feature", "bugfix", "pesquisa", "docs")
UNCATEGORIZED = "sem-categoria"
MAX_PROJECT = 120
MAX_DAYS = 3660
LIMIT_PREFIX = "Usage limit reached"
RECORD_VERSION = 1
RECORD_KEYS = frozenset((
    "v", "session", "date", "project", "category", "eq", "output", "main_eq", "main_output", "sub_eq", "sub_output",
    "limit_hits", "limit_at",
))
INT_KEYS = ("v", "eq", "output", "main_eq", "main_output", "sub_eq", "sub_output", "limit_hits")
TIMESTAMP = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]+)?Z")
VALID_SESSION = re.compile(r"[A-Za-z0-9_-]+")


class Totals(NamedTuple):
    eq: int  # same figure as the `eq` column of usage_baseline.sh --sidechain
    output: int


class Scan(NamedTuple):
    totals: Totals
    messages: int
    first_ts: str  # first valid timestamp in file order, "" when none
    limit_at: tuple[str, ...]  # one timestamp (or "") per usage-limit notice


def utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def usage_dir(state_dir: Path) -> Path:
    return state_dir / USAGE_DIR


def _session_path(state_dir: Path, session: str, suffix: str) -> Path:
    if not VALID_SESSION.fullmatch(session) or safe_session(session, cut=False) != session:
        raise ValueError("session id must be letters, digits, '_' or '-', at most 128, and not shaped like a credential")
    return usage_dir(state_dir) / f"{session}{suffix}"


def valid_timestamp(value: object) -> bool:
    if not isinstance(value, str) or not TIMESTAMP.fullmatch(value):
        return False
    try:
        dt.datetime.strptime(value[:19], "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        return False
    return True


def _count(value: object) -> int:
    """A whole number counts as is (negative too, like the jq baseline); anything else counts 0."""
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, float) and math.isfinite(value) and value.is_integer():
        return int(value)
    return 0


def _entries(path: Path) -> Iterator[dict]:
    """JSON objects of a JSONL file; a bad line is skipped. Raises OSError when the file cannot be read."""
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                raw = json.loads(line)
            except ValueError:
                continue
            if isinstance(raw, dict):
                yield raw


def _dedupe_key(entry: dict, message: dict) -> str:
    key = message.get("id")
    if key is None or key is False:  # jq: `.message.id // .uuid`
        key = entry.get("uuid")
    return json.dumps(key, sort_keys=True)


def scan(path: Path, *, main: bool) -> Scan | None:
    """Numbers of one transcript file, or None when it cannot be read.

    Claude Code writes one entry per content block, all with the usage of the whole reply, so the first entry of each
    message id counts. Usage-limit notices count only in the main thread.
    """
    replies: dict[str, dict] = {}
    first_ts = ""
    limit_at: list[str] = []
    seen_notices: set[str] = set()
    try:
        for entry in _entries(path):
            stamp = entry.get("timestamp")
            if main and not first_ts and valid_timestamp(stamp):
                first_ts = stamp
            message = entry.get("message")
            message = message if isinstance(message, dict) else {}
            if entry.get("type") == "assistant" and message.get("usage") is not None:
                replies.setdefault(_dedupe_key(entry, message), message["usage"])
            elif (main and entry.get("type") == "system" and entry.get("subtype") == "informational"
                  and isinstance(entry.get("content"), str) and entry["content"].startswith(LIMIT_PREFIX)):
                uuid = entry.get("uuid")
                if isinstance(uuid, str) and uuid:
                    if uuid in seen_notices:
                        continue
                    seen_notices.add(uuid)
                limit_at.append(stamp if valid_timestamp(stamp) else "")
    except OSError:
        return None
    sums = {"input_tokens": 0, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0, "output_tokens": 0}
    for usage in replies.values():
        for field in sums:
            sums[field] += _count(usage.get(field)) if isinstance(usage, dict) else 0
    eq = math.floor(sums["input_tokens"] + sums["cache_creation_input_tokens"] * 1.25
                    + sums["cache_read_input_tokens"] * 0.1)
    return Scan(Totals(eq, sums["output_tokens"]), len(replies), first_ts, tuple(limit_at))


def subagent_files(transcript: Path) -> list[Path]:
    return sorted((transcript.parent / transcript.stem / "subagents").glob("agent-*.jsonl"))


def clean_project(project: str) -> str:
    text = unicodedata.normalize("NFC", project)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Cc").strip()[:MAX_PROJECT]
    return "-" if secret_scan.contains_secret_shape(text) else text


def _expire(directory: Path, now: float) -> None:
    try:
        for entry in directory.iterdir():
            ttl = TMP_TTL_SECONDS if entry.suffix == ".tmp" else USAGE_TTL_DAYS * 86400
            if entry.suffix in (".json", ".task", ".tmp") and entry.stat().st_mtime < now - ttl:
                entry.unlink(missing_ok=True)
    except OSError:
        pass


def _write_atomic(state_dir: Path, target: Path, data: str) -> None:
    """The only write of this module: a unique temp file in the same directory, then os.replace."""
    if state_dir.resolve() not in target.resolve().parents:
        raise ValueError("refusing to write outside the state directory")
    state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)  # mkdir(parents=True) gives the parents the default mode
    target.parent.mkdir(exist_ok=True, mode=0o700)
    fd, tmp = tempfile.mkstemp(dir=target.parent, prefix="w-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as out:
            out.write(data)
        os.replace(tmp, target)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def write_task(state_dir: Path, session: str, category: str) -> None:
    if category not in CATEGORIES:
        raise ValueError(f"category must be one of {', '.join(CATEGORIES)}")
    _write_atomic(state_dir, _session_path(state_dir, session, ".task"), category + "\n")


def read_task(state_dir: Path, session: str) -> str | None:
    try:
        value = _session_path(state_dir, session, ".task").read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return value if value in CATEGORIES else None


def valid_record(raw: object) -> bool:
    if not isinstance(raw, dict) or set(raw) != RECORD_KEYS:
        return False
    if any(isinstance(raw[k], bool) or not isinstance(raw[k], int) for k in INT_KEYS):
        return False
    if not (isinstance(raw["category"], str) or raw["category"] is None):
        return False
    return (isinstance(raw["session"], str) and isinstance(raw["project"], str) and isinstance(raw["date"], str)
            and valid_timestamp(raw["date"] + "T00:00:00Z")
            and isinstance(raw["limit_at"], list) and all(isinstance(t, str) for t in raw["limit_at"]))


def load_record(path: Path) -> dict | None:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return raw if valid_record(raw) else None


def update(state_dir: Path, session: str, project: str, transcript: Path | None) -> dict | None:
    """Write the usage record of one session. Returns the record, or None when nothing is written.

    Nothing is written without a readable transcript that has a reply with `usage` or a limit notice, so a
    record that exists is never replaced by an empty one.
    """
    if transcript is None:
        return None
    main = scan(transcript, main=True)
    if main is None:
        return None
    subs = [s for s in (scan(p, main=False) for p in subagent_files(transcript)) if s is not None]
    if not (main.messages or main.limit_at or any(s.messages for s in subs)):
        return None
    path = _session_path(state_dir, session, ".json")
    previous = load_record(path)
    date = main.first_ts[:10] or (previous or {}).get("date") or utcnow().date().isoformat()
    sub_eq, sub_output = sum(s.totals.eq for s in subs), sum(s.totals.output for s in subs)
    record = {
        "v": RECORD_VERSION, "session": session, "date": date, "project": clean_project(project),
        "category": read_task(state_dir, session),
        "eq": main.totals.eq + sub_eq, "output": main.totals.output + sub_output,
        "main_eq": main.totals.eq, "main_output": main.totals.output, "sub_eq": sub_eq, "sub_output": sub_output,
        "limit_hits": len(main.limit_at), "limit_at": list(main.limit_at),
    }
    data = json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n"
    try:
        if path.read_text(encoding="utf-8") == data:
            return record
    except OSError:
        _expire(usage_dir(state_dir), time.time())  # a new record: sweep the old ones
    _write_atomic(state_dir, path, data)
    return record


def _event_date(stamp: str, fallback: dt.date) -> dt.date:
    try:
        return dt.date.fromisoformat(stamp[:10]) if stamp else fallback
    except ValueError:
        return fallback


def _iso_week(day: dt.date) -> str:
    year, week, _ = day.isocalendar()
    return f"{year}-W{week:02d}"


def build_report(state_dir: Path, days: int, today: dt.date) -> dict:
    """Totals per category and usage-limit notices per ISO week, over the last `days` days. Read-only."""
    start = today - dt.timedelta(days=days - 1)
    cats = {name: {"sessions": 0, "eq_total": 0, "output_total": 0} for name in (*CATEGORIES, UNCATEGORIZED)}
    weeks: dict[str, int] = {}
    for offset in range(days):
        weeks.setdefault(_iso_week(start + dt.timedelta(days=offset)), 0)
    sessions = skipped = 0
    try:
        files = sorted(usage_dir(state_dir).glob("*.json"))
    except OSError:
        files = []
    for path in files:
        record = load_record(path)
        if record is None:
            skipped += 1
            continue
        day = dt.date.fromisoformat(record["date"])
        if start <= day <= today:
            sessions += 1
            name = record["category"] if record["category"] in CATEGORIES else UNCATEGORIZED
            cats[name]["sessions"] += 1
            cats[name]["eq_total"] += record["eq"]
            cats[name]["output_total"] += record["output"]
        for stamp in record["limit_at"]:
            event = _event_date(stamp, day)
            if start <= event <= today:
                weeks[_iso_week(event)] += 1
    for row in cats.values():
        count = row["sessions"]
        row["eq_mean"] = row["eq_total"] // count if count else 0
        row["output_mean"] = row["output_total"] // count if count else 0
    return {"from": start.isoformat(), "to": today.isoformat(), "sessions": sessions, "categories": cats,
            "weeks": [{"week": week, "hits": hits} for week, hits in weeks.items()], "skipped": skipped}


def format_report(report: dict) -> str:
    lines = [f"uso por tarefa: {report['from']} a {report['to']}, {report['sessions']} sessoes",
             "categoria  sessoes  eq_total  eq_media  saida_total  saida_media"]
    for name, row in report["categories"].items():
        lines.append(f"{name}  {row['sessions']}  {row['eq_total']}  {row['eq_mean']}  "
                     f"{row['output_total']}  {row['output_mean']}")
    lines += ["", "estouros por semana"] + [f"{w['week']}  {w['hits']}" for w in report["weeks"]]
    if report["skipped"]:
        lines.append(f"ignorados: {report['skipped']}")
    return "\n".join(lines) + "\n"
