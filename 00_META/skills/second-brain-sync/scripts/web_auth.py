"""web_auth.py - Token authentication, session cookie and global failure limiter for the exposed web instance.

Decision D1: behind `tailscale serve` every request reaches the app from 127.0.0.1, so neither Host nor source IP
may open a route. With `exposed=True` every route needs `Authorization: Bearer <token>` or the `sb_session` cookie,
except GET/POST /login and /static. The token lives only in memory here: it is never logged, echoed or put in an
exception message. The audit log (web-auth.jsonl) holds `ts`, `route` and `result`, nothing else.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import hmac
import json
import math
import os
import threading
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping, Optional
from urllib.parse import parse_qs

import projects

DEFAULT_TOKEN_ENV = "SB_WEB_TOKEN"
MIN_TOKEN_LEN = 32
COOKIE_NAME = "sb_session"
COOKIE_MAX_AGE = 30 * 24 * 3600
SESSION_LABEL = b"sb-session-v1"
MAX_FAILURES = 10  # failures inside WINDOW_SECONDS ...
WINDOW_SECONDS = 60.0
BLOCK_SECONDS = 60.0  # ... block all authentication for this long
AUTH_LOG = "web-auth.jsonl"
LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})
OPEN_PATHS = frozenset({"/login"})
OPEN_PREFIX = "/static/"
UNMATCHED_ROUTE = "(unmatched)"


class AuthConfigError(ValueError):
    """The exposed instance cannot start safely. The message never carries the token."""


def token_problem(token: object) -> Optional[str]:
    """Why `token` cannot protect an exposed instance, or None when it can."""
    if not isinstance(token, str) or not token.strip():
        return "token ausente ou vazio"
    if len(token) < MIN_TOKEN_LEN:
        return f"token com menos de {MIN_TOKEN_LEN} caracteres"
    return None


def token_env_name(vault: Path) -> str:
    """The environment variable that holds the token: `web.token_env` of the manifest, else SB_WEB_TOKEN."""
    try:
        name = projects.load_manifest(vault).web.get("token_env")
    except Exception:  # no manifest, no PyYAML or bad YAML: the default name still works
        name = None
    if name is None:
        return DEFAULT_TOKEN_ENV
    if not isinstance(name, str) or not projects.ENV_VAR_RE.match(name):
        raise AuthConfigError("web.token_env do manifesto não é um nome de variável de ambiente válido")
    return name


def resolve_token(vault: Path, environ: Optional[Mapping[str, str]] = None) -> tuple[str, str]:
    """(variable name, token) read from the environment. The token may be empty; the caller validates it."""
    env = os.environ if environ is None else environ
    name = token_env_name(vault)
    return name, env.get(name, "").strip()


def session_value(token: str) -> str:
    """The `sb_session` cookie value: HMAC-SHA256(token, "sb-session-v1"). Rotating the token voids every cookie."""
    return hmac.new(token.encode("utf-8"), SESSION_LABEL, hashlib.sha256).hexdigest()


def same_secret(candidate: str, expected: str) -> bool:
    """Constant-time comparison on bytes, so non-ASCII input cannot raise."""
    return hmac.compare_digest(candidate.encode("utf-8"), expected.encode("utf-8"))


def is_open_path(method: str, path: str) -> bool:
    """Only GET/POST /login and everything under /static/ skip authentication. Anything else fails closed."""
    if path in OPEN_PATHS:
        return method in ("GET", "POST")
    return path.startswith(OPEN_PREFIX)


@dataclass(frozen=True)
class Decision:
    result: str  # ok | fail | missing | blocked
    retry_after: int = 0

    @property
    def allowed(self) -> bool:
        return self.result == "ok"


class AuthGate:
    """Credential check plus a limiter that is global on purpose: the proxy hides the origin, so there is no IP key.

    A failure is a credential that was presented and was wrong. A request with no credential is not a guess, so it
    answers 401 without counting; otherwise an expired cookie or a health probe would lock the owner out. The 10th
    failure inside the window starts the block; during the block every request, valid or not, answers 429 and does
    not extend it. A success does not reset the counter."""

    def __init__(
        self,
        token: str,
        log_path: Callable[[], Path],
        clock: Callable[[], float] = time.monotonic,
        wall: Callable[[], dt.datetime] = lambda: dt.datetime.now(dt.timezone.utc),
    ):
        problem = token_problem(token)
        if problem:
            raise AuthConfigError(problem)
        self._token = token
        self._session = session_value(token)
        self._log_path = log_path
        self.clock = clock
        self.wall = wall
        self._failures: deque[float] = deque()
        self._blocked_until = 0.0
        self._lock = threading.Lock()

    @property
    def session(self) -> str:
        return self._session

    def _blocked_for(self, now: float) -> int:
        return math.ceil(self._blocked_until - now) if self._blocked_until > now else 0

    def _fail(self, now: float) -> None:
        self._failures.append(now)
        while self._failures and now - self._failures[0] >= WINDOW_SECONDS:
            self._failures.popleft()
        if len(self._failures) >= MAX_FAILURES:
            self._blocked_until = now + BLOCK_SECONDS
            self._failures.clear()

    def check_request(self, authorization: str, cookie: str) -> Decision:
        """Decision for a protected route, from the raw Authorization header and sb_session cookie value."""
        with self._lock:
            now = self.clock()
            wait = self._blocked_for(now)
            if wait:
                return Decision("blocked", wait)
            presented = False
            if authorization.strip():
                presented = True
                scheme, _, value = authorization.strip().partition(" ")
                if scheme.lower() == "bearer" and same_secret(value.strip(), self._token):
                    return Decision("ok")
            if cookie:
                presented = True
                if same_secret(cookie, self._session):
                    return Decision("ok")
            if not presented:
                return Decision("missing")
            self._fail(now)
            return Decision("fail")

    def check_token(self, candidate: str) -> Decision:
        """Decision for POST /login with the token typed by the user."""
        with self._lock:
            now = self.clock()
            wait = self._blocked_for(now)
            if wait:
                return Decision("blocked", wait)
            if same_secret(candidate, self._token):
                return Decision("ok")
            self._fail(now)
            return Decision("fail")

    def record(self, route: str, result: str) -> None:
        """Append one audit line: ts, route, result. Failing to write must never fail the request."""
        line = json.dumps(
            {"ts": self.wall().isoformat(timespec="seconds"), "route": route, "result": result},
            ensure_ascii=True,
        ) + "\n"
        try:
            path = self._log_path()
            path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
            try:
                os.write(fd, line.encode("utf-8"))
            finally:
                os.close(fd)
        except OSError:
            pass


def login_token(content_type: str, raw: bytes) -> Optional[str]:
    """The token a POST /login carries, from a JSON body or an HTML form, or None when there is none to judge."""
    kind = content_type.split(";")[0].strip().lower()
    value: object = None
    try:
        if kind == "application/json":
            data = json.loads(raw)
            value = data.get("token") if isinstance(data, dict) else None
        elif kind == "application/x-www-form-urlencoded":
            value = parse_qs(raw.decode("utf-8"), keep_blank_values=True).get("token", [None])[0]
    except ValueError:  # bad JSON or bad UTF-8
        return None
    return value if isinstance(value, str) and value else None


def route_label(routes, path: str) -> str:
    """The route template that serves `path`, never the raw path: a token typed into a URL cannot reach the log."""
    for route in routes:
        regex = getattr(route, "path_regex", None)
        if regex is not None and regex.match(path):
            return route.path
    return UNMATCHED_ROUTE
