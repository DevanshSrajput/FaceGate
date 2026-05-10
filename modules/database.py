"""SQLite persistence for FaceGate access events."""

from __future__ import annotations

import os
import sqlite3
import sys
from typing import Any

from config import DB_PATH


LogRow = dict[str, Any]


def _ensure_parent_dir(db_path: str) -> None:
    """Create the parent directory for a database path when one is configured."""
    directory = os.path.dirname(db_path)
    if directory:
        os.makedirs(directory, exist_ok=True)


def _row_to_dict(row: sqlite3.Row) -> LogRow:
    """Convert a SQLite row into a plain dictionary."""
    return {
        "id": row["id"],
        "name": row["name"],
        "status": row["status"],
        "timestamp": row["timestamp"],
        "image_path": row["image_path"],
    }


def init_db(db_path: str = DB_PATH) -> None:
    """Create the SQLite database and access_logs table if they do not exist."""
    try:
        _ensure_parent_dir(db_path)
        with sqlite3.connect(db_path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS access_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('Granted', 'Denied')),
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    image_path TEXT
                )
                """
            )
            connection.commit()
    except sqlite3.Error as exc:
        print(f"Database initialization failed: {exc}", file=sys.stderr)
    except OSError as exc:
        print(f"Database directory setup failed: {exc}", file=sys.stderr)


def log_event(
    name: str,
    status: str,
    image_path: str | None = None,
    db_path: str = DB_PATH,
) -> int | None:
    """Insert one access event row and return its ID, or None on failure."""
    try:
        normalized_status = status.capitalize()
        if normalized_status not in {"Granted", "Denied"}:
            raise ValueError("status must be 'Granted' or 'Denied'.")

        init_db(db_path)
        with sqlite3.connect(db_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO access_logs (name, status, image_path)
                VALUES (?, ?, ?)
                """,
                (name, normalized_status, image_path),
            )
            connection.commit()
            return int(cursor.lastrowid)
    except sqlite3.Error as exc:
        print(f"Database insert failed: {exc}", file=sys.stderr)
    except ValueError as exc:
        print(f"Database insert rejected: {exc}", file=sys.stderr)
    except OSError as exc:
        print(f"Database path error: {exc}", file=sys.stderr)

    return None


def get_logs(
    limit: int = 50,
    offset: int = 0,
    filters: dict[str, str] | None = None,
    db_path: str = DB_PATH,
) -> list[LogRow]:
    """Return paginated access logs with optional name, status, and date filters."""
    filters = filters or {}
    clauses: list[str] = []
    values: list[str | int] = []

    if filters.get("name"):
        clauses.append("name LIKE ?")
        values.append(f"%{filters['name']}%")
    if filters.get("status"):
        clauses.append("status = ?")
        values.append(filters["status"].capitalize())
    if filters.get("date"):
        clauses.append("DATE(timestamp) = DATE(?)")
        values.append(filters["date"])

    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    values.extend([limit, offset])

    try:
        init_db(db_path)
        with sqlite3.connect(db_path) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                f"""
                SELECT id, name, status, timestamp, image_path
                FROM access_logs
                {where_sql}
                ORDER BY timestamp DESC, id DESC
                LIMIT ? OFFSET ?
                """,
                values,
            ).fetchall()
            return [_row_to_dict(row) for row in rows]
    except sqlite3.Error as exc:
        print(f"Database query failed: {exc}", file=sys.stderr)
    except OSError as exc:
        print(f"Database path error: {exc}", file=sys.stderr)

    return []


def get_summary(db_path: str = DB_PATH) -> dict[str, Any]:
    """Return today's access totals and the latest events for the dashboard."""
    try:
        init_db(db_path)
        with sqlite3.connect(db_path) as connection:
            connection.row_factory = sqlite3.Row
            total_today = connection.execute(
                "SELECT COUNT(*) FROM access_logs WHERE DATE(timestamp) = DATE('now')"
            ).fetchone()[0]
            granted_today = connection.execute(
                """
                SELECT COUNT(*) FROM access_logs
                WHERE status = 'Granted' AND DATE(timestamp) = DATE('now')
                """
            ).fetchone()[0]
            denied_today = connection.execute(
                """
                SELECT COUNT(*) FROM access_logs
                WHERE status = 'Denied' AND DATE(timestamp) = DATE('now')
                """
            ).fetchone()[0]
            last_rows = connection.execute(
                """
                SELECT id, name, status, timestamp, image_path
                FROM access_logs
                ORDER BY timestamp DESC, id DESC
                LIMIT 10
                """
            ).fetchall()
            last_events = [_row_to_dict(row) for row in last_rows]

        return {
            "total_today": int(total_today),
            "granted_today": int(granted_today),
            "denied_today": int(denied_today),
            "last_events": last_events,
        }
    except sqlite3.Error as exc:
        print(f"Database summary failed: {exc}", file=sys.stderr)
    except OSError as exc:
        print(f"Database path error: {exc}", file=sys.stderr)

    return {
        "total_today": 0,
        "granted_today": 0,
        "denied_today": 0,
        "last_events": [],
    }
