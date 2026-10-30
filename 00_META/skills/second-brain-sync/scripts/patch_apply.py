"""The one writer of a project in the second-brain runtime (Estudo S5, step I5).

Only `sb patch apply <id> --apply` reaches `write_target`; `sb.py` imports this module inside that branch and nowhere
else does. The apply takes no input but the stored patch: it validates the header, regenerates the patch over the
target as it is now (`patches.render`) and refuses unless the bytes equal the stored file, so a patch that was edited,
or a target that changed since the proposal, never lands. Every step runs under the patches lock.
"""
from __future__ import annotations

import contextlib
import os
import stat
import tempfile
from pathlib import Path
from typing import NamedTuple

import candidates
import patches

NEW_MODES = {"CLAUDE.md": 0o644, "AGENTS.md": 0o644, patches.SETTINGS_REL: 0o600}
NEW_DIR_MODE = 0o755  # a new `.claude/`


class Result(NamedTuple):
    code: int  # 0 clean (or applied), 1 refused, 2 unknown id
    message: str
    target: Path | None = None
    diff: str = ""


def refuse(reason: str) -> Result:
    return Result(1, f"refused: {reason}")


def write_target(path: Path, data: bytes) -> None:
    """Replace `path` with `data` through a temp file in its folder; the mode is kept, or the default for a new file.
    Nothing is left behind on failure, `.claude/` included when this call made it."""
    made = False
    mode = NEW_MODES.get(patches.SETTINGS_REL if path.parent.name == ".claude" else path.name, 0o644)
    if path.is_file():
        mode = stat.S_IMODE(path.stat().st_mode)
    tmp = None
    try:
        if not path.parent.exists():
            path.parent.mkdir(mode=NEW_DIR_MODE)
            made = True
            os.chmod(path.parent, NEW_DIR_MODE)
        fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".sb-patch-")
        with os.fdopen(fd, "wb") as out:
            out.write(data)
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    except BaseException:
        if tmp is not None:
            Path(tmp).unlink(missing_ok=True)
        if made:
            with contextlib.suppress(OSError):
                path.parent.rmdir()
        raise


def apply_patch(state_dir: Path, pid: str, *, write: bool) -> Result:
    """Validate patch `pid` and, with `write`, apply it. A dry run takes no lock and writes nothing."""
    with patches.locked(state_dir) if write else contextlib.nullcontext():
        data = patches.read(state_dir, pid)
        if data is None:
            return Result(2, f"unknown patch {pid}")
        meta = patches.parse(data)
        if meta is None or meta.id != pid:
            return refuse("the patch header is damaged or does not match its file name")
        try:
            patches.check_root(meta.root)
            if meta.days_left <= 0:
                raise patches.PatchError("the patch is past its time to live")
            built = patches.render(meta, patches.current_target(meta))
        except patches.PatchError as err:
            return refuse(str(err))
        except (OSError, ValueError, RecursionError):
            return refuse("the target cannot be read")
        if built.text != data:
            return refuse("the patch differs from the one regenerated over the target (edited, or the target changed)")
        target = Path(meta.root) / meta.target
        if os.path.realpath(target) != str(target):
            return refuse("the target is outside the root or a link")
        diff = data.decode("utf-8").split("\n--- ", 1)[1]
        if not write:
            return Result(0, "would apply (dry run, add --apply)", target, "--- " + diff)
        try:
            write_target(target, built.new)
        except OSError as err:
            return refuse(f"cannot write the target ({err.strerror or type(err).__name__})")
        patches.delete(state_dir, pid)
        return Result(0, f"applied: {pid} -> {target}", target)
