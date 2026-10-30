"""Tests of the candidate review web API (Sprint 1): python3 -m unittest test_web_service -v

Real git vault with a local bare remote (the VaultFixture of test_vault_sync) and a throwaway state dir, so the
user's vault and queue are never touched. The API is driven through starlette's TestClient. The credential below
is FAKE and assembled at run time.
"""
import ast
import datetime as dt
import json
import stat
import subprocess
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from starlette.testclient import TestClient

import candidates
import web_service
from test_vault_sync import VaultFixture

FAKE = "gh" + "p_" + "A1b2C3d4E5f6G7h8I9j0K1l2"
JIRA = "20_Permanent_Notes/Importar Issues no Jira por REST.md"
BODY = "Contexto e receita.\n\n## O que NÃO funcionou\n\nNada falhou no teste.\n"
SERVICE = Path(web_service.__file__)


class WebFixture(VaultFixture):
    def setUp(self):
        super().setUp()
        self.state.mkdir(parents=True, exist_ok=True)
        self.app = web_service.create_app(self.vault, self.state)
        self.client = TestClient(self.app)

    def add(self, title="Calibração de Câmera Estéreo", kind="trap", project="projeto_x", body=BODY, days_left=None,
            summary="resumo curto", **kw):
        cid, _ = candidates.add(self.state, kind=kind, title=title, summary=summary, project=project, body=body, **kw)
        if days_left is not None:
            self.age(cid, candidates.TTL_DAYS - days_left)
        return cid

    def age(self, cid, days):
        path = candidates.queue_path(self.state)
        ts = (candidates.utcnow() - dt.timedelta(days=days)).isoformat(timespec="seconds")
        with candidates.locked(path):
            rows = [json.loads(line) for line in candidates.read_lines(path)]
            for row in rows:
                if row["id"] == cid:
                    row["ts"] = ts
            candidates.replace_file(path, ("\n".join(json.dumps(r) for r in rows) + "\n").encode("utf-8"))

    def decide(self, cid, action, **kw):
        return self.client.post("/api/decide", json={"id": cid, "action": action, **kw})

    def undo(self, **kw):
        return self.client.post("/api/undo", json=kw)

    def head(self):
        return subprocess.run(["git", "-C", str(self.vault), "rev-parse", "HEAD"], capture_output=True,
                              text=True).stdout.strip()

    def git_status(self):
        return subprocess.run(["git", "-C", str(self.vault), "status", "--porcelain"], capture_output=True,
                              text=True).stdout

    def pending_ids(self):
        return [c["id"] for c in self.client.get("/api/candidates", params={"limit": 100}).json()["candidates"]]

    def review_rows(self):
        return self.log("review.jsonl")

    def absorb_text(self, **change):
        text = (self.vault / JIRA).read_text(encoding="utf-8")
        text = text.replace("confidence: medium\n",
                            "confidence: medium\nseen_in: [projeto_x]\nverified: 2026-10-22 via teste\n")
        return text + "\n- Entrada datada de 2026-10-22 vinda de projeto_x.\n"

    def assertError(self, resp, code):
        self.assertEqual(resp.status_code, code, resp.text)
        body = resp.json()
        self.assertIsInstance(body["detail"], str)
        self.assertIsInstance(body["errors"], list)
        return body


class ListTest(WebFixture):
    def test_empty_queue(self):
        body = self.client.get("/api/candidates").json()
        self.assertEqual((body["total"], body["candidates"]), (0, []))

    def test_item_carries_the_draft_the_age_and_the_proposal(self):
        cid = self.add()
        item = self.client.get("/api/candidates").json()["candidates"][0]
        self.assertEqual((item["id"], item["kind"], item["project"], item["source"]), (cid, "trap", "projeto_x", "agent"))
        self.assertTrue(item["has_draft"])
        self.assertEqual(item["draft_content"], BODY)
        self.assertEqual(item["days_left"], 30)
        self.assertEqual(item["proposal"], "save")
        self.assertEqual(item["similar"], [])

    def test_no_draft_means_has_draft_false_and_null_content(self):
        self.add(body=None)
        item = self.client.get("/api/candidates").json()["candidates"][0]
        self.assertFalse(item["has_draft"])
        self.assertIsNone(item["draft_content"])

    def test_l1_similarity_lists_the_covering_note_and_proposes_absorb(self):
        self.add(title="Importar Issues no Jira por REST", kind="concept", body=None)
        item = self.client.get("/api/candidates").json()["candidates"][0]
        self.assertEqual(item["similar"][0]["path"], JIRA)
        self.assertGreaterEqual(item["similar"][0]["coverage"], 0.5)
        self.assertEqual((item["proposal"], item["proposal_detail"]), ("absorb", JIRA))

    def test_order_is_days_left_then_id_and_total_ignores_the_page(self):
        old = self.add(title="Armadilha antiga distinta", days_left=3)
        mid = self.add(title="Armadilha média distinta", days_left=10)
        new = self.add(title="Armadilha nova distinta", days_left=25)
        body = self.client.get("/api/candidates").json()
        self.assertEqual([c["id"] for c in body["candidates"]], [old, mid, new])
        page = self.client.get("/api/candidates", params={"limit": 1, "offset": 1}).json()
        self.assertEqual((page["total"], page["limit"], page["offset"]), (3, 1, 1))
        self.assertEqual([c["id"] for c in page["candidates"]], [mid])
        past = self.client.get("/api/candidates", params={"offset": 3}).json()
        self.assertEqual((past["total"], past["candidates"]), (3, []))

    def test_ties_break_by_id(self):
        ids = sorted(self.add(title=f"Armadilha empatada {n} distinta") for n in range(3))
        self.assertEqual(self.pending_ids(), ids)

    def test_expired_candidates_are_not_listed_or_counted(self):
        self.add(title="Armadilha vencida distinta", days_left=-2)
        live = self.add(title="Armadilha viva distinta", days_left=5)
        body = self.client.get("/api/candidates").json()
        self.assertEqual((body["total"], [c["id"] for c in body["candidates"]]), (1, [live]))

    def test_filters_narrow_the_list_and_the_total(self):
        a = self.add(title="Armadilha do projeto x", project="projeto_x", kind="trap")
        b = self.add(title="Padrão do projeto y", project="projeto_y", kind="pattern")
        c = self.add(title="Decisão do observador", project="projeto_x", kind="decision", source="observer")
        cases = [({"project": "projeto_y"}, [b]), ({"kind": "trap"}, [a]), ({"source": "observer"}, [c]),
                 ({"project": "projeto_x", "kind": "decision"}, [c]), ({"project": "nenhum"}, [])]
        for params, expected in cases:
            with self.subTest(**params):
                body = self.client.get("/api/candidates", params=params).json()
                self.assertEqual(([x["id"] for x in body["candidates"]], body["total"]), (expected, len(expected)))

    def test_decided_candidates_leave_the_list(self):
        keep, gone = self.add(title="Armadilha mantida distinta"), self.add(title="Armadilha rejeitada distinta")
        self.assertEqual(self.decide(gone, "drop", reason="ruído").status_code, 200)
        body = self.client.get("/api/candidates").json()
        self.assertEqual((body["total"], [c["id"] for c in body["candidates"]]), (1, [keep]))

    def test_bad_paging_is_a_422_in_the_unified_error_shape(self):
        for params in ({"limit": 0}, {"limit": 101}, {"offset": -1}, {"limit": "x"}):
            with self.subTest(**params):
                body = self.assertError(self.client.get("/api/candidates", params=params), 422)
                self.assertTrue(body["errors"])

    def test_unknown_route_uses_the_unified_error_shape(self):
        self.assertEqual(self.assertError(self.client.get("/api/nada"), 404)["errors"], [])

    def test_api_filters_returns_projects_and_kinds(self):
        self.add(project="projeto_alpha", kind="trap")
        self.add(project="projeto_beta", kind="concept")
        resp = self.client.get("/api/filters")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("projects", data)
        self.assertIn("kinds", data)
        self.assertIn("projeto_alpha", data["projects"])
        self.assertIn("projeto_beta", data["projects"])
        self.assertEqual(data["kinds"], ["trap", "pattern", "decision", "concept"])


class SaveTest(WebFixture):
    def test_save_writes_commits_logs_and_consumes_the_draft(self):
        cid = self.add()
        resp = self.decide(cid, "save")
        body = resp.json()
        self.assertEqual(resp.status_code, 200, resp.text)
        self.assertEqual((body["success"], body["action"], body["id"]), (True, "save", cid))
        self.assertEqual(body["sha"], self.head())
        self.assertIsNone(body["next_candidate_id"])
        note = self.vault / "20_Permanent_Notes/Calibração de Câmera Estéreo.md"
        self.assertIn("Nada falhou no teste.", note.read_text(encoding="utf-8"))
        self.assertEqual(self.git_status(), "")
        self.assertEqual((self.review_rows()[-1]["outcome"], self.review_rows()[-1]["id"]), ("applied", cid))
        self.assertIsNone(candidates.read_draft(self.state, cid))
        self.assertEqual(self.pending_ids(), [])

    def test_next_candidate_id_points_at_another_pending_candidate(self):
        first, second = self.add(title="Armadilha primeira distinta", days_left=3), self.add(
            title="Armadilha segunda distinta", days_left=9)
        self.assertEqual(self.decide(first, "save").json()["next_candidate_id"], second)

    def test_title_tags_and_body_overrides(self):
        cid = self.add(body=None)
        resp = self.decide(cid, "save", title="Título   editado", tags=["visao", "opencv"], body=BODY + "\nextra\n")
        self.assertEqual(resp.status_code, 200, resp.text)
        text = (self.vault / "20_Permanent_Notes/Título editado.md").read_text(encoding="utf-8")
        self.assertIn("tags: [visao, opencv]", text)
        self.assertIn("extra", text)

    def test_missing_draft_and_body_scaffolds_a_trap_note(self):
        cid = self.add(body=None, summary="o resumo vira contexto")
        resp = self.decide(cid, "save")
        self.assertEqual(resp.status_code, 200, resp.text)
        text = (self.vault / "20_Permanent_Notes/Calibração de Câmera Estéreo.md").read_text(encoding="utf-8")
        self.assertIn("## Contexto\no resumo vira contexto", text)
        self.assertIn("## O que NÃO funcionou\n- A preencher", text)

    def test_scaffold_also_works_for_a_pattern(self):
        cid = self.add(body=None, kind="pattern", title="Padrão sem rascunho distinto")
        self.assertEqual(self.decide(cid, "save").status_code, 200)

    def test_body_without_the_negative_section_is_422_for_trap_and_pattern_only(self):
        for kind in ("trap", "pattern"):
            with self.subTest(kind=kind):
                cid = self.add(kind=kind, title=f"Sem seção negativa {kind}", body=None)
                body = self.assertError(self.decide(cid, "save", body="Só contexto, sem a seção."), 422)
                self.assertIn("NÃO funcionou", body["detail"])
                self.assertFalse((self.vault / f"20_Permanent_Notes/Sem seção negativa {kind}.md").exists())
        cid = self.add(kind="concept", title="Conceito sem seção", body=None)
        self.assertEqual(self.decide(cid, "save", body="Só contexto.").status_code, 200)

    def test_secret_in_title_body_or_reason_is_422_with_findings_and_nothing_is_written(self):
        cid = self.add()
        head = self.head()
        for field, extra in (("title", {"title": f"Token {FAKE}"}), ("body", {"body": BODY + FAKE}),
                             ("reason", {"reason": FAKE})):
            with self.subTest(field=field):
                action = "drop" if field == "reason" else "save"
                resp = self.decide(cid, action, **extra)
                body = self.assertError(resp, 422)
                self.assertEqual(body["detail"], "Secret detected")
                self.assertTrue(body["findings"])
                self.assertNotIn(FAKE, resp.text)
        self.assertEqual((self.head(), self.review_rows()), (head, []))
        self.assertEqual(self.pending_ids(), [cid])

    def test_existing_note_name_is_409(self):
        cid = self.add(title="Importar Issues no Jira por REST", kind="concept", body=None)
        body = self.assertError(self.decide(cid, "save", body="texto"), 409)
        self.assertIn("already exists", body["detail"])
        self.assertEqual(self.pending_ids(), [cid])

    def test_high_similarity_needs_new_because(self):
        cid = self.add(title="Importar issues no Jira via REST", kind="concept", body="Texto novo.")
        body = self.assertError(self.decide(cid, "save"), 422)
        self.assertIn("new_because", body["detail"])
        self.assertEqual(self.decide(cid, "save", new_because="cobre o caso de CSV grande").status_code, 200)

    def test_invalid_tags_are_400(self):
        cid = self.add()
        for tags in (["Maiúscula"], ["com espaço"], [""]):
            with self.subTest(tags=tags):
                self.assertError(self.decide(cid, "save", tags=tags), 400)

    def test_unusable_title_is_400(self):
        cid = self.add()
        self.assertError(self.decide(cid, "save", title="***"), 400)
        self.assertError(self.decide(cid, "save", title="///"), 400)

    def test_no_tmp_body_file_is_left_behind(self):
        cid = self.add()
        self.decide(cid, "save")
        self.assertEqual(list((self.state / "tmp_decisions").glob("*")), [])


class AbsorbTest(WebFixture):
    def setUp(self):
        super().setUp()
        self.cid = self.add(title="Importar Issues no Jira por REST", kind="concept", body=None)

    def test_absorb_updates_the_note_and_returns_the_sha(self):
        resp = self.decide(self.cid, "absorb", note=JIRA, body=self.absorb_text())
        self.assertEqual(resp.status_code, 200, resp.text)
        self.assertEqual(resp.json()["sha"], self.head())
        self.assertIn("projeto_x", (self.vault / JIRA).read_text(encoding="utf-8"))
        self.assertEqual(self.review_rows()[-1]["verdict"], "absorb")
        self.assertEqual(self.pending_ids(), [])

    def test_absorb_can_take_the_body_from_the_draft(self):
        cid = self.add(title="Outra pendência sobre Jira", kind="concept", body=self.absorb_text())
        self.assertEqual(self.decide(cid, "absorb", note=JIRA).status_code, 200)

    def test_invalid_note_paths_are_400(self):
        for note in ("../fora.md", "/etc/passwd", "x.txt", "20_Permanent_Notes/../../x.md"):
            with self.subTest(note=note):
                self.assertError(self.decide(self.cid, "absorb", note=note, body=self.absorb_text()), 400)

    def test_note_missing_from_head_is_404(self):
        body = self.assertError(
            self.decide(self.cid, "absorb", note="20_Permanent_Notes/Inexistente.md", body=self.absorb_text()), 404)
        self.assertIn("use save", body["detail"])

    def test_untracked_note_is_404_too(self):
        (self.vault / "20_Permanent_Notes/Solta.md").write_text("x", encoding="utf-8")
        self.assertError(self.decide(self.cid, "absorb", note="20_Permanent_Notes/Solta.md", body="x"), 404)

    def test_body_rules_are_400(self):
        original = (self.vault / JIRA).read_text(encoding="utf-8")
        with_seen = original.replace("confidence: medium\n", "confidence: medium\nseen_in: [projeto_x]\n")
        cases = {
            "no frontmatter": "só texto",
            "seen_in without the project": original + "\nlinha\n",
            "verified not renewed": with_seen,
        }
        for label, text in cases.items():
            with self.subTest(label):
                self.assertError(self.decide(self.cid, "absorb", note=JIRA, body=text), 400)
        self.assertEqual((self.git_status(), self.review_rows()), ("", []))

    def test_rewriting_most_of_the_note_is_refused_unless_allowed(self):
        rewritten = ("---\ntitle: Importar Issues no Jira por REST\ntype: pattern\ntags: [a]\ncreated: 2026-10-14\n"
                     "seen_in: [projeto_x]\nverified: 2026-10-22 via teste\n---\n\nTexto todo novo.\n")
        self.assertError(self.decide(self.cid, "absorb", note=JIRA, body=rewritten), 400)
        self.assertEqual(self.decide(self.cid, "absorb", note=JIRA, body=rewritten, allow_rewrite=True).status_code, 200)

    def test_secret_in_the_updated_note_is_422(self):
        self.assertError(self.decide(self.cid, "absorb", note=JIRA, body=self.absorb_text() + FAKE), 422)


class DropAndSkipTest(WebFixture):
    def test_drop_logs_the_reason_removes_the_draft_and_makes_no_commit(self):
        cid = self.add()
        head = self.head()
        resp = self.decide(cid, "drop", reason="  ruído do observador  ")
        body = resp.json()
        self.assertEqual(resp.status_code, 200, resp.text)
        self.assertEqual((body["action"], body["sha"], body["next_candidate_id"]), ("drop", None, None))
        self.assertEqual(self.head(), head)
        row = self.review_rows()[-1]
        self.assertEqual((row["outcome"], row["reason"]), ("rejected", "ruído do observador"))
        self.assertIsNone(candidates.read_draft(self.state, cid))
        self.assertEqual(self.pending_ids(), [])

    def test_drop_needs_a_real_reason(self):
        cid = self.add()
        for reason in (None, "", "   \n\t"):
            with self.subTest(reason=reason):
                self.assertError(self.decide(cid, "drop", reason=reason), 400)
        self.assertEqual(self.pending_ids(), [cid])

    def test_skip_keeps_the_candidate_pending_and_writes_nothing(self):
        first, second = self.add(title="Armadilha primeira distinta", days_left=3), self.add(
            title="Armadilha segunda distinta", days_left=9)
        head = self.head()
        body = self.decide(first, "skip").json()
        self.assertEqual((body["success"], body["sha"], body["next_candidate_id"]), (True, None, second))
        self.assertEqual((self.head(), self.review_rows()), (head, []))
        self.assertEqual(self.pending_ids(), [first, second])
        self.assertIsNotNone(candidates.read_draft(self.state, first))

    def test_skipping_the_only_candidate_still_offers_none_other_than_itself(self):
        cid = self.add()
        self.assertIsNone(self.decide(cid, "skip").json()["next_candidate_id"])
        self.assertEqual(self.pending_ids(), [cid])

    def test_skipped_candidates_come_last_in_next_candidate_id(self):
        a, b, c = (self.add(title=f"Armadilha {n} distinta", days_left=d) for n, d in (("a", 3), ("b", 6), ("c", 9)))
        self.decide(b, "skip")
        self.assertEqual(self.decide(a, "skip").json()["next_candidate_id"], c)


class ErrorTest(WebFixture):
    def test_unknown_action_is_400(self):
        cid = self.add()
        self.assertError(self.decide(cid, "merge"), 400)

    def test_action_is_case_and_space_insensitive(self):
        cid = self.add()
        self.assertEqual(self.decide(cid, " SKIP ").status_code, 200)

    def test_unknown_or_decided_candidate_is_404(self):
        cid = self.add()
        self.assertError(self.decide("naoexiste", "skip"), 404)
        self.assertEqual(self.decide(cid, "drop", reason="x").status_code, 200)
        self.assertError(self.decide(cid, "drop", reason="x"), 404)
        self.assertError(self.decide(cid, "save"), 404)

    def test_expired_candidate_is_404(self):
        cid = self.add(days_left=-1)
        self.assertError(self.decide(cid, "skip"), 404)

    def test_missing_fields_are_422_in_the_unified_shape(self):
        for payload in ({}, {"id": "x"}, {"action": "skip"}, {"id": "x", "action": "save", "tags": "nao-lista"}):
            with self.subTest(payload=payload):
                body = self.assertError(self.client.post("/api/decide", json=payload), 422)
                self.assertTrue(body["errors"])

    def test_wrong_method_uses_the_unified_shape(self):
        self.assertError(self.client.get("/api/decide"), 405)


class UndoTest(WebFixture):
    def test_empty_stack_is_404(self):
        self.assertError(self.undo(), 404)

    def test_undo_drop_reinstates_the_candidate_and_restores_the_draft_text(self):
        cid = self.add()
        self.decide(cid, "drop", reason="engano")
        resp = self.undo()
        self.assertEqual(resp.status_code, 200, resp.text)
        self.assertEqual((resp.json()["reverted_action"], resp.json()["id"]), ("drop", cid))
        self.assertEqual(self.pending_ids(), [cid])
        self.assertEqual(candidates.read_draft(self.state, cid), BODY)
        self.assertEqual([r for r in self.review_rows() if r["outcome"] in candidates.DECIDED_OUTCOMES], [])

    def test_undo_save_reverts_the_commit_and_restores_everything(self):
        cid = self.add()
        base = self.head()
        sha = self.decide(cid, "save").json()["sha"]
        note = self.vault / "20_Permanent_Notes/Calibração de Câmera Estéreo.md"
        self.assertTrue(note.exists())
        resp = self.undo(candidate_id=cid)
        self.assertEqual(resp.status_code, 200, resp.text)
        self.assertEqual(resp.json()["reverted_action"], "save")
        self.assertFalse(note.exists())
        self.assertNotIn(self.head(), (base, sha))
        subjects = subprocess.run(["git", "-C", str(self.vault), "log", "-2", "--format=%s"], capture_output=True,
                                  text=True).stdout
        self.assertIn("Revert", subjects)
        self.assertEqual(self.git_status(), "")
        self.assertEqual(self.pending_ids(), [cid])
        self.assertEqual(candidates.read_draft(self.state, cid), BODY)

    def test_undo_absorb_restores_the_old_note_text(self):
        original = (self.vault / JIRA).read_text(encoding="utf-8")
        cid = self.add(title="Importar Issues no Jira por REST", kind="concept", body=None)
        self.decide(cid, "absorb", note=JIRA, body=self.absorb_text())
        self.assertNotEqual((self.vault / JIRA).read_text(encoding="utf-8"), original)
        self.assertEqual(self.undo().status_code, 200)
        self.assertEqual((self.vault / JIRA).read_text(encoding="utf-8"), original)
        self.assertEqual(self.pending_ids(), [cid])

    def test_undo_skip_only_forgets_the_skip(self):
        a, b = self.add(title="Armadilha a distinta", days_left=3), self.add(title="Armadilha b distinta", days_left=9)
        self.decide(a, "skip")
        resp = self.undo()
        self.assertEqual((resp.status_code, resp.json()["reverted_action"]), (200, "skip"))
        self.assertEqual(self.decide(b, "skip").json()["next_candidate_id"], a)

    def test_undo_restores_the_draft_a_save_with_a_body_override_consumed(self):
        cid = self.add(body="rascunho original\n\n## O que NÃO funcionou\n- x\n")
        self.decide(cid, "save", body=BODY)
        self.undo()
        self.assertIn("rascunho original", candidates.read_draft(self.state, cid))

    def test_undo_is_lifo_and_runs_to_exhaustion(self):
        a, b, c = (self.add(title=f"Armadilha {n} distinta", days_left=d) for n, d in (("a", 3), ("b", 6), ("c", 9)))
        self.decide(a, "drop", reason="1")
        self.decide(b, "save")
        self.decide(c, "skip")
        self.assertEqual([self.undo().json()["id"] for _ in range(3)], [c, b, a])
        self.assertError(self.undo(), 404)
        self.assertEqual(self.pending_ids(), [a, b, c])

    def test_undo_out_of_order_is_400_and_unknown_id_is_404(self):
        a, b = self.add(title="Armadilha a distinta", days_left=3), self.add(title="Armadilha b distinta", days_left=9)
        self.decide(a, "drop", reason="1")
        self.decide(b, "drop", reason="2")
        self.assertError(self.undo(candidate_id=a), 400)
        self.assertError(self.undo(candidate_id="naoexiste"), 404)
        self.assertEqual(self.undo(candidate_id=b).status_code, 200)
        self.assertEqual(self.undo(candidate_id=a).status_code, 200)

    def test_a_failed_decision_does_not_enter_the_stack(self):
        cid = self.add(body=None)
        self.decide(cid, "save", body="sem seção negativa")
        self.assertError(self.undo(), 404)

    def test_redecide_after_undo(self):
        cid = self.add()
        self.decide(cid, "save")
        self.undo()
        self.assertEqual(self.decide(cid, "save").status_code, 200)
        self.assertEqual(self.pending_ids(), [])

    def test_revert_conflict_is_409_leaves_the_vault_clean_and_keeps_the_entry(self):
        cid = self.add()
        self.decide(cid, "save")
        note = self.vault / "20_Permanent_Notes/Calibração de Câmera Estéreo.md"
        note.write_text(note.read_text(encoding="utf-8") + "\nedição posterior\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.vault), "commit", "-qam", "docs: edit later"], check=True)
        head = self.head()
        body = self.assertError(self.undo(), 409)
        self.assertIn("conflict", body["detail"])
        self.assertEqual((self.head(), self.git_status()), (head, ""))
        self.assertFalse((self.vault / ".git" / "REVERT_HEAD").exists())
        self.assertEqual(self.pending_ids(), [])
        self.assertEqual(self.review_rows()[-1]["outcome"], "applied")
        self.assertEqual(self.undo().status_code, 409)  # the entry stayed on the stack

    def test_review_log_stays_private_and_keeps_unrelated_rows(self):
        a, b = self.add(title="Armadilha a distinta", days_left=3), self.add(title="Armadilha b distinta", days_left=9)
        self.decide(a, "drop", reason="1")
        self.decide(b, "drop", reason="2")
        self.undo()
        rows = self.review_rows()
        self.assertEqual([r["id"] for r in rows], [a])
        mode = stat.S_IMODE((self.state / "review.jsonl").stat().st_mode)
        self.assertEqual(mode, 0o600)


class ConcurrencyTest(WebFixture):
    def test_parallel_drops_all_land_in_a_well_formed_log(self):
        ids = [self.add(title=f"Armadilha paralela {n} distinta", body=None) for n in range(8)]
        with ThreadPoolExecutor(max_workers=8) as pool:
            codes = list(pool.map(lambda cid: self.decide(cid, "drop", reason="paralelo").status_code, ids))
        self.assertEqual(codes, [200] * 8)
        rows = self.review_rows()
        self.assertEqual(sorted(r["id"] for r in rows), sorted(ids))
        self.assertEqual(self.pending_ids(), [])

    def test_the_same_candidate_decided_twice_at_once_succeeds_once(self):
        cid = self.add()
        with ThreadPoolExecutor(max_workers=4) as pool:
            codes = sorted(pool.map(lambda _: self.decide(cid, "drop", reason="corrida").status_code, range(4)))
        self.assertEqual(codes, [200, 404, 404, 404])
        self.assertEqual(len(self.review_rows()), 1)

    def test_parallel_undos_pop_each_entry_once(self):
        ids = [self.add(title=f"Armadilha desfeita {n} distinta", body=None) for n in range(4)]
        for cid in ids:
            self.decide(cid, "drop", reason="x")
        with ThreadPoolExecutor(max_workers=6) as pool:
            codes = sorted(pool.map(lambda _: self.undo().status_code, range(6)))
        self.assertEqual(codes, [200] * 4 + [404] * 2)
        self.assertEqual(self.review_rows(), [])
        self.assertEqual(sorted(self.pending_ids()), sorted(ids))

    def test_a_listing_during_decisions_never_errors(self):
        ids = [self.add(title=f"Armadilha lida {n} distinta", body=None) for n in range(4)]
        with ThreadPoolExecutor(max_workers=5) as pool:
            writes = [pool.submit(self.decide, cid, "drop", reason="x") for cid in ids]
            reads = [pool.submit(self.client.get, "/api/candidates") for _ in range(4)]
            self.assertEqual([f.result().status_code for f in writes + reads], [200] * 8)


class InvariantTest(unittest.TestCase):
    """I1 and I3, checked on the source: the service writes no vault note and adds no dependency beyond the stack."""

    def setUp(self):
        self.tree = ast.parse(SERVICE.read_text(encoding="utf-8"))

    def test_i1_no_direct_file_write_calls(self):
        bad = []
        for node in ast.walk(self.tree):
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Attribute) and node.func.attr in ("write_text", "write_bytes"):
                bad.append(node.lineno)
            if isinstance(node.func, ast.Name) and node.func.id == "open":
                bad.append(node.lineno)
        self.assertEqual(bad, [])

    def test_i3_imports_are_stdlib_the_local_modules_or_the_web_stack(self):
        allowed = {"fastapi", "pydantic", "starlette", "uvicorn", "candidates", "review", "vault_sync", "lib"}
        roots = set()
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                roots.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                roots.add((node.module or "").split(".")[0])
        import sys
        extra = {r for r in roots if r not in allowed and r not in sys.stdlib_module_names}
        self.assertEqual(extra, set())


if __name__ == "__main__":
    unittest.main()
