from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, NamedTuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import frontmatter, secret_scan

class MissingDependency(Exception):
    pass

class Issue(NamedTuple):
    check: str
    severity: str
    path: str
    detail: str

ERROR = "error"
WARN = "warn"

ALLOWLIST_PROJECT_KEYS = {
    "slug", "note", "repo", "checkout", "branch", "setup",
    "test", "harness", "model", "effort", "env"
}

BLOCKED_TAGS = {"private", "privado", "pessoal", "personal", "sensitive", "confidential"}

ENV_VAR_RE = re.compile(r"^[A-Z_][A-Z0-9_]*$")

EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_RE = re.compile(r"(?:\+?55\s?)?(?:\(?\d{2}\)?[\s-]?)?\d{4,5}[-\s]?\d{4}")
CPF_RE = re.compile(r"\b(?:\d{3}\.\d{3}\.\d{3}-\d{2}|\d{11})\b")
CNPJ_RE = re.compile(r"\b(?:\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}|\d{14})\b")

PROJECT_PRIORITIES = {"P1", "P2", "P3"}

@dataclass
class Manifest:
    version: int
    limits: dict[str, Any]
    secretario: dict[str, Any]
    web: dict[str, Any]
    projects: list[dict[str, Any]]
    raw: dict[str, Any]

@dataclass
class Project:
    slug: str
    note: str
    repo: str
    checkout: str
    branch: str
    setup: list[str]
    test: str
    harness: str
    model: str
    effort: str
    env: list[str]
    title: str = ""
    status: str = "active"
    fase: str = ""
    prioridade: str = ""
    proximo_passo: str = ""
    bloqueio: str = ""
    traycer_task: str = ""
    raw_frontmatter: dict[str, Any] = field(default_factory=dict)

def load_manifest(vault: Path) -> Manifest:
    try:
        import yaml
    except ImportError as exc:
        raise MissingDependency("PyYAML is required to load projects manifest") from exc
    manifest_path = vault / "00_META/projects/manifest.yaml"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    raw = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    return Manifest(
        version=raw.get("version", 1),
        limits=raw.get("limits", {}),
        secretario=raw.get("secretario", {}),
        web=raw.get("web", {}),
        projects=raw.get("projects", []),
        raw=raw,
    )

def load_registry(vault: Path) -> list[Project]:
    manifest = load_manifest(vault)
    projects_list = []
    for entry in manifest.projects:
        note_rel = entry.get("note", "")
        note_path = vault / note_rel
        fm_data = {}
        if note_path.exists():
            text = note_path.read_text(encoding="utf-8", errors="replace")
            fm_lines, _ = frontmatter.split_frontmatter(text)
            if fm_lines:
                fm_data, _ = frontmatter.parse_frontmatter(fm_lines)
        proj = Project(
            slug=entry.get("slug", ""),
            note=entry.get("note", ""),
            repo=entry.get("repo", ""),
            checkout=entry.get("checkout", ""),
            branch=entry.get("branch", ""),
            setup=entry.get("setup", []),
            test=entry.get("test", ""),
            harness=entry.get("harness", ""),
            model=entry.get("model", ""),
            effort=entry.get("effort", ""),
            env=entry.get("env", []),
            title=fm_data.get("title", ""),
            status=fm_data.get("status", "active"),
            fase=fm_data.get("fase", ""),
            prioridade=fm_data.get("prioridade", ""),
            proximo_passo=fm_data.get("proximo_passo", ""),
            bloqueio=fm_data.get("bloqueio", ""),
            traycer_task=fm_data.get("traycer_task", ""),
            raw_frontmatter=fm_data,
        )
        projects_list.append(proj)
    return projects_list

def validate(vault: Path) -> list[Issue]:
    issues = []
    manifest_rel = "00_META/projects/manifest.yaml"
    manifest_path = vault / manifest_rel
    if not manifest_path.exists():
        issues.append(Issue("manifest", ERROR, manifest_rel, "manifest file missing"))
    manifest_text = manifest_path.read_text(encoding="utf-8", errors="replace")
    for f in secret_scan.scan_text(manifest_text):
        issues.append(Issue("secret", ERROR, manifest_rel, f"{f.label} (line {f.line})"))
    
    try:
        manifest = load_manifest(vault)
    except Exception as exc:
        issues.append(Issue("manifest", ERROR, manifest_rel, f"manifest load error: {exc}"))
        return issues

    denylist_rel = "00_META/jev-denylist.md"
    denylist_path = vault / denylist_rel
    denylist_rules = []
    if not denylist_path.exists():
        issues.append(Issue("denylist", WARN, denylist_rel, "denylist file missing"))
    else:
        d_text = denylist_path.read_text(encoding="utf-8", errors="replace")
        for line in d_text.splitlines():
            m = re.match(r"^\s*-\s*(folder|tag|repo|term):\s*(.+?)\s*$", line)
            if m:
                denylist_rules.append((m.group(1), m.group(2).strip()))
        if not denylist_rules:
            issues.append(Issue("denylist", WARN, denylist_rel, "denylist has no rules"))

    for p_entry in manifest.projects:
        slug = p_entry.get("slug", "unknown")
        for k in p_entry:
            if k not in ALLOWLIST_PROJECT_KEYS:
                issues.append(Issue("manifest", ERROR, manifest_rel, f"project `{slug}` has unknown key `{k}`"))
        for env_name in p_entry.get("env", []):
            if not ENV_VAR_RE.match(str(env_name)):
                issues.append(Issue("env", ERROR, manifest_rel, f"invalid env variable name: `{env_name}`"))

    for p_entry in manifest.projects:
        slug = p_entry.get("slug", "")
        note_rel = p_entry.get("note", "")
        note_path = vault / note_rel
        if not note_path.exists():
            issues.append(Issue("note", ERROR, note_rel, f"project note `{note_rel}` does not exist"))
            continue
        note_text = note_path.read_text(encoding="utf-8", errors="replace")
        for f in secret_scan.scan_text(note_text):
            issues.append(Issue("secret", ERROR, note_rel, f"{f.label} (line {f.line})"))
        
        fm_lines, body = frontmatter.split_frontmatter(note_text)
        if fm_lines is None:
            issues.append(Issue("frontmatter", ERROR, note_rel, "no frontmatter block"))
            continue
        data, _ = frontmatter.parse_frontmatter(fm_lines)
        
        status = data.get("status", "active")
        if status != "active":
            issues.append(Issue("status", WARN, note_rel, f"note has status `{status}`, not active"))
        
        prioridade = data.get("prioridade")
        if prioridade and prioridade not in PROJECT_PRIORITIES:
            issues.append(Issue("frontmatter", ERROR, note_rel, f"invalid prioridade: `{prioridade}`"))
        
        for field_name in ("proximo_passo", "bloqueio"):
            val = data.get(field_name)
            if val:
                sval = str(val)
                if len(sval) > 200 or "\n" in sval:
                    issues.append(Issue("frontmatter", ERROR, note_rel, f"`{field_name}` exceeds 200 characters or contains newlines"))
        
        for field_name in ("fase", "proximo_passo", "bloqueio"):
            val = data.get(field_name)
            if val:
                sval = str(val)
                if EMAIL_RE.search(sval):
                    issues.append(Issue("pii", ERROR, note_rel, f"`{field_name}` contains email (PII)"))
                if PHONE_RE.search(sval):
                    issues.append(Issue("pii", ERROR, note_rel, f"`{field_name}` contains phone number (PII)"))
                if CPF_RE.search(sval):
                    issues.append(Issue("pii", ERROR, note_rel, f"`{field_name}` contains CPF (PII)"))
                if CNPJ_RE.search(sval):
                    issues.append(Issue("pii", ERROR, note_rel, f"`{field_name}` contains CNPJ (PII)"))
        
        note_tags = [str(t).lower() for t in data.get("tags", [])]
        for tag in note_tags:
            if tag in BLOCKED_TAGS:
                issues.append(Issue("denylist", ERROR, note_rel, f"note has blocked tag `{tag}`"))
        
        searchable_text = f"{slug} {p_entry.get('checkout', '')} {note_rel} {data.get('title', '')} {data.get('proximo_passo', '')} {data.get('bloqueio', '')} {' '.join(note_tags)}"
        for kind, rule_val in denylist_rules:
            r_val = rule_val.lower()
            if kind == "term":
                if re.search(r"\b" + re.escape(r_val) + r"\b", searchable_text, re.IGNORECASE):
                    issues.append(Issue("denylist", ERROR, note_rel, f"matches denylist term rule `{kind}: {rule_val}`"))
            elif kind == "repo":
                repo_str = str(p_entry.get("repo", "")).lower()
                if r_val in repo_str:
                    issues.append(Issue("denylist", ERROR, note_rel, f"matches denylist repo rule `{kind}: {rule_val}`"))
            elif kind == "folder":
                if note_rel.startswith(rule_val):
                    issues.append(Issue("denylist", ERROR, note_rel, f"matches denylist folder rule `{kind}: {rule_val}`"))

    return issues


import datetime as dt
import subprocess
import json

def sync_vault(vault: Path, notes: list[str], verdict: str, message: str) -> bool:
    cmd = [
        sys.executable,
        str(Path(__file__).resolve().parent / "vault_sync.py"),
        "--vault-path", str(vault),
        "--project-name", "projects-cli",
        "--message", message,
        "--verdict", verdict,
    ]
    for n in notes:
        cmd += ["--note", n]
    res = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if res.returncode != 0:
        sys.stderr.write(f"vault_sync failed: {res.stderr or res.stdout}\n")
        return False
    return True

def cli_list(vault: Path, as_json: bool = False) -> int:
    try:
        registry = load_registry(vault)
    except MissingDependency as exc:
        sys.stderr.write(f"sb projects: {exc}\n")
        return 2
    except Exception as exc:
        sys.stderr.write(f"sb projects: error loading registry: {exc}\n")
        return 1

    if as_json:
        items = [
            {
                "slug": p.slug,
                "title": p.title,
                "status": p.status,
                "fase": p.fase,
                "prioridade": p.prioridade,
                "proximo_passo": p.proximo_passo,
                "bloqueio": p.bloqueio,
                "repo": p.repo,
                "checkout": p.checkout,
                "branch": p.branch,
                "harness": p.harness,
                "model": p.model,
                "effort": p.effort,
                "traycer_task": p.traycer_task,
            }
            for p in registry
        ]
        sys.stdout.write(json.dumps(items, ensure_ascii=False, indent=2) + "\n")
        return 0

    header = f"{'SLUG':<18} {'STATUS':<10} {'PRI':<4} {'FASE':<10} {'PRÓXIMO PASSO':<30} {'BLOQUEIO':<20}"
    sys.stdout.write(header + "\n")
    sys.stdout.write("-" * len(header) + "\n")
    for p in registry:
        sys.stdout.write(f"{p.slug:<18} {p.status:<10} {p.prioridade:<4} {p.fase:<10} {p.proximo_passo[:28]:<30} {p.bloqueio[:18]:<20}\n")
    return 0

def cli_validate(vault: Path) -> int:
    try:
        issues = validate(vault)
    except MissingDependency as exc:
        sys.stderr.write(f"sb projects: {exc}\n")
        return 2
    if not issues:
        sys.stdout.write("projects: ok, no issues\n")
        return 0
    for i in issues:
        sys.stdout.write(f"{i.severity} {i.check} {i.path}: {i.detail}\n")
    return 1 if any(i.severity == ERROR for i in issues) else 0

def cli_add(vault: Path, slug: str, repo: str, checkout: str, branch: str = "master") -> int:
    try:
        import yaml
    except ImportError as exc:
        raise MissingDependency("PyYAML is required for projects add") from exc

    manifest_path = vault / "00_META/projects/manifest.yaml"
    manifest_raw = {}
    if manifest_path.exists():
        manifest_raw = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    projects_list = manifest_raw.setdefault("projects", [])
    if any(p.get("slug") == slug for p in projects_list):
        sys.stderr.write(f"sb projects add: project `{slug}` already exists\n")
        return 1

    note_rel = f"40_Projects/{slug}.md"
    note_path = vault / note_rel
    note_backup = note_path.read_bytes() if note_path.exists() else None
    manifest_backup = manifest_path.read_bytes() if manifest_path.exists() else None

    note_path.parent.mkdir(parents=True, exist_ok=True)
    today = dt.date.today().isoformat()
    note_content = f"""---
title: {slug}
type: project
tags: [project]
created: {today}
status: active
confidence: low
prioridade: P2
fase: spec
proximo_passo: 
bloqueio: 
---

# {slug}
"""
    note_path.write_text(note_content, encoding="utf-8")

    new_entry = {
        "slug": slug,
        "note": note_rel,
        "repo": repo,
        "checkout": checkout,
        "branch": branch,
        "setup": [],
        "test": "",
        "harness": "claude",
        "model": "sonnet",
        "effort": "high",
        "env": [],
    }
    projects_list.append(new_entry)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(yaml.safe_dump(manifest_raw, sort_keys=False), encoding="utf-8")

    issues = validate(vault)
    if any(i.severity == ERROR for i in issues):
        sys.stderr.write("sb projects add: validation failed, aborting write:\n")
        for i in issues:
            if i.severity == ERROR:
                sys.stderr.write(f"  {i.path}: {i.detail}\n")
        if note_backup is None:
            note_path.unlink(missing_ok=True)
        else:
            note_path.write_bytes(note_backup)
        if manifest_backup is None:
            manifest_path.unlink(missing_ok=True)
        else:
            manifest_path.write_bytes(manifest_backup)
        return 1

    ok = sync_vault(vault, [note_rel, "00_META/projects/manifest.yaml"], verdict="save", message=f"add project {slug}")
    return 0 if ok else 1

def cli_archive(vault: Path, slug: str) -> int:
    try:
        import yaml
    except ImportError as exc:
        raise MissingDependency("PyYAML is required for projects archive") from exc

    manifest_path = vault / "00_META/projects/manifest.yaml"
    if not manifest_path.exists():
        sys.stderr.write("sb projects archive: manifest not found\n")
        return 1
    manifest_raw = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    projects_list = manifest_raw.get("projects", [])
    entry = next((p for p in projects_list if p.get("slug") == slug), None)
    if not entry:
        sys.stderr.write(f"sb projects archive: project `{slug}` not found in manifest\n")
        return 1

    note_rel = entry.get("note", f"40_Projects/{slug}.md")
    note_path = vault / note_rel
    if not note_path.exists():
        sys.stderr.write(f"sb projects archive: note `{note_rel}` not found\n")
        return 1

    note_backup = note_path.read_bytes()
    manifest_backup = manifest_path.read_bytes()

    data, order, body = frontmatter.read_note(note_path)
    data["status"] = "archived"
    if "status" not in order:
        order.append("status")
    frontmatter.write_note(note_path, data, order, body)

    manifest_raw["projects"] = [p for p in projects_list if p.get("slug") != slug]
    manifest_path.write_text(yaml.safe_dump(manifest_raw, sort_keys=False), encoding="utf-8")

    issues = validate(vault)
    if any(i.severity == ERROR for i in issues):
        sys.stderr.write("sb projects archive: validation failed, aborting write:\n")
        note_path.write_bytes(note_backup)
        manifest_path.write_bytes(manifest_backup)
        return 1

    ok = sync_vault(vault, [note_rel, "00_META/projects/manifest.yaml"], verdict="absorb", message=f"archive project {slug}")
    return 0 if ok else 1

def cli_update(vault: Path, slug: str, proximo_passo: str | None = None, bloqueio: str | None = None, fase: str | None = None, prioridade: str | None = None) -> int:
    try:
        manifest = load_manifest(vault)
    except Exception as exc:
        sys.stderr.write(f"sb projects update: cannot load manifest: {exc}\n")
        return 1

    entry = next((p for p in manifest.projects if p.get("slug") == slug), None)
    if not entry:
        sys.stderr.write(f"sb projects update: project `{slug}` not found\n")
        return 1

    note_rel = entry.get("note", f"40_Projects/{slug}.md")
    note_path = vault / note_rel
    if not note_path.exists():
        sys.stderr.write(f"sb projects update: note `{note_rel}` not found\n")
        return 1

    note_backup = note_path.read_bytes()
    data, order, body = frontmatter.read_note(note_path)

    if proximo_passo is not None:
        data["proximo_passo"] = proximo_passo
        if "proximo_passo" not in order:
            order.append("proximo_passo")
    if bloqueio is not None:
        data["bloqueio"] = bloqueio
        if "bloqueio" not in order:
            order.append("bloqueio")
    if fase is not None:
        data["fase"] = fase
        if "fase" not in order:
            order.append("fase")
    if prioridade is not None:
        data["prioridade"] = prioridade
        if "prioridade" not in order:
            order.append("prioridade")

    frontmatter.write_note(note_path, data, order, body)

    issues = validate(vault)
    if any(i.severity == ERROR for i in issues):
        sys.stderr.write("sb projects update: validation failed, aborting write:\n")
        for i in issues:
            if i.severity == ERROR:
                sys.stderr.write(f"  {i.path}: {i.detail}\n")
        note_path.write_bytes(note_backup)
        return 1

    ok = sync_vault(vault, [note_rel], verdict="absorb", message=f"update project {slug}")
    if not ok:
        note_path.write_bytes(note_backup)
        return 1
    return 0
