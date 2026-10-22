"""Testes da revisão de notas do vault (I4b): `sb review promote` e `sb review stock`.

Escritos antes do código, um ciclo por vez. Vault git real com remoto bare local (fixture do test_vault_sync).
"""

import datetime as dt
import json
import subprocess
import unittest
from pathlib import Path

import review
import review_notes
import sb
from test_review import FAKE, ReviewFixture
from test_vault_sync import git


def note_text(title, *, kind="pattern", confidence="medium", scope="global", seen=("projeto_x", "projeto_y"),
              verified="2026-10-20 via teste", created="2026-05-01", status=""):
    lines = [f"title: {title}", f"type: {kind}", "tags: [t]", f"created: {created}", "provenance: projeto_x",
             f"seen_in: [{', '.join(seen)}]", f"confidence: {confidence}", f"scope: {scope}"]
    if verified:
        lines.append(f"verified: {verified}")
    if status:
        lines.append(f"status: {status}")
    return "---\n" + "\n".join(lines) + "\n---\n\n" + f"# {title}\n\nCorpo.\n\n## O que NÃO funcionou\n\nNada.\n"


class NotesFixture(ReviewFixture):
    def put(self, title, **kw):
        rel = f"20_Permanent_Notes/{title}.md"
        (self.vault / rel).write_text(note_text(title, **kw), encoding="utf-8")
        return rel

    def commit(self):
        subprocess.run(["python3", str(Path(sb.__file__).parent / "generate_manifests.py"), "--vault-path",
                        str(self.vault)], check=True, capture_output=True)
        git(self.vault, "add", "-A")
        git(self.vault, "commit", "-q", "-m", "fixture")
        git(self.vault, "push", "-q", "origin", "master")


class PromoteListTest(NotesFixture):
    def test_lists_only_global_notes_with_medium_confidence_seen_in_two_projects(self):
        good = self.put("Padrão Bom")
        skipped = [
            self.put("Poucos Projetos", seen=("projeto_x",)),
            self.put("Escopo de Projeto", scope="project"),
            self.put("Confiança Baixa", confidence="low"),
        ]
        self.commit()
        out = review_notes.run_promote_next(self.vault, self.state, limit=5)
        self.assertIn(good, out)
        for rel in skipped:
            self.assertNotIn(rel, out)

    def test_shows_the_evidence_and_a_proposal_with_the_note_text_in_the_untrusted_frame(self):
        self.put("Padrão Bom")
        self.commit()
        out = review_notes.run_promote_next(self.vault, self.state, limit=5)
        self.assertIn("seen in 2: projeto_x, projeto_y", out)
        self.assertIn("proposal: promote as [[Padrão Bom]]", out)
        framed = out.split(review.FRAME_OPEN)[1].split(review.FRAME_CLOSE)[0]
        self.assertIn("title:    Padrão Bom", framed)
        self.assertIn("verified: 2026-10-20 via teste", framed)

    def test_skips_superseded_notes_and_types_that_are_not_knowledge(self):
        self.put("Padrão Bom")
        skipped = [self.put("Já Substituída", status="superseded"), self.put("Nota de Projeto", kind="project")]
        self.commit()
        out = review_notes.run_promote_next(self.vault, self.state, limit=5)
        for rel in skipped:
            self.assertNotIn(rel, out)

    def test_skips_a_note_the_instruction_note_already_links(self):
        rel = self.put("Padrão Bom")
        (self.vault / "00_META").mkdir(exist_ok=True)
        (self.vault / "00_META/Agent-Instruction.md").write_text(
            "---\ntitle: x\ntype: meta\n---\n- [[Padrão Bom|bom]]\n", encoding="utf-8")
        self.commit()
        self.assertNotIn(rel, review_notes.run_promote_next(self.vault, self.state, limit=5))


class PromoteApplyTest(NotesFixture):
    def apply(self, *decisions, go=True):
        return review_notes.run_promote_apply(self.vault, self.state, list(decisions), apply=go)

    def test_reject_is_logged_never_comes_back_and_leaves_the_vault_untouched(self):
        rel = self.put("Padrão Bom")
        self.commit()
        head = self.head()
        code, text = self.apply({"note": rel, "verdict": "reject", "reason": "específico de um projeto"})
        self.assertEqual(code, 0, text)
        self.assertNotIn(rel, review_notes.run_promote_next(self.vault, self.state, limit=5))
        self.assertEqual((self.head(), self.status()), (head, ""))
        event = self.log()[-1]
        self.assertEqual((event["stage"], event["note"], event["outcome"]), ("promote", rel, "rejected"))

    def test_promote_records_acceptance_and_prints_the_line_to_paste(self):
        rel = self.put("Padrão Bom")
        self.commit()
        code, text = self.apply({"note": rel, "verdict": "promote"})
        self.assertEqual(code, 0, text)
        self.assertIn("- [[Padrão Bom]]", text)
        self.assertNotIn(rel, review_notes.run_promote_next(self.vault, self.state, limit=5))
        self.assertEqual(self.log()[-1]["outcome"], "accepted")

    def test_one_invalid_decision_refuses_the_whole_file_and_records_nothing(self):
        rel = self.put("Padrão Bom")
        self.commit()
        for bad in ({"note": rel, "verdict": "reject"}, {"note": rel, "verdict": "maybe"},
                    {"note": "inexistente.md", "verdict": "promote"}):
            code, text = self.apply({"note": rel, "verdict": "promote"}, bad)
            self.assertEqual(code, 1, text)
        self.assertEqual(self.log(), [])

    def test_dry_run_records_nothing_and_says_so(self):
        rel = self.put("Padrão Bom")
        self.commit()
        code, text = self.apply({"note": rel, "verdict": "reject", "reason": "x"}, go=False)
        self.assertEqual(code, 0, text)
        self.assertIn("dry run", text)
        self.assertEqual(self.log(), [])
        self.assertIn(rel, review_notes.run_promote_next(self.vault, self.state, limit=5))


TODAY = dt.date(2026, 10, 22)


class StockListTest(NotesFixture):
    def stock_next(self, **kw):
        args = {"limit": 5, "fresh": False, "stale_days": 180, "broken": None, **kw}
        return review_notes.run_stock_next(self.vault, self.state, TODAY, **args)

    def test_lists_a_stale_note_with_its_reason_and_skips_a_fresh_one(self):
        stale = self.put("Velha", created="2026-01-01", verified="2026-01-02 via teste")
        fresh = self.put("Fresca")
        self.commit()
        out = self.stock_next()
        self.assertIn(stale, out)
        self.assertIn("stale: verified 2026-01-02", out)
        self.assertNotIn(fresh, out)

    def test_lists_a_low_confidence_note_that_was_never_reproduced(self):
        rel = self.put("Sem Prova", kind="concept", confidence="low", created="2026-08-01",
                       verified="2026-08-01 via x, não reproduzido")
        self.commit()
        out = self.stock_next()
        self.assertIn(rel, out)
        self.assertIn("unconfirmed", out)

    def test_lists_notes_that_share_a_title_and_names_the_other_one(self):
        first = self.put("Gêmea", kind="concept")
        second = "20_Permanent_Notes/Gêmea B.md"
        (self.vault / second).write_text(note_text("Gêmea", kind="concept"), encoding="utf-8")
        self.commit()
        out = self.stock_next()
        self.assertIn(f"duplicate title: {second}", out)
        self.assertIn(f"duplicate title: {first}", out)

    def test_lists_a_note_with_a_broken_link_and_names_the_target(self):
        rel = self.put("Fresca")
        self.commit()
        self.assertNotIn(rel, self.stock_next())
        out = self.stock_next(broken={rel: ["Nada"]})
        self.assertIn(rel, out)
        self.assertIn("broken link: Nada", out)

    def test_each_note_gets_a_proposal_that_fits_its_reason(self):
        self.put("Velha", created="2026-01-01", verified="2026-01-02 via teste")
        self.put("Gêmea", kind="concept")
        (self.vault / "20_Permanent_Notes/Gêmea B.md").write_text(note_text("Gêmea", kind="concept"), encoding="utf-8")
        self.commit()
        blocks = {b.split("\n")[0]: b for b in ("\n" + self.stock_next(limit=50)).split("\n20_Permanent_Notes/")[1:]}
        self.assertIn("proposal: update", blocks["Velha.md"])
        self.assertIn("proposal: merge", blocks["Gêmea.md"])

    def test_a_superseded_note_is_not_reviewed(self):
        rel = self.put("Velha", created="2026-01-01", verified="2026-01-02 via teste", status="superseded")
        self.commit()
        self.assertNotIn(rel, self.stock_next())

    def test_an_open_batch_resumes_and_fresh_ignores_it(self):
        b = self.put("B Velha", created="2026-01-01", verified="2026-01-02 via teste")
        self.put("C Velha", created="2026-01-01", verified="2026-01-02 via teste")
        self.commit()
        self.assertIn(b, self.stock_next(limit=1))
        a = self.put("A Velha", created="2026-01-01", verified="2026-01-02 via teste")
        self.commit()
        self.assertIn(b, self.stock_next(limit=1))
        self.assertNotIn(a, self.stock_next(limit=1))
        self.assertIn(a, self.stock_next(limit=1, fresh=True))


class StockApplyTest(NotesFixture):
    def setUp(self):
        super().setUp()
        self.old = self.put("Velha", created="2026-01-01", verified="2026-01-02 via teste")
        self.commit()

    def apply(self, *decisions, go=True):
        return review_notes.run_stock_apply(self.vault, self.state, TODAY, list(decisions), apply=go,
                                            stale_days=180, broken=None)

    def listed(self, today=TODAY):
        return self.old in review_notes.run_stock_next(self.vault, self.state, today, limit=50, fresh=True,
                                                       stale_days=180, broken=None)

    def test_keep_is_logged_and_the_note_stays_quiet_until_its_text_changes(self):
        code, text = self.apply({"note": self.old, "verdict": "keep", "reason": "ainda vale"})
        self.assertEqual(code, 0, text)
        self.assertEqual(self.log()[-1]["outcome"], "kept")
        self.assertFalse(self.listed())
        path = self.vault / self.old
        path.write_text(path.read_text(encoding="utf-8") + "\nMais.\n", encoding="utf-8")
        self.assertTrue(self.listed())

    def test_a_keep_expires_after_the_quiet_period(self):
        self.apply({"note": self.old, "verdict": "keep"})
        self.assertFalse(self.listed(TODAY + dt.timedelta(days=review_notes.KEEP_QUIET_DAYS - 1)))
        self.assertTrue(self.listed(TODAY + dt.timedelta(days=review_notes.KEEP_QUIET_DAYS + 1)))

    def renewed(self, tail=""):
        text = (self.vault / self.old).read_text(encoding="utf-8")
        return self.body_file("up.md", text.replace("2026-01-02 via teste", "2026-10-22 via teste novo") + tail)

    def test_update_renews_verified_commits_and_leaves_the_stock(self):
        code, text = self.apply({"note": self.old, "verdict": "update", "body_file": self.renewed()})
        self.assertEqual(code, 0, text)
        self.assertIn("2026-10-22 via teste novo", (self.vault / self.old).read_text(encoding="utf-8"))
        self.assertEqual(self.status(), "")
        self.assertFalse(self.listed())
        self.assertEqual(self.log()[-1]["outcome"], "updated")

    def test_update_without_a_new_verified_is_refused_and_nothing_is_written(self):
        text = (self.vault / self.old).read_text(encoding="utf-8")
        head = self.head()
        code, out = self.apply({"note": self.old, "verdict": "update",
                                "body_file": self.body_file("up.md", text + "\nMais.\n")})
        self.assertEqual(code, 1)
        self.assertIn("verified", out)
        self.assertEqual((self.head(), self.status(), self.log()), (head, "", []))

    def test_update_with_a_credential_is_refused_and_nothing_is_written(self):
        head = self.head()
        code, out = self.apply({"note": self.old, "verdict": "update", "body_file": self.renewed(f"\ntoken: {FAKE}\n")})
        self.assertEqual(code, 1)
        self.assertIn("secret", out)
        self.assertEqual((self.head(), self.status(), self.log()), (head, "", []))

    def test_update_that_drops_most_of_the_note_needs_allow_rewrite(self):
        head = (self.vault / self.old).read_text(encoding="utf-8").split("\n---\n", 1)[0]
        short = self.body_file("short.md", head.replace("2026-01-02 via teste", "2026-10-22 via x") + "\n---\n\nNovo.\n")
        code, out = self.apply({"note": self.old, "verdict": "update", "body_file": short})
        self.assertEqual(code, 1)
        self.assertIn("allow_rewrite", out)
        code, out = self.apply({"note": self.old, "verdict": "update", "body_file": short, "allow_rewrite": True})
        self.assertEqual(code, 0, out)

    def test_a_write_that_vault_sync_refuses_is_undone_and_logged_as_refused(self):
        solo = self.put("Solitária", seen=("projeto_x",), created="2026-01-01", verified="2026-01-02 via nota")
        self.commit()
        text = (self.vault / solo).read_text(encoding="utf-8")
        head = self.head()
        body = self.body_file("up.md", text.replace("confidence: medium", "confidence: high")
                              .replace("2026-01-02 via nota", "2026-10-22 via nota"))
        code, out = self.apply({"note": solo, "verdict": "update", "body_file": body},
                               {"note": self.old, "verdict": "keep", "reason": "ainda vale"})
        self.assertEqual(code, 1, out)
        self.assertTrue(out.startswith("REFUSED"), out)
        self.assertIn("without evidence", out)
        self.assertEqual((self.head(), self.status()), (head, ""))
        self.assertEqual((self.vault / solo).read_text(encoding="utf-8"), text)
        self.assertEqual([(e["note"], e["outcome"]) for e in self.log()],
                         [(solo, "refused"), (self.old, "kept")])
        self.assertIn("without evidence", self.log()[0]["reason"])

    def test_a_commit_whose_push_is_pending_is_logged_with_the_detail(self):
        hook = self.vault / ".git/hooks/pre-push"
        hook.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        hook.chmod(0o755)
        code, out = self.apply({"note": self.old, "verdict": "update", "body_file": self.renewed()})
        self.assertEqual(code, 0, out)
        self.assertIn("push pending", out)
        self.assertEqual(self.status(), "")
        self.assertEqual(self.log()[-1]["outcome"], "updated")
        self.assertIn("push pending", self.log()[-1]["detail"])

    def test_retire_needs_a_reason_and_sets_status_superseded(self):
        code, _ = self.apply({"note": self.old, "verdict": "retire"})
        self.assertEqual(code, 1)
        code, out = self.apply({"note": self.old, "verdict": "retire", "reason": "obsoleta"})
        self.assertEqual(code, 0, out)
        self.assertIn("status: superseded", (self.vault / self.old).read_text(encoding="utf-8"))
        self.assertEqual((self.status(), self.log()[-1]["outcome"]), ("", "retired"))
        self.assertFalse(self.listed())

    def test_merge_retires_the_note_and_points_the_target_at_it(self):
        target = self.put("Alvo")
        self.commit()
        code, out = self.apply({"note": self.old, "verdict": "merge", "into": target, "reason": "duplicada"})
        self.assertEqual(code, 0, out)
        self.assertIn("status: superseded", (self.vault / self.old).read_text(encoding="utf-8"))
        self.assertIn("supersedes: [[[Velha]]]", (self.vault / target).read_text(encoding="utf-8"))
        self.assertEqual(self.status(), "")
        issues = [i for i in sb.run_doctor(self.vault, 180, TODAY) if i.check == "supersedes"]
        self.assertEqual(issues, [])

    def test_merge_into_itself_a_missing_note_or_a_path_outside_the_vault_is_refused(self):
        for into in (self.old, "20_Permanent_Notes/Nada.md", "../x.md", ""):
            code, _ = self.apply({"note": self.old, "verdict": "merge", "into": into, "reason": "x"})
            self.assertEqual(code, 1, into)
        self.assertEqual((self.status(), self.log()), ("", []))

    def test_dry_run_writes_and_records_nothing(self):
        head = self.head()
        code, out = self.apply({"note": self.old, "verdict": "retire", "reason": "x"}, go=False)
        self.assertEqual((code, self.head(), self.status(), self.log()), (0, head, "", []))
        self.assertIn("dry run", out)
        self.assertTrue(self.listed())

    def test_a_bad_verdict_or_a_note_outside_the_stock_refuses_the_whole_file(self):
        fresh = self.put("Fresca")
        self.commit()
        good = {"note": self.old, "verdict": "keep"}
        for bad in ({"note": self.old, "verdict": "maybe"}, {"note": fresh, "verdict": "keep"},
                    {"note": "fora.md", "verdict": "keep"}, {"note": self.old, "verdict": "keep"}):
            code, _ = self.apply(good, bad)
            self.assertEqual(code, 1, bad)
        self.assertEqual(self.log(), [])


class CliTest(NotesFixture):
    def sb(self, *args):
        return subprocess.run(["python3", str(Path(sb.__file__)), *args], capture_output=True, text=True,
                              env={**self.env, "SECOND_BRAIN_VAULT": str(self.vault)})

    def decisions(self, *items):
        path = Path(self.tmp.name) / "decisions.json"
        path.write_text(json.dumps(list(items)), encoding="utf-8")
        return str(path)

    def test_promote_lists_dry_runs_applies_and_then_has_nothing_pending(self):
        rel = self.put("Padrão Bom")
        self.commit()
        self.assertIn(rel, self.sb("review", "promote", "next").stdout)
        file = self.decisions({"note": rel, "verdict": "reject", "reason": "teste"})
        dry = self.sb("review", "promote", "apply", "--decisions", file)
        self.assertIn("dry run", dry.stdout)
        self.assertIn(rel, self.sb("review", "promote", "next").stdout)
        done = self.sb("review", "promote", "apply", "--decisions", file, "--apply")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertNotIn(rel, self.sb("review", "promote", "next").stdout)

    def test_stock_lists_a_note_with_a_broken_link_and_keep_silences_it(self):
        rel = self.put("Com Link Quebrado")
        path = self.vault / rel
        path.write_text(path.read_text(encoding="utf-8") + "\nVer [[Nota Que Não Existe]].\n", encoding="utf-8")
        self.commit()
        listing = self.sb("review", "stock", "next").stdout
        self.assertIn(rel, listing)
        self.assertIn("broken link: Nota Que Não Existe", listing)
        file = self.decisions({"note": rel, "verdict": "keep", "reason": "link vai nascer"})
        self.assertIn("dry run", self.sb("review", "stock", "apply", "--decisions", file).stdout)
        done = self.sb("review", "stock", "apply", "--decisions", file, "--apply")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertNotIn(rel, self.sb("review", "stock", "next", "--fresh").stdout)

    def test_stale_days_widens_the_stock_and_a_missing_decisions_file_exits_2(self):
        rel = self.put("Meio Velha", created="2026-07-01", verified="2026-07-02 via teste")
        self.commit()
        self.assertNotIn(rel, self.sb("review", "stock", "next", "--fresh").stdout)
        self.assertIn(rel, self.sb("review", "stock", "next", "--fresh", "--stale-days", "30").stdout)
        self.assertEqual(self.sb("review", "stock", "apply", "--decisions", "/nao/existe.json").returncode, 2)


if __name__ == "__main__":
    unittest.main()
