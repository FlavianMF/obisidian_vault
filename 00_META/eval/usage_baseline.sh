#!/usr/bin/env bash
# usage_baseline.sh <jsonl>...  -> TSV: session first_ctx assistant_msgs output cache_read cache_create input  (só usage numérico, nenhum conteúdo)
# usage_baseline.sh --sidechain <jsonl>...  -> TSV: session scope agent_type model msgs output cache_read cache_create input eq
#   scope = main (thread principal) ou sub (um arquivo em <sessão>/subagents/agent-*.jsonl).
#   eq = input + cache_create*1.25 + cache_read*0.1 (tokens equivalentes a entrada, sem a saída).
#   Após as linhas da sessão vem uma linha extra, sem quebrar as colunas anteriores (mais curta, 6 colunas):
#     session router - - fires subs_after_first
#     fires = disparos do router da sessão em ${SECOND_BRAIN_STATE_DIR:-$HOME/.local/state/second-brain}/router.jsonl
#     ({"ts","session_id","class"}; class é opaca e ignorada); subs_after_first = subagentes cujo primeiro
#     timestamp é posterior ao 1º disparo. Arquivo ausente = 0 0.
# usage_baseline.sh --rereads <jsonl>...  -> TSV: session reads_main reads_sub repeated_sub_sub main_and_sub
#   Só conta tool_use "Read" (dedup por id) e compara input.file_path; nunca imprime caminho nem conteúdo.
#   repeated_sub_sub = leituras de subagente de um file_path já lido antes (timestamp) por OUTRO subagente.
#   main_and_sub = file_paths distintos lidos pela main e por >=1 subagente.
# O Claude Code grava uma entrada por bloco de conteúdo, todas com a mesma usage da resposta:
# as respostas são deduplicadas por message.id antes de somar.

DEDUP='map(select(.type=="assistant" and .message.usage != null)) | unique_by(.message.id // .uuid) | sort_by(.timestamp)'

sidechain=0 rereads=0
if [ "${1:-}" = "--sidechain" ]; then sidechain=1; shift
elif [ "${1:-}" = "--rereads" ]; then rereads=1; shift; fi

sum_tsv() {  # $1 jsonl, $2 session, $3 scope, $4 agent_type
  jq -s -r --arg s "$2" --arg scope "$3" --arg t "$4" "
    $DEDUP | if length==0 then empty else
      [\$s, \$scope, \$t, (map(.message.model // \"?\")|unique|join(\",\")), length,
       (map(.message.usage.output_tokens//0)|add),
       (map(.message.usage.cache_read_input_tokens//0)|add),
       (map(.message.usage.cache_creation_input_tokens//0)|add),
       (map(.message.usage.input_tokens//0)|add)]
      | . + [(.[8] + .[7]*1.25 + .[6]*0.1 | floor)] | @tsv end" "$1"
}

reads_stream() {  # $1 jsonl, $2 agente (main ou nome do arquivo) -> uma linha JSON por Read
  jq -c --arg a "$2" 'select(.type=="assistant") | .timestamp as $t
    | .message.content[]? | select(.type=="tool_use" and .name=="Read" and (.input.file_path|type)=="string")
    | {a:$a, id:(.id // ""), t:($t // ""), p:.input.file_path}' "$1" 2>/dev/null
}

if [ "$rereads" = 1 ]; then
  for f in "$@"; do
    s="$(basename "$f" .jsonl | cut -c1-8)"
    {
      reads_stream "$f" main
      for a in "$(dirname "$f")/$(basename "$f" .jsonl)/subagents"/agent-*.jsonl; do
        [ -e "$a" ] || continue
        reads_stream "$a" "$(basename "$a" .jsonl)"
      done
    } | jq -s -r --arg s "$s" '
      unique_by([.a, (if .id=="" then .p+.t else .id end)]) | sort_by(.t) as $r
      | ($r|map(select(.a=="main"))) as $m | ($r|map(select(.a!="main"))) as $u
      | (reduce $u[] as $x ({seen:{}, rep:0};
          if (.seen[$x.p] // [] | any(. != $x.a)) then .rep += 1 else . end
          | .seen[$x.p] = ((.seen[$x.p] // []) + [$x.a] | unique))) as $st
      | [$s, ($m|length), ($u|length), $st.rep,
         (($m|map(.p)|unique) - (($m|map(.p)|unique) - ($u|map(.p)|unique)) | length)] | @tsv'
  done
  exit 0
fi

router_file="${SECOND_BRAIN_STATE_DIR:-$HOME/.local/state/second-brain}/router.jsonl"

router_row() {  # $1 jsonl principal, $2 session curto
  local sid first=""; sid="$(basename "$1" .jsonl)"
  if [ -r "$router_file" ]; then
    first="$(jq -r --arg sid "$sid" 'select(.session_id==$sid) | .ts // empty' "$router_file" 2>/dev/null | sort | head -1)"
    fires="$(jq -r --arg sid "$sid" 'select(.session_id==$sid) | 1' "$router_file" 2>/dev/null | grep -c 1)"
  else fires=0; fi
  after=0
  if [ -n "$first" ]; then
    after="$(for a in "${1%.jsonl}/subagents"/agent-*.jsonl; do
      [ -e "$a" ] || continue
      jq -s -r --arg f "$first" '
        def e: sub("\\.[0-9]+Z$";"Z") | fromdateiso8601;
        (map(.timestamp // empty) | sort | .[0]) as $t
        | if $t != null and ($t|e) > ($f|e) then 1 else empty end' "$a" 2>/dev/null
    done | grep -c 1 || true)"
  fi
  printf '%s\trouter\t-\t-\t%s\t%s\n' "$2" "${fires:-0}" "${after:-0}"
}

for f in "$@"; do
  s="$(basename "$f" .jsonl | cut -c1-8)"
  if [ "$sidechain" = 1 ]; then
    sum_tsv "$f" "$s" main -
    d="${f%.jsonl}/subagents"
    for a in "$d"/agent-*.jsonl; do
      [ -e "$a" ] || continue
      m="${a%.jsonl}.meta.json"
      t="$( [ -e "$m" ] && jq -r '.agentType // "?"' "$m" || echo "?")"
      sum_tsv "$a" "$s" sub "$t"
    done
    router_row "$f" "$s"
    continue
  fi
  jq -s -r --arg s "$s" "
    map(select(.isSidechain|not)) | $DEDUP as \$m
    | if (\$m|length)==0 then empty else
      (\$m[0].message.usage) as \$u
      | [\$s, ((\$u.input_tokens//0)+(\$u.cache_creation_input_tokens//0)+(\$u.cache_read_input_tokens//0)),
         (\$m|length), (\$m|map(.message.usage.output_tokens//0)|add),
         (\$m|map(.message.usage.cache_read_input_tokens//0)|add),
         (\$m|map(.message.usage.cache_creation_input_tokens//0)|add),
         (\$m|map(.message.usage.input_tokens//0)|add)] | @tsv end" "$f"
done
