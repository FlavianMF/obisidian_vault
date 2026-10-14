#!/usr/bin/env bash
# note_candidates.sh [-k N] "<título>" ["<tags>"]
#
# Antes de criar nota: lista as notas do vault que já cobrem o assunto (RFC-001 §5, F2).
# Há candidato → atualize a nota existente (entrada datada + projeto em `seen_in`) em vez de
# criar outra; sem candidato, nada é impresso.
#
# Contract (keep stable):
#   - stdout: até K linhas (default 3), TSV: path<TAB>title<TAB>coverage<TAB>confidence;
#   - o ranqueador é o vault_rank.sh (o mesmo do L1 e do golden set); a query é título + tags;
#   - só candidatos com coverage >= SECOND_BRAIN_CANDIDATE_COVERAGE (default 0.25), porque
#     aqui um falso positivo custa uma leitura e um falso negativo custa nota duplicada;
#   - cada chamada vai para ~/.local/state/second-brain/note_candidates.jsonl (0600), que é o
#     detector mensurável da F2; sempre exit 0.

K=3
MIN_COVERAGE_DEFAULT=0.25
if [[ "${1:-}" == "-k" && "${2:-}" =~ ^[0-9]+$ ]]; then K="$2"; shift 2; fi

title="${1:-}"
tags="${2:-}"
[[ -n "$title" ]] || exit 0

script_path="$(readlink -f -- "${BASH_SOURCE[0]}" 2>/dev/null)" || exit 0
script_dir="$(dirname -- "$script_path")"
ranker="$script_dir/vault_rank.sh"
[[ -x "$ranker" ]] || exit 0

# SECOND_BRAIN_VAULT só existe para testes e vaults fora do padrão: aponta o manifest.
if [[ -n "${SECOND_BRAIN_VAULT:-}" && -z "${SECOND_BRAIN_MANIFEST_DIR:-}" ]]; then
  export SECOND_BRAIN_MANIFEST_DIR="$SECOND_BRAIN_VAULT/00_META/manifests/by_type"
fi

min_cov="${SECOND_BRAIN_CANDIDATE_COVERAGE:-$MIN_COVERAGE_DEFAULT}"
query="$title ${tags//,/ }"
ranked="$("$ranker" -k "$K" -c "$min_cov" -t 1 "$query" 2>/dev/null)"

if [[ -n "$ranked" ]]; then
  while IFS=$'\t' read -r _score path row_title coverage confidence; do
    printf '%s\t%s\t%s\t%s\n' "$path" "$row_title" "$coverage" "$confidence"
  done <<<"$ranked"
fi

state_dir="${SECOND_BRAIN_STATE_DIR:-$HOME/.local/state/second-brain}"
if command -v jq >/dev/null 2>&1 && (umask 077; mkdir -p "$state_dir") 2>/dev/null; then
  log_file="$state_dir/note_candidates.jsonl"
  printf '%s' "$ranked" | jq -R -s -c \
    --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" --arg title "$title" --arg tags "$tags" --arg cwd "$PWD" '
    {ts: $ts, title: $title, tags: $tags, cwd: $cwd,
     candidates: (split("\n") | map(select(length > 0) | split("\t")) |
       map({path: .[1], score: (.[0] | tonumber), coverage: (.[3] | tonumber)}))}' >>"$log_file" 2>/dev/null
  chmod 600 "$log_file" 2>/dev/null
fi
exit 0
