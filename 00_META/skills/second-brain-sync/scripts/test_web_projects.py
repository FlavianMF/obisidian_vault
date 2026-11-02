import datetime as dt
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from starlette.testclient import TestClient

import web_projects
import web_service
from test_projects import make_vault


class WebProjectsTest(unittest.TestCase):
    def test_derive_situacao_precedence(self):
        # 1. pausado tem precedência máxima
        self.assertEqual(
            web_projects.derive_situacao(is_paused=True, bloqueio="Bloqueado", active_agents=2, last_session_age_days=10),
            "pausado",
        )
        # 2. bloqueado tem precedência sobre trabalhando e parado
        self.assertEqual(
            web_projects.derive_situacao(is_paused=False, bloqueio="Falta credencial", active_agents=1, last_session_age_days=12),
            "bloqueado",
        )
        # 3. trabalhando tem precedência sobre parado
        self.assertEqual(
            web_projects.derive_situacao(is_paused=False, bloqueio="", active_agents=1, last_session_age_days=15),
            "trabalhando",
        )
        # 4. parado (última sessão > 7 dias)
        self.assertEqual(
            web_projects.derive_situacao(is_paused=False, bloqueio="", active_agents=0, last_session_age_days=8),
            "parado",
        )
        # 5. ocioso (sessão recente <= 7 dias ou sem agente)
        self.assertEqual(
            web_projects.derive_situacao(is_paused=False, bloqueio="", active_agents=0, last_session_age_days=3),
            "ocioso",
        )
        self.assertEqual(
            web_projects.derive_situacao(is_paused=False, bloqueio="", active_agents=0, last_session_age_days=None),
            "ocioso",
        )

    def test_no_snapshot_returns_200_and_sem_dados(self):
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            vault = make_vault(tmp_path / "vault")
            state_dir = tmp_path / "state"
            state_dir.mkdir(parents=True, exist_ok=True)

            app = web_service.create_app(vault, state_dir)
            client = TestClient(app)

            # HTML
            r_html = client.get("/projects")
            self.assertEqual(r_html.status_code, 200)
            self.assertIn("sem dados", r_html.text)

            # API JSON
            r_json = client.get("/api/projects")
            self.assertEqual(r_json.status_code, 200)
            data = r_json.json()
            self.assertFalse(data["has_data"])
            self.assertEqual(len(data["projects"]), 0)

    def test_api_projects_and_allowlist_and_ordering(self):
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            vault = make_vault(tmp_path / "vault")
            state_dir = tmp_path / "state"
            state_dir.mkdir(parents=True, exist_ok=True)

            now = dt.datetime.now()
            snapshot = {
                "ts": now.isoformat(),
                "quota": {
                    "claude": {"free_pct": 45.0, "used_5h": 55.0, "used_7d": 10.0},
                    "antigravity": {"free_pct": 80.0},
                },
                "projects": [
                    {
                        "slug": "projeto_p2",
                        "prioridade": "P2",
                        "fase": "desenvolvimento",
                        "proximo_passo": "fazer testes",
                        "bloqueio": "",
                        "git": {"branch": "feat/x", "dirty": False, "commit_date": now.isoformat()},
                        "prs": 1,
                        "tickets": {"0": 2},
                        "tests": {"status": "ok"},
                        # Campo fora da allowlist proposital para testar vazamento
                        "secret_token_leaked": "super_secret_value",
                        "internal_debug_info": {"foo": "bar"},
                    },
                    {
                        "slug": "projeto_p1",
                        "prioridade": "P1",
                        "fase": "planejamento",
                        "proximo_passo": "aprovar PRD",
                        "bloqueio": "aguardando review",
                        "git": {"branch": "master", "dirty": True, "commit_date": now.isoformat()},
                        "prs": 0,
                        "tickets": {"0": 5},
                        "tests": None,
                        "extra_disallowed_key": 999,
                    },
                ],
            }
            (state_dir / "projects.json").write_text(json.dumps(snapshot), encoding="utf-8")

            # suggestions
            sug_entry = {
                "id": "s-1234",
                "project": "projeto_p1",
                "ticket": "ticket-1",
                "harness": "claude",
                "model": "sonnet",
                "effort": "high",
                "reason": "pronto para implementar",
                "state": "pending",
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
                "agent_id": None,
                "internal_secret": "do_not_leak",
            }
            (state_dir / "suggestions.jsonl").write_text(json.dumps(sug_entry) + "\n", encoding="utf-8")

            app = web_service.create_app(vault, state_dir)
            client = TestClient(app)

            # 1. API JSON Check
            res = client.get("/api/projects")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertTrue(data["has_data"])

            # Quota in header
            self.assertIn("claude", data["header"]["quota"])
            self.assertEqual(data["header"]["quota"]["claude"]["free_pct"], 45.0)

            # Suggestions
            self.assertEqual(len(data["suggestions"]), 1)
            s = data["suggestions"][0]
            self.assertEqual(s["id"], "s-1234")
            self.assertNotIn("internal_secret", s)

            # Projects order: P1 first, then P2
            projs = data["projects"]
            # Find the two projects
            slugs = [p["slug"] for p in projs]
            self.assertIn("projeto_p1", slugs)
            self.assertIn("projeto_p2", slugs)
            idx_p1 = slugs.index("projeto_p1")
            idx_p2 = slugs.index("projeto_p2")
            self.assertLess(idx_p1, idx_p2, "P1 deve vir antes de P2")

            # Allowlist verification
            for p in projs:
                keys = set(p.keys())
                self.assertTrue(keys.issubset(web_projects.ALLOWED_PROJECT_KEYS))
                self.assertNotIn("secret_token_leaked", keys)
                self.assertNotIn("internal_debug_info", keys)
                self.assertNotIn("extra_disallowed_key", keys)

            # 2. HTML View Check
            r_html = client.get("/projects")
            self.assertEqual(r_html.status_code, 200)
            html_text = r_html.text
            self.assertIn("projeto_p1", html_text)
            self.assertIn("projeto_p2", html_text)
            self.assertIn("Sugestão s-1234", html_text)
            # Sprint 11 enables the action buttons: each one carries the text command it posts to /api/command
            self.assertIn('data-cmd="aprovar s-1234"', html_text)
            self.assertIn('data-cmd="pausar projeto_p1"', html_text)
            self.assertNotIn("<button disabled", html_text)
            self.assertNotIn("secret_token_leaked", html_text)


if __name__ == "__main__":
    unittest.main()
