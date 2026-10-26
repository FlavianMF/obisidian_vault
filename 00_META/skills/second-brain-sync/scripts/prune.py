"""Pruner de saída de ferramenta (PostToolUse): corta saída longa de Bash/Grep/Glob e guarda a íntegra em spill.

Estado: <state>/spill/<session>/<tool_use_id>.txt (dirs 0700, arquivos 0600) e <state>/prune.jsonl (só métricas,
nunca conteúdo nem o comando inteiro). Todo ponto de entrada engole erros: um hook não pode quebrar a sessão.
Desliga com SB_PRUNE=0|false|off|no, arquivo DISABLED no state dir ou `# sb:raw` no comando Bash.
"""
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

SPILL_DIR = "spill"
LOG_NAME = "prune.jsonl"
GC_STAMP = ".gc"
TTL_DAYS = 7
DEFAULT_MIN_CHARS = 10000
DIFF_MIN_CHARS = 30000
TEST_MIN_CHARS = 2000
LIST_MAX_LINES = 80
HEAD_LINES = 60
TAIL_LINES = 40
TEST_TAIL_LINES = 15
TEST_CONTEXT = 3
TEST_MAX_FAIL_LINES = 200
EXEMPT_PROGS = {"cat", "sed", "head", "tail", "less", "nl", "bat", "jq"}
LIST_PROGS = {"ls", "find", "fd", "rg", "grep"}
DIFF_SUBCMDS = {"diff", "show", "log"}
SEPARATORS = ("&&", "||", ";", "|", "\n")
FAIL_RE = re.compile(r"FAIL|ERROR|Error|error:|Traceback|assert|Assertion|panic|not ok|Exception|✗|✘")
PASS_RE = re.compile(r"PASSED|\.\.\. ok$|^ok\b|^PASS\b|✓")  # linha de teste aprovado nunca puxa contexto
SAFE_NAME = re.compile(r"[^A-Za-z0-9_.-]")
OFF_VALUES = ("0", "false", "off", "no")


def enabled(state_dir: Path, env: dict) -> bool:
    if (state_dir / "DISABLED").exists():
        return False
    return (env.get("SB_PRUNE") or "").strip().lower() not in OFF_VALUES


def min_chars(env: dict) -> int:
    try:
        return max(1, int(env.get("SB_PRUNE_MIN_CHARS") or DEFAULT_MIN_CHARS))
    except ValueError:
        return DEFAULT_MIN_CHARS


# ---------------------------------------------------------------- análise do comando

def split_command(command: str) -> list[tuple[str, str]]:
    """[(separador_anterior, segmento)] respeitando aspas simples e duplas."""
    parts: list[tuple[str, str]] = []
    buf: list[str] = []
    sep = ""
    quote = ""
    i = 0
    while i < len(command):
        ch = command[i]
        if quote:
            buf.append(ch)
            if ch == "\\" and quote == '"' and i + 1 < len(command):
                buf.append(command[i + 1])
                i += 1
            elif ch == quote:
                quote = ""
            i += 1
            continue
        if ch in "'\"":
            quote = ch
            buf.append(ch)
            i += 1
            continue
        hit = next((s for s in SEPARATORS if command.startswith(s, i)), "")
        if hit:
            parts.append((sep, "".join(buf).strip()))
            buf, sep = [], hit
            i += len(hit)
            continue
        buf.append(ch)
        i += 1
    parts.append((sep, "".join(buf).strip()))
    return [(s, seg) for s, seg in parts if seg]


def tokens(segment: str) -> list[str]:
    out = re.findall(r"""(?:[^\s'"]+|'[^']*'|"[^"]*")+""", segment)
    while out and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=\S*", out[0]):  # VAR=x
        out.pop(0)
    while out and out[0] in ("time", "sudo", "nice"):
        out.pop(0)
    if out[:2] == ["uv", "run"]:
        out = out[2:]
    return [t.strip("'\"") if i == 0 else t for i, t in enumerate(out)]


def analyze(command: str) -> tuple[list[str], bool]:
    """(tokens do 1º programa, True se o pipeline dele termina em head/tail/sed -n/wc)."""
    parts = split_command(command)
    start = -1
    for idx, (_, seg) in enumerate(parts):
        toks = tokens(seg)
        if toks and toks[0] not in ("cd", "export", "set", "source", "."):
            start = idx
            break
    if start < 0:
        return [], False
    first = tokens(parts[start][1])
    last = first
    piped = False
    for sep, seg in parts[start + 1:]:
        if sep != "|":
            break
        last = tokens(seg)
        piped = True
    limited = piped and bool(last) and (os.path.basename(last[0]) in ("head", "tail", "wc")
                                        or (os.path.basename(last[0]) == "sed" and "-n" in last[1:]))
    return first, limited


def program_name(toks: list[str]) -> str:
    return os.path.basename(toks[0]) if toks else ""


def is_test_command(toks: list[str]) -> bool:
    if not toks:
        return False
    prog, rest = program_name(toks), toks[1:]
    if prog in ("pytest", "py.test", "bats"):
        return True
    if prog in ("python", "python3") and rest[:1] == ["-m"] and rest[1:2] in (["pytest"], ["unittest"]):
        return True
    if prog in ("npm", "pnpm", "yarn") and (rest[:1] == ["test"] or rest[:2] == ["run", "test"]):
        return True
    if prog in ("go", "cargo", "make") and rest[:1] == ["test"]:
        return True
    return prog in ("bash", "sh") and bool(rest) and re.fullmatch(r"(?:.*/)?tests/[^/]*_test\.sh", rest[0]) is not None


def is_list_command(toks: list[str]) -> bool:
    if program_name(toks) in LIST_PROGS:
        return True
    return program_name(toks) == "git" and "ls-files" in toks[1:3]


def git_diff_like(toks: list[str]) -> bool:
    if program_name(toks) != "git":
        return False
    sub = next((t for t in toks[1:] if not t.startswith("-")), "")
    return sub in DIFF_SUBCMDS


# ---------------------------------------------------------------- regras

def marker(shown: int, total: int, rule: str, path: str) -> str:
    return (f"[sb-prune: {shown} de {total} linhas mostradas (regra {rule}); saída completa em {path}; "
            f"leia trechos com sed -n 'a,bp' {path} ou rode de novo com # sb:raw]")


def _with_gaps(lines: list[str], idxs: list[int]) -> list[str]:
    out: list[str] = []
    prev = -1
    for idx in idxs:
        if idx != prev + 1:
            out.append(f"[... {idx - prev - 1} linhas omitidas ...]")
        out.append(lines[idx])
        prev = idx
    if prev != len(lines) - 1:
        out.append(f"[... {len(lines) - 1 - prev} linhas omitidas ...]")
    return out


def _rule_tests(lines: list[str]) -> list[str]:
    keep: set[int] = set()
    fails = 0
    for idx, line in enumerate(lines):
        if FAIL_RE.search(line) and not PASS_RE.search(line):
            fails += 1
            if fails > TEST_MAX_FAIL_LINES:
                break
            keep.update(range(max(0, idx - TEST_CONTEXT), min(len(lines), idx + TEST_CONTEXT + 1)))
    keep.update(range(max(0, len(lines) - TEST_TAIL_LINES), len(lines)))
    return _with_gaps(lines, sorted(keep))


def select_rule(toks: list[str], limited: bool, tool: str) -> tuple[str, int]:
    """(regra, limiar de chars; 0 = usa o da regra). Regra '' = isento (R0)."""
    if tool in ("Grep", "Glob"):
        return "R2", 0
    if not toks or limited or program_name(toks) in EXEMPT_PROGS:
        return "", 0
    if is_test_command(toks):
        return "R1", TEST_MIN_CHARS
    if is_list_command(toks):
        return "R2", 0
    if git_diff_like(toks):
        return "R3", DIFF_MIN_CHARS
    return "R3", 0


def apply_rule(rule: str, text: str, threshold: int, env: dict) -> tuple[list[str], int, int] | None:
    """(linhas a mostrar, quantas são originais, total de linhas) ou None quando nada a podar."""
    limit = threshold or (min_chars(env) if rule == "R3" else 0)
    if len(text) <= limit:
        return None
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    total = len(lines)
    if rule == "R1":
        shown = _rule_tests(lines)
        count = sum(1 for x in shown if not x.startswith("[... "))
    elif rule == "R2":
        shown, count = lines[:LIST_MAX_LINES], min(LIST_MAX_LINES, total)
    else:
        omitted = total - HEAD_LINES - TAIL_LINES
        if omitted <= 0:
            return None
        shown = lines[:HEAD_LINES] + [f"[... {omitted} linhas omitidas ...]"] + lines[-TAIL_LINES:]
        count = HEAD_LINES + TAIL_LINES
    if count >= total:
        return None
    return shown, count, total


def prune_text(rule: str, text: str, threshold: int, env: dict, path: str) -> tuple[str, dict] | None:
    result = apply_rule(rule, text, threshold, env)
    if result is None:
        return None
    shown, count, total = result
    out = "\n".join(shown) + "\n" + marker(count, total, rule, path)
    return out, {"lines_in": total, "lines_out": count, "chars_in": len(text), "chars_out": len(out)}


# ---------------------------------------------------------------- por ferramenta (ajustar aqui a forma real)

def prune_bash(payload: dict, resp: dict, env: dict, path: str) -> tuple[dict, str, dict] | None:
    command = (payload.get("tool_input") or {}).get("command")
    if not isinstance(command, str) or "# sb:raw" in command:
        return None
    toks, limited = analyze(command)
    rule, threshold = select_rule(toks, limited, "Bash")
    if not rule:
        return None
    new = dict(resp)
    stats = {"lines_in": 0, "lines_out": 0, "chars_in": 0, "chars_out": 0}
    changed = False
    for key in ("stdout", "stderr"):
        text = resp.get(key)
        if not isinstance(text, str):
            continue
        done = prune_text(rule, text, threshold, env, path)
        if done is None:
            continue
        new[key], part = done
        changed = True
        for name in stats:
            stats[name] += part[name]
    return (new, rule, {**stats, "prog": program_name(toks)}) if changed else None


def prune_listing(tool: str, resp: dict, env: dict, path: str) -> tuple[dict, str, dict] | None:
    """Grep/Glob: campo string `content` ou lista `filenames`; qualquer outra forma é no-op."""
    new = dict(resp)
    content = resp.get("content")
    names = resp.get("filenames")
    if isinstance(content, str):
        done = prune_text("R2", content, 0, env, path)
        if done is None:
            return None
        new["content"], stats = done
        if isinstance(resp.get("numLines"), int):
            new["numLines"] = stats["lines_out"]  # totalLines fica com o original
        return new, "R2", {**stats, "prog": tool.lower()}
    if isinstance(names, list) and all(isinstance(x, str) for x in names) and len(names) > LIST_MAX_LINES:
        total = len(names)
        new["filenames"] = names[:LIST_MAX_LINES] + [marker(LIST_MAX_LINES, total, "R2", path)]
        if tool == "Glob":
            new["truncated"] = True  # numFiles/totalMatches ficam com o original
        return new, "R2", {"lines_out": LIST_MAX_LINES, "lines_in": total, "prog": tool.lower(),
                           "chars_in": sum(len(x) + 1 for x in names),
                           "chars_out": sum(len(x) + 1 for x in new["filenames"])}
    return None


def prune_grep(payload: dict, resp: dict, env: dict, path: str):
    return prune_listing("Grep", resp, env, path)


def prune_glob(payload: dict, resp: dict, env: dict, path: str):
    return prune_listing("Glob", resp, env, path)


TOOLS = {"Bash": prune_bash, "Grep": prune_grep, "Glob": prune_glob}


# ---------------------------------------------------------------- spill, log, gc

def safe_name(value: object, fallback: str) -> str:
    text = SAFE_NAME.sub("_", value).lstrip(".")[:120] if isinstance(value, str) else ""
    return text or fallback


def spill_path(state_dir: Path, payload: dict) -> Path:
    session = safe_name(payload.get("session_id"), "nosession")
    use = safe_name(payload.get("tool_use_id"), f"t{int(time.time() * 1000)}")
    return state_dir / SPILL_DIR / session / f"{use}.txt"


def write_spill(target: Path, resp: dict, tool: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(target.parent, 0o700)
    os.chmod(target.parent.parent, 0o700)
    if tool == "Bash":
        body = f"== stdout ==\n{resp.get('stdout') or ''}\n== stderr ==\n{resp.get('stderr') or ''}\n"
    else:
        body = json.dumps(resp, ensure_ascii=False, indent=1)
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as out:
        out.write(body)
    os.chmod(target, 0o600)


def log_event(state_dir: Path, entry: dict) -> None:
    state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(state_dir / LOG_NAME, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    with os.fdopen(fd, "a", encoding="utf-8") as out:
        out.write(json.dumps(entry, ensure_ascii=False) + "\n")


def gc(state_dir: Path, force: bool = False) -> int:
    """Apaga spills com mais de TTL_DAYS; no máximo uma vez por dia, a menos que force."""
    root = state_dir / SPILL_DIR
    stamp = root / GC_STAMP
    now = time.time()
    try:
        if not force and now - stamp.stat().st_mtime < 86400:
            return 0
    except OSError:
        pass
    removed = 0
    try:
        for session in root.iterdir():
            if not session.is_dir():
                continue
            for item in session.iterdir():
                if item.is_file() and item.stat().st_mtime < now - TTL_DAYS * 86400:
                    item.unlink(missing_ok=True)
                    removed += 1
            try:
                session.rmdir()  # só se vazio
            except OSError:
                pass
        stamp.touch()
    except OSError:
        pass
    return removed


# ---------------------------------------------------------------- hook

def hook_output(state_dir: Path, payload: dict, env: dict) -> str:
    """JSON do PostToolUse, ou '' quando não poda."""
    if not enabled(state_dir, env):
        return ""
    tool = payload.get("tool_name")
    resp = payload.get("tool_response")
    handler = TOOLS.get(tool)
    if handler is None or not isinstance(resp, dict):
        return ""
    target = spill_path(state_dir, payload)
    done = handler(payload, resp, env, str(target))
    if done is None:
        return ""
    new, rule, stats = done
    try:
        write_spill(target, resp, tool)  # sem spill a marca mentiria: então não poda
    except OSError:
        return ""
    try:
        log_event(state_dir, {"ts": int(time.time()), "session_id": safe_name(payload.get("session_id"), ""),
                              "tool": tool, "prog": stats["prog"], "rule": rule,
                              **{k: stats[k] for k in ("chars_in", "chars_out", "lines_in", "lines_out")}})
    except OSError:
        pass
    gc(state_dir)
    return json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "updatedToolOutput": new}},
                      ensure_ascii=False)


def run(action: str, state_dir: Path, stdin, stdout, env: dict) -> int:
    """Entry point do hook: sempre 0, stdout só quando poda."""
    try:
        if action == "gc":
            gc(state_dir, force=True)
            return 0
        payload = json.load(stdin)
        if isinstance(payload, dict):
            out = hook_output(state_dir, payload, env)
            if out:
                stdout.write(out + "\n")
    except Exception:  # noqa: BLE001 - um hook nunca quebra a sessão
        pass
    return 0


# ---------------------------------------------------------------- replay

def _result_text(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(b.get("text", "") for b in content if isinstance(b, dict) and isinstance(b.get("text"), str))
    return ""


def replay(projects: Path, env: dict) -> dict:
    """Aplica as regras aos transcripts, sem spill nem log. Devolve contagens por regra e totais."""
    rules: dict[str, dict] = {}
    total_all = 0
    for file in sorted(projects.glob("**/*.jsonl")):
        uses: dict[str, tuple[str, dict]] = {}
        try:
            handle = file.open(encoding="utf-8", errors="replace")
        except OSError:
            continue
        with handle:
            for line in handle:
                try:
                    item = json.loads(line)
                except ValueError:
                    continue
                content = (item.get("message") or {}).get("content") if isinstance(item, dict) else None
                if not isinstance(content, list):
                    continue
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") == "tool_use" and isinstance(block.get("id"), str):
                        uses[block["id"]] = (str(block.get("name")), block.get("input") or {})
                    elif block.get("type") == "tool_result":
                        text = _result_text(block.get("content"))
                        total_all += len(text)
                        name, tinput = uses.get(block.get("tool_use_id"), ("", {}))
                        # PostToolUseFailure não aceita reescrita: erro nunca é podável
                        if name in TOOLS and isinstance(tinput, dict) and not block.get("is_error"):
                            _replay_one(name, tinput, text, env, rules)
    return {"rules": rules, "total_chars": total_all}


def _replay_one(name: str, tinput: dict, text: str, env: dict, rules: dict) -> None:
    if name == "Bash":
        command = tinput.get("command")
        if not isinstance(command, str) or "# sb:raw" in command:
            return
        toks, limited = analyze(command)
        rule, threshold = select_rule(toks, limited, name)
    else:
        rule, threshold = "R2", 0
    if not rule:
        return
    done = prune_text(rule, text, threshold, env, "/spill/x.txt")
    if done is None:
        return
    row = rules.setdefault(rule, {"n": 0, "chars_in": 0, "chars_out": 0})
    row["n"] += 1
    row["chars_in"] += len(text)
    row["chars_out"] += len(done[0])


def _row(rule: str, row: dict) -> str:
    pct = 100 * (row["chars_in"] - row["chars_out"]) / row["chars_in"] if row["chars_in"] else 0
    return f"{rule}\t{row['n']}\t{row['chars_in']}\t{row['chars_out']}\t{pct:.1f}"


def format_replay(result: dict) -> str:
    rows = result["rules"]
    lines = ["rule\tn\tchars_in\tchars_out\tsaved_pct"]
    totals = {"n": 0, "chars_in": 0, "chars_out": 0}
    for rule in sorted(rows):
        for key in totals:
            totals[key] += rows[rule][key]
        lines.append(_row(rule, rows[rule]))
    lines.append(_row("total", totals))
    saved = totals["chars_in"] - totals["chars_out"]
    every = result["total_chars"]
    lines.append(f"cortado/total_todas_saidas\t{saved}\t{every}\t{100 * saved / every if every else 0:.2f}")
    return "\n".join(lines) + "\n"
