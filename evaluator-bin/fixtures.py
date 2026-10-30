"""evaluator-bin/fixtures.py
Test fixtures and sandbox environment helpers for Evaluator.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

# Ensure scripts dir is on sys.path
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "00_META" / "skills" / "second-brain-sync" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import candidates
import review


class IsolatedSandbox:
    """Creates a temporary, self-contained git vault and state directory."""

    def __init__(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.vault = self.root / "vault"
        self.state = self.root / "state"
        self.remote = self.root / "remote.git"

        # Initialize bare remote
        subprocess.run(["git", "init", "-q", "--bare", "-b", "master", str(self.remote)], check=True)

        # Initialize local vault
        subprocess.run(["git", "init", "-q", "-b", "master", str(self.vault)], check=True)
        subprocess.run(["git", "-C", str(self.vault), "config", "user.email", "evaluator@example.com"], check=True)
        subprocess.run(["git", "-C", str(self.vault), "config", "user.name", "Evaluator"], check=True)
        subprocess.run(["git", "-C", str(self.vault), "remote", "add", "origin", str(self.remote)], check=True)

        # Set up vault folders
        (self.vault / "20_Permanent_Notes").mkdir(parents=True, exist_ok=True)
        (self.vault / "00_META" / "manifests" / "by_type").mkdir(parents=True, exist_ok=True)
        self.state.mkdir(parents=True, exist_ok=True)
        (self.state / "drafts").mkdir(parents=True, exist_ok=True)

        # Create an initial commit
        readme = self.vault / "README.md"
        readme.write_text("# Test Vault\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.vault), "add", "README.md"], check=True)
        subprocess.run(["git", "-C", str(self.vault), "commit", "-q", "-m", "chore: initial commit"], check=True)
        subprocess.run(["git", "-C", str(self.vault), "push", "-q", "origin", "master"], check=True)

    def add_candidate(
        self,
        *,
        kind: str = "trap",
        title: str = "Calibração de Câmera Estéreo",
        summary: str = "Resumo para teste de calibração",
        project: str = "residencia_cariri_projects",
        source: str = "agent",
        body: Optional[str] = None,
        days_left: int = 15,
    ) -> str:
        """Adds a candidate to queue.jsonl and optionally creates draft."""
        cid, _ = candidates.add(
            self.state,
            kind=kind,
            title=title,
            summary=summary,
            project=project,
            source=source,
            body=body or "",
        )
        if days_left != candidates.TTL_DAYS:
            path = candidates.queue_path(self.state)
            with candidates.locked(path):
                lines = candidates.read_lines(path)
                updated = []
                target_ts = (candidates.utcnow() - dt.timedelta(days=candidates.TTL_DAYS - days_left)).isoformat(timespec="seconds")
                for line in lines:
                    try:
                        row = json.loads(line)
                        if row.get("id") == cid:
                            row["ts"] = target_ts
                        updated.append(json.dumps(row, ensure_ascii=False))
                    except ValueError:
                        updated.append(line)
                candidates.replace_file(path, ("\n".join(updated) + "\n").encode("utf-8"))
        return cid

    def add_sample_note(
        self,
        filename: str,
        title: str,
        tags: list[str],
        body: str,
        confidence: str = "medium",
        seen_in: Optional[list[str]] = None,
        verified: Optional[str] = None,
    ) -> Path:
        """Adds an existing permanent note to the vault and commits it."""
        note_path = self.vault / "20_Permanent_Notes" / filename
        seen = seen_in or ["residencia_cariri_projects"]
        ver = verified or "2026-10-15 teste manual"
        tags_str = ", ".join(tags)
        seen_str = ", ".join(seen)
        content = (
            f"---\n"
            f"title: \"{title}\"\n"
            f"tags: [{tags_str}]\n"
            f"provenance: manual\n"
            f"confidence: {confidence}\n"
            f"seen_in: [{seen_str}]\n"
            f"verified: \"{ver}\"\n"
            f"---\n\n"
            f"# {title}\n\n"
            f"{body}\n"
        )
        note_path.write_text(content, encoding="utf-8")
        subprocess.run(["git", "-C", str(self.vault), "add", str(note_path)], check=True)
        subprocess.run(["git", "-C", str(self.vault), "commit", "-q", "-m", f"docs: add sample note {filename}"], check=True)
        subprocess.run(["git", "-C", str(self.vault), "push", "-q", "origin", "master"], check=True)
        return note_path

    def cleanup(self):
        self._tmp.cleanup()

    def __enter__(self) -> IsolatedSandbox:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
