#!/usr/bin/env bash
# vault_rank.sh [-k N] [-m MIN] [-c COV] [-t TERMS] [-n] <query...>      (sem argumentos, lê a query do stdin)
#
# Ranqueador único do second brain (RFC-001 §4.2): o L1, o note_candidates.sh e o
# adaptador `rank` do run_eval.py chamam este script, para o golden set medir o código
# que roda de verdade.
#
# Contract (keep stable):
#   - reads only 00_META/manifests/by_type/*.md (override: SECOND_BRAIN_MANIFEST_DIR);
#   - prints at most K lines (default 5), TSV: score<TAB>path<TAB>title<TAB>coverage<TAB>confidence, best first;
#     -n appends one more column, `terms`, the number of query terms (the denominator of coverage), so a caller
#     can tell a coverage of 1.0 over one term from one over six; without -n the columns do not change;
#   - only rows with score > MIN (default 0); prints nothing when no term matches;
#   - learning (on by default): a note that entered the context in >= 10 sessions of the last 7 days (<sid>.injected in
#     the state dir) has its score times 0.8 + 0.4 * r, r = share of those sessions where the agent also opened it
#     (<sid>.opened, session weight 1 -> 0.25 over the 7 days). The factor stays in [0.8, 1.2], never zeroes a note.
#     The rows (MIN and coverage use the base score) and the other columns stay the same, so a printed score can be
#     <= MIN. SECOND_BRAIN_RANK_LEARN=0|false|no|off turns it off (output identical to the script without learning);
#     SECOND_BRAIN_RANK_MIN_INJECTIONS=N sets the minimum; SECOND_BRAIN_RANK_NOW=<epoch> fixes "now" (tests);
#     state is read, never written; more than 3000 valid session files, or an unreadable state dir, skip it.
#     The golden set (run_eval.py) calls this script as is: measure it with SECOND_BRAIN_RANK_LEARN=0;
#   - the query reaches awk through ENVIRON, never `-v` (-v interprets backslashes);
#   - accents and case are folded on both sides (mawk's tolower is ASCII-only);
#   - grep/awk only, always exits 0, silent when the vault or the manifests are missing.
#
# State dir: SECOND_BRAIN_STATE_DIR (empty counts as unset), default ~/.local/state/second-brain.
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

learn=1
case "${SECOND_BRAIN_RANK_LEARN,,}" in 0 | false | no | off) learn=0 ;; esac
min_inj="${SECOND_BRAIN_RANK_MIN_INJECTIONS:-10}"
[[ "$min_inj" =~ ^[1-9][0-9]{0,8}$ ]] || min_inj=10
now="${SECOND_BRAIN_RANK_NOW:-}"
[[ "$now" =~ ^[0-9]{1,12}$ ]] || printf -v now '%(%s)T' -1
state_dir="${SECOND_BRAIN_STATE_DIR:-${HOME:-}/.local/state/second-brain}"
[[ "$state_dir" == /* ]] || state_dir="./$state_dir"  # a name starting with "-" must not become a find option

# find lists only regular files named <[A-Za-z0-9_-]+>.injected|.opened at depth 1: a FIFO, a directory (mawk aborts
# reading one) or a name with a newline never reaches the awk. The state dir is no awk operand, so "x=y" is no assignment.
export VR_QUERY="$query" VR_MIN="$min" VR_COV="$cov" VR_TERMS="$terms_min" VR_SHOW_TERMS="$show_terms" \
  VR_LEARN="$learn" VR_MINSESS="$min_inj" VR_NOW="$now" VR_STATE="$state_dir" \
  VR_FIND='find "$VR_STATE" -maxdepth 1 -type f \( -name "*.injected" -o -name "*.opened" \) ! -name "*[!A-Za-z0-9_-]*.injected" ! -name "*[!A-Za-z0-9_-]*.opened" -printf "%Ts %f\n"'

awk -F'|' '
  function trim(s) { gsub(/^[ \t]+|[ \t]+$/, "", s); return s }
  function fold(s,   i) {
    s = tolower(s)
    for (i = 1; i <= nacc; i++) gsub(acc_from[i], acc_to[i], s)
    return s
  }
  # Learning (see the header): reads <sid>.injected / <sid>.opened with getline, so an unreadable or vanished file
  # (-1) is skipped and never aborts the program, as an awk operand would. Changes sc[] for the rows in keep[].
  function learn(   cmd, line, sp, mt, name, age, w, n, i, f, sess, rc, p, nval, ni, no, minsess, now, dir, r, ratio) {
    now = ENVIRON["VR_NOW"] + 0; dir = ENVIRON["VR_STATE"]; minsess = ENVIRON["VR_MINSESS"] + 0
    cmd = ENVIRON["VR_FIND"]
    ni = 0; no = 0; nval = 0
    while ((cmd | getline line) > 0) {
      sp = index(line, " ")
      if (sp < 2) continue
      mt = substr(line, 1, sp - 1) + 0; name = substr(line, sp + 1)
      if (name !~ /^[A-Za-z0-9_-]+[.](injected|opened)$/) continue
      if (name ~ /[.]opened$/) { no++; ofile[no] = name; continue }  # its own age does not matter: the session decides
      age = now - mt; if (age < 0) age = 0
      if (age > WINDOW) continue
      ni++; ifile[ni] = name
      sess = name; sub(/[.]injected$/, "", sess)
      sessw[sess] = 1 - 0.75 * age / WINDOW
    }
    close(cmd)
    nval = ni
    for (i = 1; i <= no; i++) { sess = ofile[i]; sub(/[.]opened$/, "", sess); if (sess in sessw) nval++ }
    if (nval > MAXFILES) return
    for (i = 1; i <= ni; i++) {
      sess = ifile[i]; sub(/[.]injected$/, "", sess); w = sessw[sess]
      f = dir "/" ifile[i]
      while ((rc = (getline line < f)) > 0) {
        if (line in want && !((sess SUBSEP line) in injseen)) { injseen[sess, line] = 1; ninj[line]++; winj[line] += w }
      }
      close(f)
    }
    for (i = 1; i <= no; i++) {
      sess = ofile[i]; sub(/[.]opened$/, "", sess)
      if (!(sess in sessw)) continue
      f = dir "/" ofile[i]
      while ((rc = (getline line < f)) > 0) {
        if ((sess SUBSEP line) in injseen && !((sess SUBSEP line) in opseen)) { opseen[sess, line] = 1; wop[line] += sessw[sess] }
      }
      close(f)
    }
    for (i = 1; i <= nkeep; i++) {
      r = keep[i]; p = row_path[r]
      if (ninj[p] >= minsess && winj[p] > 0) {
        ratio = wop[p] / winj[p]
        sc[r] = sc[r] * (0.8 + 0.4 * ratio)
      }
    }
  }
  BEGIN {
    WINDOW = 604800; MAXFILES = 3000
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
    nkeep = 0
    for (r = 1; r <= nrows; r++) {
      score = 0; hit = 0
      for (j = 1; j <= nt; j++) {
        t = terms[j]
        w = index(ft[r], t) ? 3 : index(fg[r], t) ? 2 : (index(fp[r], t) || index(fs[r], t)) ? 1 : 0
        if (w) { idf = log((nrows + 1) / (df[t] + 0.5)); score += w * idf; hit += idf }
      }
      coverage = total > 0 ? hit / total : 0
      if (score > min && coverage >= mincov) {
        keep[++nkeep] = r; sc[r] = score; cv[r] = coverage; want[row_path[r]] = 1
      }
    }
    if (nkeep > 0 && ENVIRON["VR_LEARN"] == "1") learn()
    for (i = 1; i <= nkeep; i++) {
      r = keep[i]
      printf "%.3f\t%s\t%s\t%.3f\t%s", sc[r], row_path[r], row_title[r], cv[r], row_conf[r]
      if (ENVIRON["VR_SHOW_TERMS"] == "1") printf "\t%d", nt
      printf "\n"
    }
  }
' "${files[@]}" 2>/dev/null \
  | sort -t "$(printf '\t')" -k1,1nr -k2,2 2>/dev/null \
  | head -n "$k"

exit 0
