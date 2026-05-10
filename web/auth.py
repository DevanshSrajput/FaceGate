"""Authentication helpers for the FaceGate dashboard."""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any

from flask import redirect, session, url_for
from werkzeug.security import check_password_hash

from config import ADMIN_PASSWORD_HASH, ADMIN_USERNAME


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
