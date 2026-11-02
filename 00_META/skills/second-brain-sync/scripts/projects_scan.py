from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import projects
import quota
from lib import frontmatter


def collect_git(checkout_path: Path) -> dict[str, Any]:
    if not checkout_path.exists() or not checkout_path.is_dir():
        return {"branch": None, "dirty": None, "ahead": None, "behind": None, "commit_date": None, "error": "checkout not found"}
    try:
        branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=checkout_path, capture_output=True, text=True, timeout=5).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain"], cwd=checkout_path, capture_output=True, text=True, timeout=5).stdout.strip() != ""
        commit_date = subprocess.run(["git", "log", "-1", "--format=%cI"], cwd=checkout_path, capture_output=True, text=True, timeout=5).stdout.strip()
        ahead_behind = subprocess.run(["git", "rev-list", "--left-right", "--count", "HEAD...@{upstream}"], cwd=checkout_path, capture_output=True, text=True, timeout=5).stdout.strip()
        ahead, behind = map(int, ahead_behind.split()) if ahead_behind else (0, 0)
    except subprocess.SubprocessError as err:
        return {"branch": None, "dirty": None, "ahead": None, "behind": None, "commit_date": None, "error": str(err)}
    return {"branch": branch, "dirty": dirty, "ahead": ahead, "behind": behind, "commit_date": commit_date}


def collect_gh_prs(repo_or_checkout: str) -> int | None:
    try:
        output = subprocess.run(["gh", "pr", "list", "--json", "number"], capture_output=True, text=True, timeout=15).stdout
        return len(json.loads(output))
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def collect_traycer_tickets(epic_slug: str) -> dict[str, int]:
    if not epic_slug:
        return {}
    traycer_root = Path.home() / ".traycer/epics" / epic_slug / "artifacts"
    if not traycer_root.exists():
        return {}
    counts = {"0": 0, "1": 0, "2": 0}
    for p in traycer_root.rglob("index.md"):
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
            fm_lines, _ = frontmatter.split_frontmatter(text)
            if fm_lines:
                d, _ = frontmatter.parse_frontmatter(fm_lines)
                if d.get("kind") == "ticket" and "status" in d:
                    st = str(d["status"]).strip()
                    if st in counts:
                        counts[st] += 1
        except Exception:
            pass
    return counts


def collect_quota() -> dict[str, Any]:
    res = {}
    for h in ("claude", "antigravity"):
        try:
            proc = subprocess.run(
                ["traycer", "--json", "agent", "profile-rate-limits", h, "--profile", "ambient"],
                capture_output=True, text=True, timeout=10, check=False
            )
            if proc.returncode == 0:
                q = quota.parse(proc.stdout, h)
                res[h] = {"used_5h": q.used_5h, "used_7d": q.used_7d, "free_pct": q.free_pct, "resets_at": q.resets_at}
            else:
                res[h] = None
        except Exception:
            res[h] = None
    return res


def scan(vault: Path, state_dir: Path, project_slug: str | None = None, run_tests: bool = False) -> int:
    state_dir.mkdir(parents=True, exist_ok=True)
    snap_file = state_dir / "projects.json"
    existing_data = {"ts": "", "quota": {}, "projects": []}
    if snap_file.exists():
        try:
            existing_data = json.loads(snap_file.read_text(encoding="utf-8"))
        except Exception:
            pass

    registry = projects.load_registry(vault)
    now_iso = dt.datetime.now().isoformat()

    # If project_slug specified, only update that project
    existing_projects_map = {p.get("slug"): p for p in existing_data.get("projects", []) if isinstance(p, dict)}

    quota_data = existing_data.get("quota", {}) if project_slug else collect_quota()

    target_projects = [p for p in registry if p.slug == project_slug] if project_slug else registry

    for p in target_projects:
        checkout_dir = Path(os.path.expanduser(p.checkout))
        git_info = collect_git(checkout_dir)
        prs = collect_gh_prs(p.repo)
        tickets = collect_traycer_tickets(p.traycer_task)

        test_result = None
        if run_tests and p.test and checkout_dir.is_dir():
            t0 = dt.datetime.now()
            try:
                t_proc = subprocess.run(p.test, shell=True, cwd=checkout_dir, capture_output=True, timeout=600, check=False)
                dur = (dt.datetime.now() - t0).total_seconds()
                test_result = {"status": "ok" if t_proc.returncode == 0 else "falha", "duration_sec": dur}
            except subprocess.TimeoutExpired:
                test_result = {"status": "falha", "error": "timeout"}
            except Exception as exc:
                test_result = {"status": "falha", "error": str(exc)}

        entry_data = {
            "slug": p.slug,
            "title": p.title,
            "status": p.status,
            "fase": p.fase,
            "prioridade": p.prioridade,
            "proximo_passo": p.proximo_passo,
            "bloqueio": p.bloqueio,
            "traycer_task": p.traycer_task,
            "git": git_info,
            "prs": prs,
            "tickets": tickets,
            "tests": test_result,
            "updated_at": now_iso,
        }
        existing_projects_map[p.slug] = entry_data

    final_snapshot = {
        "ts": now_iso,
        "quota": quota_data,
        "projects": list(existing_projects_map.values()),
    }

    # Atomic write mode 0600
    fd, tmp_path = tempfile.mkstemp(dir=str(state_dir), prefix="projects_snap_")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(final_snapshot, f, ensure_ascii=False, indent=2)
    os.chmod(tmp_path, 0o600)
    os.replace(tmp_path, str(snap_file))
    return 0
