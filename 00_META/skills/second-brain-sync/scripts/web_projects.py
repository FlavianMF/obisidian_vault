from __future__ import annotations

import datetime as dt
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field
from starlette.templating import Jinja2Templates

import commands
import projects
import projects_state

router = APIRouter()

TEMPLATES_DIR = Path(__file__).resolve().parent / "web" / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

ALLOWED_PROJECT_KEYS = {
    "prioridade",
    "slug",
    "situacao",
    "fase",
    "proximo_passo",
    "bloqueio",
    "active_agents",
    "tickets_status_0",
    "git_branch",
    "git_dirty",
    "prs_open",
    "tests_status",
    "tests_age",
    "last_session_age",
}

ALLOWED_HEADER_KEYS = {
    "quota",
    "active_implementers",
    "max_implementers",
    "snapshot_age_min",
    "activity_age_min",
    "has_data",
}

ALLOWED_SUGGESTION_KEYS = {
    "id",
    "project",
    "ticket",
    "harness",
    "model",
    "effort",
    "reason",
    "state",
}


def derive_situacao(
    is_paused: bool,
    bloqueio: Optional[str],
    active_agents: int,
    last_session_age_days: Optional[float | int] = None,
) -> str:
    """Deriva a situação do projeto estritamente na ordem definida em D2:
    1. pausado (se está no paused.json)
    2. bloqueado (campo bloqueio preenchido)
    3. trabalhando (agente ativo > 0)
    4. parado (última sessão com mais de 7 dias)
    5. ocioso
    """
    if is_paused:
        return "pausado"
    if bloqueio and str(bloqueio).strip():
        return "bloqueado"
    if active_agents > 0:
        return "trabalhando"
    if last_session_age_days is not None and last_session_age_days > 7:
        return "parado"
    return "ocioso"


def format_age_short(dt_iso: Optional[str], now: Optional[dt.datetime] = None) -> str:
    if not dt_iso:
        return "—"
    try:
        t = dt.datetime.fromisoformat(dt_iso)
    except Exception:
        return "—"
    if now is None:
        now = dt.datetime.now(t.tzinfo) if t.tzinfo else dt.datetime.now()
    delta = (now - t).total_seconds()
    if delta < 0:
        return "0 min"
    if delta < 3600:
        return f"{int(delta // 60)} min"
    if delta < 86400:
        return f"{int(delta // 3600)}h"
    days = int(delta // 86400)
    return f"{days} d"


def get_vault_path(request: Request) -> Path:
    vault = getattr(request.app.state, "vault_path", None)
    if not vault:
        env = os.environ.get("SECOND_BRAIN_VAULT")
        vault = Path(env).resolve() if env else Path(__file__).resolve().parents[3]
    return Path(vault).resolve()


def get_state_dir(request: Request) -> Path:
    state = getattr(request.app.state, "state_dir", None)
    if not state:
        env = os.environ.get("SECOND_BRAIN_STATE_DIR")
        state = Path(env).resolve() if env else Path.home() / ".local" / "state" / "second-brain"
    return Path(state).resolve()


def collect_dashboard_data(vault: Path, state_dir: Path) -> dict[str, Any]:
    snap_file = state_dir / "projects.json"
    if not snap_file.exists():
        return {
            "has_data": False,
            "header": {
                "has_data": False,
                "message": "sem dados",
                "quota": {},
                "active_implementers": 0,
                "max_implementers": 2,
                "snapshot_age_min": None,
                "activity_age_min": None,
            },
            "suggestions": [],
            "projects": [],
        }

    try:
        snap_data = json.loads(snap_file.read_text(encoding="utf-8"))
    except Exception:
        return {
            "has_data": False,
            "header": {
                "has_data": False,
                "message": "sem dados",
                "quota": {},
                "active_implementers": 0,
                "max_implementers": 2,
                "snapshot_age_min": None,
                "activity_age_min": None,
            },
            "suggestions": [],
            "projects": [],
        }

    now = dt.datetime.now()

    # Snapshot age
    snap_age_min = None
    try:
        snap_ts = dt.datetime.fromisoformat(snap_data["ts"])
        snap_age_min = max(0, int((now - snap_ts).total_seconds() // 60))
    except Exception:
        pass

    # Activity data & age
    act_file = state_dir / "activity.json"
    act_data = None
    act_age_min = None
    if act_file.exists():
        try:
            act_data = json.loads(act_file.read_text(encoding="utf-8"))
            act_ts = dt.datetime.fromisoformat(act_data["ts"])
            act_age_min = max(0, int((now - act_ts).total_seconds() // 60))
        except Exception:
            pass

    max_impl = 2
    try:
        manifest = projects.load_manifest(vault)
        max_impl = int(manifest.limits.get("max_implementers", 2))
    except Exception:
        pass

    active_impl = projects_state.active_implementers(state_dir)

    # Quota allowlist
    quota_clean = {}
    for h, q in snap_data.get("quota", {}).items():
        if isinstance(q, dict):
            quota_clean[h] = {
                k: q[k] for k in ("used_5h", "used_7d", "free_pct", "resets_at") if k in q
            }
        else:
            quota_clean[h] = None

    quota_display = {}
    for h, q in quota_clean.items():
        if not q:
            quota_display[h] = "indisponível"
            continue
        txt = f"{q.get('free_pct', 0):.0f}% livre"
        if q.get("used_5h") is not None:
            txt += " (5h)"
        if q.get("used_7d") is not None:
            txt += f" · {100 - q['used_7d']:.0f}% (7d)"
        quota_display[h] = txt

    header = {
        "has_data": True,
        "quota": quota_clean,
        "active_implementers": active_impl,
        "max_implementers": max_impl,
        "snapshot_age_min": snap_age_min,
        "activity_age_min": act_age_min,
        "_quota_display": quota_display,
    }

    # Suggestions allowlist (only pending)
    raw_sug = projects_state.suggest_list(state_dir, state="pending")
    clean_sug = []
    for s in raw_sug:
        entry = {k: s[k] for k in ALLOWED_SUGGESTION_KEYS if k in s}
        clean_sug.append(entry)

    # Projects
    try:
        reg = projects.load_registry(vault)
    except Exception:
        reg = []

    reg_map = {p.slug: p for p in reg}
    snap_projects = {
        p.get("slug"): p for p in snap_data.get("projects", []) if isinstance(p, dict) and p.get("slug")
    }

    all_slugs = set(reg_map.keys()) | set(snap_projects.keys())

    def sort_key(s: str) -> tuple[int, str]:
        p_entry = reg_map.get(s)
        pri = p_entry.prioridade if p_entry else snap_projects.get(s, {}).get("prioridade", "P3")
        pri_order = {"P1": 1, "P2": 2, "P3": 3}.get(pri, 4)
        return (pri_order, s)

    sorted_slugs = sorted(all_slugs, key=sort_key)

    project_rows = []
    for s in sorted_slugs:
        p_entry = reg_map.get(s)
        p_snap = snap_projects.get(s, {})

        prioridade = p_entry.prioridade if p_entry else p_snap.get("prioridade", "P3")
        fase = p_entry.fase if p_entry else p_snap.get("fase", "")
        proximo_passo = p_entry.proximo_passo if p_entry else p_snap.get("proximo_passo", "")
        bloqueio = p_entry.bloqueio if p_entry else p_snap.get("bloqueio", "")
        traycer_task = p_entry.traycer_task if p_entry else p_snap.get("traycer_task", "")

        is_p = projects_state.is_paused(state_dir, s)

        # Count active agents
        act_agents = 0
        if act_data and "tasks" in act_data:
            for t in act_data.get("tasks", []):
                if t.get("working"):
                    if (traycer_task and t.get("traycer_task") == traycer_task) or t.get("project") == s:
                        act_agents += 1

        # Git info
        git_info = p_snap.get("git", {})
        branch = git_info.get("branch") or "—"
        dirty = bool(git_info.get("dirty"))
        commit_date = git_info.get("commit_date")

        last_session_days = None
        if commit_date:
            try:
                c_dt = dt.datetime.fromisoformat(commit_date)
                ref_now = dt.datetime.now(c_dt.tzinfo) if c_dt.tzinfo else dt.datetime.now()
                last_session_days = (ref_now - c_dt).total_seconds() / 86400
            except Exception:
                pass
        last_session_str = format_age_short(commit_date)

        situacao = derive_situacao(is_p, bloqueio, act_agents, last_session_days)

        prs = int(p_snap.get("prs", 0) or 0)
        t_info = p_snap.get("tests")
        t_status = t_info.get("status") if isinstance(t_info, dict) else "—"
        t_age = format_age_short(p_snap.get("updated_at")) if t_info else "—"

        tickets_0 = int(p_snap.get("tickets", {}).get("0", 0))

        dirty_str = "sujo" if dirty else "0 sujos"
        git_summary = f"{branch} · {dirty_str} · PR {prs}"
        tests_summary = f"{t_status} · {t_age}" if t_status != "—" else "—"

        # Explicit allowlist enforcement: ONLY ALLOWED_PROJECT_KEYS
        row = {
            "prioridade": prioridade,
            "slug": s,
            "situacao": situacao,
            "fase": fase,
            "proximo_passo": proximo_passo,
            "bloqueio": bloqueio,
            "active_agents": act_agents,
            "tickets_status_0": tickets_0,
            "git_branch": branch,
            "git_dirty": dirty,
            "prs_open": prs,
            "tests_status": t_status,
            "tests_age": t_age,
            "last_session_age": last_session_str,
            # Display helpers for HTML
            "_git_summary": git_summary,
            "_tests_summary": tests_summary,
        }
        project_rows.append(row)

    return {
        "has_data": len(project_rows) > 0,
        "header": header,
        "suggestions": clean_sug,
        "projects": project_rows,
    }


@router.get("/api/projects")
def api_projects(request: Request) -> JSONResponse:
    vault = get_vault_path(request)
    state_dir = get_state_dir(request)
    data = collect_dashboard_data(vault, state_dir)

    # Filter projects to strip internal template display keys
    filtered_projects = []
    for p in data["projects"]:
        filtered_projects.append({k: p[k] for k in ALLOWED_PROJECT_KEYS if k in p})

    resp = {
        "has_data": data["has_data"],
        "header": {k: data["header"][k] for k in ALLOWED_HEADER_KEYS if k in data["header"]},
        "suggestions": data["suggestions"],
        "projects": filtered_projects,
    }
    return JSONResponse(content=resp)


def notify_secretary_approved(vault: Path, suggestion_id: str) -> None:
    try:
        manifest = projects.load_manifest(vault)
        sec = manifest.secretario or manifest.raw.get("secretary", {})
        sec_agent_id = sec.get("agent_id")
        if sec_agent_id:
            traycer_bin = shutil.which("traycer") or "/home/flv/.traycer/cli/bin/traycer"
            subprocess.run(
                [traycer_bin, "agent", "send", "--to", str(sec_agent_id), "--message", f"aprovado {suggestion_id}"],
                capture_output=True,
                timeout=5,
            )
    except Exception:
        pass


class CommandRequest(BaseModel):
    text: str = Field(max_length=500)


@router.post("/api/command")
def api_command(req: CommandRequest, request: Request) -> JSONResponse:
    """The dashboard buttons and voice clients send the same text commands as `sb projects cmd`."""
    vault = get_vault_path(request)
    state_dir = get_state_dir(request)
    parsed = commands.parse(req.text, vault=vault)
    if isinstance(parsed, commands.ParseError):
        return JSONResponse(status_code=400, content={"ok": False, "message": parsed.message})
    with request.app.state.lock:  # pausing, prioritising and approving write state and the vault like /api/decide
        result = commands.execute(parsed, vault, state_dir)
    if result.ok and getattr(parsed, "action", None) == "suggest_decide" and getattr(parsed, "decision", None) == "approve":
        notify_secretary_approved(vault, parsed.id)
    return JSONResponse(status_code=200 if result.ok else 400, content={"ok": result.ok, "message": result.message})


@router.get("/projects", response_class=HTMLResponse)
def get_projects_html(request: Request) -> HTMLResponse:
    vault = get_vault_path(request)
    state_dir = get_state_dir(request)
    data = collect_dashboard_data(vault, state_dir)
    ctx = {
        "request": request,
        "has_data": data["has_data"],
        "header": data["header"],
        "suggestions": data["suggestions"],
        "projects": data["projects"],
    }
    return templates.TemplateResponse(request, "projects.html", ctx)
