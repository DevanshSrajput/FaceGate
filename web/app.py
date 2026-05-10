"""Flask dashboard application for FaceGate monitoring and control."""

from __future__ import annotations

import os
import secrets
import threading
import time
from pathlib import Path
from typing import Any

from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)

from config import FLASK_PORT, FLASK_SECRET_KEY, INTRUDERS_DIR
from modules.database import get_logs, get_summary, init_db
from web.auth import is_authenticated, login_required, login_user, logout_user, validate_credentials


camera_stop_event = threading.Event()
camera_thread: threading.Thread | None = None
camera_state: dict[str, Any] = {
    "running": False,
    "fps": 0.0,
    "last_event": None,
    "last_error": None,
}
camera_state_lock = threading.Lock()


def create_app() -> Flask:
    """Create and configure the FaceGate Flask application."""
    app = Flask(__name__)
    app.secret_key = FLASK_SECRET_KEY or secrets.token_hex(32)
    app.add_template_filter(image_basename, "image_basename")
    init_db()
    register_routes(app)
    return app


def image_basename(image_path: str | None) -> str:
    """Return the filename portion of a stored intruder image path."""
    if not image_path:
        return ""
    return Path(image_path).name


def get_camera_status() -> dict[str, Any]:
    """Return a thread-safe snapshot of recognition-loop status."""
    with camera_state_lock:
        return dict(camera_state)


def set_camera_status(**updates: Any) -> None:
    """Update recognition-loop status fields safely."""
    with camera_state_lock:
        camera_state.update(updates)


def camera_frame_callback(_frame: Any) -> None:
    """Update simple FPS telemetry when the camera loop produces a frame."""
    now = time.monotonic()
    previous = getattr(camera_frame_callback, "_last_frame_at", None)
    fps = 0.0 if previous is None else 1 / max(now - previous, 0.001)
    setattr(camera_frame_callback, "_last_frame_at", now)
    set_camera_status(fps=round(fps, 2))


def camera_worker() -> None:
    """Run the recognition loop in a background thread for dashboard control."""
    from modules.camera import run_camera_loop

    set_camera_status(running=True, last_error=None)
    try:
        run_camera_loop(stop_event=camera_stop_event, frame_callback=camera_frame_callback)
    except Exception as exc:
        set_camera_status(last_error=str(exc))
    finally:
        set_camera_status(running=False, fps=0.0)
        camera_stop_event.clear()


def start_camera_thread() -> bool:
    """Start the recognition loop if it is not already running."""
    global camera_thread

    if camera_thread is not None and camera_thread.is_alive():
        return False

    camera_stop_event.clear()
    camera_thread = threading.Thread(target=camera_worker, daemon=True)
    camera_thread.start()
    return True


def stop_camera_thread() -> bool:
    """Signal the recognition loop to stop if it is currently running."""
    if camera_thread is None or not camera_thread.is_alive():
        set_camera_status(running=False, fps=0.0)
        return False

    camera_stop_event.set()
    return True


def get_log_filters() -> dict[str, str]:
    """Build a sanitized log filter dictionary from query parameters."""
    filters: dict[str, str] = {}
    for key in ("name", "status", "date"):
        value = request.args.get(key, "").strip()
        if value:
            filters[key] = value
    return filters


def list_intruder_images() -> list[dict[str, str]]:
    """Return intruder image metadata for the protected gallery page."""
    intruders_path = Path(INTRUDERS_DIR)
    if not intruders_path.exists():
        return []

    images: list[dict[str, str]] = []
    for path in sorted(intruders_path.glob("*.jpg"), key=os.path.getmtime, reverse=True):
        images.append(
            {
                "filename": path.name,
                "timestamp": time.strftime(
                    "%Y-%m-%d %H:%M:%S",
                    time.localtime(path.stat().st_mtime),
                ),
            }
        )
    return images


def register_routes(app: Flask) -> None:
    """Register all FaceGate dashboard routes."""

    @app.get("/")
    def index() -> Any:
        """Redirect users to the dashboard or login page."""
        if is_authenticated():
            return redirect(url_for("dashboard"))
        return redirect(url_for("login"))

    @app.route("/login", methods=["GET", "POST"])
    def login() -> Any:
        """Render and process the admin login form."""
        error = None
        if request.method == "POST":
            username = request.form.get("username", "")
            password = request.form.get("password", "")
            if validate_credentials(username, password):
                login_user(username)
                return redirect(url_for("dashboard"))
            error = "Invalid credentials or missing password hash."
        return render_template("login.html", error=error)

    @app.get("/logout")
    def logout() -> Any:
        """Clear the current dashboard session."""
        logout_user()
        return redirect(url_for("login"))

    @app.get("/dashboard")
    @login_required
    def dashboard() -> Any:
        """Render the dashboard summary page."""
        return render_template(
            "dashboard.html",
            summary=get_summary(),
            camera=get_camera_status(),
        )

    @app.get("/logs")
    @login_required
    def logs() -> Any:
        """Render paginated access logs."""
        page = max(int(request.args.get("page", "1")), 1)
        limit = min(max(int(request.args.get("limit", "25")), 1), 100)
        offset = (page - 1) * limit
        filters = get_log_filters()
        rows = get_logs(limit=limit, offset=offset, filters=filters)
        return render_template(
            "logs.html",
            logs=rows,
            filters=filters,
            page=page,
            limit=limit,
        )

    @app.get("/logs/filter")
    @login_required
    def logs_filter() -> Any:
        """Return filtered logs as JSON or render the logs template."""
        filters = get_log_filters()
        rows = get_logs(limit=100, offset=0, filters=filters)
        if request.args.get("format") == "json":
            return jsonify(rows)
        return render_template("logs.html", logs=rows, filters=filters, page=1, limit=100)

    @app.get("/intruders")
    @login_required
    def intruders() -> Any:
        """Render a protected intruder-image gallery."""
        return render_template("intruders.html", images=list_intruder_images())

    @app.get("/intruders/image/<path:filename>")
    @login_required
    def intruder_image(filename: str) -> Any:
        """Serve an intruder image only to authenticated dashboard users."""
        return send_from_directory(INTRUDERS_DIR, filename)

    @app.route("/start", methods=["GET", "POST"])
    @login_required
    def start() -> Any:
        """Start the background recognition loop."""
        started = start_camera_thread()
        status = get_camera_status()
        if request.method == "GET":
            return redirect(url_for("dashboard"))
        return jsonify({"started": started, **status})

    @app.route("/stop", methods=["GET", "POST"])
    @login_required
    def stop() -> Any:
        """Stop the background recognition loop."""
        stopped = stop_camera_thread()
        status = get_camera_status()
        if request.method == "GET":
            return redirect(url_for("dashboard"))
        return jsonify({"stopped": stopped, **status})

    @app.get("/status")
    @login_required
    def status() -> Any:
        """Return recognition-loop status as JSON."""
        return jsonify(get_camera_status())


app = create_app()


def main() -> int:
    """Run the FaceGate dashboard development server."""
    app.run(host="127.0.0.1", port=FLASK_PORT, debug=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
