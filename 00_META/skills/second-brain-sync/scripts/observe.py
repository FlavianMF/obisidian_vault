"""Deterministic observer of the second-brain runtime (no model, no daemon).

`record` runs from a PostToolUse hook: one JSON line of metadata per tool call (tool name, file path, size of
the result), never content and never a command line. `summarize` runs from the Stop hook: it reads that log plus
the numeric `usage` fields of the transcript, and queues at most MAX_CANDIDATES candidates. It never writes the
vault. The log lives in `<state>/observe/<session>.jsonl` (mode 0600) and expires after LOG_TTL_DAYS.
"""
from __future__ import annotations

import json
import os
import re
import time
from collections import Counter
from pathlib import Path
from typing import NamedTuple

import candidates

LOG_DIR = "observe"
LOG_TTL_DAYS = 7
MAX_LOG_LINES = 5000
REREAD_MIN = 3  # same file read this many times in one session
BIG_READ_CHARS = 40_000
EXPENSIVE_TURN_TOKENS = 30_000  # cache_creation_input_tokens of one assistant message
MAX_CANDIDATES = 3
SKIP_PATH = re.compile(
    r"(^|/)(secrets|\.ssh|\.aws|\.gnupg)(/|$)|(^|/)\.env[^/]*$"
    r"|ecc-observer-analysis|(^|/)\.observer-tmp(/|$)"  # the ECC observer's own temp files: 63 of 141 candidates were noise
)
SAFE_SESSION = re.compile(r"[^A-Za-z0-9_-]")


class Finding(NamedTuple):
    kind: str
    title: str
    summary: str


def log_path(state_dir: Path, session: str) -> Path:
    return state_dir / LOG_DIR / f"{SAFE_SESSION.sub('', session)}.jsonl"


def _path_of(tool_input: object) -> str:
    if not isinstance(tool_input, dict):
        return ""
    for key in ("file_path", "notebook_path", "path"):
        value = tool_input.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def _size_of(tool_response: object) -> int:
    try:
        return len(tool_response) if isinstance(tool_response, str) else len(json.dumps(tool_response))
    except (TypeError, ValueError):
        return 0


def _expire_old_logs(directory: Path, now: float) -> None:
    cutoff = now - LOG_TTL_DAYS * 86400
    try:
        for entry in directory.iterdir():
            if entry.suffix == ".jsonl" and entry.stat().st_mtime < cutoff:
                entry.unlink(missing_ok=True)
    except OSError:
        pass


def record(state_dir: Path, payload: dict) -> bool:
    """Append one metadata line for a PostToolUse payload. Returns False when nothing was written."""
    session = SAFE_SESSION.sub("", str(payload.get("session_id") or ""))
    tool = str(payload.get("tool_name") or "")
    if not session or not tool or payload.get("agent_id"):
        return False
    path = _path_of(payload.get("tool_input"))
    if path and SKIP_PATH.search(path):
        return False
    target = log_path(state_dir, session)
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    now = time.time()
    if not target.exists():
        _expire_old_logs(target.parent, now)
    try:
        with target.open("rb") as existing:
            if sum(1 for _ in existing) >= MAX_LOG_LINES:
                return False
    except OSError:
        pass
    entry = {"ts": int(now), "tool": tool, "path": path, "size": _size_of(payload.get("tool_response"))}
    fd = os.open(target, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    with os.fdopen(fd, "a", encoding="utf-8") as out:
        out.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return True


def read_log(state_dir: Path, session: str) -> list[dict]:
    entries = []
    try:
        for line in log_path(state_dir, session).read_text(encoding="utf-8").splitlines():
            try:
                raw = json.loads(line)
            except ValueError:
                continue
            if isinstance(raw, dict) and isinstance(raw.get("tool"), str):
                entries.append(raw)
    except OSError:
        pass
    return entries


def expensive_turns(transcript: Path | None) -> int:
    """Assistant messages that created a lot of cache: numeric `usage` fields only, never content."""
    if transcript is None:
        return 0
    count = 0
    try:
        with transcript.open(encoding="utf-8") as handle:
            for line in handle:
                try:
                    raw = json.loads(line)
                except ValueError:
                    continue
                usage = (raw.get("message") or {}).get("usage") if isinstance(raw, dict) else None
                if isinstance(usage, dict) and raw.get("type") == "assistant":
                    created = usage.get("cache_creation_input_tokens")
                    if isinstance(created, int) and created >= EXPENSIVE_TURN_TOKENS:
                        count += 1
    except OSError:
        return 0
    return count


def analyze(entries: list[dict]) -> list[Finding]:
    reads = Counter(e["path"] for e in entries if e["tool"] == "Read" and e.get("path"))
    findings: list[Finding] = []
    for path, times in reads.most_common():
        if times >= REREAD_MIN:
            findings.append(Finding(
                "trap", f"Releitura repetida de {Path(path).name}",
                f"{Path(path).name} foi lido {times} vezes na mesma sessao; ler o trecho necessario ou guardar "
                f"o fato evita reprocessar o arquivo inteiro a cada turno."))
    big = {}
    for e in entries:
        if e["tool"] == "Read" and e.get("path") and isinstance(e.get("size"), int) and e["size"] >= BIG_READ_CHARS:
            big[e["path"]] = max(big.get(e["path"], 0), e["size"])
    for path, size in sorted(big.items(), key=lambda kv: -kv[1]):
        findings.append(Finding(
            "pattern", f"Read grande de {Path(path).name}",
            f"{Path(path).name} devolveu ~{size // 1000} mil caracteres de uma vez; buscar antes e ler so o "
            f"trecho (offset/limit) mantem o contexto pequeno."))
    return findings


def summarize(state_dir: Path, session: str, project: str, transcript: Path | None = None) -> dict:
    """Queue up to MAX_CANDIDATES findings. Returns counts; idempotent because the queue dedupes by id."""
    entries = read_log(state_dir, session)
    queued = 0
    findings = analyze(entries)
    for finding in findings[:MAX_CANDIDATES]:
        try:
            _, created = candidates.add(state_dir, kind=finding.kind, title=finding.title,
                                        summary=finding.summary, project=project, source="observer")
        except candidates.QueueError:
            continue
        queued += created
    return {"calls": len(entries), "findings": len(findings), "queued": queued,
            "expensive_turns": expensive_turns(transcript)}


def format_summary(result: dict) -> str:
    return (f"observer: {result['calls']} tool calls, {result['findings']} findings, "
            f"{result['queued']} queued, {result['expensive_turns']} expensive turns\n")

