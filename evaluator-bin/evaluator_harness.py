"""evaluator-bin/evaluator_harness.py
Adversarial evaluator suite and mutation testing harness for Vault Candidate Review Web.
"""
from __future__ import annotations

import ast
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT / "00_META" / "skills" / "second-brain-sync" / "scripts"
WEB_SERVICE_PATH = SCRIPTS_DIR / "web_service.py"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def check_i1_exclusive_vault_sync(web_service_path: Path = WEB_SERVICE_PATH) -> tuple[bool, str]:
    """Inspects web_service.py to ensure zero direct writes to vault .md files."""
    if not web_service_path.exists():
        return False, f"File {web_service_path} does not exist"

    content = web_service_path.read_text(encoding="utf-8")
    tree = ast.parse(content, filename=str(web_service_path))

    violations = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                if node.func.attr in ("write_text", "write_bytes"):
                    violations.append(f"Line {node.lineno}: direct '{node.func.attr}' called")
            elif isinstance(node.func, ast.Name) and node.func.id == "open":
                violations.append(f"Line {node.lineno}: direct 'open()' called")

    if violations:
        return False, f"I1 violation: direct write operations found:\n" + "\n".join(violations)

    return True, "I1 passed: No direct write operations outside authorized handlers."


def check_i3_zero_build_step(root: Path = ROOT) -> tuple[bool, str]:
    """Verifies that no node_modules, package.json, or frontend build artifacts exist."""
    forbidden = ["package.json", "package-lock.json", "node_modules", "yarn.lock", "pnpm-lock.yaml", "webpack.config.js"]
    found = []
    for item in forbidden:
        if (root / item).exists():
            found.append(item)
    if found:
        return False, f"I3 violation: found build artifacts or npm config: {found}"
    return True, "I3 passed: zero build step."


MUTATIONS: Dict[str, Tuple[str, str, str]] = {
    "MUT_SECRET_BYPASS": (
        "Bypass secret scanning validation in save and dry_run",
        "findings = secret_scan.scan_text(text)",
        "findings = []",
    ),
    "MUT_NEGATIVE_SECTION_BYPASS": (
        "Bypass mandatory negative section check for trap/pattern",
        "if cand.kind in SECTION_TYPES and not NEGATIVE_SECTION.search(body_text):",
        "if False:",
    ),
    "MUT_TITLE_COLLISION_BYPASS": (
        "Bypass 409 Conflict title collision detection",
        "if (v_path / target_note).exists() or vault_sync.in_head(v_path, target_note):",
        "if False:",
    ),
    "MUT_HOST_ORIGIN_GUARD_BYPASS": (
        "Bypass DNS rebinding and CSRF origin guard middleware",
        "if bad_host or bad_origin:",
        "if False:",
    ),
    "MUT_FILTER_BYPASS": (
        "Bypass project and kind filtering in candidate_context",
        "queue = review.pending(s_dir, project=project, kind=kind, source=source)",
        "queue = review.pending(s_dir)",
    ),
    "MUT_UNDO_RESTORE_BYPASS": (
        "Bypass restoring candidate back to queue during undo",
        "remove_decision_from_log(s_dir, cand_id)",
        "# remove_decision_from_log(s_dir, cand_id) bypassed",
    ),
}


class MutationTestingHarness:
    """Executes mutation testing against web_service.py to assess test suite strength."""

    def __init__(self, target_file: Path = WEB_SERVICE_PATH):
        self.target_file = target_file
        self.original_code = target_file.read_text(encoding="utf-8")

    def run_mutation(self, mutation_id: str, desc: str, find_str: str, replace_str: str) -> bool:
        """Applies a mutation, runs test suite, reverts, and returns True if mutation was killed."""
        if find_str not in self.original_code:
            raise ValueError(f"Pattern for {mutation_id} not found in {self.target_file}")

        mutated_code = self.original_code.replace(find_str, replace_str, 1)
        try:
            self.target_file.write_text(mutated_code, encoding="utf-8")
            # Run targeted test files via pytest
            res = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "-q",
                    str(SCRIPTS_DIR / "test_web_service.py"),
                    str(SCRIPTS_DIR / "test_web_ui.py"),
                    str(SCRIPTS_DIR / "test_web_editor.py"),
                ],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
            )
            # If tests failed, the mutation was caught (killed)
            killed = res.returncode != 0
            return killed
        finally:
            self.target_file.write_text(self.original_code, encoding="utf-8")

    def run_all(self) -> Dict[str, bool]:
        """Runs all mutations and returns {mutation_id: killed}."""
        results = {}
        for mid, (desc, f_str, r_str) in MUTATIONS.items():
            killed = self.run_mutation(mid, desc, f_str, r_str)
            results[mid] = killed
        return results


def run_evaluator_audit() -> bool:
    """Runs the full Evaluator assessment including Invariants and Mutation Testing."""
    print("=== EVALUATOR AUDIT FOR CANDIDATE REVIEW WEB ===")

    # 1. Invariants
    i1_ok, i1_msg = check_i1_exclusive_vault_sync()
    print(f"[{'PASS' if i1_ok else 'FAIL'}] {i1_msg}")

    i3_ok, i3_msg = check_i3_zero_build_step()
    print(f"[{'PASS' if i3_ok else 'FAIL'}] {i3_msg}")

    if not (i1_ok and i3_ok):
        print("Invariants check failed!")
        return False

    # 2. Mutation Testing
    print("\nRunning Mutation Testing Suite...")
    harness = MutationTestingHarness()
    results = harness.run_all()

    total = len(results)
    killed = sum(1 for k, v in results.items() if v)
    score = (killed / total) * 100

    for mid, is_killed in results.items():
        status = "KILLED" if is_killed else "SURVIVED"
        desc = MUTATIONS[mid][0]
        print(f" - {mid:28} [{status}]: {desc}")

    print(f"\nMutation Score: {score:.1f}% ({killed}/{total} killed)")
    if killed < total:
        print("Evaluation FAILED: Not all mutations were caught by tests.")
        return False

    print("Evaluation PASSED: 100% of adversarial mutations caught.")
    return True


if __name__ == "__main__":
    success = run_evaluator_audit()
    sys.exit(0 if success else 1)
