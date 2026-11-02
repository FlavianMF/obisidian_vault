from __future__ import annotations

import datetime as dt
import json
import os
import secrets
import tempfile
from pathlib import Path
from typing import Any

import projects


def _write_atomic_json(target_path: Path, data: Any) -> None:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(target_path.parent), prefix="tmp_state_")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.chmod(tmp, 0o600)
    os.replace(tmp, str(target_path))


def activity_set(state_dir: Path, tasks: list[dict[str, Any]]) -> int:
    state_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "ts": dt.datetime.now().isoformat(),
        "tasks": tasks,
    }
    _write_atomic_json(state_dir / "activity.json", data)
    return 0


def active_implementers(state_dir: Path) -> int:
    act_file = state_dir / "activity.json"
    if not act_file.exists():
        return 0
    try:
        data = json.loads(act_file.read_text(encoding="utf-8"))
        count = 0
        for t in data.get("tasks", []):
            role = str(t.get("role", "")).lower()
            if "impl" in role and t.get("working"):
                count += 1
        return count
    except Exception:
        return 0


def is_paused(state_dir: Path, slug: str) -> bool:
    paused_file = state_dir / "paused.json"
    if not paused_file.exists():
        return False
    try:
        data = json.loads(paused_file.read_text(encoding="utf-8"))
        return slug in data.get("paused", [])
    except Exception:
        return False


def pause(state_dir: Path, slug: str) -> int:
    paused_file = state_dir / "paused.json"
    data = {"paused": []}
    if paused_file.exists():
        try:
            data = json.loads(paused_file.read_text(encoding="utf-8"))
        except Exception:
            pass
    paused_list = set(data.get("paused", []))
    paused_list.add(slug)
    _write_atomic_json(paused_file, {"paused": sorted(paused_list)})
    return 0


def resume(state_dir: Path, slug: str) -> int:
    paused_file = state_dir / "paused.json"
    if not paused_file.exists():
        return 0
    try:
        data = json.loads(paused_file.read_text(encoding="utf-8"))
        paused_list = set(data.get("paused", []))
        paused_list.discard(slug)
        _write_atomic_json(paused_file, {"paused": sorted(paused_list)})
    except Exception:
        pass
    return 0


def suggest_add(state_dir: Path, project: str, ticket: str, harness: str, model: str, effort: str, reason: str) -> str:
    state_dir.mkdir(parents=True, exist_ok=True)
    sug_file = state_dir / "suggestions.jsonl"
    s_id = f"s-{secrets.token_hex(2)}"
    now = dt.datetime.now().isoformat()
    entry = {
        "id": s_id,
        "project": project,
        "ticket": ticket,
        "harness": harness,
        "model": model,
        "effort": effort,
        "reason": reason,
        "state": "pending",
        "created_at": now,
        "updated_at": now,
        "agent_id": None,
    }
    mode = 0o600
    with open(sug_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    os.chmod(sug_file, mode)
    return s_id


def suggest_list(state_dir: Path, state: str | None = None) -> list[dict[str, Any]]:
    sug_file = state_dir / "suggestions.jsonl"
    if not sug_file.exists():
        return []
    items = []
    for line in sug_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
            if state is None or d.get("state") == state:
                items.append(d)
        except Exception:
            pass
    return items


def _update_suggestion(state_dir: Path, s_id: str, updates: dict[str, Any]) -> int:
    sug_file = state_dir / "suggestions.jsonl"
    if not sug_file.exists():
        return 1
    lines = sug_file.read_text(encoding="utf-8").splitlines()
    found = False
    new_lines = []
    for line in lines:
        if not line.strip():
            continue
        try:
            d = json.loads(line)
            if d.get("id") == s_id:
                d.update(updates)
                d["updated_at"] = dt.datetime.now().isoformat()
                found = True
            new_lines.append(json.dumps(d, ensure_ascii=False))
        except Exception:
            new_lines.append(line)
    if not found:
        return 1
    fd, tmp = tempfile.mkstemp(dir=str(state_dir), prefix="tmp_sug_")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines) + "\n")
    os.chmod(tmp, 0o600)
    os.replace(tmp, str(sug_file))
    return 0


def suggest_decide(state_dir: Path, s_id: str, decision: str) -> int:
    if decision not in ("approve", "reject"):
        return 1
    new_state = "approved" if decision == "approve" else "rejected"
    return _update_suggestion(state_dir, s_id, {"state": new_state})


def suggest_done(state_dir: Path, s_id: str, agent_id: str) -> int:
    return _update_suggestion(state_dir, s_id, {"state": "done", "agent_id": agent_id})


def gate(vault: Path, state_dir: Path, project_slug: str, harness: str) -> tuple[int, str]:
    if is_paused(state_dir, project_slug):
        return 1, f"Project {project_slug} is paused"

    try:
        manifest = projects.load_manifest(vault)
    except Exception as exc:
        return 1, f"Cannot load manifest: {exc}"

    limits = manifest.limits
    min_free_pct = float(limits.get("quota_min_free_pct", 30))
    max_impl = int(limits.get("max_implementers", 2))
    max_act_age_min = float(limits.get("activity_max_age_min", 30))

    snap_file = state_dir / "projects.json"
    if not snap_file.exists():
        return 1, "Snapshot projects.json not found"
    try:
        snap_data = json.loads(snap_file.read_text(encoding="utf-8"))
        snap_ts = dt.datetime.fromisoformat(snap_data["ts"])
    except Exception as exc:
        return 1, f"Invalid snapshot: {exc}"

    now = dt.datetime.now()
    if (now - snap_ts).total_seconds() > 30 * 60:
        return 1, "Snapshot is older than 30 minutes"

    quota_data = snap_data.get("quota", {}).get(harness)
    if not quota_data:
        return 1, f"No quota data for harness {harness}"
    free_pct = float(quota_data.get("free_pct", 0.0))
    if free_pct < min_free_pct:
        return 1, f"Quota free ({free_pct:.1f}%) is below minimum ({min_free_pct}%)"

    act_file = state_dir / "activity.json"
    if not act_file.exists():
        return 1, "Activity file activity.json not found"
    try:
        act_data = json.loads(act_file.read_text(encoding="utf-8"))
        act_ts = dt.datetime.fromisoformat(act_data["ts"])
    except Exception as exc:
        return 1, f"Invalid activity data: {exc}"

    if (now - act_ts).total_seconds() > max_act_age_min * 60:
        return 1, f"Activity data is older than {max_act_age_min} minutes"

    active_impl = active_implementers(state_dir)
    if active_impl >= max_impl:
        return 1, f"Active implementers ({active_impl}) reached limit ({max_impl})"

    return 0, ""
