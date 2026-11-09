#!/usr/bin/env bash
# session_hint.sh <repo_basename> [--full]
#
# Contract (consumed by the dotfiles SessionStart hook — keep stable):
#   - default: prints a compact 1-line hint informing that the vault is active and can be queried on demand via `sb search <termo>`.
#   - with --full: prints at most 5 lines: "<title> — <path> (<type>)", most relevant first;
#   - relevance: provenance/seen_in naming the repo beat title/tags/path mentioning
#     it; then trap/pattern/decision beat project/moc/concept beat the rest; ties
#     break by newest `created`, then path;
#   - prints nothing when there is no match, no argument, or no vault;
#   - always exits 0; grep/awk only (no python), reads only 00_META/manifests/.
# The vault root is resolved from this script's own location (symlinks followed)
# or SECOND_BRAIN_MANIFEST_DIR / SECOND_BRAIN_VAULT when set,
# so it works from any cwd and via ~/.claude/skills or ~/.agents/skills links.

full=0
repo=""
for arg in "$@"; do
  case "$arg" in
    --full) full=1 ;;
    *) [ -z "$repo" ] && repo="$arg" ;;
  esac
done

[ -n "$repo" ] || exit 0

if [ -n "${SECOND_BRAIN_MANIFEST_DIR:-}" ]; then
  manifest_dir="$SECOND_BRAIN_MANIFEST_DIR"
else
  script_path="$(readlink -f -- "${BASH_SOURCE[0]}" 2>/dev/null)" || exit 0
  vault_root="${SECOND_BRAIN_VAULT:-$(cd -- "$(dirname -- "$script_path")/../../../.." 2>/dev/null && pwd)}" || exit 0
  manifest_dir="$vault_root/00_META/manifests/by_type"
fi
[ -d "$manifest_dir" ] || exit 0

shopt -s nullglob
files=("$manifest_dir"/*.md)
[ "${#files[@]}" -gt 0 ] || exit 0

matches="$(awk -F'|' -v repo="$repo" '
  function trim(s) { gsub(/^[ \t]+|[ \t]+$/, "", s); return s }
  function has(hay, a, b) { hay = tolower(hay); return index(hay, a) || index(hay, b) }
  BEGIN {
    a = tolower(repo); b = a
    gsub(/-/, "_", a); gsub(/_/, "-", b)
  }
  FNR <= 2 { next }                       # header + separator
  {
    path = trim($2); title = trim($3); tags = trim($4)
    created = trim($5); prov = trim($6); seen = trim($8)
    if (path == "") next
    tier = 0
    if (has(prov, a, b) || has(seen, a, b)) tier = 2
    else if (has(title, a, b) || has(tags, a, b) || has(path, a, b)) tier = 1
    if (!tier) next
    type = FILENAME; sub(/.*\//, "", type); sub(/(_[0-9]{4}H[12](-[0-9]+)?)?\.md$/, "", type)
    prio = (type ~ /^(trap|pattern|decision)$/) ? 2 : (type ~ /^(project|moc|concept)$/) ? 1 : 0
    printf "%d\t%d\t%s\t%s\t%s — %s (%s)\n", tier, prio, created, path, title, path, type
  }
' "${files[@]}" 2>/dev/null \
  | sort -t "$(printf '\t')" -k1,1nr -k2,2nr -k3,3r -k4,4 2>/dev/null \
  | head -n 5 \
  | cut -f5-)"

[ -n "$matches" ] || exit 0

if [ "$full" -eq 1 ]; then
  printf '%s\n' "$matches"
else
  printf '[Second Brain] Cofre ativo. Consulte notas sob demanda via: sb search <termo>\n'
fi

exit 0
