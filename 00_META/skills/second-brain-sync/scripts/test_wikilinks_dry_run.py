#!/usr/bin/env python3
import sqlite3
import tempfile
from pathlib import Path
import pytest

import dry_run_wikilinks as dw
import sb


def test_resolve_target_stems_and_paths():
    index = sb.LinkIndex(
        stems={"nota-a": ["20_Permanent_Notes/nota-a.md"], "comum": ["00_Inbox/comum.md"]},
        paths={"20_permanent_notes/nota-a", "00_inbox/comum"},
        files={"nota-a.md", "comum.md"},
    )
    by_title = {"meu título": ["10_Literature_Notes/titulo.md"]}

    # Bare stem
    assert dw.resolve_target("nota-a", index, by_title) == "20_Permanent_Notes/nota-a.md"
    # Bare stem case-insensitive
    assert dw.resolve_target("NOTA-A", index, by_title) == "20_Permanent_Notes/nota-a.md"
    # Stem with .md extension
    assert dw.resolve_target("nota-a.md", index, by_title) == "20_Permanent_Notes/nota-a.md"
    # Title resolution
    assert dw.resolve_target("meu título", index, by_title) == "10_Literature_Notes/titulo.md"
    # Path resolution
    assert dw.resolve_target("20_Permanent_Notes/nota-a", index, by_title) == "20_Permanent_Notes/nota-a.md"
    # Non-existent
    assert dw.resolve_target("inexistente", index, by_title) is None


def test_dry_run_mock_vault():
    with tempfile.TemporaryDirectory() as tmp_dir:
        vault = Path(tmp_dir)
        (vault / "20_Permanent_Notes").mkdir(parents=True)
        (vault / "30_MOCs").mkdir(parents=True)

        note_a = vault / "20_Permanent_Notes" / "Nota A.md"
        note_b = vault / "20_Permanent_Notes" / "Nota B.md"
        moc = vault / "30_MOCs" / "Index.md"

        # Note A links to Note B, has a code block link (should be ignored), self-link, and duplicate link
        note_a.write_text(
            """---
title: Nota A
---
Link para [[Nota B|Apelido B]] e novamente [[Nota B]].
Self link: [[Nota A]]
No código:
```python
# [[Nota B]] inside code block
```
Inline `[[Nota B]]` inline code.
""",
            encoding="utf-8",
        )

        # Note B links back to Note A (reciprocal)
        note_b.write_text(
            """---
title: Nota B
---
Link de volta para [[Nota A#Subseção]].
""",
            encoding="utf-8",
        )

        # MOC links to A and B
        moc.write_text(
            """---
title: Index
---
- [[Nota A]]
- [[Nota B]]
- [[Nota Fantasma Que Nao Existe]]
""",
            encoding="utf-8",
        )

        stats, conn = dw.run_dry_run(vault)

        assert stats.total_notes_scanned == 3
        assert stats.notes_with_links == 3
        assert stats.self_links_found == 1
        assert stats.duplicate_links_in_same_note == 1
        assert stats.unresolved_links_count == 1
        # Edges expected:
        # Note A -> Note B
        # Note B -> Note A
        # MOC -> Note A
        # MOC -> Note B
        assert stats.unique_explicit_edges == 4
        assert stats.reciprocal_pairs_count == 1  # Note A <-> Note B
        assert stats.reciprocal_directed_edges == 2

        # Verify SQLite contents
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM note_edges WHERE is_explicit = 1 AND weight = 0.50")
        assert cur.fetchone()[0] == 4
