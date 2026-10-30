"""Credential-shape scanner for the vault (stdlib only).

Used by `sb doctor` today and by `sb sync` / `sb review` later. It reports a label and a line
number, never the matched text, so a report cannot leak the secret it found.

Coverage = the ECC memory-vault validator (provider, Stripe, npm, Hugging Face, GitHub, Google,
Slack, AWS, private key) plus the shapes the ECC observer redactor misses (I0, 2026-10-15): JWT,
URL with credentials, Bearer tokens, and `name = value` assignments with an opaque value.

A line that contains `sb-allow-secret` is skipped, so a note can show a fake example on purpose.
"""
from __future__ import annotations

import re
from typing import NamedTuple

ALLOW_MARKER = "sb-allow-secret"

_OPAQUE_VALUE = r"""(?=[A-Za-z0-9/+_.=-]{12,})(?=[A-Za-z0-9/+_.=-]*\d)(?=[A-Za-z0-9/+_.=-]*[A-Za-z])[A-Za-z0-9/+_.=-]{12,}"""

PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = tuple(
    (label, re.compile(pattern))
    for label, pattern in (
        ("provider API key", r"(?i)\bsk-[A-Za-z0-9_-]{16,}\b"),
        ("Stripe key", r"\b(?:sk|rk)_live_[A-Za-z0-9]{16,}\b"),
        ("npm token", r"\bnpm_[A-Za-z0-9]{20,}\b"),
        ("Hugging Face token", r"\bhf_[A-Za-z0-9]{20,}\b"),
        ("GitHub token", r"\bgh[pors]_[A-Za-z0-9]{16,}\b"),
        ("GitHub token", r"\bgithub_pat_[A-Za-z0-9_]{16,}\b"),
        ("Google API key", r"\bAIza[A-Za-z0-9_-]{16,}\b"),
        ("Slack token", r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
        ("AWS access key id", r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
        ("private key", r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----"),
        ("JSON web token", r"\beyJ[A-Za-z0-9_-]{8,}\.eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}"),
        ("URL with credentials", r"\b[a-z][a-z0-9+.-]*://[^\s/:@]+:[^\s/@]{3,}@[^\s/]+"),
        ("bearer token", r"\bBearer\s+[A-Za-z0-9._~+/=-]{20,}"),
        (
            "credential assignment",
            r"""(?i)[A-Za-z0-9_-]*(?:api[_-]?key|secret|token|passwd|password)[A-Za-z0-9_-]*["']?\s*[:=]\s*["']?"""
            + _OPAQUE_VALUE,
        ),
    )
)


class Finding(NamedTuple):
    label: str
    line: int


def scan_text(text: str) -> list[Finding]:
    """Return one Finding per (label, line); the matched text is never included."""
    findings: list[Finding] = []
    for number, line in enumerate(text.splitlines(), start=1):
        if ALLOW_MARKER in line:
            continue
        seen: set[str] = set()
        for label, pattern in PATTERNS:
            if label not in seen and pattern.search(line):
                seen.add(label)
                findings.append(Finding(label, number))
    return findings


def contains_secret_shape(text: str) -> bool:
    """True when `text` looks like a credential. Unlike scan_text, the allow marker does not exempt it.

    For values the runtime stores on its own (a path, a project name): a marker in the value must not
    let a credential through.
    """
    return bool(scan_text(text.replace(ALLOW_MARKER, " ")))
