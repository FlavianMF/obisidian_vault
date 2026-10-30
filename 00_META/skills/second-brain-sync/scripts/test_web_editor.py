"""Tests of the editor drawer, the drop modal and dry_run (Sprint 3): python3 -m unittest test_web_editor -v

Same sandbox as test_web_service. The modal JS cannot run here: its contract is checked on the served text, and the
browser smoke test uses dev_sandbox.py.
"""
import datetime as dt
import re
import subprocess
import unittest
from html import unescape

import candidates
from test_web_service import BODY, FAKE, JIRA, WebFixture

HOSTILE_BODY = "</textarea><script>alert(1)</script>"


def textarea(html):
    return unescape(re.search(r'<textarea[^>]*id="ed-body"[^>]*>(.*?)</textarea>', html, re.S).group(1))


def field(html, name):
    return unescape(re.search(rf'id="ed-{name}"[^>]*value="([^"]*)"', html).group(1))


class EditorFragmentTest(WebFixture):
    def editor(self, **params):
        return self.client.get("/ui/editor", params=params)

    def test_prefill_for_a_save(self):
        cid = self.add()
        resp = self.editor(id=cid)
        self.assertEqual(resp.status_code, 200)
        text = resp.text
        self.assertEqual(field(text, "title"), "Calibração de Câmera Estéreo")
        self.assertEqual(field(text, "tags"), "trap, projeto_x")
        self.assertEqual(textarea(text), BODY)
        self.assertRegex(text, r'value="save" checked')
        self.assertIn(f'data-id="{cid}"', text)
        self.assertIn('role="dialog"', text)
        self.assertIn('aria-modal="true"', text)
        self.assertIn('aria-labelledby="ed-heading"', text)
        self.assertIn('role="alert"', text)

    def test_no_draft_gets_the_scaffold_for_every_kind(self):
        for kind in candidates.KINDS:
            with self.subTest(kind=kind):
                cid = self.add(kind=kind, title=f"Sem rascunho {kind} distinto", body=None, summary="resumo base")
                body = textarea(self.editor(id=cid).text)
                self.assertEqual(body, "## Contexto\nresumo base\n\n## O que NÃO funcionou\n- A preencher\n")

    def test_a_blank_draft_is_replaced_by_the_scaffold(self):
        cid = self.add(body="   \n")
        self.assertIn("## O que NÃO funcionou", textarea(self.editor(id=cid).text))

    def test_default_mode_is_absorb_when_the_ranker_proposes_it(self):
        cid = self.add(title="Importar Issues no Jira por REST", kind="concept", body=None)
        text = self.editor(id=cid).text
        self.assertRegex(text, r'value="absorb" checked')
        self.assertIn(f'<option value="{JIRA}" selected>', text)
        body = textarea(text)
        self.assertTrue(body.startswith("---\n"))
        self.assertIn("seen_in: [projeto_x]", body)
        self.assertIn(f"verified: {dt.date.today().isoformat()} via revisão web", body)

    def test_explicit_mode_and_note(self):
        cid = self.add(title="Importar Issues no Jira por REST", kind="concept", body=None)
        self.assertRegex(self.editor(id=cid, mode="save").text, r'value="save" checked')
        self.assertEqual(textarea(self.editor(id=cid, mode="save").text)[:10], "## Context")
        self.assertIn("seen_in", textarea(self.editor(id=cid, mode="absorb", note=JIRA).text))

    def test_absorb_uses_a_draft_only_when_it_is_a_whole_note(self):
        whole = (self.vault / JIRA).read_text(encoding="utf-8").replace(
            "confidence: medium\n", "confidence: medium\nseen_in: [projeto_x]\n") + "\nlinha do rascunho\n"
        cid = self.add(title="Importar Issues no Jira por REST", kind="concept", body=whole)
        self.assertEqual(textarea(self.editor(id=cid, mode="absorb").text), whole)

    def test_absorb_ignores_a_body_only_draft_and_composes_the_note(self):
        cid = self.add(title="Importar Issues no Jira por REST", kind="concept", body="texto do rascunho\n")
        body = textarea(self.editor(id=cid, mode="absorb").text)
        self.assertTrue(body.startswith("---\n"))
        self.assertNotIn("texto do rascunho", body)
        self.assertEqual(self.post_absorb(cid).status_code, 200)

    def post_absorb(self, cid):
        return self.client.post("/api/decide", json={"id": cid, "action": "absorb", "note": JIRA})

    def test_errors_are_html_fragments(self):
        cid = self.add()
        cases = [({"id": "naoexiste"}, 404), ({"id": cid, "mode": "merge"}, 422), ({"id": cid, "mode": "absorb"}, 404),
                 ({"id": cid, "mode": "absorb", "note": "20_Permanent_Notes/Nada.md"}, 404),
                 ({"id": cid, "mode": "absorb", "note": "../x.md"}, 404), ({"id": cid, "mode": "absorb", "note": "/etc/passwd"}, 404),
                 ({}, 422)]
        for params, code in cases:
            with self.subTest(**params):
                resp = self.editor(**params)
                self.assertEqual(resp.status_code, code)
                self.assertTrue(resp.headers["content-type"].startswith("text/html"))
                self.assertIn('data-error="true"', resp.text)

    def test_decided_candidate_has_no_editor(self):
        cid = self.add()
        self.decide(cid, "drop", reason="x")
        self.assertEqual(self.editor(id=cid).status_code, 404)

    def test_hostile_text_is_escaped(self):
        cid = self.add(title=f"Armadilha <b>negrito</b> distinta", summary=f"resumo {HOSTILE_BODY}",
                       body=f"{HOSTILE_BODY}\n\n## O que NÃO funcionou\n- x\n", project="p<i>")
        text = self.editor(id=cid).text
        self.assertNotIn("<script>alert(1)</script>", text)
        self.assertNotIn("<b>negrito</b>", text)
        self.assertEqual(text.count("</textarea>"), 1)
        self.assertIn(HOSTILE_BODY, textarea(text))  # it survives as text, not as markup

    def test_hostile_note_name_in_the_select_is_escaped(self):
        hostile = "<b onmouseover=alert(1)>"
        self.write(f"Importar Issues no Jira {hostile}", tags="jira, rest", provenance="manual", confidence="medium")
        from test_vault_sync import GEN, git
        subprocess.run(["python3", str(GEN), "--vault-path", str(self.vault)], check=True, capture_output=True)
        git(self.vault, "add", "-A")
        git(self.vault, "commit", "-q", "-m", "x")
        cid = self.add(title="Importar Issues no Jira", kind="concept", body=None)
        text = self.editor(id=cid, mode="save").text
        self.assertNotIn(hostile, text)
        self.assertIn("&lt;b onmouseover=alert(1)&gt;", text)


class DryRunTest(WebFixture):
    def post(self, cid, action, **kw):
        return self.client.post("/api/decide", json={"id": cid, "action": action, **kw})

    def state_listing(self):
        return sorted(str(p.relative_to(self.state)) for p in self.state.rglob("*"))

    def snapshot(self):
        queue = candidates.queue_path(self.state)
        log = self.state / "review.jsonl"
        return (self.head(), self.git_status(), self.state_listing(),
                queue.read_bytes() if queue.exists() else None, log.read_bytes() if log.exists() else None)

    def assertNoEffect(self, cid, before):
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.app.state.undo_stack, [])
        self.assertEqual(self.app.state.skipped_ids, set())
        self.assertError(self.undo(), 404)
        self.assertIn(cid, self.pending_ids())

    def assertParity(self, cid, action, **kw):
        dry = self.post(cid, action, dry_run=True, **kw)
        real = self.post(cid, action, **kw)
        self.assertGreaterEqual(real.status_code, 400, real.text)
        self.assertEqual((dry.status_code, dry.json()), (real.status_code, real.json()))
        return dry

    def test_valid_save_has_no_effect_and_the_real_run_then_succeeds(self):
        cid = self.add()
        before = self.snapshot()
        resp = self.post(cid, "save", dry_run=True)
        self.assertEqual(resp.status_code, 200, resp.text)
        body = resp.json()
        self.assertEqual((body["success"], body["dry_run"], body["sha"], body["message"]), (True, True, None, "valid"))
        self.assertNoEffect(cid, before)
        self.assertFalse((self.vault / "20_Permanent_Notes/Calibração de Câmera Estéreo.md").exists())
        self.assertEqual(self.post(cid, "save").status_code, 200)

    def test_valid_absorb_has_no_effect(self):
        cid = self.add(title="Importar Issues no Jira por REST", kind="concept", body=None)
        before = self.snapshot()
        original = (self.vault / JIRA).read_text(encoding="utf-8")
        for kw in ({}, {"note": JIRA}, {"note": JIRA, "body": self.absorb_text()}):
            with self.subTest(**kw):
                resp = self.post(cid, "absorb", dry_run=True, **kw)
                self.assertEqual((resp.status_code, resp.json()["dry_run"]), (200, True), resp.text)
                self.assertNoEffect(cid, before)
        self.assertEqual((self.vault / JIRA).read_text(encoding="utf-8"), original)

    def test_valid_drop_and_skip_have_no_effect(self):
        cid = self.add()
        before = self.snapshot()
        for action, kw in (("drop", {"reason": "motivo"}), ("skip", {})):
            with self.subTest(action=action):
                resp = self.post(cid, action, dry_run=True, **kw)
                self.assertEqual((resp.status_code, resp.json()["dry_run"], resp.json()["sha"]), (200, True, None))
                self.assertNoEffect(cid, before)
        self.assertIsNotNone(candidates.read_draft(self.state, cid))

    def test_dry_run_with_a_body_leaves_no_temp_file_behind(self):
        cid = self.add()
        self.post(cid, "save", dry_run=True, body=BODY)
        self.assertFalse((self.state / "tmp_decisions").exists())

    def test_save_errors_match_the_real_run(self):
        cid = self.add(body=None)
        cases = {
            "secret in title": {"title": f"Token {FAKE}"},
            "secret in body": {"body": BODY + FAKE},
            "no negative section": {"body": "só contexto"},
            "unusable title": {"title": "***"},
            "bad tags": {"tags": ["Maiúscula"]},
            "frontmatter in the body": {"body": "---\ntitle: x\n---\n\n" + BODY},
        }
        for label, kw in cases.items():
            with self.subTest(label):
                self.assertParity(cid, "save", **kw)
        dry = self.post(cid, "save", dry_run=True, title=f"Token {FAKE}")
        self.assertEqual(dry.json()["detail"], "Secret detected")
        self.assertNotIn(FAKE, dry.text)

    def test_save_conflict_and_similarity_match_the_real_run(self):
        taken = self.add(title="Importar Issues no Jira por REST", kind="concept", body="texto")
        self.assertEqual(self.assertParity(taken, "save").status_code, 409)
        near = self.add(title="Importar issues no Jira via REST", kind="concept", body="Texto novo.")
        dry = self.assertParity(near, "save")
        self.assertEqual(dry.status_code, 422)
        self.assertIn("new_because", dry.json()["detail"])
        self.assertEqual(self.post(near, "save", dry_run=True, new_because="cobre CSV grande").status_code, 200)

    def test_absorb_errors_match_the_real_run(self):
        cid = self.add(title="Importar Issues no Jira por REST", kind="concept", body=None)
        original = (self.vault / JIRA).read_text(encoding="utf-8")
        rewritten = ("---\ntitle: Importar Issues no Jira por REST\ntype: pattern\ntags: [a]\ncreated: 2026-10-14\n"
                     "seen_in: [projeto_x]\nverified: 2026-10-22 via teste\n---\n\nTexto todo novo.\n")
        cases = {
            "traversal": {"note": "../x.md", "body": self.absorb_text()},
            "not in HEAD": {"note": "20_Permanent_Notes/Nada.md", "body": self.absorb_text()},
            "no frontmatter": {"note": JIRA, "body": "só texto"},
            "no seen_in": {"note": JIRA, "body": original + "\nlinha\n"},
            "verified not renewed": {"note": JIRA, "body": original.replace(
                "confidence: medium\n", "confidence: medium\nseen_in: [projeto_x]\n")},
            "rewrite": {"note": JIRA, "body": rewritten},
            "secret": {"note": JIRA, "body": self.absorb_text() + FAKE},
        }
        for label, kw in cases.items():
            with self.subTest(label):
                self.assertParity(cid, "absorb", **kw)
        self.assertEqual(self.post(cid, "absorb", dry_run=True, note=JIRA, body=rewritten, allow_rewrite=True).status_code, 200)

    def test_drop_errors_match_the_real_run(self):
        cid = self.add()
        for reason in (None, "", "  \n"):
            with self.subTest(reason=reason):
                self.assertParity(cid, "drop", reason=reason)
        dry = self.assertParity(cid, "drop", reason=FAKE)
        self.assertEqual(dry.status_code, 422)
        self.assertNotIn(FAKE, dry.text)

    def test_unknown_candidate_and_action_match_the_real_run(self):
        cid = self.add()
        self.assertParity("naoexiste", "skip")
        self.assertParity(cid, "merge")

    def test_dry_run_defaults_to_false(self):
        cid = self.add()
        self.assertIs(self.post(cid, "skip").json()["dry_run"], False)
        self.assertIn(cid, self.app.state.skipped_ids)


class ModalContractTest(WebFixture):
    def setUp(self):
        super().setUp()
        self.js = self.client.get("/static/review.js").text
        self.page = self.client.get("/").text

    def test_triage_keys_are_off_while_a_modal_is_open(self):
        self.assertIn('var modal = null', self.js)
        self.assertRegex(self.js, r"if \(modal\) \{ modalKey\(event\); return; \}")
        self.assertRegex(self.js, r"if \(!action \|\| modal\)")

    def test_modal_keys(self):
        for needle in ('"Escape"', '"Enter"', "ctrlKey", "metaKey", '"Tab"', "isComposing", "focusables", "app.inert = true",
                       "app.inert = false"):
            self.assertIn(needle, self.js)

    def test_confirmations_and_validation(self):
        for needle in ("Descartar edições não salvas?", "window.confirm", "dry_run: true", "VALIDATE_DELAY = 500",
                       "var mine = ++seq", "mine !== seq", "/ui/editor?"):
            self.assertIn(needle, self.js)

    def test_the_fixed_drop_reason_is_gone(self):
        self.assertNotIn("descartado na revisão web", self.js)

    def test_no_new_dependency(self):
        self.assertNotRegex(self.js + self.page, r"htmx|unpkg|jsdelivr|require\(|import ")
        self.assertEqual(sorted(re.findall(r'<script[^>]+src="([^"]+)"', self.page)),
                         ["/static/review.js", "https://cdn.tailwindcss.com/3.4.17"])

    def test_page_hosts_the_modals_outside_the_app_shell(self):
        self.assertIn('<div id="overlay"></div>', self.page)
        self.assertIn('<template id="drop-template">', self.page)
        self.assertLess(self.page.index('id="app"'), self.page.index('id="overlay"'))
        self.assertGreater(self.page.index('id="overlay"'), self.page.index("</footer>"))
        self.assertNotRegex(self.page, r'data-key="e" disabled')

    def test_drop_modal_markup(self):
        drop = re.search(r'<template id="drop-template">(.*?)</template>', self.page, re.S).group(1)
        for needle in ('role="dialog"', 'aria-modal="true"', 'aria-labelledby="drop-heading"', 'maxlength="300"',
                       'id="drop-reason"', 'role="alert"', "Motivo do descarte"):
            self.assertIn(needle, drop)
        self.assertRegex(drop, r'id="drop-confirm" disabled')

    def test_templates_still_have_a_single_safe_filter(self):
        from test_web_service import SERVICE
        uses = {}
        for path in (SERVICE.parent / "web" / "templates").glob("*.html"):
            uses[path.name] = len(re.findall(r"\|\s*safe", path.read_text(encoding="utf-8")))
        self.assertEqual({k: v for k, v in uses.items() if v}, {"index.html": 1})


if __name__ == "__main__":
    unittest.main()
