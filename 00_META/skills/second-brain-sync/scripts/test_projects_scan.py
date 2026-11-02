import unittest
import json
import os
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from test_projects import make_vault
import projects_scan

class ProjectsScanTest(unittest.TestCase):
    def test_scan_git_and_snapshot_mode(self):
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            vault = make_vault(tmp_path / "vault")
            state_dir = tmp_path / "state"
            state_dir.mkdir(parents=True, exist_ok=True)

            checkout = tmp_path / "checkout"
            checkout.mkdir(parents=True, exist_ok=True)
            subprocess.run(["git", "init", "-b", "master"], cwd=checkout, capture_output=True, check=True)
            subprocess.run(["git", "config", "user.name", "Tester"], cwd=checkout, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=checkout, check=True)
            (checkout / "README.md").write_text("# Test\n")
            subprocess.run(["git", "add", "."], cwd=checkout, check=True)
            subprocess.run(["git", "commit", "-m", "init"], cwd=checkout, check=True)

            # Update manifest to point checkout to our test checkout
            manifest_file = vault / "00_META/projects/manifest.yaml"
            text = manifest_file.read_text(encoding="utf-8")
            text = text.replace("~/projetos_apps/outlet_promo", str(checkout))
            manifest_file.write_text(text, encoding="utf-8")

            with patch("projects_scan.collect_quota", return_value={"claude": None, "antigravity": None}):
                with patch("projects_scan.collect_gh_prs", return_value=0):
                    with patch("projects_scan.collect_traycer_tickets", return_value={"0": 1, "1": 0, "2": 0}):
                        res = projects_scan.scan(vault, state_dir)
                        self.assertEqual(res, 0)

            snap_file = state_dir / "projects.json"
            self.assertTrue(snap_file.exists())
            mode = snap_file.stat().st_mode & 0o777
            self.assertEqual(mode, 0o600)

            data = json.loads(snap_file.read_text(encoding="utf-8"))
            self.assertIn("ts", data)
            self.assertIn("projects", data)
            proj = data["projects"][0]
            self.assertEqual(proj["slug"], "outlet_promo")
            self.assertEqual(proj["git"]["branch"], "master")
            self.assertFalse(proj["git"]["dirty"])
            self.assertIsNotNone(proj["git"]["commit_date"])

    def test_scan_isolated_failure_does_not_crash(self):
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            vault = make_vault(tmp_path / "vault")
            state_dir = tmp_path / "state"

            # Point to non-existent checkout
            manifest_file = vault / "00_META/projects/manifest.yaml"
            text = manifest_file.read_text(encoding="utf-8")
            text = text.replace("~/projetos_apps/outlet_promo", str(tmp_path / "non_existent"))
            manifest_file.write_text(text, encoding="utf-8")

            res = projects_scan.scan(vault, state_dir)
            self.assertEqual(res, 0)
            data = json.loads((state_dir / "projects.json").read_text(encoding="utf-8"))
            proj = data["projects"][0]
            self.assertIsNone(proj["git"]["branch"])
            self.assertIn("error", proj["git"])

    def test_scan_single_project_preserves_others(self):
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            vault = make_vault(tmp_path / "vault")
            state_dir = tmp_path / "state"
            state_dir.mkdir(parents=True, exist_ok=True)

            existing_snap = {
                "ts": "2026-11-01T12:00:00",
                "quota": {},
                "projects": [
                    {"slug": "outlet_promo", "fase": "old"},
                    {"slug": "outro_app", "fase": "keep_me"}
                ]
            }
            (state_dir / "projects.json").write_text(json.dumps(existing_snap), encoding="utf-8")

            with patch("projects_scan.collect_git", return_value={"branch": "main", "dirty": False, "commit_date": "2026-11-02", "ahead": 0, "behind": 0}):
                with patch("projects_scan.collect_gh_prs", return_value=0):
                    with patch("projects_scan.collect_traycer_tickets", return_value={}):
                        res = projects_scan.scan(vault, state_dir, project_slug="outlet_promo")
                        self.assertEqual(res, 0)

            data = json.loads((state_dir / "projects.json").read_text(encoding="utf-8"))
            slugs = {p["slug"]: p for p in data["projects"]}
            self.assertIn("outro_app", slugs)
            self.assertEqual(slugs["outro_app"]["fase"], "keep_me")
            self.assertEqual(slugs["outlet_promo"]["git"]["branch"], "main")

if __name__ == "__main__":
    unittest.main()
