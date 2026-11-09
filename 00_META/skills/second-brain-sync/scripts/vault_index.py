#!/usr/bin/env python3
"""SQLite FTS5 index of the vault with BM25 ranking (stdlib only).

`generate_manifests.write_manifests` rebuilds `00_META/manifests/index.sqlite` (override the path with
SECOND_BRAIN_INDEX_PATH); `sb search` queries it and falls back to `vault_rank.sh` when it does not exist.
SECOND_BRAIN_INDEX=0|false|no|off disables both the build and the use of the index.

    python3 vault_index.py build  [--vault-path P] [--db PATH]
    python3 vault_index.py search [--vault-path P] [--db PATH] [-k N] <query...>

The index is a derived artifact, never a source of truth: it is rebuilt from the notes, written to a
temporary file and renamed into place, so a reader never sees a half-built database.
"""
from __future__ import annotations

import argparse
import os
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

INDEX_RELPATH = "00_META/manifests/index.sqlite"
SCHEMA = """
CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts5(
    path UNINDEXED,
    title,
    type,
    tags,
    summary,
    content,
    confidence UNINDEXED,
    tokenize='unicode61'
)
"""
# bm25() weights, one per column in declaration order (path, title, type, tags, summary, content, confidence).
BM25_WEIGHTS = (0.0, 10.0, 1.0, 5.0, 3.0, 1.0, 0.0)
TERM = re.compile(r"\w+", re.UNICODE)
OPERATORS = {"AND", "OR"}
STOPWORDS = frozenset(
    "para como mais mas pelo pela pelos pelas seu sua seus suas ele ela eles elas isso esse essa esses essas este esta "
    "estes estas quando onde qual quais todo toda todos todas tudo ser ter foi sao tem sem sobre entre depois antes "
    "ainda tambem muito meu minha meus minhas fazer feito faco pode podem posso deve devo quero preciso usar uso vez "
    "uma uns umas nao nos nas dos das com por que the and for with that this from how what when where which into your "
    "have been does using use should would could".split()
)
MIN_PREFIX_LEN = 3  # "agente" also finds "agentes", as the substring match of vault_rank.sh does


def index_enabled(env=None) -> bool:
    value = (os.environ if env is None else env).get("SECOND_BRAIN_INDEX", "")
    return value.strip().lower() not in {"0", "false", "no", "off"}


def default_db_path(vault_root: Path, env=None) -> Path:
    override = (os.environ if env is None else env).get("SECOND_BRAIN_INDEX_PATH", "").strip()
    return Path(override).expanduser() if override else Path(vault_root) / INDEX_RELPATH


def fold(text: str) -> str:
    """Lower-case and strip accents, so 'Pão' and 'pao' are the same term."""
    decomposed = unicodedata.normalize("NFKD", text.lower())
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def query_terms(query: str) -> list[str]:
    """Distinct folded terms of the query, operators and stopwords removed (stopwords stay if nothing else is left)."""
    seen: dict[str, None] = {}
    for token in TERM.findall(query):
        if token in OPERATORS:
            continue
        seen.setdefault(fold(token), None)
    terms = list(seen)
    useful = [t for t in terms if t not in STOPWORDS and len(t) >= 2]
    return useful or terms


def _quote(term: str) -> str:
    quoted = '"' + term.replace('"', '""') + '"'
    return quoted + "*" if len(term) >= MIN_PREFIX_LEN else quoted


def build_match(query: str, mode: str = "and") -> str:
    """Safe FTS5 MATCH expression: every term quoted, so no raw FTS5 syntax can reach the parser.

    Explicit uppercase AND / OR between terms are honoured (mode "explicit"); otherwise the terms are joined
    with `mode` ("and" = all terms, "or" = any term).
    """
    tokens = TERM.findall(query)
    if any(t in OPERATORS for t in tokens) and mode == "and":
        parts: list[str] = []
        pending = None
        for token in tokens:
            if token in OPERATORS:
                pending = token if parts else None
                continue
            term = fold(token)
            if term in STOPWORDS and not parts and len(tokens) > 1:
                continue
            if parts:
                parts.append(pending or "AND")
            parts.append(_quote(term))
            pending = None
        return " ".join(parts)
    terms = query_terms(query)
    return f" {mode.upper()} ".join(_quote(t) for t in terms)


def _connect_new(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=OFF")
    conn.execute("PRAGMA synchronous=OFF")
    return conn


def build_index(vault_root: Path, db_path: Path | None = None) -> int:
    """Rebuild the FTS5 index from the vault notes; returns the number of notes indexed.

    Written to `<db>.tmp` and renamed over `db_path`, so the old index stays usable until the new one is whole.
    """
    import generate_manifests as gm

    vault_root = Path(vault_root)
    db_path = Path(db_path) if db_path else default_db_path(vault_root)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = db_path.with_name(db_path.name + ".tmp")
    tmp.unlink(missing_ok=True)
    count = 0
    conn = _connect_new(tmp)
    try:
        conn.execute(SCHEMA)
        for path, rel in gm.iter_notes(vault_root):
            try:
                if path.stat().st_size == 0:
                    continue
                data, _, body = gm.frontmatter.read_note(path)
            except OSError:
                continue
            note_type = str(data.get("type") or "unclassified").strip() or "unclassified"
            conn.execute(
                "INSERT INTO notes_fts(path, title, type, tags, summary, content, confidence) VALUES (?,?,?,?,?,?,?)",
                (
                    rel.as_posix(),
                    gm.clean_title(data.get("title"), path.stem),
                    note_type,
                    gm.as_list_str(data.get("tags")),
                    gm.extract_summary(body),
                    body,
                    str(data.get("confidence") or ""),
                ),
            )
            count += 1
        conn.execute("INSERT INTO notes_fts(notes_fts) VALUES ('optimize')")
        conn.commit()
        conn.close()
        os.replace(tmp, db_path)
    except BaseException:
        conn.close()
        tmp.unlink(missing_ok=True)
        raise
    return count


def _run_query(conn: sqlite3.Connection, match: str, limit: int) -> list[sqlite3.Row]:
    weights = ", ".join(str(w) for w in BM25_WEIGHTS)
    sql = (
        f"SELECT path, title, type, tags, summary, content, confidence, bm25(notes_fts, {weights}) AS rank "
        "FROM notes_fts WHERE notes_fts MATCH ? ORDER BY rank, path LIMIT ?"
    )
    try:
        return conn.execute(sql, (match, limit)).fetchall()
    except sqlite3.OperationalError as err:
        if "fts5" in str(err).lower() and "syntax" in str(err).lower():
            return []
        raise


def search_fts(query: str, db_path: Path, limit: int = 10) -> list[dict]:
    """Best-first hits: {path, title, type, summary, coverage, confidence, score, terms}.

    All terms must match (AND); when nothing does, any term (OR) is tried and `coverage` tells how many did (terms found anywhere in the note).
    `score` is >= 0 and higher is better (-bm25). An unreadable/absent database raises sqlite3.Error.
    """
    terms = query_terms(query)
    if not terms or limit <= 0:
        return []
    db_path = Path(db_path)
    if not db_path.is_file():
        raise sqlite3.OperationalError(f"index not found: {db_path}")
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        rows = _run_query(conn, build_match(query, "and"), limit)
        if not rows:
            rows = _run_query(conn, build_match(query, "or"), limit)
    finally:
        conn.close()
    hits = []
    for row in rows:
        haystack = fold(" ".join((row["path"], row["title"], row["type"], row["tags"], row["summary"], row["content"])))
        matched = sum(1 for t in terms if t in haystack)
        hits.append({
            "path": row["path"], "title": row["title"], "type": row["type"], "summary": row["summary"],
            "coverage": round(matched / len(terms), 3), "confidence": row["confidence"],
            "score": round(-row["rank"], 3), "terms": len(terms),
        })
    return hits


def format_tsv(hits: list[dict]) -> str:
    """Same columns as vault_rank.sh without -n: score, path, title, coverage, confidence."""
    return "".join(
        f"{h['score']:.3f}\t{h['path']}\t{h['title']}\t{h['coverage']:.3f}\t{h['confidence']}\n" for h in hits
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("build", "search"):
        p = sub.add_parser(name)
        p.add_argument("--vault-path", type=Path, default=Path(os.environ.get("SECOND_BRAIN_VAULT") or Path(__file__).resolve().parents[4]))
        p.add_argument("--db", type=Path, default=None)
        if name == "search":
            p.add_argument("-k", type=int, default=5)
            p.add_argument("query", nargs="+")
    args = parser.parse_args(argv)
    vault = args.vault_path.resolve()
    db = args.db or default_db_path(vault)
    if args.command == "build":
        print(f"indexed {build_index(vault, db)} notes -> {db}")
        return 0
    sys.stdout.write(format_tsv(search_fts(" ".join(args.query), db, args.k)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
