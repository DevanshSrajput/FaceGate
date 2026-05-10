"""Authentication helpers for the FaceGate dashboard."""

from __future__ import annotations

import time
from collections.abc import Callable
from functools import wraps
from typing import Any

from flask import redirect, request, session, url_for
from werkzeug.security import check_password_hash

from config import ADMIN_PASSWORD_HASH, ADMIN_USERNAME

_MAX_ATTEMPTS = 5
_LOCKOUT_SEC = 300
_failed_logins: dict[str, list[float]] = {}


def _prune_old_attempts(ip_address: str) -> None:
    """Remove failed login attempts older than the lockout window."""
    now = time.monotonic()
    if ip_address in _failed_logins:
        _failed_logins[ip_address] = [
            ts for ts in _failed_logins[ip_address] if now - ts < _LOCKOUT_SEC
        ]


def is_rate_limited(ip_address: str) -> bool:
    """Return True when the given IP has exceeded the login attempt threshold."""
    _prune_old_attempts(ip_address)
    return len(_failed_logins.get(ip_address, [])) >= _MAX_ATTEMPTS


def record_failed_attempt(ip_address: str) -> None:
    """Record a failed login attempt for the given IP address."""
    _prune_old_attempts(ip_address)
    _failed_logins.setdefault(ip_address, []).append(time.monotonic())


def validate_credentials(username: str, password: str) -> bool:
    """Return True when submitted dashboard credentials are valid."""
    if not ADMIN_PASSWORD_HASH:
        return False
    if username != ADMIN_USERNAME:
        return False
    return check_password_hash(ADMIN_PASSWORD_HASH, password)


def login_user(username: str) -> None:
    """Store the authenticated admin identity in the Flask session."""
    session["authenticated"] = True
    session["username"] = username


def logout_user() -> None:
    """Remove dashboard authentication state from the Flask session."""
    session.clear()


def is_authenticated() -> bool:
    """Return True when the current session is authenticated."""
    return bool(session.get("authenticated"))


def login_required(view_func: Callable[..., Any]) -> Callable[..., Any]:
    """Redirect anonymous users to the login page before protected views."""
    @wraps(view_func)
    def wrapped_view(*args: Any, **kwargs: Any) -> Any:
        """Run a protected Flask view after authentication is confirmed."""
        if not is_authenticated():
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    return wrapped_view
