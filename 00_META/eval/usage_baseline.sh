#!/usr/bin/env bash
# usage_baseline.sh <jsonl>...  -> TSV: session first_ctx assistant_msgs output cache_read cache_create input  (só usage numérico, nenhum conteúdo)
for f in "$@"; do
  jq -s -r --arg s "$(basename "$f" .jsonl | cut -c1-8)" '
    map(select(.type=="assistant" and (.isSidechain|not) and .message.usage != null)) as $m
    | if ($m|length)==0 then empty else
      ($m[0].message.usage) as $u
      | [$s, (($u.input_tokens//0)+($u.cache_creation_input_tokens//0)+($u.cache_read_input_tokens//0)),
         ($m|length), ($m|map(.message.usage.output_tokens//0)|add),
         ($m|map(.message.usage.cache_read_input_tokens//0)|add),
         ($m|map(.message.usage.cache_creation_input_tokens//0)|add),
         ($m|map(.message.usage.input_tokens//0)|add)] | @tsv end' "$f"
done
