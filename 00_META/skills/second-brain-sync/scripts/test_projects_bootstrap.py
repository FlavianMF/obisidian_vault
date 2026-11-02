import io
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import projects
import projects_bootstrap
from test_projects import make_vault


class ProjectsBootstrapTest(unittest.TestCase):
    def test_dry_run_creates_nothing(self):
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            vault = make_vault(tmp_path / "vault")
            state_dir = tmp_path / "state"

            chk_target = tmp_path / "checkout_target"
            manifest_file = vault / "00_META/projects/manifest.yaml"
            manifest_text = manifest_file.read_text(encoding="utf-8")
            # Point outlet_promo checkout to chk_target
            manifest_text = manifest_text.replace("checkout: ~/projetos_apps/outlet_promo", f"checkout: {chk_target}")
            manifest_file.write_text(manifest_text, encoding="utf-8")

            # Capture stdout
            buf = io.StringIO()
            with patch("sys.stdout", buf):
                res = projects_bootstrap.bootstrap(vault, state_dir, slug="outlet_promo", apply=False)

            self.assertEqual(res, 0)
            output = buf.getvalue()
            self.assertIn("Plano de bootstrap", output)
            self.assertIn("git clone", output)
            self.assertFalse(chk_target.exists(), "Dry-run não deve criar o checkout")

            snap_file = state_dir / "projects.json"
            self.assertFalse(snap_file.exists(), "Dry-run não deve gravar snapshot")

    def test_apply_clones_switches_branch_runs_setup_and_checks_env(self):
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            vault = make_vault(tmp_path / "vault")
            state_dir = tmp_path / "state"

            # 1. Cria um repo git de origem
            origin_repo = tmp_path / "origin.git"
            origin_repo.mkdir()
            subprocess.run(["git", "init", "-b", "master"], cwd=origin_repo, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=origin_repo, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=origin_repo, check=True)
            (origin_repo / "README.md").write_text("# Origin\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=origin_repo, check=True)
            subprocess.run(["git", "commit", "-m", "init"], cwd=origin_repo, check=True, capture_output=True)

            # Cria branch 'develop'
            subprocess.run(["git", "checkout", "-b", "develop"], cwd=origin_repo, check=True, capture_output=True)
            (origin_repo / "dev.txt").write_text("dev\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=origin_repo, check=True)
            subprocess.run(["git", "commit", "-m", "dev commit"], cwd=origin_repo, check=True, capture_output=True)
            subprocess.run(["git", "checkout", "master"], cwd=origin_repo, check=True, capture_output=True)

            chk_target = tmp_path / "cloned_checkout"
            marker_file = chk_target / "marker_setup.done"

            # 2. Configura o manifesto com repo, checkout, branch develop, setup e env
            manifest_file = vault / "00_META/projects/manifest.yaml"
            manifest_data = {
                "version": 1,
                "limits": {"max_implementers": 2, "quota_min_free_pct": 30, "activity_max_age_min": 30},
                "projects": [
                    {
                        "slug": "outlet_promo",
                        "note": "40_Projects/outlet_promo.md",
                        "repo": str(origin_repo),
                        "checkout": str(chk_target),
                        "branch": "develop",
                        "setup": [f"touch {marker_file}"],
                        "env": ["TEST_SECRET_ENV_VAR", "TEST_MISSING_ENV_VAR"],
                    }
                ],
            }
            import yaml
            manifest_file.write_text(yaml.safe_dump(manifest_data), encoding="utf-8")

            # Define env var secreta para testar que o VALOR nunca é impresso
            secret_value = "super_secret_password_value_12345"
            os.environ["TEST_SECRET_ENV_VAR"] = secret_value
            if "TEST_MISSING_ENV_VAR" in os.environ:
                del os.environ["TEST_MISSING_ENV_VAR"]

            try:
                buf = io.StringIO()
                with patch("sys.stdout", buf):
                    res = projects_bootstrap.bootstrap(vault, state_dir, slug="outlet_promo", apply=True)

                self.assertEqual(res, 0)
                output = buf.getvalue()

                # Verifica que clonou
                self.assertTrue(chk_target.exists(), "Checkout foi criado")
                # Verifica que trocou para a branch develop
                b_name = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=chk_target, capture_output=True, text=True).stdout.strip()
                self.assertEqual(b_name, "develop")

                # Verifica que rodou o setup e gerou o arquivo marcador
                self.assertTrue(marker_file.exists(), "Comando de setup criou o marcador")

                # Verifica env status: presente e ausente
                self.assertIn("TEST_SECRET_ENV_VAR: presente", output)
                self.assertIn("TEST_MISSING_ENV_VAR: ausente", output)

                # NUNCA deve conter o valor da variável de ambiente na saída
                self.assertNotIn(secret_value, output)

                # Verifica gravação no snapshot
                snap_file = state_dir / "projects.json"
                self.assertTrue(snap_file.exists())
                self.assertEqual(snap_file.stat().st_mode & 0o777, 0o600)
                snap_data = json.loads(snap_file.read_text(encoding="utf-8"))
                self.assertIn("bootstrap", snap_data)
                self.assertIn("outlet_promo", snap_data["bootstrap"])
                b_info = snap_data["bootstrap"]["outlet_promo"]
                self.assertEqual(b_info["clone"], "ok")
                self.assertEqual(b_info["branch"], "ok")
                self.assertEqual(b_info["env"]["TEST_SECRET_ENV_VAR"], "presente")
                self.assertEqual(b_info["env"]["TEST_MISSING_ENV_VAR"], "ausente")
            finally:
                os.environ.pop("TEST_SECRET_ENV_VAR", None)

    def test_validation_error_aborts_bootstrap(self):
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            vault = make_vault(tmp_path / "vault")
            state_dir = tmp_path / "state"

            # Injeta erro no manifesto (chave desconhecida)
            manifest_file = vault / "00_META/projects/manifest.yaml"
            manifest_text = manifest_file.read_text(encoding="utf-8")
            manifest_text += "\n  invalid_key_foo: bar\n"
            manifest_file.write_text(manifest_text, encoding="utf-8")

            res = projects_bootstrap.bootstrap(vault, state_dir, slug="outlet_promo", apply=True)
            self.assertEqual(res, 1)

    def test_sb_doctor_warns_when_checkout_missing(self):
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            vault = make_vault(tmp_path / "vault")

            # Altera checkout para caminho inexistente
            manifest_file = vault / "00_META/projects/manifest.yaml"
            manifest_text = manifest_file.read_text(encoding="utf-8")
            manifest_text = manifest_text.replace("checkout: ~/projetos_apps/outlet_promo", f"checkout: {tmp_path}/caminho_inexistente")
            manifest_file.write_text(manifest_text, encoding="utf-8")

            issues = projects.validate(vault)
            chk_issues = [i for i in issues if i.check == "checkout"]
            self.assertEqual(len(chk_issues), 1)
            self.assertEqual(chk_issues[0].severity.lower(), "warn")
            self.assertIn("does not exist", chk_issues[0].detail)


if __name__ == "__main__":
    unittest.main()
