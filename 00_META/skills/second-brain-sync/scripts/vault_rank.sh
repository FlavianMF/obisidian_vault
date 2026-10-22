#!/usr/bin/env bash
# vault_rank.sh [-k N] [-m MIN] [-c COV] [-t TERMS] [-n] <query...>      (sem argumentos, lê a query do stdin)
#
# Ranqueador único do second brain (RFC-001 §4.2): o L1, o note_candidates.sh e o
# adaptador `rank` do run_eval.py chamam este script, para o golden set medir o código
# que roda de verdade.
#
# Contract (keep stable):
#   - reads only 00_META/manifests/by_type/*.md (override: SECOND_BRAIN_MANIFEST_DIR);
#   - prints at most K lines (default 5), TSV: score<TAB>path<TAB>title, best first;
#     -n appends one more column, the number of query terms (the denominator of coverage), so a caller
#     can tell a coverage of 1.0 over one term from one over six; without -n the columns do not change;
#   - only rows with score > MIN (default 0); prints nothing when no term matches;
#   - the query reaches awk through ENVIRON, never `-v` (-v interprets backslashes);
#   - accents and case are folded on both sides (mawk's tolower is ASCII-only);
#   - grep/awk only, always exits 0, silent when the vault or the manifests are missing.
#
# Score = sum over distinct query terms (>= 4 chars, no stopwords) of idf(term) * weight,
# weight = 3 title, 2 tags, 1 path/summary (the highest field that contains the term; a
# term matches as a substring, so "agente" also hits "agentes"). idf = ln((N+1)/(df+0.5)).

k=5
min=0
cov=0
terms_min=1
show_terms=0
while getopts "k:m:c:t:n" opt; do
  case "$opt" in
    k) k="$OPTARG" ;;
    m) min="$OPTARG" ;;
    c) cov="$OPTARG" ;;
    t) terms_min="$OPTARG" ;;
    n) show_terms=1 ;;
    *) exit 0 ;;
  esac
done
shift $((OPTIND - 1))
[[ "$k" =~ ^[0-9]+$ ]] || k=5
[[ "$min" =~ ^[0-9]+([.][0-9]+)?$ ]] || min=0
[[ "$cov" =~ ^[0-9]+([.][0-9]+)?$ ]] || cov=0
[[ "$terms_min" =~ ^[0-9]+$ ]] || terms_min=1

if [ "$#" -gt 0 ]; then
  query="$*"
else
  query="$(cat)"
fi
[ -n "$query" ] || exit 0

script_path="$(readlink -f -- "${BASH_SOURCE[0]}" 2>/dev/null)" || exit 0
vault_root="$(cd -- "$(dirname -- "$script_path")/../../../.." 2>/dev/null && pwd)" || exit 0
manifest_dir="${SECOND_BRAIN_MANIFEST_DIR:-$vault_root/00_META/manifests/by_type}"
[ -d "$manifest_dir" ] || exit 0

shopt -s nullglob
files=("$manifest_dir"/*.md)
[ "${#files[@]}" -gt 0 ] || exit 0

export VR_QUERY="$query" VR_MIN="$min" VR_COV="$cov" VR_TERMS="$terms_min" VR_SHOW_TERMS="$show_terms"

awk -F'|' '
  function trim(s) { gsub(/^[ \t]+|[ \t]+$/, "", s); return s }
  function fold(s,   i) {
    s = tolower(s)
    for (i = 1; i <= nacc; i++) gsub(acc_from[i], acc_to[i], s)
    return s
  }
  BEGIN {
    nacc = split("á à â ã ä é è ê ë í ì î ï ó ò ô õ ö ú ù û ü ç ñ Á À Â Ã Ä É È Ê Ë Í Ì Î Ï Ó Ò Ô Õ Ö Ú Ù Û Ü Ç Ñ", acc_from, " ")
    split("a a a a a e e e e i i i i o o o o o u u u u c n a a a a a e e e e i i i i o o o o o u u u u c n", acc_to, " ")
    stoplist = "para como mais mas pelo pela pelos pelas seu sua seus suas ele ela eles elas isso esse essa esses essas este esta estes estas quando onde qual quais todo toda todos todas tudo ser ter foi sao tem sem sobre entre depois antes ainda tambem muito meu minha meus minhas fazer feito faco pode podem posso deve devo quero preciso usar uso vez uma uns umas nao nos nas dos das com por que the and for with that this from how what when where which into your have been does using use should would could"
    ns = split(stoplist, sw, " "); for (i = 1; i <= ns; i++) stop[sw[i]] = 1
    q = fold(ENVIRON["VR_QUERY"])
    n = split(q, raw, /[^a-z0-9]+/)
    nt = 0
    for (i = 1; i <= n; i++) {
      t = raw[i]
      if (length(t) >= 4 && !(t in stop) && !(t in seen)) { seen[t] = 1; terms[++nt] = t }
    }
    if (nt == 0 || nt < ENVIRON["VR_TERMS"] + 0) { skip = 1; exit }
    nrows = 0
  }
  /^\| / {
    path = trim($2)
    if (path == "" || path == "Path" || path ~ /^-+$/) next
    nrows++
    row_path[nrows] = path
    row_title[nrows] = trim($3)
    row_conf[nrows] = trim($7)
    ft[nrows] = fold(trim($3)); fg[nrows] = fold(trim($4)); fp[nrows] = fold(path)
    fs[nrows] = (NF >= 10) ? fold(trim($9)) : ""
    for (j = 1; j <= nt; j++) {
      t = terms[j]
      if (index(ft[nrows], t) || index(fg[nrows], t) || index(fp[nrows], t) || index(fs[nrows], t)) df[t]++
    }
  }
  END {
    if (skip || nrows == 0) exit
    min = ENVIRON["VR_MIN"] + 0
    mincov = ENVIRON["VR_COV"] + 0
    total = 0
    for (j = 1; j <= nt; j++) total += log((nrows + 1) / (df[terms[j]] + 0.5))
    for (r = 1; r <= nrows; r++) {
      score = 0; hit = 0
      for (j = 1; j <= nt; j++) {
        t = terms[j]
        w = index(ft[r], t) ? 3 : index(fg[r], t) ? 2 : (index(fp[r], t) || index(fs[r], t)) ? 1 : 0
        if (w) { idf = log((nrows + 1) / (df[t] + 0.5)); score += w * idf; hit += idf }
      }
      coverage = total > 0 ? hit / total : 0
      if (score > min && coverage >= mincov) {
        printf "%.3f\t%s\t%s\t%.3f\t%s", score, row_path[r], row_title[r], coverage, row_conf[r]
        if (ENVIRON["VR_SHOW_TERMS"] == "1") printf "\t%d", nt
        printf "\n"
      }
    }
  }
' "${files[@]}" 2>/dev/null \
  | sort -t "$(printf '\t')" -k1,1nr -k2,2 2>/dev/null \
  | head -n "$k"

exit 0
