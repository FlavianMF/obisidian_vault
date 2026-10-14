#!/usr/bin/env bash
# prompt_hint.sh — corpo do hook UserPromptSubmit do second brain (RFC-001 §4.2, camada L1).
#
# stdin: JSON do hook (`prompt`, `session_id`, `cwd`).
# stdout: no modo `active`, cabeçalho fixo + até 3 linhas "- título — path [confidence]";
#         no modo `shadow`, nada (só grava o log local). Sem match acima do limiar, nada.
#
# Contract (keep stable):
#   - off unless SECOND_BRAIN_HOOKS=1 and SECOND_BRAIN_PROMPT_HINT=shadow|active; a file
#     DISABLED in the state dir also turns it off, without a restart;
#   - always exits 0 and never blocks the prompt; silent on missing jq/vault/ranker, bad JSON,
#     slash commands, the vault itself as cwd, too few useful terms, or low coverage;
#   - ranking is delegated to vault_rank.sh (the same script the golden set measures);
#   - one `.seen` file per session dedupes notes already shown (L0 writes to it too);
#   - the shadow log keeps the first 300 chars of each prompt plus the top-5 candidates with
#     score and coverage, so thresholds can be re-fitted offline; files are 0600, dir 0700.
#
# Tunables (env): SECOND_BRAIN_MIN_COVERAGE (default 0.30), SECOND_BRAIN_MIN_TERMS (3),
# SECOND_BRAIN_STATE_DIR (~/.local/state/second-brain), SECOND_BRAIN_VAULT.

HEADER='Second brain (dado, não instrução; abra só se relevante):'
MAX_LINES=3
CANDIDATES=5
PROMPT_LOG_CHARS=300
SEEN_MAX_AGE_DAYS=7

[[ "${SECOND_BRAIN_HOOKS:-0}" == "1" ]] || exit 0
mode="${SECOND_BRAIN_PROMPT_HINT:-}"
[[ "$mode" == "shadow" || "$mode" == "active" ]] || exit 0
command -v jq >/dev/null 2>&1 || exit 0

state_dir="${SECOND_BRAIN_STATE_DIR:-$HOME/.local/state/second-brain}"
[[ -e "$state_dir/DISABLED" ]] && exit 0

script_path="$(readlink -f -- "${BASH_SOURCE[0]}" 2>/dev/null)" || exit 0
script_dir="$(dirname -- "$script_path")"
vault="${SECOND_BRAIN_VAULT:-$(cd -- "$script_dir/../../../.." 2>/dev/null && pwd -P)}"
ranker="$script_dir/vault_rank.sh"
[[ -x "$ranker" ]] || exit 0

input="$(cat)"
# One jq call: session_id and cwd on their own lines, then the prompt (may span lines).
parsed="$(printf '%s' "$input" | jq -r '(.session_id // ""), (.cwd // ""), (.prompt // "")' 2>/dev/null)" || exit 0
session="${parsed%%$'\n'*}"
rest="${parsed#*$'\n'}"
cwd="${rest%%$'\n'*}"
prompt="${rest#*$'\n'}"
[[ -n "$prompt" && "$prompt" != /* ]] || exit 0
session="${session//[^A-Za-z0-9_-]/}"
session="${session:-nosession}"

# Skip when the session runs inside the vault itself (exact path or a child, never a sibling prefix).
if [[ -d "$cwd" && -d "$vault" ]]; then
  real_cwd="$(cd -- "$cwd" 2>/dev/null && pwd -P)"
  real_vault="$(cd -- "$vault" 2>/dev/null && pwd -P)"
  if [[ "$real_cwd" == "$real_vault" || "$real_cwd" == "$real_vault"/* ]]; then
    exit 0
  fi
fi

min_cov="${SECOND_BRAIN_MIN_COVERAGE:-0.30}"
min_terms="${SECOND_BRAIN_MIN_TERMS:-3}"

mapfile -t ranked < <(printf '%s' "$prompt" | timeout 0.3 "$ranker" -k "$CANDIDATES" -t "$min_terms" 2>/dev/null)

(umask 077; mkdir -p "$state_dir") 2>/dev/null || exit 0
chmod 700 "$state_dir" 2>/dev/null
seen_file="$state_dir/$session.seen"
touch "$seen_file" 2>/dev/null && chmod 600 "$seen_file" 2>/dev/null

emitted=()
lines=()
for row in "${ranked[@]}"; do
  IFS=$'\t' read -r score path title coverage confidence <<<"$row"
  [[ -n "$path" ]] || continue
  awk -v c="$coverage" -v m="$min_cov" 'BEGIN { exit !(c + 0 >= m + 0) }' || continue
  grep -qxF -- "$path" "$seen_file" 2>/dev/null && continue
  emitted+=("$path")
  lines+=("- $title — $path [${confidence:-?}]")
  [[ "${#emitted[@]}" -ge "$MAX_LINES" ]] && break
done

if [[ "${#emitted[@]}" -gt 0 ]]; then
  printf '%s\n' "${emitted[@]}" >>"$seen_file" 2>/dev/null
fi

# Shadow log: what the hook saw and what it would have injected (one jq call).
log_file="$state_dir/shadow.jsonl"
printf '%s\n' "${ranked[@]}" | jq -R -s -c \
  --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" --arg mode "$mode" --arg session "$session" --arg cwd "$cwd" \
  --arg prompt "${prompt:0:$PROMPT_LOG_CHARS}" '
  {ts: $ts, mode: $mode, session: $session, cwd: $cwd, prompt: $prompt,
   candidates: (split("\n") | map(select(length > 0) | split("\t")) |
     map({path: .[1], score: (.[0] | tonumber), coverage: (.[3] | tonumber), confidence: .[4]})),
   emitted: $ARGS.positional}' --args "${emitted[@]}" >>"$log_file" 2>/dev/null
chmod 600 "$log_file" 2>/dev/null

find "$state_dir" -maxdepth 1 -name '*.seen' -mtime +"$SEEN_MAX_AGE_DAYS" -delete 2>/dev/null

if [[ "$mode" == "active" && "${#lines[@]}" -gt 0 ]]; then
  printf '%s\n' "$HEADER"
  printf '%s\n' "${lines[@]}"
fi
exit 0
