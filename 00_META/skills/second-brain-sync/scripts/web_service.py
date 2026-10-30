"""web_service.py - FastAPI Service Layer and REST Endpoints for Candidate Review.

Handles candidate listing with L1 similarity matching, atomic decisions (save, absorb, drop, skip)
via the review.py / vault_sync.py pipeline, and LIFO undo operations.
Never directly writes to vault .md files (delegates strictly to review.run_apply).
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlsplit

from fastapi import FastAPI, HTTPException, Query, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

# Ensure local scripts are importable
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import candidates
import review
import vault_sync
from lib import frontmatter, secret_scan

WEB_DIR = HERE / "web"
DEFAULT_ALLOWED_HOSTS = frozenset({"127.0.0.1", "localhost", "::1", "testserver"})
SAFE_METHODS = ("GET", "HEAD", "OPTIONS")
DROP_REASON_WEB = "descartado na revisão web"
# key -> action; the page serialises this dict, so it is the single source of the keyboard map
SHORTCUTS = {"s": "save", "a": "absorb", "d": "drop", "p": "skip", "z": "undo", "j": "next", "k": "prev", "e": "edit"}

# Negative section regex matching vault_sync
NEGATIVE_SECTION = vault_sync.NEGATIVE_SECTION
SECTION_TYPES = vault_sync.SECTION_TYPES
TAG_REGEX = review.TAG


# ---------------------------------------------------------------- Models
class ErrorResponse(BaseModel):
    detail: str
    errors: List[str] = Field(default_factory=list)


class SecretErrorResponse(BaseModel):
    detail: str = "Secret detected"
    findings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class SimilarNote(BaseModel):
    path: str
    title: str
    coverage: float
    terms: int = 0


class CandidateItem(BaseModel):
    id: str
    kind: str
    title: str
    summary: str
    project: str
    source: str
    count: int
    sessions: int
    session_ids: List[str]
    ts: str
    age_days: int
    days_left: int
    has_draft: bool
    draft_content: Optional[str] = None
    similar: List[SimilarNote] = Field(default_factory=list)
    proposal: str
    proposal_detail: str


class CandidatesResponse(BaseModel):
    total: int
    limit: int
    offset: int
    candidates: List[CandidateItem]


class DecideRequest(BaseModel):
    id: str
    action: str  # save, absorb, drop, skip
    title: Optional[str] = None
    tags: Optional[List[str]] = None
    note: Optional[str] = None
    body: Optional[str] = None
    reason: Optional[str] = None
    new_because: Optional[str] = None
    allow_rewrite: Optional[bool] = False
    dry_run: bool = False  # validate exactly like a real decision, change nothing


class DecideResponse(BaseModel):
    success: bool
    action: str
    id: str
    message: str
    sha: Optional[str] = None
    next_candidate_id: Optional[str] = None
    dry_run: bool = False


class UndoRequest(BaseModel):
    candidate_id: Optional[str] = None


class UndoResponse(BaseModel):
    success: bool
    reverted_action: str
    id: str
    message: str


# ---------------------------------------------------------------- Helpers
def get_vault_path(app: FastAPI) -> Path:
    vault = getattr(app.state, "vault_path", None)
    if not vault:
        env = os.environ.get("SECOND_BRAIN_VAULT")
        vault = Path(env).resolve() if env else HERE.parents[3]
    return Path(vault).resolve()


def get_state_dir(app: FastAPI) -> Path:
    state = getattr(app.state, "state_dir", None)
    if not state:
        env = os.environ.get("SECOND_BRAIN_STATE_DIR")
        state = Path(env).resolve() if env else Path.home() / ".local" / "state" / "second-brain"
    return Path(state).resolve()


def check_secrets_in_texts(texts: Dict[str, Optional[str]]) -> List[str]:
    findings_labels = set()
    for field, text in texts.items():
        if text:
            findings = secret_scan.scan_text(text)
            for f in findings:
                findings_labels.add(f.label)
    return sorted(findings_labels)


def remove_decision_from_log(state_dir: Path, cid: str) -> None:
    review_log = state_dir / candidates.REVIEW_LOG
    if not review_log.exists():
        return
    with candidates.locked(review_log):
        lines = candidates.read_lines(review_log)
        filtered = []
        for line in lines:
            try:
                row = json.loads(line)
                if isinstance(row, dict) and row.get("id") == cid and row.get("outcome") in candidates.DECIDED_OUTCOMES:
                    continue
                filtered.append(line)
            except ValueError:
                filtered.append(line)
        data = "\n".join(filtered) + ("\n" if filtered else "")
        candidates.replace_file(review_log, data.encode("utf-8"))


def apply_decision(v_path: Path, s_dir: Path, decision: Dict[str, Any], body_text: Optional[str], dry_run: bool):
    """review.run_apply for one decision. The body travels as a file: in tmp_decisions for a real run, in a throwaway
    system temp dir for a dry run, so a dry run leaves nothing in the state dir or the vault."""
    if body_text is None:
        return review.run_apply(v_path, s_dir, [decision], apply=not dry_run)
    if dry_run:
        with tempfile.TemporaryDirectory(prefix="sb-dry-") as tmp:
            body_file = Path(tmp) / "body.txt"
            candidates.replace_file(body_file, body_text.encode("utf-8"))
            return review.run_apply(v_path, s_dir, [{**decision, "body_file": str(body_file)}], apply=False)
    temp_dir = s_dir / "tmp_decisions"
    temp_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    body_file = temp_dir / f"body-{decision['id']}.txt"
    candidates.replace_file(body_file, body_text.encode("utf-8"))
    try:
        return review.run_apply(v_path, s_dir, [{**decision, "body_file": str(body_file)}], apply=True)
    finally:
        body_file.unlink(missing_ok=True)


def build_item(v_path: Path, s_dir: Path, cand: candidates.Candidate) -> CandidateItem:
    matches = review.matches_for(v_path, cand)
    verdict, detail = review.propose(cand, matches, v_path)
    draft_text = candidates.read_draft(s_dir, cand.id)
    return CandidateItem(
        id=cand.id,
        kind=cand.kind,
        title=cand.title,
        summary=cand.summary,
        project=cand.project,
        source=cand.source,
        count=cand.count,
        sessions=cand.sessions,
        session_ids=list(cand.session_ids),
        ts=cand.ts.isoformat(),
        age_days=cand.age_days,
        days_left=cand.days_left,
        has_draft=draft_text is not None,
        draft_content=draft_text,
        similar=[SimilarNote(path=m.path, title=m.title, coverage=m.coverage, terms=m.terms) for m in matches],
        proposal=verdict,
        proposal_detail=detail,
    )


class StatsResponse(BaseModel):
    pending: int
    today_applied: int
    today_rejected: int


def request_host(host_header: str) -> str:
    """The host part of a Host header, without port or IPv6 brackets."""
    host = host_header.strip().lower()
    if host.startswith("["):
        return host[1:].split("]", 1)[0]
    return host.rsplit(":", 1)[0] if host.count(":") == 1 else host


def today_counts(state_dir: Path) -> Tuple[int, int]:
    """(applied, rejected) decisions logged today (UTC) in review.jsonl."""
    review_log = state_dir / candidates.REVIEW_LOG
    today = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    applied = rejected = 0
    for line in candidates.read_lines(review_log):
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if not isinstance(row, dict) or not str(row.get("ts", "")).startswith(today):
            continue
        applied += row.get("outcome") == "applied"
        rejected += row.get("outcome") == "rejected"
    return applied, rejected


def scaffold_body(cand: candidates.Candidate) -> str:
    """The starting body of a candidate that has no draft; it carries the negative section trap/pattern notes need."""
    return f"## Contexto\n{cand.summary}\n\n## O que NÃO funcionou\n- A preencher\n"


def compose_absorb_text(old_text: str, cand: candidates.Candidate) -> str:
    """The updated note, in memory only: project in `seen_in`, renewed `verified`, one dated history line."""
    project, day = review.slug(cand.project), review.today()
    lines = old_text.splitlines(keepends=True)
    fm_lines, _ = frontmatter.split_frontmatter(old_text)
    if fm_lines is None:
        return old_text
    end = len(fm_lines) + 1  # index of the closing `---`
    verified = f"verified: {day} via revisão web, não reproduzido\n"
    seen_done = verified_done = False
    for index in range(1, end):
        key = lines[index].partition(":")[0].strip()
        if key == "seen_in":
            data, _ = frontmatter.parse_frontmatter([lines[index]])
            known = data.get("seen_in", [])
            known = known if isinstance(known, list) else [str(known)]
            if project not in known:
                known = [*[k for k in known if k], project]
            lines[index] = f"seen_in: [{', '.join(known)}]\n"
            seen_done = True
        elif key == "verified":
            lines[index] = verified
            verified_done = True
    extra = ([] if seen_done else [f"seen_in: [{project}]\n"]) + ([] if verified_done else [verified])
    lines[end:end] = extra
    text = "".join(lines)
    return text.rstrip("\n") + f"\n\n- {day} ({project}): {cand.summary}\n"


# ---------------------------------------------------------------- App Factory
def create_app(
    vault_path: Optional[Path] = None,
    state_dir: Optional[Path] = None,
    allowed_hosts: Optional[set[str]] = None,
) -> FastAPI:
    app = FastAPI(title="Candidate Review Web API", version="1.0.0")
    templates = Jinja2Templates(directory=str(WEB_DIR / "templates"))  # autoescape is on for .html
    app.mount("/static", StaticFiles(directory=str(WEB_DIR / "static")), name="static")
    hosts = {h.lower() for h in (allowed_hosts if allowed_hosts is not None else DEFAULT_ALLOWED_HOSTS)}

    app.state.vault_path = Path(vault_path).resolve() if vault_path else None
    app.state.state_dir = Path(state_dir).resolve() if state_dir else None
    app.state.undo_stack: List[Dict[str, Any]] = []
    app.state.skipped_ids: set[str] = set()
    app.state.lock = threading.RLock()  # decide/undo mutate the vault, the log and the stack: one at a time

    def error_fragment(request: Request, code: int, detail: str, errors: List[str]):
        return templates.TemplateResponse(request, "_error.html", {"code": code, "detail": detail, "errors": errors},
                                          status_code=code)

    # The app can write to the vault and listens on loopback: refuse DNS rebinding and cross-site posts
    @app.middleware("http")
    async def local_only_guard(request: Request, call_next):
        host_header = request.headers.get("host", "")
        origin = request.headers.get("origin")
        bad_host = request_host(host_header) not in hosts
        bad_origin = (
            request.method not in SAFE_METHODS
            and origin is not None
            and urlsplit(origin).netloc.lower() != host_header.strip().lower()
        )
        if bad_host or bad_origin:
            reason = "host" if bad_host else "origin"
            return JSONResponse(
                status_code=403,
                content={"detail": "Forbidden host/origin", "errors": [f"{reason} not allowed"]},
            )
        return await call_next(request)

    # Unified error exception handlers
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors_list = [f"{'.'.join(str(l) for l in err.get('loc', []))}: {err.get('msg')}" for err in exc.errors()]
        if request.url.path.startswith("/ui/"):
            return error_fragment(request, 422, "Request validation failed", errors_list)
        return JSONResponse(
            status_code=422,
            content={"detail": "Request validation failed", "errors": errors_list},
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": detail, "errors": []},
        )

    @app.get("/api/candidates", response_model=CandidatesResponse)
    def list_candidates(
        limit: int = Query(default=10, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
        project: Optional[str] = None,
        kind: Optional[str] = None,
        source: Optional[str] = None,
    ):
        v_path = get_vault_path(app)
        s_dir = get_state_dir(app)

        all_pending = review.pending(s_dir, project=project or "", kind=kind or "", source=source or "")
        total = len(all_pending)

        slice_items = all_pending[offset : offset + limit]
        result_candidates = [build_item(v_path, s_dir, cand) for cand in slice_items]

        return CandidatesResponse(
            total=total,
            limit=limit,
            offset=offset,
            candidates=result_candidates,
        )

    @app.post("/api/decide", response_model=DecideResponse)
    def decide_candidate(req: DecideRequest):
        with app.state.lock:
            return _decide(req)

    def _decide(req: DecideRequest):
        v_path = get_vault_path(app)
        s_dir = get_state_dir(app)

        action = req.action.lower().strip()
        if action not in ("save", "absorb", "drop", "skip"):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": f"Invalid action '{req.action}'. Must be save, absorb, drop, or skip", "errors": ["invalid action"]},
            )

        # 1. Check secrets (I2)
        secret_findings = check_secrets_in_texts({"title": req.title, "body": req.body, "reason": req.reason})
        if secret_findings:
            return JSONResponse(
                status_code=422,
                content={"detail": "Secret detected", "findings": secret_findings, "errors": secret_findings},
            )

        # 2. Candidate existence in pending
        pending_list = review.pending(s_dir)
        cand_map = {c.id: c for c in pending_list}
        cand = cand_map.get(req.id)
        if not cand:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": f"Candidate '{req.id}' not found in pending queue", "errors": []},
            )

        # Pre-capture draft content in memory for Undo
        existing_draft = candidates.read_draft(s_dir, cand.id)

        # Helper to find next candidate
        def find_next_candidate_id(exclude_id: str) -> Optional[str]:
            refreshed = review.pending(s_dir)
            for c in refreshed:
                if c.id != exclude_id and c.id not in app.state.skipped_ids:
                    return c.id
            for c in refreshed:
                if c.id != exclude_id:
                    return c.id
            return None

        # -------------------------------- SKIP --------------------------------
        if action == "skip":
            if req.dry_run:
                return DecideResponse(success=True, action="skip", id=cand.id, message="valid", dry_run=True)
            app.state.skipped_ids.add(cand.id)
            app.state.undo_stack.append({
                "action": "skip",
                "id": cand.id,
                "cand": cand,
                "draft_content": existing_draft,
                "sha": None,
            })
            next_id = find_next_candidate_id(cand.id)
            return DecideResponse(
                success=True,
                action="skip",
                id=cand.id,
                message=f"Candidate {cand.id} skipped for this session",
                sha=None,
                next_candidate_id=next_id,
            )

        # -------------------------------- DROP --------------------------------
        if action == "drop":
            reason = (req.reason or "").strip()
            if not reason:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": "drop needs non-empty reason", "errors": ["reason is required"]},
                )

            code, msg = apply_decision(v_path, s_dir, {"id": cand.id, "verdict": "drop", "reason": reason}, None, req.dry_run)
            if code != 0:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": msg.strip(), "errors": [msg.strip()]},
                )
            if req.dry_run:
                return DecideResponse(success=True, action="drop", id=cand.id, message="valid", dry_run=True)

            app.state.undo_stack.append({
                "action": "drop",
                "id": cand.id,
                "cand": cand,
                "draft_content": existing_draft,
                "sha": None,
            })

            next_id = find_next_candidate_id(cand.id)
            return DecideResponse(
                success=True,
                action="drop",
                id=cand.id,
                message=f"Candidate {cand.id} rejected",
                sha=None,
                next_candidate_id=next_id,
            )

        # -------------------------------- SAVE --------------------------------
        if action == "save":
            title = re.sub(r"\s+", " ", str(req.title or cand.title)).strip()
            filename = review.note_filename(title)
            if not filename:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": "The title leaves no usable file name", "errors": ["invalid title"]},
                )
            target_note = f"{review.NOTE_DIR}/{filename}.md"

            # Check 409 conflict
            if (v_path / target_note).exists() or vault_sync.in_head(v_path, target_note):
                return JSONResponse(
                    status_code=status.HTTP_409_CONFLICT,
                    content={"detail": f"{target_note} already exists; use absorb to update it", "errors": [f"{target_note} already exists"]},
                )

            # Body resolution: req.body > existing_draft > scaffold
            body_text = req.body
            if not body_text or not body_text.strip():
                if existing_draft and existing_draft.strip():
                    body_text = existing_draft
                else:
                    # Auto-scaffold
                    body_text = scaffold_body(cand)

            # Validate negative section for trap / pattern
            if cand.kind in SECTION_TYPES and not NEGATIVE_SECTION.search(body_text):
                return JSONResponse(
                    status_code=422,
                    content={"detail": f"a new {cand.kind} note needs an 'O que NÃO funcionou' section", "errors": ["Missing required negative section '## O que NÃO funcionou'"]},
                )

            # Validate tags
            tags = req.tags or [cand.kind, review.slug(cand.project)]
            if not isinstance(tags, list) or not all(isinstance(t, str) and TAG_REGEX.match(t) for t in tags):
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": "`tags` must be a list of lowercase words (letters, digits, - _ .)", "errors": ["Invalid tags"]},
                )

            # Check duplicate coverage threshold (>= 0.5 requires new_because)
            matches = review.matches_for(v_path, cand)
            top = matches[0] if matches else review.Match("", "", 0.0)
            if top.coverage >= vault_sync.DEFAULT_DUP_COVERAGE and not req.new_because:
                return JSONResponse(
                    status_code=422,
                    content={
                        "detail": f"Similar note exists with coverage {top.coverage:.2f} >= 0.50. `new_because` is required.",
                        "errors": ["new_because is required for high similarity notes"],
                    },
                )

            decision_payload = {
                "id": cand.id,
                "verdict": "save",
                "title": title,
                "tags": tags,
                "new_because": req.new_because or "",
            }
            code, msg = apply_decision(v_path, s_dir, decision_payload, body_text, req.dry_run)
            if code != 0:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": msg.strip(), "errors": [msg.strip()]},
                )
            if req.dry_run:
                return DecideResponse(success=True, action="save", id=cand.id, message="valid", dry_run=True)

            full_sha = vault_sync.run_git(v_path, ["rev-parse", "HEAD"], check=False).stdout.strip()

            app.state.undo_stack.append({
                "action": "save",
                "id": cand.id,
                "cand": cand,
                "draft_content": existing_draft,
                "sha": full_sha,
                "note": target_note,
            })

            next_id = find_next_candidate_id(cand.id)
            return DecideResponse(
                success=True,
                action="save",
                id=cand.id,
                message=msg.strip(),
                sha=full_sha,
                next_candidate_id=next_id,
            )

        # -------------------------------- ABSORB ------------------------------
        if action == "absorb":
            note_rel = (req.note or "").strip()
            if not note_rel:  # no target given: the note the ranker covers best
                found = review.matches_for(v_path, cand)
                note_rel = found[0].path if found else ""
                if not note_rel:
                    return JSONResponse(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        content={"detail": "absorb needs `note`: no similar note was found to default to", "errors": []},
                    )
            if not note_rel.endswith(".md") or Path(note_rel).is_absolute() or ".." in Path(note_rel).parts:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": "absorb needs `note` (a vault-relative .md path) and valid body", "errors": []},
                )

            if not (v_path / note_rel).exists() or not vault_sync.in_head(v_path, note_rel):
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={"detail": f"{note_rel} is not in the vault yet; use save", "errors": []},
                )

            # a draft is a note body; it only stands for the whole updated note when it brings its own frontmatter
            whole_draft = existing_draft if existing_draft and frontmatter.has_frontmatter(existing_draft) else None
            body_text = req.body or whole_draft
            composed = not body_text or not body_text.strip()
            if composed:  # no text sent and no draft: build the update in memory, review.run_apply persists it
                body_text = compose_absorb_text((v_path / note_rel).read_text(encoding="utf-8"), cand)
                composed_findings = check_secrets_in_texts({"note": body_text})
                if composed_findings:
                    return JSONResponse(
                        status_code=422,
                        content={"detail": "Secret detected", "findings": composed_findings, "errors": composed_findings},
                    )

            # Check frontmatter in body_text
            fm_lines, _ = frontmatter.split_frontmatter(body_text)
            if fm_lines is None:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": "the updated note has no frontmatter", "errors": []},
                )
            new_data, _ = frontmatter.parse_frontmatter(fm_lines)
            old_data, _, _ = frontmatter.read_note(v_path / note_rel)

            seen = new_data.get("seen_in", [])
            seen_set = set(seen if isinstance(seen, list) else [str(seen)])
            if cand.project not in seen_set and review.slug(cand.project) not in seen_set:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": f"add `{cand.project}` to `seen_in` of {note_rel}", "errors": []},
                )

            if new_data.get("verified") == old_data.get("verified"):
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": "renew `verified:` (today's date and how it was checked)", "errors": []},
                )

            decision_payload = {
                "id": cand.id,
                "verdict": "absorb",
                "note": note_rel,
                "allow_rewrite": bool(req.allow_rewrite) or composed,  # a composed update only touches two lines
            }
            code, msg = apply_decision(v_path, s_dir, decision_payload, body_text, req.dry_run)
            if code != 0:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": msg.strip(), "errors": [msg.strip()]},
                )
            if req.dry_run:
                return DecideResponse(success=True, action="absorb", id=cand.id, message="valid", dry_run=True)

            full_sha = vault_sync.run_git(v_path, ["rev-parse", "HEAD"], check=False).stdout.strip()

            app.state.undo_stack.append({
                "action": "absorb",
                "id": cand.id,
                "cand": cand,
                "draft_content": existing_draft,
                "sha": full_sha,
                "note": note_rel,
            })

            next_id = find_next_candidate_id(cand.id)
            return DecideResponse(
                success=True,
                action="absorb",
                id=cand.id,
                message=msg.strip(),
                sha=full_sha,
                next_candidate_id=next_id,
            )

    @app.post("/api/undo", response_model=UndoResponse)
    def undo_decision(req: Optional[UndoRequest] = None):
        req = req or UndoRequest()
        with app.state.lock:
            return _undo(req)

    def _undo(req: UndoRequest):
        v_path = get_vault_path(app)
        s_dir = get_state_dir(app)

        if not app.state.undo_stack:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": "Undo stack is empty", "errors": []},
            )

        top = app.state.undo_stack[-1]
        cid = req.candidate_id
        if cid and all(entry["id"] != cid for entry in app.state.undo_stack):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": f"Candidate '{cid}' has no reversible decision", "errors": []},
            )
        if cid and cid != top["id"]:
            # If attempting non-LIFO undo, return 400 Bad Request
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": f"Cannot undo candidate '{cid}': not on top of LIFO stack (expected '{top['id']}')", "errors": ["LIFO violation"]},
            )

        item = app.state.undo_stack.pop()
        action = item["action"]
        cand_id = item["id"]
        draft_content = item["draft_content"]
        sha = item.get("sha")

        # Undo based on action
        if action == "skip":
            app.state.skipped_ids.discard(cand_id)
            return UndoResponse(
                success=True,
                reverted_action="skip",
                id=cand_id,
                message=f"Skipped candidate {cand_id} restored to active queue",
            )

        if action == "drop":
            remove_decision_from_log(s_dir, cand_id)
            if draft_content is not None:
                candidates.write_draft(s_dir, cand_id, draft_content)
            return UndoResponse(
                success=True,
                reverted_action="drop",
                id=cand_id,
                message=f"Rejection of candidate {cand_id} undone; reinstated as pending",
            )

        if action in ("save", "absorb"):
            if sha:
                # Revert git commit
                done = subprocess.run(
                    ["git", "-C", str(v_path), "revert", "--no-edit", sha],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if done.returncode != 0:
                    # Merge conflict in revert: abort and return 409
                    subprocess.run(["git", "-C", str(v_path), "revert", "--abort"], capture_output=True, check=False)
                    # Put back on stack since revert failed
                    app.state.undo_stack.append(item)
                    return JSONResponse(
                        status_code=status.HTTP_409_CONFLICT,
                        content={"detail": f"git revert of commit {sha} resulted in conflicts; aborted", "errors": [done.stderr.strip()]},
                    )

            remove_decision_from_log(s_dir, cand_id)
            if draft_content is not None:
                candidates.write_draft(s_dir, cand_id, draft_content)

            return UndoResponse(
                success=True,
                reverted_action=action,
                id=cand_id,
                message=f"Action '{action}' on candidate {cand_id} reverted successfully",
            )

        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": f"Unknown action '{action}' in undo stack", "errors": []},
        )

    # ---------------------------------------------------------------- UI
    def candidate_context(id: Optional[str], offset: int, project: str, kind: str, source: str):
        """(context, error): the data one fragment renders, or why that candidate cannot be shown."""
        v_path, s_dir = get_vault_path(app), get_state_dir(app)
        queue = review.pending(s_dir, project=project, kind=kind, source=source)
        total = len(queue)
        position: Optional[int] = None
        if id:
            position = next((i for i, c in enumerate(queue) if c.id == id), None)
            if position is None:
                return None, f"Candidate '{id}' is not pending"
        elif queue:
            if offset >= total:
                return None, f"Offset {offset} is past the end of the queue ({total})"
            position = offset
        item = build_item(v_path, s_dir, queue[position]) if position is not None else None
        return {"item": item, "offset": position or 0, "total": total}, None

    @app.get("/ui/candidate", response_class=HTMLResponse)
    def ui_candidate(
        request: Request,
        id: Optional[str] = None,
        offset: int = Query(default=0, ge=0),
        project: str = "",
        kind: str = "",
        source: str = "",
    ):
        ctx, err = candidate_context(id, offset, project, kind, source)
        if err:
            return error_fragment(request, 404, err, [])
        return templates.TemplateResponse(request, "_candidate.html", ctx)

    @app.get("/ui/editor", response_class=HTMLResponse)
    def ui_editor(request: Request, id: str, mode: Optional[str] = None, note: str = ""):
        v_path, s_dir = get_vault_path(app), get_state_dir(app)
        cand = next((c for c in review.pending(s_dir) if c.id == id), None)
        if cand is None:
            return error_fragment(request, 404, f"Candidate '{id}' is not pending", [])
        item = build_item(v_path, s_dir, cand)
        if mode is None:
            mode = "absorb" if item.proposal == "absorb" and item.similar else "save"
        if mode not in ("save", "absorb"):
            return error_fragment(request, 422, "mode must be save or absorb", [f"mode: {mode}"])
        targets = [m.path for m in item.similar]
        draft = item.draft_content if item.draft_content and item.draft_content.strip() else None
        if mode == "save":
            body, target = draft or scaffold_body(cand), ""
        else:
            target = note.strip() or (targets[0] if targets else "")
            path = Path(target)
            if not target or path.is_absolute() or ".." in path.parts or path.suffix != ".md":
                return error_fragment(request, 404, "No similar note to absorb into; use save", [])
            if not (v_path / target).exists() or not vault_sync.in_head(v_path, target):
                return error_fragment(request, 404, f"{target} is not in the vault yet; use save", [])
            whole = draft if draft and frontmatter.has_frontmatter(draft) else None
            body = whole or compose_absorb_text((v_path / target).read_text(encoding="utf-8"), cand)
            if target not in targets:
                targets.append(target)
        ctx = {
            "item": item,
            "mode": mode,
            "title": item.title,
            "tags": ", ".join([item.kind, review.slug(item.project)]),
            "body": body,
            "target": target,
            "targets": targets,
        }
        return templates.TemplateResponse(request, "_editor.html", ctx)

    @app.get("/api/filters")
    def filters():
        s_dir = get_state_dir(app)
        all_pending = review.pending(s_dir)
        projects = sorted({c.project for c in all_pending if c.project})
        return {"projects": projects, "kinds": list(candidates.KINDS)}

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request, project: str = "", kind: str = "", source: str = ""):
        s_dir = get_state_dir(app)
        ctx, _ = candidate_context(None, 0, project, kind, source)
        applied, rejected = today_counts(s_dir)
        all_pending = review.pending(s_dir)
        projects = sorted({c.project for c in all_pending if c.project})
        ctx = {
            **ctx,
            "pending": ctx["total"],
            "today_applied": applied,
            "today_rejected": rejected,
            "shortcuts": SHORTCUTS,
            "shortcuts_json": json.dumps(SHORTCUTS),
            "projects": projects,
            "kinds": list(candidates.KINDS),
            "current_project": project,
            "current_kind": kind,
            "current_source": source,
            "query": {k: v for k, v in (("project", project), ("kind", kind), ("source", source)) if v},
        }
        return templates.TemplateResponse(request, "index.html", ctx)

    @app.get("/api/stats", response_model=StatsResponse)
    def stats():
        s_dir = get_state_dir(app)
        applied, rejected = today_counts(s_dir)
        return StatsResponse(pending=len(review.pending(s_dir)), today_applied=applied, today_rejected=rejected)

    return app


def run_server(
    vault_path: Optional[Path] = None,
    state_dir: Optional[Path] = None,
    host: str = "127.0.0.1",
    port: int = 8000,
    open_browser: bool = True,
    log_level: str = "info",
) -> int:
    """Runs the FastAPI candidate review app with uvicorn, optionally opens browser, and handles shutdown cleanly."""
    import time
    import webbrowser
    import uvicorn

    app = create_app(vault_path, state_dir)
    url = f"http://{host}:{port}/"
    sys.stdout.write(f"Iniciando Second Brain Review Web em {url}\n")
    sys.stdout.flush()

    if open_browser:
        def _open():
            time.sleep(0.4)
            try:
                webbrowser.open(url)
            except Exception:
                pass
        t = threading.Thread(target=_open, daemon=True)
        t.start()

    config = uvicorn.Config(app=app, host=host, port=port, log_level=log_level)
    server = uvicorn.Server(config=config)
    try:
        server.run()
        return 0
    except (KeyboardInterrupt, SystemExit):
        sys.stdout.write("\nServidor finalizado.\n")
        return 0


if __name__ == "__main__":
    run_server()
