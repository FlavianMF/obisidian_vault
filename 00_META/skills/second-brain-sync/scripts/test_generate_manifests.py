"""Testes do gerador de manifests: python3 -m unittest discover -s 00_META/skills/second-brain-sync/scripts -v"""

import tempfile
import unittest
from pathlib import Path

import generate_manifests as gm


class ExtractSummaryTest(unittest.TestCase):
    def test_uses_first_prose_paragraph_and_skips_heading(self):
        body = "# Título\n\nPrimeira frase da nota. Segunda frase.\n\nOutro parágrafo.\n"
        self.assertEqual(gm.extract_summary(body), "Primeira frase da nota. Segunda frase.")

    def test_joins_wrapped_lines_of_the_paragraph(self):
        body = "# T\n\nQuando o usuário veta\nas ferramentas de leitura.\n\n- item\n"
        self.assertEqual(gm.extract_summary(body), "Quando o usuário veta as ferramentas de leitura.")

    def test_skips_blockquote_navigation_and_code_fences(self):
        body = (
            "> Ver [[claude-code]] para a nota-conceito.\n\n# Subagentes\n\n[← Índice](00_indice.md)\n\n"
            "```bash\nrm -rf x\n```\n\nTrês formas de unidade de comportamento.\n"
        )
        self.assertEqual(gm.extract_summary(body), "Três formas de unidade de comportamento.")

    def test_strips_markdown_and_keeps_link_text(self):
        body = "# T\n\nUse **negrito**, `código`, [[Nota Alvo|apelido]], [[Outra]] e [texto](http://x).\n"
        self.assertEqual(gm.extract_summary(body), "Use negrito, código, apelido, Outra e texto.")

    def test_falls_back_to_first_list_item_when_no_paragraph(self):
        body = "# T\n\n- Primeiro item relevante\n- Segundo\n"
        self.assertEqual(gm.extract_summary(body), "Primeiro item relevante")

    def test_truncates_at_word_boundary_within_limit(self):
        body = "# T\n\n" + " ".join(["palavra"] * 60) + "\n"
        summary = gm.extract_summary(body)
        self.assertLessEqual(len(summary), gm.SUMMARY_MAX_CHARS)
        self.assertTrue(summary.endswith("…"))
        self.assertNotIn("palavr…", summary)

    def test_empty_when_body_has_no_prose(self):
        self.assertEqual(gm.extract_summary("# Só título\n\n| a | b |\n| - | - |\n"), "")
        self.assertEqual(gm.extract_summary(""), "")


class EscapeCellTest(unittest.TestCase):
    def test_pipe_and_newlines_cannot_break_the_table(self):
        out = gm.escape_cell("a | b\nc\r\nd")
        self.assertNotIn("|", out)
        self.assertNotIn("\n", out)
        self.assertEqual(out, "a ¦ b c d")


class ManifestTableTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.vault = Path(self.tmp.name)
        (self.vault / "20_Permanent_Notes").mkdir()
        (self.vault / "20_Permanent_Notes" / "n1.md").write_text(
            "---\ntitle: Título | com pipe\ntype: trap\ntags: [a, b]\ncreated: 2026-01-02\n"
            "provenance: x\nconfidence: low\nseen_in: [p]\n---\n\n# H\n\nResumo da nota.\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_summary_is_the_last_column_and_old_columns_keep_their_positions(self):
        table = gm.build_manifest_files(self.vault)["by_type/trap.md"]
        header, _, row = table.splitlines()[:3]
        cells = [c.strip() for c in row.split("|")]
        self.assertEqual(
            [c.strip() for c in header.split("|")][1:-1],
            ["Path", "Title", "Tags", "Created", "Provenance", "Confidence", "Seen in", "Summary"],
        )
        self.assertEqual(cells[1], "20_Permanent_Notes/n1.md")
        self.assertEqual(cells[2], "Título ¦ com pipe")
        self.assertEqual(cells[7], "p")  # session_hint.sh lê $8 = Seen in
        self.assertEqual(cells[8], "Resumo da nota.")
        self.assertEqual(len(cells), 10)

    def test_every_column_is_escaped_so_a_row_always_has_ten_cells(self):
        (self.vault / "20_Permanent_Notes" / "pipe|name.md").write_text(
            "---\ntitle: x\ntype: trap\ntags: [a|b]\ncreated: 2026-01-02\nprovenance: p|q\n"
            "confidence: low\nseen_in: [r|s]\n---\n\nCorpo.\n",
            encoding="utf-8",
        )
        table = gm.build_manifest_files(self.vault)["by_type/trap.md"]
        for row in table.splitlines()[2:]:
            self.assertEqual(len(row.split("|")), 10, row)

    def test_title_drops_surrounding_quotes_and_blank_titles_fall_back_to_the_file_name(self):
        (self.vault / "20_Permanent_Notes" / "q.md").write_text(
            '---\ntitle: "Com aspas"\ntype: trap\ntags: []\n---\n\nCorpo.\n', encoding="utf-8"
        )
        (self.vault / "20_Permanent_Notes" / "branco.md").write_text(
            "---\ntitle:    \ntype: trap\ntags: []\n---\n\nCorpo.\n", encoding="utf-8"
        )
        table = gm.build_manifest_files(self.vault)["by_type/trap.md"]
        self.assertIn("| Com aspas |", table)
        self.assertIn("| branco |", table)

    def test_write_is_atomic_leaves_no_temp_files_and_is_idempotent(self):
        self.assertTrue(gm.write_manifests(self.vault))
        self.assertFalse(gm.write_manifests(self.vault))
        leftovers = [p.name for p in (self.vault / gm.MANIFEST_DIR_NAME).rglob("*") if p.name.endswith(".tmp")]
        self.assertEqual(leftovers, [])
        self.assertTrue(gm.check_manifests(self.vault))

    def test_generator_never_writes_into_notes(self):
        note = self.vault / "20_Permanent_Notes" / "n1.md"
        before = note.read_bytes()
        gm.write_manifests(self.vault)
        self.assertEqual(note.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
