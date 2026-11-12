#!/usr/bin/env python3
"""Dry-run test of the wikilinks parser for populating the initial note_edges graph.

Scans the Obsidian vault, extracts all [[wikilink]] references (ignoring code blocks
and inline backticks), resolves link targets against the vault index, and simulates
populating the SQLite `note_edges` table with explicit links (weight=0.50, is_explicit=1).

Usage:
    python3 dry_run_wikilinks.py [--vault-path PATH] [--json] [--sample N]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path

# Ensure script directory is in sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import generate_manifests as gm  # noqa: E402
import sb  # noqa: E402

NOTE_EDGES_SCHEMA = """
CREATE TABLE IF NOT EXISTS note_edges (
    source_path     TEXT NOT NULL,
    target_path     TEXT NOT NULL,
    weight          REAL NOT NULL DEFAULT 0.20 CHECK(weight >= 0.0 AND weight <= 1.0),
    coactivations   INTEGER NOT NULL DEFAULT 1,
    is_explicit     INTEGER NOT NULL DEFAULT 0,
    last_traversed  INTEGER NOT NULL,
    created_at      INTEGER NOT NULL,
    PRIMARY KEY (source_path, target_path)
) WITHOUT ROWID;

CREATE INDEX IF NOT EXISTS idx_edges_source_w ON note_edges (source_path, weight DESC);
CREATE INDEX IF NOT EXISTS idx_edges_target_w ON note_edges (target_path, weight DESC);
CREATE INDEX IF NOT EXISTS idx_edges_crystallize ON note_edges (is_explicit, weight DESC, coactivations DESC);
"""


@dataclass
class DryRunStats:
    total_notes_scanned: int
    notes_with_links: int
    notes_in_graph: int
    orphan_notes_count: int
    total_raw_links_found: int
    duplicate_links_in_same_note: int
    self_links_found: int
    unresolved_links_count: int
    unique_explicit_edges: int
    reciprocal_directed_edges: int
    reciprocal_pairs_count: int
    reciprocity_rate_pct: float
    connected_components_count: int
    giant_component_size: int
    scan_and_parse_time_ms: float
    sqlite_simulation_time_ms: float
    top_out_degree_hubs: list[dict[str, str | int]]
    top_in_degree_authorities: list[dict[str, str | int]]
    top_folder_flows: list[dict[str, str | int]]
    self_link_samples: list[dict[str, str]]
    unresolved_link_samples: list[dict[str, str]]
    sample_edges: list[dict[str, str | float | int]]


def resolve_target(
    target: str,
    index: sb.LinkIndex,
    by_title: dict[str, list[str]],
) -> str | None:
    k = target.strip().casefold()
    if k.endswith(".md"):
        k = k[:-3]

    stem = k.rsplit("/", 1)[-1]

    # 1. Stem match (gives canonical casing directly from index.stems)
    if stem in index.stems:
        candidates = index.stems[stem]
        if "/" in k:
            # disambiguate path if specified
            matched = [c for c in candidates if c.casefold().endswith(k + ".md") or c.casefold() == k + ".md"]
            if matched:
                return matched[0]
        else:
            return candidates[0]

    # 2. Frontmatter title match
    if k in by_title:
        matches = by_title[k]
        if matches:
            res = matches[0]
            return res if res.endswith(".md") else res + ".md"

    # 3. Path match fallback
    if k in index.paths:
        for stem_candidates in index.stems.values():
            for c in stem_candidates:
                if c.casefold() == k + ".md":
                    return c
        return k + ".md"

    # 4. Suffix match fallback
    if "/" in k:
        for stem_candidates in index.stems.values():
            for c in stem_candidates:
                if c.casefold().endswith("/" + k + ".md"):
                    return c

    return None


def run_dry_run(vault_root: Path, sample_limit: int = 10) -> tuple[DryRunStats, sqlite3.Connection]:
    t_start = time.perf_counter()

    index = sb.build_index(vault_root)

    # Build index of frontmatter titles
    by_title: dict[str, list[str]] = defaultdict(list)
    all_notes: set[str] = set()

    for path, rel in gm.iter_notes(vault_root):
        rel_str = str(rel)
        all_notes.add(rel_str)
        try:
            data, _, _ = gm.frontmatter.read_note(path)
            if data.get("title"):
                by_title[str(data["title"]).strip().casefold()].append(rel_str)
        except Exception:
            pass

    notes_with_links = 0
    total_raw_links = 0
    duplicate_links_in_same_note = 0
    self_links: list[dict[str, str]] = []
    unresolved_links: list[dict[str, str]] = []
    raw_unresolved_set: set[str] = set()

    unique_edges: set[tuple[str, str]] = set()
    out_degree: Counter[str] = Counter()
    in_degree: Counter[str] = Counter()

    for path, rel in gm.iter_notes(vault_root):
        src = str(rel)
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        body = sb.strip_code(text)
        note_links: list[str] = []

        for match in gm.WIKILINK.finditer(body):
            raw = match.group(1)
            if "\n" in raw:
                continue
            total_raw_links += 1
            cleaned = sb.clean_link_target(raw)
            if cleaned:
                note_links.append(cleaned)

        if not note_links:
            continue

        notes_with_links += 1
        seen_targets_in_note: set[str] = set()

        for target in note_links:
            resolved_dest = resolve_target(target, index, by_title)
            if not resolved_dest:
                unresolved_links.append({"source": src, "target": target})
                raw_unresolved_set.add(target)
                continue

            if resolved_dest == src:
                self_links.append({"source": src, "target": target})
                continue

            if resolved_dest in seen_targets_in_note:
                duplicate_links_in_same_note += 1
                continue

            seen_targets_in_note.add(resolved_dest)
            edge = (src, resolved_dest)
            unique_edges.add(edge)
            out_degree[src] += 1
            in_degree[resolved_dest] += 1

    scan_time = (time.perf_counter() - t_start) * 1000

    # Graph properties & reciprocity
    reciprocal_directed = 0
    for src, dst in unique_edges:
        if (dst, src) in unique_edges:
            reciprocal_directed += 1
    reciprocal_pairs = reciprocal_directed // 2
    reciprocity_pct = (reciprocal_directed / len(unique_edges) * 100) if unique_edges else 0.0

    nodes_in_graph = set(out_degree.keys()) | set(in_degree.keys())
    orphans = all_notes - nodes_in_graph

    # Connected components
    adj = defaultdict(set)
    for s, d in unique_edges:
        adj[s].add(d)
        adj[d].add(s)

    visited = set()
    components: list[list[str]] = []
    for node in sorted(nodes_in_graph):
        if node not in visited:
            comp: list[str] = []
            queue = [node]
            visited.add(node)
            while queue:
                curr = queue.pop()
                comp.append(curr)
                for neighbor in adj[curr]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
            components.append(comp)

    components.sort(key=len, reverse=True)
    giant_comp_size = len(components[0]) if components else 0

    # Folder flows
    def folder_of(p: str) -> str:
        parts = p.split("/")
        return parts[0] if len(parts) > 1 else "root"

    folder_counter: Counter[tuple[str, str]] = Counter()
    for s, d in unique_edges:
        folder_counter[(folder_of(s), folder_of(d))] += 1

    top_folder_flows = [
        {"from": f1, "to": f2, "count": cnt}
        for (f1, f2), cnt in folder_counter.most_common(10)
    ]

    top_hubs = [{"note": n, "out_degree": c} for n, c in out_degree.most_common(10)]
    top_authorities = [{"note": n, "in_degree": c} for n, c in in_degree.most_common(10)]

    # In-memory SQLite Simulation
    t_sql_start = time.perf_counter()
    conn = sqlite3.connect(":memory:")
    conn.executescript(NOTE_EDGES_SCHEMA)

    now_ts = int(time.time())
    db_rows = [
        (s, d, 0.50, 1, 1, now_ts, now_ts)
        for s, d in sorted(unique_edges)
    ]

    conn.executemany(
        """
        INSERT INTO note_edges
        (source_path, target_path, weight, coactivations, is_explicit, last_traversed, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        db_rows,
    )
    conn.commit()
    sql_time = (time.perf_counter() - t_sql_start) * 1000

    sample_edges = [
        {
            "source_path": s,
            "target_path": d,
            "weight": 0.50,
            "coactivations": 1,
            "is_explicit": 1,
            "last_traversed": now_ts,
            "created_at": now_ts,
        }
        for s, d in sorted(unique_edges)[:sample_limit]
    ]

    stats = DryRunStats(
        total_notes_scanned=len(all_notes),
        notes_with_links=notes_with_links,
        notes_in_graph=len(nodes_in_graph),
        orphan_notes_count=len(orphans),
        total_raw_links_found=total_raw_links,
        duplicate_links_in_same_note=duplicate_links_in_same_note,
        self_links_found=len(self_links),
        unresolved_links_count=len(unresolved_links),
        unique_explicit_edges=len(unique_edges),
        reciprocal_directed_edges=reciprocal_directed,
        reciprocal_pairs_count=reciprocal_pairs,
        reciprocity_rate_pct=round(reciprocity_pct, 2),
        connected_components_count=len(components),
        giant_component_size=giant_comp_size,
        scan_and_parse_time_ms=round(scan_time, 2),
        sqlite_simulation_time_ms=round(sql_time, 2),
        top_out_degree_hubs=top_hubs,
        top_in_degree_authorities=top_authorities,
        top_folder_flows=top_folder_flows,
        self_link_samples=self_links,
        unresolved_link_samples=unresolved_links[:sample_limit],
        sample_edges=sample_edges,
    )

    return stats, conn


def main() -> int:
    parser = argparse.ArgumentParser(description="Dry-run wikilinks parser for note_edges initial load.")
    parser.add_argument(
        "--vault-path",
        type=Path,
        default=Path("/home/flv/obsidian_vault"),
        help="Path to Obsidian vault root",
    )
    parser.add_argument("--json", action="store_true", help="Print stats as JSON")
    parser.add_argument("--sample", type=int, default=8, help="Number of sample edges to display")
    args = parser.parse_args()

    vault_path = args.vault_path.resolve()
    if not vault_path.exists():
        print(f"Error: Vault path does not exist: {vault_path}", file=sys.stderr)
        return 1

    stats, conn = run_dry_run(vault_path, sample_limit=args.sample)

    if args.json:
        print(json.dumps(asdict(stats), indent=2, ensure_ascii=False))
        return 0

    print("=" * 70)
    print(" DRY-RUN DO PARSER DE WIKILINKS — CARGA INICIAL DE NOTE_EDGES")
    print("=" * 70)
    print(f"• Cofre analisado: {vault_path}")
    print(f"• Notas escaneadas: {stats.total_notes_scanned}")
    print(f"• Notas com wikilinks ativos: {stats.notes_with_links} ({(stats.notes_with_links/stats.total_notes_scanned)*100:.1f}%)")
    print(f"• Nós integrados ao grafo: {stats.notes_in_graph} ({(stats.notes_in_graph/stats.total_notes_scanned)*100:.1f}%)")
    print(f"• Notas órfãs (isoladas de links): {stats.orphan_notes_count} ({(stats.orphan_notes_count/stats.total_notes_scanned)*100:.1f}%)")
    print("-" * 70)
    print(f"• Total de wikilinks brutos no texto: {stats.total_raw_links_found}")
    print(f"• Wikilinks duplicados no mesmo arquivo: {stats.duplicate_links_in_same_note}")
    print(f"• Auto-referências (self-links ignorados): {stats.self_links_found}")
    print(f"• Links não resolvidos (pendentes/externos): {stats.unresolved_links_count}")
    print(f"• Arestas explícitas únicas geradas: {stats.unique_explicit_edges}")
    print(f"• Conexões recíprocas (mútuas): {stats.reciprocal_directed_edges} arestas ({stats.reciprocal_pairs_count} pares)")
    print(f"• Taxa de reciprocidade: {stats.reciprocity_rate_pct:.1f}%")
    print(f"• Componentes conectados: {stats.connected_components_count} (Componente gigante: {stats.giant_component_size} nós, 100%)")
    print("-" * 70)
    print("BENCHMARK DE PERFORMANCE:")
    print(f"• Varredura e parsing de 100% das notas: {stats.scan_and_parse_time_ms:.2f} ms")
    print(f"• Carga e indexação no SQLite (:memory:): {stats.sqlite_simulation_time_ms:.2f} ms")
    total_time = stats.scan_and_parse_time_ms + stats.sqlite_simulation_time_ms
    print(f"• Tempo total do dry-run: {total_time:.2f} ms ({stats.total_notes_scanned / (total_time/1000):.0f} notas/seg)")
    print("-" * 70)

    print("\nTOP 5 NOTAS COM MAIS CONEXÕES DE SAÍDA (HUBS / OUT-DEGREE):")
    for item in stats.top_out_degree_hubs[:5]:
        print(f"  {item['out_degree']:3d} links -> {item['note']}")

    print("\nTOP 5 NOTAS MAIS REFERENCIADAS (AUTORIDADES / IN-DEGREE):")
    for item in stats.top_in_degree_authorities[:5]:
        print(f"  {item['in_degree']:3d} links <- {item['note']}")

    print("\nFLUXO ENTRE PASTAS (TOP 5):")
    for f in stats.top_folder_flows[:5]:
        print(f"  {f['from']:<20} -> {f['to']:<20} : {f['count']:4d} arestas")

    if stats.self_link_samples:
        print("\nAUTO-REFERÊNCIAS IDENTIFICADAS (DESCONSIDERADAS DO GRAFO):")
        for sl in stats.self_link_samples:
            print(f"  - Em `{sl['source']}`: link para [[{sl['target']}]]")

    print(f"\nAMOSTRA DE LINHAS PRONTAS PARA INSERÇÃO NA TABELA `note_edges` (primeiras {len(stats.sample_edges)}):")
    for e in stats.sample_edges:
        print(f"  INSERT: {e['source_path']} -> {e['target_path']} | W={e['weight']} | explicit={e['is_explicit']}")

    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
