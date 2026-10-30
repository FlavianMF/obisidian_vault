"""Proposed patches of the second-brain runtime (Estudo S5, step I5).

The observer turns a repeated finding into a patch FILE under `<state>/patches/`: one line for the project's
`CLAUDE.md` or `AGENTS.md`, and, for a big read seen in two sessions, one `permissions.deny` entry. Nothing here writes
a project: this module reads the target and writes the state only. The one writer of a project is the apply module,
and only `sb patch apply <id> --apply` runs it.

A patch is a pure insertion: the diff has `+` lines and `@@` headers, no context, no `-` line, so no byte of the
target travels into the state. `render` is a function of the header and the target, so `apply` can regenerate the
patch over the current target and refuse unless the bytes equal the stored file.
"""
from __future__ import annotations

import datetime as dt
import fcntl
import hashlib
import json
import os
import re
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, NamedTuple

import candidates
from lib import secret_scan

PATCH_DIR = "patches"
MAX_PATCHES = 50  # live files; above it no new patch is born
MAX_TARGET_BYTES = 256 * 1024
MAX_PATCH_BYTES = 64 * 1024  # a stored patch is far smaller; a bigger file is not ours
DENY_MIN_SESSIONS = 2
MAX_REL = 200
LINE_RULES = ("reread", "big")
RULES = (*LINE_RULES, "deny")
LINE_TARGETS = ("CLAUDE.md", "AGENTS.md")
SETTINGS_REL = ".claude/settings.local.json"
RESERVED_REL = {name.casefold() for name in (*LINE_TARGETS, SETTINGS_REL)}
GLOB_CHARS = frozenset("*?[]{}\\!")
BAD_REL_CHARS = frozenset("`()")
ID_RE = re.compile(r"[0-9a-f]{8}")
HEADER_RE = re.compile(r"# ([a-z_-]+): (.*)")
HEADER_KEYS = ("sb-patch", "rule", "project", "root", "target", "file", "count", "sessions", "session_ids", "created")
LINE_PREFIXES = ("- Leia `{rel}` com offset/limit", "- Evite ler `{rel}` inteiro")


class PatchError(ValueError):
    """No patch for this case; the message is a reason and never carries project content."""


class Meta(NamedTuple):
    id: str
    rule: str
    project: str
    root: str
    target: str
    file: str  # path of the finding, relative to the root
    count: int
    session_ids: tuple[str, ...]
    created: str  # ISO date of the first proposal; never renewed
    size: int = 0  # characters of the biggest read (rules big and deny)

    @property
    def sessions(self) -> int:
        return len(self.session_ids)

    @property
    def days_left(self) -> int:
        return candidates.TTL_DAYS - (candidates.utcnow().date() - dt.date.fromisoformat(self.created)).days


class Built(NamedTuple):
    text: bytes  # the patch file
    new: bytes  # the target once the patch is applied
    old: bytes | None  # the target now (None: it does not exist)


def patches_dir(state_dir: Path) -> Path:
    return state_dir / PATCH_DIR


@contextmanager
def locked(state_dir: Path) -> Iterator[None]:
    """Serialise the writers of the patches (a Stop and an apply). The lock is the `patches/` folder itself, so no
    lock file is left in the state."""
    directory = patches_dir(state_dir)
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        os.close(fd)  # closing the descriptor releases the lock


def patch_id(rule: str, root: str, rel: str) -> str:
    return hashlib.sha1(f"{rule}|{root}|{rel}".encode("utf-8")).hexdigest()[:8]


def patch_file(state_dir: Path, pid: str) -> Path:
    return patches_dir(state_dir) / f"{pid}.patch"


def read(state_dir: Path, pid: str) -> bytes | None:
    """The stored file of a patch, or None when it is absent, unreadable or too big."""
    if not ID_RE.fullmatch(pid):
        return None
    try:
        with patch_file(state_dir, pid).open("rb") as handle:
            data = handle.read(MAX_PATCH_BYTES + 1)
    except OSError:
        return None
    return None if len(data) > MAX_PATCH_BYTES else data


def delete(state_dir: Path, pid: str) -> None:
    patch_file(state_dir, pid).unlink(missing_ok=True)


# ---------------------------------------------------------------- the file format

def plural(count: int, one: str, many: str) -> str:
    return f"{count} {one if count == 1 else many}"


def _why(meta: Meta) -> str:
    if meta.rule == "reread":
        return (f"regra REREAD_MIN: {meta.file} foi lido {plural(meta.count, 'vez', 'vezes')} numa sessão; "
                f"{plural(meta.sessions, 'sessão repetiu', 'sessões repetiram')} o achado.")
    base = (f"regra BIG_READ_CHARS: {meta.file} devolveu ~{meta.size // 1000} mil caracteres numa leitura "
            f"({plural(meta.count, 'leitura', 'leituras')}); "
            f"{plural(meta.sessions, 'sessão repetiu', 'sessões repetiram')} o achado.")
    if meta.rule == "big":
        return base
    return (f"{base} A entrada bloqueia todo Read, offset/limit incluído, de {meta.file}; "
            "a linha guia do patch de linha sugere o contrário.")


def _header(meta: Meta) -> list[str]:
    rows = [("sb-patch", meta.id), ("rule", meta.rule), ("project", meta.project), ("root", meta.root),
            ("target", meta.target), ("file", meta.file), ("count", meta.count), ("sessions", meta.sessions),
            ("session_ids", ",".join(meta.session_ids)), ("created", meta.created)]
    if meta.rule != "reread":
        rows.append(("size", meta.size))
    rows.append(("why", _why(meta)))
    return [f"# {key}: {value}" for key, value in rows]


def parse(data: bytes) -> Meta | None:
    """The header of a stored patch, or None unless every field is well formed. The diff below it is not read."""
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return None
    fields: dict[str, str] = {}
    for line in text.split("\n"):
        if not line.startswith("# "):
            break
        found = HEADER_RE.fullmatch(line)
        if not found or found.group(1) in fields:
            return None
        fields[found.group(1)] = found.group(2)
    rule = fields.get("rule", "")
    needed = {*HEADER_KEYS, "why"} | ({"size"} if rule in ("big", "deny") else set())
    if rule not in RULES or set(fields) != needed:
        return None
    numbers = [fields[k] for k in ("count", "sessions") + (("size",) if "size" in fields else ())]
    if not all(re.fullmatch(r"[0-9]{1,9}", n) for n in numbers):
        return None
    ids = tuple(fields["session_ids"].split(","))
    if (not 1 <= len(ids) <= candidates.MAX_SESSION_IDS or int(fields["sessions"]) != len(ids)
            or any(candidates.safe_session(i) != i for i in ids)):
        return None
    try:
        created = dt.date.fromisoformat(fields["created"])
    except ValueError:
        return None
    if created.isoformat() != fields["created"]:
        return None
    return Meta(id=fields["sb-patch"], rule=rule, project=fields["project"], root=fields["root"],
                target=fields["target"], file=fields["file"], count=int(fields["count"]), session_ids=ids,
                created=fields["created"], size=int(fields.get("size", 0)))


def line_text(meta: Meta) -> str:
    if meta.rule == "reread":
        return (f"- Leia `{meta.file}` com offset/limit: {plural(meta.count, 'releitura', 'releituras')} em "
                f"{plural(meta.sessions, 'sessão', 'sessões')} (regra REREAD_MIN, sb observer).")
    return (f"- Evite ler `{meta.file}` inteiro: {plural(meta.count, 'leitura', 'leituras')} de ~{meta.size // 1000} "
            f"mil caracteres em {plural(meta.sessions, 'sessão', 'sessões')}; busque antes e leia com offset/limit (regra BIG_READ_CHARS, sb observer).")


# ---------------------------------------------------------------- eligibility

def printable(text: str, limit: int) -> bool:
    return bool(text) and len(text) <= limit and text.isprintable() and text == text.strip()


def eligible_rel(rel: str) -> bool:
    """A project-relative path fit for a patch line: printable, no backtick or parenthesis, already normalised."""
    return (printable(rel, MAX_REL) and not BAD_REL_CHARS & set(rel) and not rel.startswith("/")
            and os.path.normpath(rel) == rel and ".." not in rel.split("/") and rel != ".")


def deny_rel(rel: str) -> bool:
    folded = rel.casefold()
    return (not GLOB_CHARS & set(rel) and folded not in RESERVED_REL and folded != ".claude"
            and not folded.startswith(".claude/"))


def home_roots() -> set[str]:
    return {"/", os.path.realpath(os.path.expanduser("~")), os.path.realpath(str(Path.home()))}


def check_root(root: str) -> None:
    """The root a patch may name: an absolute, real directory that is neither `/` nor `$HOME`."""
    if not printable(root, 4096) or not os.path.isabs(root) or os.path.realpath(root) != root:
        raise PatchError("root is not an absolute real path")
    if root in home_roots():
        raise PatchError("root is the home directory")
    if not os.path.isdir(root):
        raise PatchError("root is not a directory")


def relative_to(root: Path | str, path: str) -> str | None:
    """`path` relative to the root (compared as written and against the real root), or None when it is outside."""
    if not isinstance(path, str) or not os.path.isabs(path):
        return None
    for base in dict.fromkeys((str(root), os.path.realpath(str(root)))):
        prefix = base.rstrip("/") + "/"
        if path.startswith(prefix):
            rel = path[len(prefix):]
            return rel if eligible_rel(rel) else None
    return None


def validate(meta: Meta) -> None:
    """Field rules shared by the proposal and the apply; the filesystem is not touched."""
    if meta.rule not in RULES or meta.id != patch_id(meta.rule, meta.root, meta.file):
        raise PatchError("id does not match rule, root and file")
    if not eligible_rel(meta.file) or not printable(meta.project, 120) or meta.project != candidates.normalize(meta.project):
        raise PatchError("file or project is not fit for a patch")
    if not printable(meta.root, 4096) or not os.path.isabs(meta.root):
        raise PatchError("root is not fit for a patch")
    if meta.rule == "deny":
        if meta.target != SETTINGS_REL or not deny_rel(meta.file):
            raise PatchError("deny target is not allowed")
    elif meta.target not in LINE_TARGETS:
        raise PatchError("target is not allowed for this rule")
    if not 1 <= meta.count <= 999_999_999 or not 0 <= meta.size <= 999_999_999 or not meta.session_ids:
        raise PatchError("numbers out of range")
    for part in (meta.root, meta.file, meta.project):
        if secret_scan.contains_secret_shape(part):
            raise PatchError("looks like a secret")


# ---------------------------------------------------------------- targets

def _regular(path: Path) -> bool:
    return path.is_file() and not path.is_symlink()


def read_target(path: Path) -> bytes:
    """A regular file of up to MAX_TARGET_BYTES; PatchError otherwise."""
    try:
        with path.open("rb") as handle:
            data = handle.read(MAX_TARGET_BYTES + 1)
    except OSError:
        raise PatchError("target is not readable") from None
    if len(data) > MAX_TARGET_BYTES:
        raise PatchError("target is over the size limit")
    return data


def choose_target(root: Path | str) -> tuple[str, bytes | None]:
    """Name of the file that takes the line, and its bytes (None: a new CLAUDE.md). PatchError: no patch."""
    root = Path(root)
    claude, agents = root / "CLAUDE.md", root / "AGENTS.md"
    for path in (claude, agents):
        if _regular(path):
            return path.name, read_target(path)
    if not os.path.lexists(claude) and not os.path.lexists(agents):
        return "CLAUDE.md", None
    raise PatchError("no usable CLAUDE.md or AGENTS.md")


def read_settings(root: Path | str) -> bytes | None:
    """Bytes of `.claude/settings.local.json`, or None when absent. A link or a non-file is refused."""
    base = Path(root) / ".claude"
    if os.path.lexists(base) and (base.is_symlink() or not base.is_dir()):
        raise PatchError(".claude is not a real directory")
    path = base / "settings.local.json"
    if not os.path.lexists(path):
        return None
    if not _regular(path):
        raise PatchError("settings.local.json is not a regular file")
    return read_target(path)


def current_target(meta: Meta) -> bytes | None:
    """The bytes the patch of `meta` must apply over, read now; raises when the target is not the one named."""
    if meta.rule == "deny":
        return read_settings(meta.root)
    name, old = choose_target(meta.root)
    if name != meta.target:
        raise PatchError("the target file changed")
    return old


def _strict_text(data: bytes) -> str:
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        raise PatchError("target is not UTF-8") from None


def _lines(data: bytes) -> list[bytes]:
    return [row + b"\n" for row in data.split(b"\n")[:-1]]


def has_line(old: bytes | None, rel: str) -> bool:
    if old is None:
        return False
    prefixes = tuple(p.format(rel=rel) for p in LINE_PREFIXES)
    return any(row.rstrip("\r").startswith(prefixes) for row in _strict_text(old).split("\n"))


# ---------------------------------------------------------------- building

def git_safe(position: int, count: int) -> bool:
    """`git apply` takes a hunk without context only after line 2 or later, or into an empty file (measured, git 2.43)."""
    return count == 0 or position >= 2


def insertion(old: bytes, new: bytes) -> tuple[int, list[bytes]]:
    """(lines before the insertion, the inserted lines) when `new` is `old` with lines added, else PatchError."""
    before, after = _lines(old), _lines(new)
    extra = len(after) - len(before)
    if extra <= 0:
        raise PatchError("not an insertion")
    at = 0
    while at < len(before) and before[at] == after[at]:
        at += 1
    if after[at + extra:] != before[at:]:
        raise PatchError("not a pure insertion")
    if not git_safe(at, len(before)):
        raise PatchError("position that git apply refuses")
    return at, after[at:at + extra]


def _dump(obj: object) -> bytes:
    return (json.dumps(obj, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def deny_entry(rel: str) -> str:
    return f"Read(./{rel})"


def deny_new(old: bytes | None, rel: str) -> bytes:
    """`settings.local.json` with the entry as the first item of `deny`, or `deny` as the first key of `permissions`."""
    entry = deny_entry(rel)
    if old is None:
        return _dump({"permissions": {"deny": [entry]}})
    text = _strict_text(old)
    try:
        obj = json.loads(text)
        canonical = _dump(obj) == old
    except (ValueError, RecursionError):
        raise PatchError("settings.local.json is not valid JSON") from None
    if not canonical or not isinstance(obj, dict) or not isinstance(obj.get("permissions"), dict) or not obj["permissions"]:
        raise PatchError("settings.local.json is not in the canonical shape")
    perms = obj["permissions"]
    if "deny" in perms:
        deny = perms["deny"]
        if not isinstance(deny, list) or not deny:
            raise PatchError("deny is not a non-empty list")
        if entry in deny:
            raise PatchError("entry already present")
        perms = {**perms, "deny": [entry, *deny]}
    else:
        perms = {"deny": [entry], **perms}
    return _dump({**obj, "permissions": perms})


def has_deny(old: bytes | None, rel: str) -> bool:
    if old is None:
        return False
    try:
        deny = json.loads(_strict_text(old))["permissions"]["deny"]
    except (ValueError, KeyError, TypeError, RecursionError, PatchError):
        return False
    return isinstance(deny, list) and deny_entry(rel) in deny


def render(meta: Meta, old: bytes | None) -> Built:
    """The patch file of `meta` over the target `old`, and the target as it will be. PatchError: no patch."""
    validate(meta)
    if meta.rule == "deny":
        new = deny_new(old, meta.file)
    else:
        if old and not old.endswith(b"\n"):
            raise PatchError("target does not end with a newline")
        if has_line(old, meta.file):  # also refuses a target that is not UTF-8
            raise PatchError("line already present")
        new = (old or b"") + (line_text(meta) + "\n").encode("utf-8")
    at, added = insertion(old or b"", new)
    first = f"@@ -{at},0 +{at + 1}{'' if len(added) == 1 else f',{len(added)}'} @@"
    names = ("/dev/null" if old is None else f"a/{meta.target}", f"b/{meta.target}")
    body = [f"--- {names[0]}", f"+++ {names[1]}", first, *("+" + row.decode("utf-8").rstrip("\n") for row in added)]
    text = ("\n".join([*_header(meta), *body]) + "\n").encode("utf-8")
    if secret_scan.contains_secret_shape(text.decode("utf-8")):
        raise PatchError("looks like a secret")
    return Built(text, new, old)


# ---------------------------------------------------------------- the store

def live_files(state_dir: Path) -> list[Path]:
    try:
        return sorted(p for p in patches_dir(state_dir).iterdir() if p.suffix == ".patch" and ID_RE.fullmatch(p.stem))
    except OSError:
        return []


def list_patches(state_dir: Path) -> list[Meta]:
    """Live, readable patches, oldest first; a file that cannot be read or parsed is left out."""
    found = []
    for path in live_files(state_dir):
        meta = parse(read(state_dir, path.stem) or b"")
        if meta is not None and meta.id == path.stem and meta.days_left > 0:
            found.append(meta)
    return sorted(found, key=lambda m: (m.created, m.id))


def expire(state_dir: Path) -> int:
    """Delete the patches older than the candidate TTL. Returns how many went."""
    gone = 0
    if not live_files(state_dir):
        return 0  # nothing to expire: no lock file is born
    with locked(state_dir):
        for path in live_files(state_dir):
            meta = parse(read(state_dir, path.stem) or b"")
            if meta is not None and meta.days_left <= 0:
                path.unlink(missing_ok=True)
                gone += 1
    return gone


def _store(state_dir: Path, meta: Meta, old: bytes | None) -> tuple[bool, bool]:
    """Write the patch of `meta` over `old`. Returns (the patch file exists afterwards, the bytes changed)."""
    built = render(meta, old)
    if read(state_dir, meta.id) == built.text:
        return True, False
    if not patch_file(state_dir, meta.id).exists() and len(live_files(state_dir)) >= MAX_PATCHES:
        return False, False
    patches_dir(state_dir).mkdir(parents=True, exist_ok=True, mode=0o700)
    candidates.replace_file(patch_file(state_dir, meta.id), built.text)
    return True, True


def _merge(base: Meta, old: Meta | None, ids: tuple[str, ...] = ()) -> Meta:
    """Recurrence: the earliest `created`, the largest numbers, the union of the session ids (first seen first)."""
    if old is not None:
        ids = (*old.session_ids, *base.session_ids, *ids)
    else:
        ids = (*base.session_ids, *ids)
    kept = tuple(dict.fromkeys(ids))[:candidates.MAX_SESSION_IDS]
    return base._replace(count=max(base.count, old.count if old else 0), size=max(base.size, old.size if old else 0),
                         session_ids=kept, created=old.created if old else base.created)


def propose(state_dir: Path, findings: list, *, root: Path | str, project: str, session: str | None) -> int:
    """Write or refresh the patches of up to `findings` (objects with kind, title, rule, path, count, size).

    Needs a usable session id: the patch counts sessions. Returns how many patch files were written or changed.
    Any case that cannot be a patch is skipped; only an unwritable state raises (OSError), and the caller catches it.
    """
    sid = candidates.safe_session(session)
    project = candidates.normalize(project)
    try:
        real = os.path.realpath(str(root))
        check_root(real)
    except PatchError:
        return 0
    if sid is None:
        return 0
    inside = [(f, rel) for f in findings if f.rule in LINE_RULES and (rel := relative_to(root, f.path)) is not None]
    if not inside:
        return 0  # no lock file is born for a session that read nothing of this project
    written = 0
    with locked(state_dir):
        for finding, rel in inside:
            try:
                written += _propose_one(state_dir, finding, rel, real, project, sid)
            except (PatchError, ValueError, RecursionError, OSError):
                continue  # one finding that cannot be stored must not stop the next
    return written


def _propose_one(state_dir: Path, finding, rel: str, root: str, project: str, sid: str) -> int:
    today = candidates.utcnow().date().isoformat()
    rule = finding.rule
    pid = patch_id(rule, root, rel)
    name, old = choose_target(root)
    if has_line(old, rel):
        delete(state_dir, pid)
        return 0
    base = Meta(pid, rule, project, root, name, rel, finding.count, (sid,), today, finding.size if rule == "big" else 0)
    line = _merge(base, parse(read(state_dir, pid) or b""))
    exists, changed = _store(state_dir, line, old)
    if not exists or rule != "big":
        return int(changed)
    return int(changed) + _propose_deny(state_dir, finding, line, project)


def _propose_deny(state_dir: Path, finding, line: Meta, project: str) -> int:
    """The `deny` patch, only while the line patch of the same finding has seen DENY_MIN_SESSIONS sessions and the
    candidate is alive and undecided with as many (E3: checked when the patch is born or refreshed, not at apply)."""
    if line.sessions < DENY_MIN_SESSIONS or not deny_rel(line.file):
        return 0
    cid = candidates.candidate_id(finding.kind, finding.title, project)
    seen = candidates.get(state_dir, cid)
    if seen is None or seen.sessions < DENY_MIN_SESSIONS:
        return 0
    pid = patch_id("deny", line.root, line.file)
    old = read_settings(line.root)
    if has_deny(old, line.file):
        delete(state_dir, pid)
        return 0
    base = line._replace(id=pid, rule="deny", target=SETTINGS_REL, created=candidates.utcnow().date().isoformat())
    merged = _merge(base, parse(read(state_dir, pid) or b""))
    return int(_store(state_dir, merged, old)[1])
