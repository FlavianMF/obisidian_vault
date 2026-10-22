"""Review of notes already in the vault (Estudo S5, step I4b): `sb review promote` and `sb review stock`."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import uuid
from pathlib import Path
from typing import NamedTuple

import candidates
import generate_manifests as gm
import review
import vault_sync
from lib import frontmatter

INSTRUCTION_NOTE = "00_META/Agent-Instruction.md"
PROMOTE_TYPES = ("pattern", "trap", "decision", "concept")
PROMOTE_CONFIDENCE = ("medium", "high")
MIN_SEEN_IN = 2
STOCK_FILE = "review/stock.json"
KEEP_QUIET_DAYS = gm.DEFAULT_STALE_DAYS
UNCONFIRMED_DAYS = 30
UNCONFIRMED_MARK = "não reproduzido"


def last_events(state_dir: Path, stage: str) -> dict[str, dict]:
    """The last logged decision of one stage, per note."""
    last: dict[str, dict] = {}
    for line in candidates.read_lines(state_dir / candidates.REVIEW_LOG):
        try:
            raw = json.loads(line)
        except ValueError:
            continue
        if isinstance(raw, dict) and raw.get("stage") == stage and isinstance(raw.get("note"), str):
            last[raw["note"]] = raw
    return last


def decided_notes(state_dir: Path, stage: str) -> set[str]:
    return set(last_events(state_dir, stage))


def sha_of(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


def run_promote_apply(vault: Path, state_dir: Path, raw: list, *, apply: bool) -> tuple[int, str]:
    """`promote` only records: Agent-Instruction.md stays a manual edit, so the paste line is printed."""
    pending = {rel for rel, _ in promote_pending(vault, state_dir)}
    errors = []
    for n, d in enumerate(raw, start=1):
        if d.get("note") not in pending:
            errors.append(f"decision {n}: not pending for promotion")
        elif d.get("verdict") not in ("promote", "reject"):
            errors.append(f"decision {n}: verdict must be promote or reject")
        elif d["verdict"] == "reject" and not str(d.get("reason") or "").strip():
            errors.append(f"decision {n}: reject needs `reason`")
    if errors:
        return 1, "refused, nothing was changed:\n" + "\n".join(f"  {e}" for e in errors) + "\n"
    if not apply:
        return 0, f"{len(raw)} decision(s) valid\ndry run: nothing recorded (add --apply)\n"
    lines = []
    for d in raw:
        accepted = d["verdict"] == "promote"
        review.log_event(state_dir, {"stage": "promote", "note": d["note"],
                                     "outcome": "accepted" if accepted else "rejected", "reason": d.get("reason", "")})
        if accepted:
            lines.append(f"paste in {INSTRUCTION_NOTE}: - [[{Path(d['note']).stem}]]")
    return 0, "\n".join(lines + ["recorded"]) + "\n"


def promote_pending(vault: Path, state_dir: Path) -> list[tuple[str, dict]]:
    """Notes that earned a place in Agent-Instruction.md: global, medium or high confidence, seen in 2+ projects."""
    try:
        linked = {m.group(1).split("|", 1)[0].strip().casefold()
                  for m in gm.WIKILINK.finditer((vault / INSTRUCTION_NOTE).read_text(encoding="utf-8"))}
    except OSError:
        linked = set()
    done = decided_notes(state_dir, "promote")
    found = []
    for path, rel in gm.iter_notes(vault):
        fm_lines, _ = frontmatter.split_frontmatter(path.read_text(encoding="utf-8"))
        data, _ = frontmatter.parse_frontmatter(fm_lines or [])
        seen = data.get("seen_in", [])
        if rel.stem.casefold() in linked or str(rel) in done or data.get("status", "active") != "active":
            continue
        if data.get("type") not in PROMOTE_TYPES:
            continue
        if (data.get("scope") == "global" and data.get("confidence") in PROMOTE_CONFIDENCE
                and len(seen if isinstance(seen, list) else [seen]) >= MIN_SEEN_IN):
            found.append((str(rel), data))
    return found


def run_promote_next(vault: Path, state_dir: Path, *, limit: int) -> str:
    items = promote_pending(vault, state_dir)
    if not items:
        return "promote: nothing pending\n"
    lines = [f"promote: {min(limit, len(items))} of {len(items)} pending"]
    for n, (rel, data) in enumerate(items[:limit], start=1):
        seen = as_list(data.get("seen_in", []))
        lines += [f"[{n}] {rel}  {data.get('type')}  {data.get('confidence')}  seen in {len(seen)}: {', '.join(seen)}",
                  review.FRAME_OPEN, f"  | title:    {data.get('title', '')}",
                  f"  | verified: {data.get('verified') or '-'}", review.FRAME_CLOSE,
                  f"  proposal: promote as [[{Path(rel).stem}]]"]
    lines.append("Decide with `sb review promote apply --decisions FILE` (dry run unless --apply).")
    return "\n".join(lines) + "\n"


def stock_pending(vault: Path, state_dir: Path, today: dt.date, stale_days: int,
                  broken: dict[str, list[str]] | None) -> list[tuple[str, list[str]]]:
    """Notes that need a second look, each with its reasons."""
    quiet = {}
    for note, event in last_events(state_dir, "stock").items():
        on = gm.parse_date(str(event.get("on", "")))
        if event.get("outcome") == "kept" and on and today < on + dt.timedelta(days=KEEP_QUIET_DAYS):
            quiet[note] = event.get("sha")
    rows = []
    titles: dict[str, list[str]] = {}
    for path, rel in gm.iter_notes(vault):
        text = path.read_text(encoding="utf-8")
        if quiet.get(str(rel)) == sha_of(text):
            continue
        fm_lines, _ = frontmatter.split_frontmatter(text)
        data, _ = frontmatter.parse_frontmatter(fm_lines or [])
        if data.get("status", "active") != "active":
            continue
        rows.append((str(rel), data))
        titles.setdefault(str(data.get("title", "")).casefold(), []).append(str(rel))
    found = []
    for rel, data in rows:
        reasons = []
        verified = str(data.get("verified", ""))
        source = "verified" if gm.parse_date(verified) else "created"
        date = gm.parse_date(str(data.get(source, "")))
        if data.get("type") in gm.STALE_TYPES and (date is None or date < today - dt.timedelta(days=stale_days)):
            reasons.append(f"stale: {source} {date or '?'}")
        created = gm.parse_date(str(data.get("created", "")))
        if (data.get("confidence") == "low" and (not verified or UNCONFIRMED_MARK in verified)
                and created and created < today - dt.timedelta(days=UNCONFIRMED_DAYS)):
            reasons.append("unconfirmed: confidence low, never reproduced")
        twins = [r for r in titles[str(data.get("title", "")).casefold()] if r != rel]
        if data.get("title") and twins:
            reasons.append("duplicate title: " + ", ".join(twins))
        if broken and broken.get(rel):
            reasons.append("broken link: " + ", ".join(broken[rel][:3]))
        if reasons:
            found.append((rel, reasons))
    return found


def proposal_for(reasons: list[str]) -> str:
    text = " ".join(reasons)
    if "duplicate title" in text:
        return "merge into the other note, or retire"
    if "stale" in text or "broken link" in text:
        return "update (re-verify and renew `verified:`), or retire"
    return "update with a reproduction, or keep"


def run_stock_next(vault: Path, state_dir: Path, today: dt.date, *, limit: int, fresh: bool, stale_days: int,
                   broken: dict[str, list[str]] | None) -> str:
    pending = stock_pending(vault, state_dir, today, stale_days, broken)
    state = {} if fresh else review.load_batch_state(state_dir, STOCK_FILE)
    by_rel = dict(pending)
    items = [(rel, by_rel[rel]) for rel in state.get("ids", []) if rel in by_rel]
    if not items:
        items = pending[:limit]
        review.save_batch_state(state_dir, f"stock-{uuid.uuid4().hex[:6]}", review.now_iso(), [r for r, _ in items],
                                STOCK_FILE)
    blocks = [rel + "".join(f"\n  reason: {r}" for r in reasons) + f"\n  proposal: {proposal_for(reasons)}"
              for rel, reasons in items]
    return "\n".join(blocks) + "\n"


class Edit(NamedTuple):
    """What `review.sync_group` needs: the note and its whole new text."""
    note: str
    text: str
    new_because: str | None = None


class NoDraft:
    """Stand-in for review.read_body: a stock update has no queued draft, only `body_file`."""
    id = "none"


def verified_of(text: str) -> object:
    data, _ = frontmatter.parse_frontmatter(frontmatter.split_frontmatter(text)[0] or [])
    return data.get("verified")


def plan_update(vault: Path, state_dir: Path, d: dict) -> Edit:
    new_text = review.read_body(state_dir, NoDraft, d)
    old_text = (vault / d["note"]).read_text(encoding="utf-8")
    if verified_of(new_text) == verified_of(old_text):
        raise ValueError("renew `verified:` (today's date and how it was checked)")
    old_lines = {l.strip() for l in old_text.splitlines() if l.strip()}
    new_lines = {l.strip() for l in new_text.splitlines() if l.strip()}
    kept = len(old_lines & new_lines) / len(old_lines) if old_lines else 1.0
    if kept < review.MIN_KEEP_RATIO and not d.get("allow_rewrite"):
        raise ValueError(f"the update drops {1 - kept:.0%} of the old lines (limit {1 - review.MIN_KEEP_RATIO:.0%}); "
                         "keep the old text, or set `allow_rewrite` on purpose")
    review.refuse_secret(new_text)
    return Edit(d["note"], new_text)


STATUS_LINE = re.compile(r"(?m)^status:.*$")
OUTCOMES = {"keep": "kept", "update": "updated", "retire": "retired", "merge": "merged"}
SUPERSEDES_LINE = re.compile(r"(?m)^supersedes:.*$")


def set_status(text: str, value: str) -> str:
    fm_lines, _ = frontmatter.split_frontmatter(text)
    if fm_lines is None:
        raise ValueError("the note has no frontmatter")
    head = "".join(fm_lines)
    new_head = STATUS_LINE.sub(f"status: {value}", head, count=1) if STATUS_LINE.search(head) else head + f"status: {value}\n"
    return text.replace(head, new_head, 1)


def plan_retire(vault: Path, d: dict) -> list[Edit]:
    if not str(d.get("reason") or "").strip():
        raise ValueError("retire needs `reason`")
    return [Edit(d["note"], set_status((vault / d["note"]).read_text(encoding="utf-8"), "superseded"))]


def add_supersedes(text: str, title: str) -> str:
    fm_lines, _ = frontmatter.split_frontmatter(text)
    if fm_lines is None:
        raise ValueError("the target note has no frontmatter")
    head = "".join(fm_lines)
    data, _ = frontmatter.parse_frontmatter(fm_lines)
    current = [t for t in (str(x).strip("[]") for x in as_list(data.get("supersedes", []))) if t]
    if title in current:
        return text
    new_line = f"supersedes: [{', '.join([f'[[{t}]]' for t in current] + [f'[[{title}]]'])}]"
    new_head = SUPERSEDES_LINE.sub(lambda _: new_line, head, count=1) if SUPERSEDES_LINE.search(head) else head + new_line + "\n"
    return text.replace(head, new_head, 1)


def as_list(value: object) -> list[str]:
    items = value if isinstance(value, list) else [str(value or "")]
    return [i.strip() for i in items if i.strip()]


def plan_merge(vault: Path, d: dict) -> list[Edit]:
    edits = plan_retire(vault, d)
    into = str(d.get("into") or "").strip()
    path = Path(into)
    if not into or path.is_absolute() or ".." in path.parts or path.suffix != ".md" or into == d["note"]:
        raise ValueError("merge needs `into` (a vault-relative .md path of another note)")
    if not vault_sync.in_head(vault, into):
        raise ValueError(f"{into} is not in the vault yet")
    retired, _ = frontmatter.parse_frontmatter(frontmatter.split_frontmatter(edits[0].text)[0] or [])
    return edits + [Edit(into, add_supersedes((vault / into).read_text(encoding="utf-8"), str(retired.get("title"))))]


def run_stock_apply(vault: Path, state_dir: Path, today: dt.date, raw: list, *, apply: bool, stale_days: int,
                    broken: dict[str, list[str]] | None) -> tuple[int, str]:
    plans, errors = [], []
    pending = {rel for rel, _ in stock_pending(vault, state_dir, today, stale_days, broken)}
    seen: set[str] = set()
    for n, d in enumerate(raw, start=1):
        try:
            if d["note"] not in pending:
                raise ValueError("not pending in the stock review")
            if d["note"] in seen:
                raise ValueError("listed twice")
            seen.add(d["note"])
            if d["verdict"] not in OUTCOMES:
                raise ValueError(f"verdict must be one of {', '.join(OUTCOMES)}")
            if d["verdict"] == "update":
                plans.append((d, [plan_update(vault, state_dir, d)]))
            elif d["verdict"] == "retire":
                plans.append((d, plan_retire(vault, d)))
            elif d["verdict"] == "merge":
                plans.append((d, plan_merge(vault, d)))
            else:
                plans.append((d, []))
        except ValueError as err:
            errors.append(f"decision {n} ({d['note']}): {err}")
    if errors:
        return 1, "refused, nothing was changed:\n" + "\n".join(f"  {e}" for e in errors) + "\n"
    if not apply:
        return 0, f"{len(plans)} decision(s) valid\ndry run: nothing written (add --apply)\n"
    edits = [e for _, group in plans for e in group]
    sha = ""
    if edits:
        done, sha, detail = review.sync_group(vault, state_dir, edits, "absorb",
                                              f"docs(vault): review {len(edits)} note(s) in stock")
    for d, group in plans:
        text = (vault / d["note"]).read_text(encoding="utf-8")
        review.log_event(state_dir, {"stage": "stock", "note": d["note"], "outcome": OUTCOMES[d["verdict"]],
                                     "sha": sha_of(text), "on": today.isoformat(), "reason": d.get("reason", "")})
    return 0, "done\n"
