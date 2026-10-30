"""The one guard for a session id (stdlib only).

A session id becomes a stored value and a file name in several places: the observe log, the usage record and its
`.task`, and the sessions of a candidate. Each of them asks `safe_session`, so the rule is written once.
"""
from __future__ import annotations

import functools
import re

from lib import secret_scan

SAFE_SESSION = re.compile(r"[^A-Za-z0-9_-]")  # the one pattern for every session id the runtime stores
MAX_SESSION_LEN = 64  # what a candidate keeps of an id
MAX_SESSION_RAW = 128  # a longer id is refused before any scan: the suffix scan grows with the cube of the length


def safe_session(raw: object, *, cut: bool = True) -> str | None:
    """A session id fit to store and to name a file, or None. None for an empty id, for one longer than
    MAX_SESSION_RAW (a real id is a 36-character UUID) and for one shaped like a credential, in its raw, cleaned or cut
    form: cleaning can build the shape (`ghp_` and 36 characters split by `/`), and cutting can too. Every place that
    turns a session id into a stored value or a file name asks here."""
    return _safe_session(raw, cut) if isinstance(raw, str) else None


@functools.lru_cache(maxsize=64)  # the observer asks once per finding, always about the same id
def _safe_session(raw: str, cut: bool) -> str | None:
    if len(raw) > MAX_SESSION_RAW:
        return None
    clean = SAFE_SESSION.sub("", raw)
    forms = [raw, clean]
    if cut:
        clean = clean[:MAX_SESSION_LEN]
        forms.append(clean)
    if not clean or any(shaped_like_secret(form) for form in forms):
        return None
    return clean


def shaped_like_secret(text: str) -> bool:
    """`contains_secret_shape` at every point where a word boundary could hide a token (`aaaaghp_...`): ids are stored
    verbatim, so a token glued to other letters would still leak its prefix."""
    return any(secret_scan.contains_secret_shape(text[i:]) for i in range(len(text))
               if i == 0 or text[i - 1].isalnum())
