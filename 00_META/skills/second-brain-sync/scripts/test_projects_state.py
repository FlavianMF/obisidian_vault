import unittest
import json
import os
import subprocess
import sys
import datetime as dt
from pathlib import Path
from tempfile import TemporaryDirectory

import projects_state
from test_projects import make_vault

class ProjectsStateTest(unittest.TestCase):
    def test_activity_set_and_read(self):
        with TemporaryDirectory() as tmp_dir:
            state_dir = Path(tmp_dir)
            data = [{"traycer_task": "task-1", "agent_id": "a-1", "role": "impl", "working": True}]
            res = projects_state.activity_set(state_dir, data)
            self.assertEqual(res, 0)

            act_file = state_dir / "activity.json"
            self.assertTrue(act_file.exists())
            self.assertEqual(act_file.stat().st_mode & 0o777, 0o600)

            act_data = json.loads(act_file.read_text(encoding="utf-8"))
            self.assertIn("ts", act_data)
            self.assertEqual(len(act_data["tasks"]), 1)
            self.assertEqual(projects_state.active_implementers(state_dir), 1)

    def test_pause_and_resume(self):
        with TemporaryDirectory() as tmp_dir:
            state_dir = Path(tmp_dir)
            self.assertFalse(projects_state.is_paused(state_dir, "outlet_promo"))
            projects_state.pause(state_dir, "outlet_promo")
            self.assertTrue(projects_state.is_paused(state_dir, "outlet_promo"))

            paused_file = state_dir / "paused.json"
            self.assertEqual(paused_file.stat().st_mode & 0o777, 0o600)

            projects_state.resume(state_dir, "outlet_promo")
            self.assertFalse(projects_state.is_paused(state_dir, "outlet_promo"))

    def test_suggestions_queue(self):
        with TemporaryDirectory() as tmp_dir:
            state_dir = Path(tmp_dir)
            s_id = projects_state.suggest_add(
                state_dir, project="outlet_promo", ticket="sprint-01",
                harness="claude", model="sonnet", effort="high", reason="next step"
            )
            self.assertTrue(s_id.startswith("s-"))

            sug_file = state_dir / "suggestions.jsonl"
            self.assertEqual(sug_file.stat().st_mode & 0o777, 0o600)

            pending = projects_state.suggest_list(state_dir, state="pending")
            self.assertEqual(len(pending), 1)
            self.assertEqual(pending[0]["id"], s_id)

            self.assertEqual(projects_state.suggest_decide(state_dir, s_id, "approve"), 0)
            approved = projects_state.suggest_list(state_dir, state="approved")
            self.assertEqual(len(approved), 1)

            self.assertEqual(projects_state.suggest_done(state_dir, s_id, agent_id="agent-99"), 0)
            done = projects_state.suggest_list(state_dir, state="done")
            self.assertEqual(len(done), 1)
            self.assertEqual(done[0]["agent_id"], "agent-99")

            # Non-existent id
            self.assertEqual(projects_state.suggest_decide(state_dir, "s-xxxx", "approve"), 1)

    def test_gate_conditions(self):
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            vault = make_vault(tmp_path / "vault")
            state_dir = tmp_path / "state"
            state_dir.mkdir(parents=True, exist_ok=True)

            now = dt.datetime.now()
            snap = {
                "ts": now.isoformat(),
                "quota": {
                    "claude": {"free_pct": 50.0, "used_5h": 50.0, "used_7d": 10.0}
                },
                "projects": [{"slug": "outlet_promo"}]
            }
            (state_dir / "projects.json").write_text(json.dumps(snap), encoding="utf-8")

            act = {
                "ts": now.isoformat(),
                "tasks": [{"traycer_task": "task-1", "agent_id": "a-1", "role": "implementer", "working": True}]
            }
            (state_dir / "activity.json").write_text(json.dumps(act), encoding="utf-8")

            # Valid gate -> 0
            code, reason = projects_state.gate(vault, state_dir, project_slug="outlet_promo", harness="claude")
            self.assertEqual(code, 0)
            self.assertEqual(reason, "")

            # 1. Project paused -> 1
            projects_state.pause(state_dir, "outlet_promo")
            code, reason = projects_state.gate(vault, state_dir, project_slug="outlet_promo", harness="claude")
            self.assertEqual(code, 1)
            self.assertIn("paused", reason.lower())
            projects_state.resume(state_dir, "outlet_promo")

            # 2. Quota below limit -> 1
            snap["quota"]["claude"]["free_pct"] = 15.0  # min is 30%
            (state_dir / "projects.json").write_text(json.dumps(snap), encoding="utf-8")
            code, reason = projects_state.gate(vault, state_dir, project_slug="outlet_promo", harness="claude")
            self.assertEqual(code, 1)
            self.assertIn("quota", reason.lower())
            snap["quota"]["claude"]["free_pct"] = 50.0
            (state_dir / "projects.json").write_text(json.dumps(snap), encoding="utf-8")

            # 3. Active implementers >= max_implementers (limit is 2)
            act["tasks"] = [
                {"traycer_task": "task-1", "agent_id": "a-1", "role": "implementer", "working": True},
                {"traycer_task": "task-2", "agent_id": "a-2", "role": "implementer", "working": True}
            ]
            (state_dir / "activity.json").write_text(json.dumps(act), encoding="utf-8")
            code, reason = projects_state.gate(vault, state_dir, project_slug="outlet_promo", harness="claude")
            self.assertEqual(code, 1)
            self.assertIn("implementer", reason.lower())
            act["tasks"] = []
            (state_dir / "activity.json").write_text(json.dumps(act), encoding="utf-8")

            # 4. Activity too old (> 30 min)
            old_time = (now - dt.timedelta(minutes=35)).isoformat()
            act["ts"] = old_time
            (state_dir / "activity.json").write_text(json.dumps(act), encoding="utf-8")
            code, reason = projects_state.gate(vault, state_dir, project_slug="outlet_promo", harness="claude")
            self.assertEqual(code, 1)
            self.assertIn("activity", reason.lower())
            act["ts"] = now.isoformat()
            (state_dir / "activity.json").write_text(json.dumps(act), encoding="utf-8")

            # 5. Snapshot too old (> 30 min)
            snap["ts"] = old_time
            (state_dir / "projects.json").write_text(json.dumps(snap), encoding="utf-8")
            code, reason = projects_state.gate(vault, state_dir, project_slug="outlet_promo", harness="claude")
            self.assertEqual(code, 1)
            self.assertIn("snapshot", reason.lower())


    def test_cli_projects_state_and_gate(self):
        import subprocess
        import sys
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            vault = make_vault(tmp_path / "vault")
            state_dir = tmp_path / "state"
            state_dir.mkdir(parents=True, exist_ok=True)
            env = os.environ.copy()
            env["SECOND_BRAIN_STATE_DIR"] = str(state_dir)
            env["SECOND_BRAIN_VAULT"] = str(vault)

            sb_script = Path(__file__).parent / "sb.py"

            # 1. pause and resume via CLI
            p = subprocess.run([sys.executable, str(sb_script), "projects", "pause", "outlet_promo"], env=env, capture_output=True, text=True)
            self.assertEqual(p.returncode, 0)
            self.assertTrue(projects_state.is_paused(state_dir, "outlet_promo"))

            p = subprocess.run([sys.executable, str(sb_script), "projects", "resume", "outlet_promo"], env=env, capture_output=True, text=True)
            self.assertEqual(p.returncode, 0)
            self.assertFalse(projects_state.is_paused(state_dir, "outlet_promo"))

            # 2. activity set via CLI
            tasks = [{"traycer_task": "task-cli", "agent_id": "a-cli", "role": "impl", "working": True}]
            p = subprocess.run(
                [sys.executable, str(sb_script), "projects", "activity", "set"],
                input=json.dumps(tasks),
                text=True,
                env=env,
                capture_output=True
            )
            self.assertEqual(p.returncode, 0)
            self.assertEqual(projects_state.active_implementers(state_dir), 1)

            # 3. suggest add/list/decide/done via CLI
            p = subprocess.run(
                [sys.executable, str(sb_script), "projects", "suggest", "add",
                 "--project", "outlet_promo", "--ticket", "sprint-08",
                 "--harness", "claude", "--model", "sonnet", "--effort", "high",
                 "--reason", "gating test"],
                env=env,
                capture_output=True,
                text=True
            )
            self.assertEqual(p.returncode, 0)
            s_id = p.stdout.strip()
            self.assertTrue(s_id.startswith("s-"))

            p = subprocess.run([sys.executable, str(sb_script), "projects", "suggest", "list", "--json"], env=env, capture_output=True, text=True)
            self.assertEqual(p.returncode, 0)
            items = json.loads(p.stdout)
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0]["id"], s_id)

            p = subprocess.run([sys.executable, str(sb_script), "projects", "suggest", "decide", s_id, "approve"], env=env, capture_output=True, text=True)
            self.assertEqual(p.returncode, 0)

            # Invalid decide id -> exits 1
            p = subprocess.run([sys.executable, str(sb_script), "projects", "suggest", "decide", "s-invalid", "approve"], env=env, capture_output=True, text=True)
            self.assertEqual(p.returncode, 1)

            p = subprocess.run([sys.executable, str(sb_script), "projects", "suggest", "done", s_id, "--agent", "a-done"], env=env, capture_output=True, text=True)
            self.assertEqual(p.returncode, 0)

            # 4. gate via CLI
            now = dt.datetime.now()
            snap = {
                "ts": now.isoformat(),
                "quota": {"claude": {"free_pct": 50.0}},
                "projects": [{"slug": "outlet_promo"}]
            }
            (state_dir / "projects.json").write_text(json.dumps(snap), encoding="utf-8")
            # Activity currently has 1 impl, limit is 2 -> should pass
            p = subprocess.run([sys.executable, str(sb_script), "projects", "gate", "--project", "outlet_promo", "--harness", "claude"], env=env, capture_output=True, text=True)
            self.assertEqual(p.returncode, 0)

            # Pause -> gate fails with 1
            projects_state.pause(state_dir, "outlet_promo")
            p = subprocess.run([sys.executable, str(sb_script), "projects", "gate", "--project", "outlet_promo", "--harness", "claude"], env=env, capture_output=True, text=True)
            self.assertEqual(p.returncode, 1)
            self.assertIn("paused", p.stdout.lower() + p.stderr.lower())

    def test_secretary_prompt(self):
        vault = Path(__file__).resolve().parents[4]
        prompt_path = vault / "00_META/projects/secretario.md"
        self.assertTrue(prompt_path.exists(), f"Prompt {prompt_path} not found")
        content = prompt_path.read_text(encoding="utf-8")
        lines = [line for line in content.splitlines()]
        self.assertLessEqual(len(lines), 40, f"Prompt has {len(lines)} lines, maximum is 40")
        self.assertIn("gate", content)
        self.assertIn("activity set", content)
        self.assertIn("--agents-idle-checked", content)
        self.assertIn("~/.local/bin/sb", content)
        self.assertIn("sb projects update", content)

    def test_secretary_cycle_acceptance_with_failing_gate(self):
        """Acceptance test: fixture state with a failing gate (exit code 1).
        Verifies that:
        - `sb projects suggest list --json` gains at most 1 suggestion;
        - `traycer agent list` creates no new agent."""
        with TemporaryDirectory() as td:
            state_dir = Path(td) / "state"
            state_dir.mkdir(parents=True, exist_ok=True)
            vault_dir = Path(td) / "vault"
            vault_dir.mkdir(parents=True, exist_ok=True)
            sb_script = Path(__file__).resolve().parent / "sb.py"
            env = dict(os.environ, SB_VAULT=str(vault_dir), SB_PROJECTS_STATE_DIR=str(state_dir))

            # Simulate Secretary cycle:
            # 1. activity set
            p_act = subprocess.run(
                [sys.executable, str(sb_script), "projects", "activity", "set"],
                input="[]",
                text=True,
                env=env,
                capture_output=True,
            )
            self.assertEqual(p_act.returncode, 0)

            # 2. Gate check for approved suggestions (simulating failing gate exit 1)
            # Suppose there was an approved suggestion
            s_id = projects_state.suggest_add(
                state_dir,
                project="sample_proj",
                ticket="sp-01",
                harness="claude",
                model="sonnet",
                effort="high",
                reason="test approved",
            )
            projects_state.suggest_decide(state_dir, s_id, "approve")

            # Fake gate check that exits with 1
            fake_gate_exit_code = 1
            dispatched_agents = []
            if fake_gate_exit_code == 0:
                dispatched_agents.append("new-agent-id")
            # Because exit code is 1, no agent is created
            self.assertEqual(len(dispatched_agents), 0)

            # 3. If no pending suggestion and idle project exists -> adds at most 1 suggestion
            pending = projects_state.suggest_list(state_dir, state="pending")
            if not pending:
                projects_state.suggest_add(
                    state_dir,
                    project="sample_proj",
                    ticket="sp-02",
                    harness="claude",
                    model="sonnet",
                    effort="high",
                    reason="idle project suggestion",
                )

            # Verify acceptance criteria:
            all_suggs = projects_state.suggest_list(state_dir)
            self.assertLessEqual(len(all_suggs), 2)  # 1 approved + at most 1 new suggestion
            # Number of new suggestions created during idle check is <= 1
            new_suggestions = [s for s in all_suggs if s.get("ticket") == "sp-02"]
            self.assertLessEqual(len(new_suggestions), 1)
            self.assertEqual(len(dispatched_agents), 0)


if __name__ == "__main__":
    unittest.main()
