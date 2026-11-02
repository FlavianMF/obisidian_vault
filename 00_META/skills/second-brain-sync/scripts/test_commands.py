import os
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import commands
import projects_state
from test_projects import make_vault


class CommandsTest(unittest.TestCase):
    def test_parse_empty_and_unknown(self):
        err = commands.parse("")
        self.assertIsInstance(err, commands.ParseError)
        self.assertIn("vazio", err.message.lower())

        err = commands.parse("   ")
        self.assertIsInstance(err, commands.ParseError)
        self.assertIn("vazio", err.message.lower())

        err = commands.parse("fazer algo inexistente")
        self.assertIsInstance(err, commands.ParseError)
        self.assertIn("não reconhecido", err.message.lower())

    def test_parse_verbs_and_accents(self):
        # status
        cmd = commands.parse("status")
        self.assertEqual(cmd.action, "status")

        cmd = commands.parse("STATUS outlet_promo")
        self.assertEqual(cmd.action, "status_project")
        self.assertEqual(cmd.slug, "outlet_promo")

        # aprovar / rejeitar com acentos
        cmd = commands.parse("aprovár s-1234")
        self.assertEqual(cmd.action, "suggest_decide")
        self.assertEqual(cmd.id, "s-1234")
        self.assertEqual(cmd.decision, "approve")

        cmd = commands.parse("REJEITÁR s-5678")
        self.assertEqual(cmd.action, "suggest_decide")
        self.assertEqual(cmd.id, "s-5678")
        self.assertEqual(cmd.decision, "reject")

        # pausar / retomar com acentos
        cmd = commands.parse("  Pausár   outlet_promo  ")
        self.assertEqual(cmd.action, "pause")
        self.assertEqual(cmd.slug, "outlet_promo")

        cmd = commands.parse("retomár outlet_promo")
        self.assertEqual(cmd.action, "resume")
        self.assertEqual(cmd.slug, "outlet_promo")

        # priorizar com acentos e case
        cmd = commands.parse("Priorizár outlet_promo p2")
        self.assertEqual(cmd.action, "prioritize")
        self.assertEqual(cmd.slug, "outlet_promo")
        self.assertEqual(cmd.priority, "P2")

    def test_parse_invalid_args_and_slug(self):
        # Invalid priority
        err = commands.parse("priorizar outlet_promo P4")
        self.assertIsInstance(err, commands.ParseError)
        self.assertIn("prioridade inválida", err.message.lower())

        # Unknown slug when valid_slugs provided
        err = commands.parse("pausar slug_desconhecido", valid_slugs=["outlet_promo", "dotfiles"])
        self.assertIsInstance(err, commands.ParseError)
        self.assertIn("slug desconhecido", err.message.lower())
        self.assertIn("outlet_promo", err.message)
        self.assertIn("dotfiles", err.message)

        # Missing argument
        err = commands.parse("pausar")
        self.assertIsInstance(err, commands.ParseError)

    def test_execute_status(self):
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            vault = make_vault(tmp_path / "vault")
            state_dir = tmp_path / "state"

            cmd = commands.parse("status")
            res = commands.execute(cmd, vault, state_dir)
            self.assertTrue(res.ok)
            self.assertIn("outlet_promo", res.message)
            self.assertLessEqual(len(res.message), 300)

            cmd = commands.parse("status outlet_promo")
            res = commands.execute(cmd, vault, state_dir)
            self.assertTrue(res.ok)
            self.assertIn("outlet_promo", res.message)
            self.assertIn("active", res.message)
            self.assertLessEqual(len(res.message), 300)

    def test_execute_pause_resume(self):
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            vault = make_vault(tmp_path / "vault")
            state_dir = tmp_path / "state"

            cmd = commands.parse("pausar outlet_promo")
            res = commands.execute(cmd, vault, state_dir)
            self.assertTrue(res.ok)
            self.assertTrue(projects_state.is_paused(state_dir, "outlet_promo"))
            self.assertLessEqual(len(res.message), 300)

            cmd = commands.parse("retomar outlet_promo")
            res = commands.execute(cmd, vault, state_dir)
            self.assertTrue(res.ok)
            self.assertFalse(projects_state.is_paused(state_dir, "outlet_promo"))

    def test_execute_suggestions(self):
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            vault = make_vault(tmp_path / "vault")
            state_dir = tmp_path / "state"

            s_id = projects_state.suggest_add(
                state_dir, project="outlet_promo", ticket="t-1",
                harness="claude", model="sonnet", effort="high", reason="test"
            )

            cmd = commands.parse(f"aprovar {s_id}")
            res = commands.execute(cmd, vault, state_dir)
            self.assertTrue(res.ok)
            self.assertIn("aprovada", res.message)

            cmd = commands.parse("rejeitar s-inexistente")
            res = commands.execute(cmd, vault, state_dir)
            self.assertFalse(res.ok)
            self.assertIn("não encontrada", res.message)

    def test_execute_prioritize(self):
        from unittest.mock import patch
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            vault = make_vault(tmp_path / "vault")
            state_dir = tmp_path / "state"

            with patch("projects.sync_vault", return_value=True):
                cmd = commands.parse("priorizar outlet_promo P3")
                res = commands.execute(cmd, vault, state_dir)
                self.assertTrue(res.ok)
                self.assertIn("P3", res.message)

                # verify vault note was updated
                note_content = (vault / "40_Projects/outlet_promo.md").read_text(encoding="utf-8")
                self.assertIn("prioridade: P3", note_content)

    def test_cli_cmd(self):
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            vault = make_vault(tmp_path / "vault")
            state_dir = tmp_path / "state"
            state_dir.mkdir(parents=True, exist_ok=True)

            env = os.environ.copy()
            env["SECOND_BRAIN_STATE_DIR"] = str(state_dir)
            env["SECOND_BRAIN_VAULT"] = str(vault)

            sb_script = Path(__file__).parent / "sb.py"

            p = subprocess.run(
                [sys.executable, str(sb_script), "projects", "cmd", "pausar outlet_promo"],
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(p.returncode, 0)
            self.assertIn("pausado com sucesso", p.stdout)
            self.assertTrue(projects_state.is_paused(state_dir, "outlet_promo"))


if __name__ == "__main__":
    unittest.main()
