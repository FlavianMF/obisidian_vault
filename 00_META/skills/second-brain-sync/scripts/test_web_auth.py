"""Tests of the exposed web instance (Sprint 11): token auth, session cookie, global failure limiter, audit log and
the command endpoint. python3 -m unittest test_web_auth -v

Every token is generated at run time with secrets.token_urlsafe(32); no real credential appears in this file.
"""
from __future__ import annotations

import hashlib
import hmac
import io
import json
import os
import secrets
import stat
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from starlette.routing import Mount
from starlette.testclient import TestClient

import candidates
import projects_state
import review
import web_auth
import web_projects
import web_service
from test_projects import make_vault

LOOPBACK = "http://127.0.0.1"  # the Host the app sees behind `tailscale serve`
MAGIC = "pc.tailnet.ts.net"


def cookie_for(token: str) -> str:
    """The spec's cookie value, computed here on purpose instead of through web_auth."""
    return hmac.new(token.encode(), b"sb-session-v1", hashlib.sha256).hexdigest()


def bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def session(token: str) -> dict:
    return {"Cookie": f"sb_session={cookie_for(token)}"}


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


class ExposedCase(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        root = Path(self._tmp.name)
        self.vault = make_vault(root / "vault")
        self.state = root / "state"
        self.state.mkdir()
        self.token = secrets.token_urlsafe(32)
        self.app = web_service.create_app(
            self.vault, self.state, {"127.0.0.1", "localhost", MAGIC}, self.token, exposed=True)
        self.clock = FakeClock()
        self.app.state.auth_gate.clock = self.clock
        self.client = TestClient(self.app, base_url=LOOPBACK)
        self.seen: list = []  # every response of the test, for the "token never leaks" search

    def call(self, method: str, url: str, **kw):
        response = self.client.request(method, url, **kw)
        self.seen.append(response)
        return response

    def fail_n(self, n: int, **kw) -> list:
        return [self.call("GET", "/api/projects", headers=bearer(secrets.token_urlsafe(32)), **kw).status_code
                for _ in range(n)]

    def log_rows(self) -> list:
        path = self.state / "web-auth.jsonl"
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []


class AuthenticationTest(ExposedCase):
    def test_no_credential_is_401_on_every_route_with_loopback_host(self):
        routes = [r for r in [*self.app.routes, *web_projects.router.routes] if hasattr(r, "path")]
        paths = {r.path for r in routes if r.path != "/login" and not isinstance(r, Mount)}
        for expected in ("/", "/projects", "/api/projects", "/api/command", "/api/decide", "/api/undo", "/docs"):
            self.assertIn(expected, paths)
        for path in sorted(paths):
            url = path.replace("{", "").replace("}", "")
            for method in ("GET", "POST"):
                self.assertEqual(self.call(method, url).status_code, 401, f"{method} {path}")

    def test_decide_undo_projects_and_command_are_401_with_loopback_host(self):
        cid, _ = candidates.add(self.state, kind="trap", title="Falha de rede", summary="resumo", project="proj",
                                body="Contexto.\n")
        for method, url, body in (
            ("POST", "/api/decide", {"id": cid, "action": "drop", "reason": "ruído"}),
            ("POST", "/api/undo", {}),
            ("GET", "/api/projects", None),
            ("GET", "/projects", None),
            ("POST", "/api/command", {"text": "pausar outlet_promo"}),
        ):
            response = self.call(method, url, json=body)
            self.assertEqual(response.status_code, 401, url)
        self.assertEqual([c.id for c in review.pending(self.state)], [cid], "an unauthenticated drop must change nothing")
        self.assertFalse(projects_state.is_paused(self.state, "outlet_promo"))

    def test_valid_bearer_is_200(self):
        for url in ("/api/projects", "/projects", "/api/stats", "/api/filters", "/"):
            self.assertEqual(self.call("GET", url, headers=bearer(self.token)).status_code, 200, url)
        # the scheme name is case-insensitive
        lower = {"Authorization": f"bearer {self.token}"}
        self.assertEqual(self.call("GET", "/api/projects", headers=lower).status_code, 200)

    def test_valid_cookie_is_200(self):
        for url in ("/api/projects", "/projects"):
            self.assertEqual(self.call("GET", url, headers=session(self.token)).status_code, 200, url)

    def test_cookie_derived_from_another_token_is_401(self):
        other = secrets.token_urlsafe(32)
        self.assertEqual(self.call("GET", "/api/projects", headers=session(other)).status_code, 401)

    def test_bearer_of_another_token_and_wrong_schemes_are_401(self):
        for header in (f"Bearer {secrets.token_urlsafe(32)}", f"Basic {self.token}", "Bearer", self.token,
                       f"Bearer {self.token}x"):
            response = self.call("GET", "/api/projects", headers={"Authorization": header})
            self.assertEqual(response.status_code, 401, header[:12])
        # the cookie value is not the token, and the token is not a cookie
        self.assertEqual(self.call("GET", "/api/projects", headers={"Cookie": f"sb_session={self.token}"}).status_code, 401)

    def test_non_ascii_credentials_are_401_not_500(self):
        for headers in ({"Cookie": "sb_session=çãõ".encode("utf-8")}, {"Authorization": "Bearer tökén".encode("latin-1")},
                        {"Authorization": "Bearer tökén".encode("utf-8")}):
            self.assertEqual(self.call("GET", "/api/projects", headers=headers).status_code, 401)

    def test_open_routes_need_no_credential(self):
        page = self.call("GET", "/login")
        self.assertEqual(page.status_code, 200)
        self.assertIn('name="token"', page.text)
        self.assertEqual(self.call("GET", "/static/review.js").status_code, 200)

    def test_browser_navigation_without_credential_gets_the_login_form_with_401(self):
        response = self.call("GET", "/projects", headers={"Accept": "text/html"})
        self.assertEqual(response.status_code, 401)
        self.assertIn('action="/login"', response.text)

    def test_origin_and_host_guards_stay_active(self):
        cross = self.call("POST", "/api/command", headers={**bearer(self.token), "Origin": "https://evil.example"},
                          json={"text": "status"})
        self.assertEqual(cross.status_code, 403)
        login_cross = self.call("POST", "/login", headers={"Origin": "https://evil.example"}, json={"token": self.token})
        self.assertEqual(login_cross.status_code, 403)
        rebind = TestClient(self.app, base_url="http://evil.example").get("/api/projects", headers=bearer(self.token))
        self.assertEqual(rebind.status_code, 403)
        magic = TestClient(self.app, base_url=f"https://{MAGIC}").get("/api/projects")
        self.assertEqual(magic.status_code, 401, "the MagicDNS name is allowed by Host and still needs a credential")
        ok = TestClient(self.app, base_url=f"https://{MAGIC}").get("/api/projects", headers=bearer(self.token))
        self.assertEqual(ok.status_code, 200)

    def test_session_value_matches_the_spec(self):
        self.assertEqual(web_auth.session_value(self.token), cookie_for(self.token))
        self.assertNotEqual(web_auth.session_value(self.token), web_auth.session_value(secrets.token_urlsafe(32)))


class LoginTest(ExposedCase):
    def test_json_login_sets_the_cookie_with_the_required_attributes(self):
        response = self.call("POST", "/login", json={"token": self.token})
        self.assertEqual(response.status_code, 200)
        header = response.headers["set-cookie"]
        self.assertTrue(header.startswith(f"sb_session={cookie_for(self.token)};"), "value is the HMAC, not the token")
        attrs = header.lower()
        for expected in ("httponly", "secure", "samesite=strict", "max-age=2592000", "path=/"):
            self.assertIn(expected, attrs)
        # the Secure cookie is not replayed over http by the test client, so send it as a browser on https would
        self.assertEqual(self.call("GET", "/api/projects", headers=session(self.token)).status_code, 200)

    def test_form_login_redirects_to_the_dashboard_with_the_cookie(self):
        response = self.call("POST", "/login", data={"token": self.token}, follow_redirects=False)
        self.assertEqual(response.status_code, 303)
        self.assertEqual(response.headers["location"], "/projects")
        self.assertIn(f"sb_session={cookie_for(self.token)}", response.headers["set-cookie"])

    def test_wrong_token_is_401_without_cookie_for_form_and_json(self):
        wrong = secrets.token_urlsafe(32)
        as_form = self.call("POST", "/login", data={"token": wrong})
        self.assertEqual(as_form.status_code, 401)
        self.assertIn('role="alert"', as_form.text)
        self.assertNotIn("set-cookie", as_form.headers)
        as_json = self.call("POST", "/login", json={"token": wrong})
        self.assertEqual(as_json.status_code, 401)
        self.assertNotIn("set-cookie", as_json.headers)

    def test_login_without_a_token_is_400_and_does_not_count_as_a_failure(self):
        for _ in range(15):
            self.assertEqual(self.call("POST", "/login", json={}).status_code, 400)
            self.assertEqual(self.call("POST", "/login", data={"token": ""}).status_code, 400)
            self.assertEqual(self.call("POST", "/login", content=b"{", headers={"Content-Type": "application/json"}
                                       ).status_code, 400)
        self.assertEqual(self.call("POST", "/login", json={"token": self.token}).status_code, 200)

    def test_oversized_login_body_is_rejected_without_comparison(self):
        response = self.call("POST", "/login", json={"token": "x" * 10_000})
        self.assertEqual(response.status_code, 400)


class RateLimitTest(ExposedCase):
    def test_eleventh_failure_is_429(self):
        self.assertEqual(self.fail_n(10), [401] * 10)
        eleventh = self.call("GET", "/api/projects", headers=bearer(secrets.token_urlsafe(32)))
        self.assertEqual(eleventh.status_code, 429)
        self.assertEqual(eleventh.headers["retry-after"], "60")

    def test_block_covers_all_authentication_even_valid_credentials_and_login(self):
        self.fail_n(10)
        self.assertEqual(self.call("GET", "/api/projects", headers=bearer(self.token)).status_code, 429)
        self.assertEqual(self.call("GET", "/projects", headers=session(self.token)).status_code, 429)
        login = self.call("POST", "/login", json={"token": self.token})
        self.assertEqual(login.status_code, 429)
        self.assertNotIn("set-cookie", login.headers)
        no_credential = self.call("GET", "/api/projects")
        self.assertEqual(no_credential.status_code, 429)

    def test_block_lasts_60_seconds_and_blocked_requests_do_not_extend_it(self):
        self.fail_n(10)
        self.clock.now += 30
        self.assertEqual(self.call("GET", "/api/projects", headers=bearer(self.token)).status_code, 429)
        self.clock.now += 29
        self.assertEqual(self.call("GET", "/api/projects", headers=bearer(self.token)).status_code, 429)
        self.clock.now += 2  # 61 s after the 10th failure
        self.assertEqual(self.call("GET", "/api/projects", headers=bearer(self.token)).status_code, 200)

    def test_failures_older_than_a_minute_do_not_count(self):
        self.fail_n(9)
        self.clock.now += 61
        self.assertEqual(self.fail_n(9), [401] * 9)
        self.assertEqual(self.call("GET", "/api/projects", headers=bearer(self.token)).status_code, 200)

    def test_counter_is_global_not_per_origin(self):
        statuses = []
        for i in range(11):
            headers = {**bearer(secrets.token_urlsafe(32)), "X-Forwarded-For": f"10.0.0.{i}"}
            statuses.append(self.call("GET", "/api/projects", headers=headers).status_code)
        self.assertEqual(statuses, [401] * 10 + [429])

    def test_failed_logins_count_toward_the_same_counter(self):
        for _ in range(10):
            self.assertEqual(self.call("POST", "/login", json={"token": secrets.token_urlsafe(32)}).status_code, 401)
        self.assertEqual(self.call("GET", "/api/projects", headers=bearer(self.token)).status_code, 429)

    def test_requests_without_a_credential_never_count(self):
        for _ in range(30):
            self.assertEqual(self.call("GET", "/api/projects").status_code, 401)
        self.assertEqual(self.call("GET", "/api/projects", headers=bearer(self.token)).status_code, 200)

    def test_a_success_does_not_reset_the_counter(self):
        self.fail_n(9)
        self.assertEqual(self.call("GET", "/api/projects", headers=bearer(self.token)).status_code, 200)
        self.assertEqual(self.fail_n(1), [401])
        self.assertEqual(self.call("GET", "/api/projects", headers=bearer(self.token)).status_code, 429)


class SecretHygieneTest(ExposedCase):
    def test_token_is_in_no_response_and_no_log_line(self):
        wrong = secrets.token_urlsafe(32)
        self.call("GET", "/api/projects", headers=bearer(self.token))
        self.call("GET", "/api/projects", headers=bearer(wrong))
        self.call("GET", "/api/projects")
        self.call("GET", "/projects", headers={**session(self.token), "Accept": "text/html"})
        self.call("GET", "/login")
        self.call("POST", "/login", json={"token": self.token})
        self.call("POST", "/login", data={"token": self.token}, follow_redirects=False)
        self.call("POST", "/login", json={"token": wrong})
        self.call("POST", "/login", data={"token": wrong})
        self.call("POST", "/api/command", headers=bearer(self.token), json={"text": "status"})
        self.call("GET", f"/zzz/{self.token}", headers=bearer(self.token))  # a token typed into a URL
        self.call("GET", f"/api/projects?token={self.token}", headers=bearer(wrong))
        self.call("GET", "/projects", headers={"Accept": "text/html"})
        self.fail_n(10)
        self.call("GET", "/api/projects", headers=bearer(self.token))  # 429

        for response in self.seen:
            for where, blob in (("body", response.text), ("headers", str(dict(response.headers)))):
                self.assertNotIn(self.token, blob, f"{response.request.method} {response.url.path} {where}")

        log_text = (self.state / "web-auth.jsonl").read_text(encoding="utf-8")
        for secret in (self.token, wrong, cookie_for(self.token)):
            self.assertNotIn(secret, log_text)
        rows = self.log_rows()
        self.assertGreater(len(rows), 15)
        for row in rows:
            self.assertEqual(set(row), {"ts", "route", "result"})
            self.assertIn(row["result"], {"ok", "fail", "missing", "blocked", "malformed"})
        routes = {row["route"] for row in rows}
        self.assertIn("/api/projects", routes)
        self.assertIn("/login", routes)
        self.assertIn(web_auth.UNMATCHED_ROUTE, routes)
        self.assertTrue(all(r == web_auth.UNMATCHED_ROUTE or r.startswith("/") for r in routes))

    def test_log_records_each_outcome_and_the_file_is_private(self):
        self.call("GET", "/api/projects", headers=bearer(self.token))
        self.call("GET", "/api/projects", headers=bearer(secrets.token_urlsafe(32)))
        self.call("GET", "/api/projects")
        results = [(row["route"], row["result"]) for row in self.log_rows()]
        self.assertEqual(results, [("/api/projects", "ok"), ("/api/projects", "fail"), ("/api/projects", "missing")])
        self.assertEqual(stat.S_IMODE((self.state / "web-auth.jsonl").stat().st_mode), 0o600)

    def test_open_routes_are_not_logged(self):
        self.call("GET", "/login")
        self.call("GET", "/static/review.js")
        self.assertEqual(self.log_rows(), [])

    def test_login_page_never_echoes_the_submitted_token(self):
        wrong = secrets.token_urlsafe(32)
        response = self.call("POST", "/login", data={"token": wrong})
        self.assertNotIn(wrong, response.text)


class CommandEndpointTest(ExposedCase):
    def test_command_runs_and_returns_the_result_json(self):
        pause = self.call("POST", "/api/command", headers=bearer(self.token), json={"text": "pausar outlet_promo"})
        self.assertEqual(pause.status_code, 200)
        self.assertTrue(pause.json()["ok"])
        self.assertIn("outlet_promo", pause.json()["message"])
        self.assertTrue(projects_state.is_paused(self.state, "outlet_promo"))
        resume = self.call("POST", "/api/command", headers=session(self.token), json={"text": "retomar outlet_promo"})
        self.assertEqual(resume.status_code, 200)
        self.assertFalse(projects_state.is_paused(self.state, "outlet_promo"))
        with patch("projects.cli_update", return_value=0) as update:  # the real one commits to a git vault
            prio = self.call("POST", "/api/command", headers=bearer(self.token), json={"text": "priorizar outlet_promo P2"})
        self.assertEqual(prio.status_code, 200, prio.text)
        update.assert_called_once_with(self.vault, "outlet_promo", prioridade="P2")
        status = self.call("POST", "/api/command", headers=bearer(self.token), json={"text": "status"})
        self.assertTrue(status.json()["ok"])

    def test_bad_commands_are_400_with_ok_false(self):
        for text in ("", "dançar", "pausar slug_que_nao_existe", "priorizar outlet_promo P9", "aprovar s-inexistente"):
            response = self.call("POST", "/api/command", headers=bearer(self.token), json={"text": text})
            self.assertEqual(response.status_code, 400, text)
            self.assertFalse(response.json()["ok"])
            self.assertTrue(response.json()["message"])

    def test_missing_or_oversized_text_is_422(self):
        self.assertEqual(self.call("POST", "/api/command", headers=bearer(self.token), json={}).status_code, 422)
        long = self.call("POST", "/api/command", headers=bearer(self.token), json={"text": "x" * 501})
        self.assertEqual(long.status_code, 422)

    def test_dashboard_buttons_are_enabled_and_carry_their_command(self):
        snapshot = {"ts": __import__("datetime").datetime.now().isoformat(), "quota": {}, "projects": []}
        (self.state / "projects.json").write_text(json.dumps(snapshot), encoding="utf-8")
        page = self.call("GET", "/projects", headers=bearer(self.token))
        self.assertEqual(page.status_code, 200)
        self.assertIn('data-cmd="pausar outlet_promo"', page.text)
        self.assertIn("/api/command", page.text)
        self.assertNotIn("<button disabled", page.text)
        self.assertNotIn(self.token, page.text)


class StartupTest(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        root = Path(self._tmp.name)
        self.vault = make_vault(root / "vault")
        self.state = root / "state"
        self.state.mkdir()

    def run_exposed(self, env: dict, **kw):
        err = io.StringIO()
        base = {k: v for k, v in os.environ.items() if k not in ("SB_WEB_TOKEN", "SB_TEST_TOKEN")}
        with patch.dict(os.environ, {**base, **env}, clear=True), patch("uvicorn.Server.run") as run, \
                patch("uvicorn.Config") as config, redirect_stderr(err):
            code = web_service.run_server(self.vault, self.state, open_browser=False, exposed=True, **kw)
        return code, err.getvalue(), run, config

    def test_create_app_refuses_a_missing_empty_or_short_token(self):
        short = secrets.token_urlsafe(8)
        for token in (None, "", "   ", short, "x" * 31):
            with self.assertRaises(web_auth.AuthConfigError) as caught:
                web_service.create_app(self.vault, self.state, token=token, exposed=True)
            if token:
                self.assertNotIn(token, str(caught.exception))
        web_service.create_app(self.vault, self.state, token="x" * 32, exposed=True)

    def test_run_server_refuses_to_start_without_a_valid_token(self):
        short = secrets.token_urlsafe(8)
        for env in ({}, {"SB_WEB_TOKEN": ""}, {"SB_WEB_TOKEN": "   \n"}, {"SB_WEB_TOKEN": short}):
            code, err, run, _ = self.run_exposed(env)
            self.assertEqual(code, 2, env)
            self.assertIn("Partida recusada", err)
            self.assertIn("$SB_WEB_TOKEN", err)
            self.assertNotIn(short, err)
            run.assert_not_called()

    def test_run_server_starts_with_a_32_char_token_from_the_default_variable(self):
        code, err, run, config = self.run_exposed({"SB_WEB_TOKEN": secrets.token_urlsafe(32)})
        self.assertEqual((code, err), (0, ""))
        run.assert_called_once()
        self.assertIsNotNone(config.call_args.kwargs["app"].state.auth_gate)

    def test_token_variable_name_comes_from_the_manifest(self):
        manifest = self.vault / "00_META/projects/manifest.yaml"
        manifest.write_text(manifest.read_text(encoding="utf-8").replace(
            "port: 8765", "port: 8765\n  token_env: SB_TEST_TOKEN"), encoding="utf-8")
        refused, err, run, _ = self.run_exposed({"SB_WEB_TOKEN": secrets.token_urlsafe(32)})
        self.assertEqual(refused, 2)
        self.assertIn("$SB_TEST_TOKEN", err)
        run.assert_not_called()
        token = secrets.token_urlsafe(32)
        code, _, run, config = self.run_exposed({"SB_TEST_TOKEN": token})
        self.assertEqual(code, 0)
        client = TestClient(config.call_args.kwargs["app"], base_url=LOOPBACK)
        self.assertEqual(client.get("/api/projects", headers=bearer(token)).status_code, 200)

    def test_invalid_token_variable_name_in_the_manifest_is_refused(self):
        manifest = self.vault / "00_META/projects/manifest.yaml"
        manifest.write_text(manifest.read_text(encoding="utf-8").replace(
            "port: 8765", "port: 8765\n  token_env: 'bad name; rm'"), encoding="utf-8")
        code, err, run, _ = self.run_exposed({"SB_WEB_TOKEN": secrets.token_urlsafe(32)})
        self.assertEqual(code, 2)
        self.assertIn("token_env", err)
        run.assert_not_called()

    def test_allow_host_without_exposed_is_refused(self):
        """A non-loopback Host with no token would hand the write routes to the whole tailnet."""
        err = io.StringIO()
        with patch("uvicorn.Server.run") as run, redirect_stderr(err):
            code = web_service.run_server(self.vault, self.state, open_browser=False, allow_hosts=[MAGIC])
        self.assertEqual(code, 2)
        self.assertIn("--allow-host exige --exposed", err.getvalue())
        run.assert_not_called()

    def test_exposed_refuses_a_non_loopback_bind(self):
        for host in ("0.0.0.0", "192.168.0.10", ""):
            code, err, run, _ = self.run_exposed({"SB_WEB_TOKEN": secrets.token_urlsafe(32)}, host=host)
            self.assertEqual(code, 2, host)
            self.assertIn("loopback", err)
            run.assert_not_called()

    def test_allow_host_extends_the_accepted_hosts_and_is_validated(self):
        token = secrets.token_urlsafe(32)
        code, _, _, config = self.run_exposed({"SB_WEB_TOKEN": token}, allow_hosts=["PC.Tailnet.ts.net"])
        self.assertEqual(code, 0)
        app = config.call_args.kwargs["app"]
        self.assertEqual(TestClient(app, base_url=f"https://{MAGIC}").get("/api/projects", headers=bearer(token)
                                                                          ).status_code, 200)
        self.assertEqual(TestClient(app, base_url="http://other.example").get("/api/projects", headers=bearer(token)
                                                                              ).status_code, 403)
        self.assertEqual(TestClient(app, base_url="http://testserver").get("/api/projects", headers=bearer(token)
                                                                           ).status_code, 403)
        for bad in ("https://pc.ts.net", "pc.ts.net:8765", "pc.ts.net/x", "*", ""):
            code, err, run, _ = self.run_exposed({"SB_WEB_TOKEN": token}, allow_hosts=[bad])
            self.assertEqual(code, 2, bad)
            self.assertIn("--allow-host", err)
            run.assert_not_called()


class NotExposedTest(unittest.TestCase):
    """Without --exposed nothing changes: no token, no /login, same routes."""

    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        root = Path(self._tmp.name)
        self.vault = make_vault(root / "vault")
        self.state = root / "state"
        self.state.mkdir()

    def test_routes_work_without_a_token(self):
        client = TestClient(web_service.create_app(self.vault, self.state))
        for url in ("/api/projects", "/projects", "/api/stats", "/api/filters", "/", "/api/candidates"):
            self.assertEqual(client.get(url).status_code, 200, url)
        self.assertEqual(client.post("/api/undo", json={}).status_code, 404)  # empty stack: reached the handler
        command = client.post("/api/command", json={"text": "status"})
        self.assertEqual(command.status_code, 200)
        self.assertTrue(command.json()["ok"])

    def test_a_token_is_ignored_and_login_does_not_exist(self):
        app = web_service.create_app(self.vault, self.state, token=secrets.token_urlsafe(32))
        self.assertIsNone(app.state.auth_gate)
        client = TestClient(app)
        self.assertEqual(client.get("/api/projects").status_code, 200)
        self.assertEqual(client.get("/login").status_code, 404)
        self.assertEqual(client.post("/login", json={"token": "x"}).status_code, 404)
        self.assertFalse((self.state / "web-auth.jsonl").exists())

    def test_host_and_origin_guards_unchanged(self):
        app = web_service.create_app(self.vault, self.state)
        self.assertEqual(TestClient(app, base_url="http://evil.example").get("/api/projects").status_code, 403)
        origin = TestClient(app).post("/api/command", headers={"Origin": "https://evil.example"}, json={"text": "status"})
        self.assertEqual(origin.status_code, 403)


if __name__ == "__main__":
    unittest.main()
