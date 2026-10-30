"""Tests of the review web UI (Sprint 2): python3 -m unittest test_web_ui -v

Same sandbox as test_web_service (real git vault, throwaway state dir, TestClient). The keyboard JS cannot run
here; its contract is checked on the served text, and the browser smoke test lives in dev_sandbox.py.
"""
import ast
import datetime as dt
import json
import re
import unittest
from concurrent.futures import ThreadPoolExecutor
from html import unescape
from pathlib import Path

from starlette.testclient import TestClient

import candidates
import web_service
from test_web_service import BODY, FAKE, JIRA, SERVICE, WebFixture

ROOT = Path(__file__).resolve().parents[3]
XSS = "<script>alert(1)</script>"
KEYS = {"s", "a", "d", "p", "z", "j", "k", "e"}


def shortcuts_in(html):
    return json.loads(re.search(r'<script id="shortcuts" type="application/json">(.*?)</script>', html, re.S).group(1))


class IndexTest(WebFixture):
    def test_index_is_html_with_the_eight_shortcuts_and_a_button_per_key(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.headers["content-type"].startswith("text/html"))
        self.assertEqual(shortcuts_in(resp.text), web_service.SHORTCUTS)
        self.assertEqual(set(web_service.SHORTCUTS), KEYS)
        self.assertEqual(set(re.findall(r'data-key="(\w)"', resp.text)), KEYS)
        self.assertIn('/static/review.js', resp.text)
        self.assertIn('id="toasts"', resp.text)

    def test_empty_queue_shows_the_empty_state(self):
        text = self.client.get("/").text
        self.assertIn('data-empty="true"', text)
        self.assertIn("0 pendentes", text)

    def test_first_candidate_is_rendered_on_the_server(self):
        first = self.add(title="Armadilha primeira distinta", days_left=3)
        self.add(title="Armadilha segunda distinta", days_left=9)
        text = self.client.get("/").text
        self.assertIn(f'data-id="{first}"', text)
        self.assertIn("2 pendentes", text)
        self.assertIn("Armadilha primeira distinta", text)

    def test_filters_reach_the_page_and_the_js_query(self):
        self.add(title="Armadilha do x distinta", project="projeto_x")
        other = self.add(title="Padrão do y distinto", project="projeto_y", kind="pattern")
        text = self.client.get("/", params={"project": "projeto_y"}).text
        self.assertIn(f'data-id="{other}"', text)
        self.assertIn("1 pendentes", text)
        self.assertIn("projeto_y", re.search(r"data-query='([^']*)'", text).group(1))

    def test_hostile_filter_value_cannot_break_out_of_the_attribute(self):
        text = self.client.get("/", params={"project": "x'\"><script>alert(1)</script>"}).text
        self.assertNotIn("<script>alert(1)</script>", text)

    def test_filter_dropdowns_render_projects_and_kinds(self):
        self.add(title="Item Alpha", project="projeto_alpha", kind="trap")
        self.add(title="Item Beta", project="projeto_beta", kind="decision")
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        html = resp.text
        self.assertIn('id="filter-project"', html)
        self.assertIn('id="filter-kind"', html)
        self.assertIn('aria-label="Filtrar por projeto"', html)
        self.assertIn('aria-label="Filtrar por tipo"', html)
        self.assertIn('Todos os projetos', html)
        self.assertIn('Todos os tipos', html)
        self.assertIn('<option value="projeto_alpha"', html)
        self.assertIn('<option value="projeto_beta"', html)
        self.assertIn('<option value="trap"', html)
        self.assertIn('<option value="decision"', html)

    def test_filter_dropdowns_preselect_active_query_values(self):
        self.add(title="Item Alpha", project="projeto_alpha", kind="trap")
        resp = self.client.get("/", params={"project": "projeto_alpha", "kind": "trap"})
        self.assertEqual(resp.status_code, 200)
        html = resp.text
        self.assertIn('<option value="projeto_alpha" selected>', html)
        self.assertIn('<option value="trap" selected>', html)


class FragmentTest(WebFixture):
    def frag(self, **params):
        return self.client.get("/ui/candidate", params=params)

    def test_fields_of_the_card(self):
        cid = self.add(summary="o resumo do candidato")
        resp = self.frag()
        self.assertEqual(resp.status_code, 200)
        text = resp.text
        for expected in (f'data-id="{cid}"', 'data-offset="0"', 'data-total="1"', 'data-kind="trap"', "projeto_x",
                         "30 dias restantes", "Calibração de Câmera Estéreo", "o resumo do candidato",
                         "Nada falhou no teste.", "Proposta automática: SAVE", f"ID: {cid}"):
            self.assertIn(expected, text)

    def test_no_draft_shows_the_notice(self):
        self.add(body=None)
        text = self.frag().text
        self.assertIn("será gerado a partir do resumo", text)
        self.assertNotIn("<pre", text)

    def test_similar_notes_with_percent_and_the_absorb_target(self):
        self.add(title="Importar Issues no Jira por REST", kind="concept", body=None)
        text = self.frag().text
        self.assertIn(JIRA, text)
        self.assertRegex(text, r"\d+% cobertura")
        self.assertIn(f'data-absorb-target="{JIRA}"', text)
        self.assertIn("Proposta automática: ABSORB", text)

    def test_no_similar_note_means_no_absorb_target(self):
        self.add()
        text = self.frag().text
        self.assertIn('data-absorb-target=""', text)
        self.assertIn("Nenhuma nota similar", text)

    def test_offset_id_and_order_match_the_api(self):
        ids = [self.add(title=f"Armadilha {n} distinta", days_left=d) for n, d in ((1, 3), (2, 9), (3, 20))]
        self.assertEqual(self.pending_ids(), ids)
        for n, cid in enumerate(ids):
            self.assertIn(f'data-id="{cid}"', self.frag(offset=n).text)
            self.assertIn(f'data-offset="{n}"', self.frag(id=cid).text)
        self.assertIn('data-total="3"', self.frag(id=ids[2]).text)

    def test_filters_apply(self):
        self.add(title="Armadilha x distinta", project="projeto_x")
        other = self.add(title="Padrão y distinto", project="projeto_y", kind="pattern")
        self.assertIn(f'data-id="{other}"', self.frag(kind="pattern").text)
        self.assertIn('data-total="1"', self.frag(project="projeto_y").text)

    def test_empty_queue_is_200_with_the_empty_fragment(self):
        resp = self.frag()
        self.assertEqual(resp.status_code, 200)
        self.assertIn('data-empty="true"', resp.text)

    def test_bad_offset_or_id_is_404_with_an_html_fragment(self):
        self.add()
        for params in ({"offset": 5}, {"id": "naoexiste"}):
            with self.subTest(**params):
                resp = self.frag(**params)
                self.assertEqual(resp.status_code, 404)
                self.assertTrue(resp.headers["content-type"].startswith("text/html"))
                self.assertIn('data-error="true"', resp.text)

    def test_invalid_param_is_422_html(self):
        for params in ({"offset": -1}, {"offset": "x"}):
            with self.subTest(**params):
                resp = self.frag(**params)
                self.assertEqual(resp.status_code, 422)
                self.assertIn('data-error="true"', resp.text)

    def test_decided_candidate_is_not_pending(self):
        cid = self.add()
        self.decide(cid, "drop", reason="x")
        self.assertEqual(self.frag(id=cid).status_code, 404)


class XssTest(WebFixture):
    def test_candidate_and_vault_text_is_escaped(self):
        title = f"Armadilha {XSS} distinta"
        self.add(title=title, summary=f"resumo {XSS}", body=f"{XSS}\n\n## O que NÃO funcionou\n- x\n", project=f"p{XSS}"[:30])
        for text in (self.client.get("/ui/candidate").text, self.client.get("/").text):
            self.assertNotIn(XSS, text)
            self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", text)

    def test_similar_note_title_is_escaped(self):
        hostile = "<b onmouseover=alert(1)>"  # no slash: the title is also a file name
        rel = self.write(f"Importar Issues no Jira {hostile}", tags="jira, rest", provenance="manual", confidence="medium")
        import subprocess
        from test_vault_sync import GEN, git
        subprocess.run(["python3", str(GEN), "--vault-path", str(self.vault)], check=True, capture_output=True)
        git(self.vault, "add", "-A")
        git(self.vault, "commit", "-q", "-m", "x")
        self.add(title="Importar Issues no Jira", kind="concept", body=None)
        text = self.client.get("/ui/candidate").text
        self.assertIn(rel, unescape(text))  # the hostile note is listed as a similar note
        self.assertNotIn(hostile, text)
        self.assertIn("&lt;b onmouseover=alert(1)&gt;", text)

    def test_error_fragment_escapes_the_id(self):
        resp = self.client.get("/ui/candidate", params={"id": XSS})
        self.assertEqual(resp.status_code, 404)
        self.assertNotIn(XSS, resp.text)

    def test_templates_never_use_safe_except_the_static_shortcut_map(self):
        for path in (SERVICE.parent / "web" / "templates").glob("*.html"):
            uses = re.findall(r"\|\s*safe", path.read_text(encoding="utf-8"))
            self.assertEqual(len(uses), 1 if path.name == "index.html" else 0, path.name)


class ShortcutJsTest(WebFixture):
    def setUp(self):
        super().setUp()
        resp = self.client.get("/static/review.js")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("javascript", resp.headers["content-type"])
        self.js = resp.text

    def test_the_js_reads_the_served_map_and_posts_to_the_api(self):
        self.assertIn('getElementById("shortcuts")', self.js)
        for needle in ('"/api/decide"', '"/api/undo"', "/ui/candidate?", "/api/stats"):
            self.assertIn(needle, self.js)
        for action in ("save", "drop", "skip", "absorb", "undo", "next", "prev", "edit"):
            self.assertIn(f'"{action}"', self.js)

    def test_guards_are_present(self):
        for needle in ("event.repeat", "ctrlKey", "metaKey", "altKey", "INPUT", "TEXTAREA", "SELECT", "isContentEditable",
                       "dialog", "inflight", "preventDefault", "document.body.focus", "toLowerCase"):
            self.assertIn(needle, self.js)

    def test_toast_kinds_are_styled(self):
        page = self.client.get("/").text
        for kind in ("success", "info", "error"):
            self.assertIn(f"toast-{kind}", page)
            self.assertIn(f'"{kind}"', self.js)

    def test_edit_button_is_enabled(self):
        self.assertNotRegex(self.client.get("/").text, r'data-key="e" disabled')

    def test_js_has_filter_change_handlers_and_url_sync(self):
        self.assertIn('$("filter-project")', self.js)
        self.assertIn('$("filter-kind")', self.js)
        self.assertIn('onFilterChange', self.js)
        self.assertIn('history.replaceState', self.js)

    def test_no_external_script_besides_the_pinned_tailwind_cdn(self):
        srcs = re.findall(r'<script[^>]+src="([^"]+)"', self.client.get("/").text)
        self.assertEqual(sorted(srcs), ["/static/review.js", "https://cdn.tailwindcss.com/3.4.17"])


class StatsTest(WebFixture):
    def log_row(self, days_ago, outcome):
        ts = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")
        with (self.state / "review.jsonl").open("a", encoding="utf-8") as out:
            out.write(json.dumps({"ts": ts, "id": f"x{days_ago}{outcome}", "outcome": outcome}) + "\n")

    def test_empty(self):
        self.assertEqual(self.client.get("/api/stats").json(), {"pending": 0, "today_applied": 0, "today_rejected": 0})

    def test_counts_only_todays_rows_and_skips_garbage(self):
        self.log_row(0, "applied")
        self.log_row(0, "applied")
        self.log_row(0, "rejected")
        self.log_row(0, "refused")
        self.log_row(2, "applied")
        with (self.state / "review.jsonl").open("a", encoding="utf-8") as out:
            out.write("not json\n[1]\n")
        self.add()
        self.assertEqual(self.client.get("/api/stats").json(), {"pending": 1, "today_applied": 2, "today_rejected": 1})

    def test_decisions_move_the_counters(self):
        a, b = self.add(title="Armadilha a distinta", days_left=3), self.add(title="Armadilha b distinta", days_left=9)
        self.decide(a, "drop", reason="x")
        self.decide(b, "save")
        self.assertEqual(self.client.get("/api/stats").json(), {"pending": 0, "today_applied": 1, "today_rejected": 1})


class AbsorbDefaultTest(WebFixture):
    def setUp(self):
        super().setUp()
        self.cid = self.add(title="Importar Issues no Jira por REST", kind="concept", body=None,
                            summary="detalhe novo do candidato")

    def test_absorb_without_note_or_body_composes_the_update_on_the_top_match(self):
        before = (self.vault / JIRA).read_text(encoding="utf-8")
        resp = self.decide(self.cid, "absorb")
        self.assertEqual(resp.status_code, 200, resp.text)
        after = (self.vault / JIRA).read_text(encoding="utf-8")
        today = dt.date.today().isoformat()
        self.assertIn("seen_in: [projeto_x]", after)
        self.assertIn(f"verified: {today} via revisão web, não reproduzido", after)
        self.assertTrue(after.rstrip().endswith(f"- {today} (projeto_x): detalhe novo do candidato"))
        self.assertTrue(after.startswith(before.split("\n---\n")[0].split("\nconfidence")[0]))
        self.assertEqual(resp.json()["sha"], self.head())
        self.assertEqual(self.git_status(), "")
        self.assertEqual(self.review_rows()[-1]["verdict"], "absorb")

    def test_undo_restores_the_note(self):
        before = (self.vault / JIRA).read_text(encoding="utf-8")
        self.decide(self.cid, "absorb")
        self.assertEqual(self.undo().status_code, 200)
        self.assertEqual((self.vault / JIRA).read_text(encoding="utf-8"), before)
        self.assertEqual(self.pending_ids(), [self.cid])

    def test_explicit_note_also_composes_when_there_is_no_body(self):
        self.assertEqual(self.decide(self.cid, "absorb", note=JIRA).status_code, 200)

    def test_existing_seen_in_and_verified_are_updated_not_duplicated(self):
        path = self.vault / JIRA
        path.write_text(path.read_text(encoding="utf-8").replace(
            "confidence: medium\n", "confidence: medium\nseen_in: [outro]\nverified: 2026-01-01 antes\n"), encoding="utf-8")
        import subprocess
        subprocess.run(["git", "-C", str(self.vault), "commit", "-qam", "docs: seen_in"], check=True)
        self.assertEqual(self.decide(self.cid, "absorb").status_code, 200)
        text = path.read_text(encoding="utf-8")
        self.assertEqual(text.count("seen_in:"), 1)
        self.assertEqual(text.count("verified:"), 1)
        self.assertIn("seen_in: [outro, projeto_x]", text)

    def test_no_similar_note_and_no_note_is_400(self):
        cid = self.add(title="Algo sem nenhuma similar zzyx", body=None)
        self.assertError(self.decide(cid, "absorb"), 400)

    def test_bad_explicit_targets_stay_400_or_404(self):
        for note in ("../x.md", "/etc/passwd", "x.txt"):
            self.assertError(self.decide(self.cid, "absorb", note=note), 400)
        self.assertError(self.decide(self.cid, "absorb", note="20_Permanent_Notes/Inexistente.md"), 404)

    def test_secret_in_the_candidate_summary_is_refused_with_nothing_written(self):
        before = (self.vault / JIRA).read_text(encoding="utf-8")
        head = self.head()
        # the queue refuses secrets on entry, so inject one into the queued line the way a hand edit would
        path = candidates.queue_path(self.state)
        rows = [json.loads(line) for line in candidates.read_lines(path)]
        for row in rows:
            row["summary"] = f"token {FAKE}"
        candidates.replace_file(path, ("\n".join(json.dumps(r) for r in rows) + "\n").encode("utf-8"))
        resp = self.decide(self.cid, "absorb")
        self.assertEqual(resp.status_code, 422, resp.text)
        self.assertEqual((self.vault / JIRA).read_text(encoding="utf-8"), before)
        self.assertEqual(self.head(), head)
        self.assertNotIn(FAKE, resp.text)


class GuardTest(WebFixture):
    def test_foreign_host_is_403_in_the_unified_shape(self):
        for path in ("/", "/api/candidates", "/ui/candidate", "/api/stats", "/static/review.js"):
            with self.subTest(path=path):
                body = self.assertError(self.client.get(path, headers={"host": "evil.example"}), 403)
                self.assertEqual(body["detail"], "Forbidden host/origin")
                self.assertTrue(body["errors"])

    def test_allowed_hosts_with_ports_and_brackets(self):
        for host in ("127.0.0.1:8765", "localhost:8000", "localhost", "[::1]:8000", "testserver"):
            with self.subTest(host=host):
                self.assertEqual(self.client.get("/api/stats", headers={"host": host}).status_code, 200)

    def test_post_with_a_foreign_origin_is_403_and_changes_nothing(self):
        cid = self.add()
        resp = self.client.post("/api/decide", json={"id": cid, "action": "drop", "reason": "x"},
                                headers={"origin": "http://evil.example"})
        self.assertError(resp, 403)
        self.assertEqual(self.pending_ids(), [cid])
        self.assertError(self.client.post("/api/undo", json={}, headers={"origin": "http://evil.example"}), 403)

    def test_post_with_a_matching_or_absent_origin_passes(self):
        cid = self.add()
        resp = self.client.post("/api/decide", json={"id": cid, "action": "skip"}, headers={"origin": "http://testserver"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.decide(cid, "skip").status_code, 200)

    def test_get_ignores_origin(self):
        self.assertEqual(self.client.get("/api/stats", headers={"origin": "http://evil.example"}).status_code, 200)

    def test_allowed_hosts_is_injectable(self):
        app = web_service.create_app(self.vault, self.state, allowed_hosts={"review.local"})
        client = TestClient(app)
        self.assertEqual(client.get("/api/stats").status_code, 403)
        self.assertEqual(client.get("/api/stats", headers={"host": "review.local"}).status_code, 200)


class UiConcurrencyTest(WebFixture):
    def test_fragments_during_decisions_never_error(self):
        ids = [self.add(title=f"Armadilha ui {n} distinta", body=None) for n in range(4)]
        with ThreadPoolExecutor(max_workers=6) as pool:
            writes = [pool.submit(self.decide, cid, "drop", reason="x") for cid in ids]
            reads = [pool.submit(self.client.get, "/ui/candidate") for _ in range(4)]
            stats = [pool.submit(self.client.get, "/api/stats") for _ in range(2)]
            codes = [f.result().status_code for f in writes + reads + stats]
        self.assertEqual(codes, [200] * 10)


class InvariantTest(unittest.TestCase):
    def test_i1_still_no_direct_writes(self):
        tree = ast.parse(SERVICE.read_text(encoding="utf-8"))
        bad = [n.lineno for n in ast.walk(tree) if isinstance(n, ast.Call) and (
            (isinstance(n.func, ast.Attribute) and n.func.attr in ("write_text", "write_bytes"))
            or (isinstance(n.func, ast.Name) and n.func.id == "open"))]
        self.assertEqual(bad, [])

    def test_i3_no_node_build_artifacts_anywhere_in_the_repo(self):
        found = []
        for name in ("package.json", "package-lock.json", "node_modules", "yarn.lock", "pnpm-lock.yaml", "webpack.config.js"):
            found += [p for p in ROOT.rglob(name) if ".git" not in p.parts]
        self.assertEqual(found, [])

    def test_i3_imports_stay_within_the_stack(self):
        import sys
        tree = ast.parse(SERVICE.read_text(encoding="utf-8"))
        roots = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                roots.add((node.module or "").split(".")[0])
        allowed = {"fastapi", "pydantic", "starlette", "uvicorn", "jinja2", "candidates", "review", "vault_sync", "lib"}
        self.assertEqual({r for r in roots if r not in allowed and r not in sys.stdlib_module_names}, set())


if __name__ == "__main__":
    unittest.main()
