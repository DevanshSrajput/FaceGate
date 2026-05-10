"""Unit tests for FaceGate core modules."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np

from modules.access_control import AccessController
from modules.alert import AlertManager
from modules.database import get_logs, get_summary, init_db, log_event
from modules.face_engine import load_encodings, match_face, save_encodings


class FaceEngineTests(unittest.TestCase):
    """Tests for face engine helpers."""

    def test_match_face_known_identical_encoding(self) -> None:
        """UT-01: identical encodings should match the known name with zero distance."""
        encoding = np.zeros(128)
        name, distance = match_face(encoding, [("Alice", encoding)], 0.6)
        self.assertEqual(name, "Alice")
        self.assertAlmostEqual(distance, 0.0, places=6)

    def test_match_face_unknown_encoding(self) -> None:
        """UT-02: distant encodings should return Unknown."""
        known = np.zeros(128)
        unknown = np.ones(128)
        name, distance = match_face(unknown, [("Alice", known)], 0.6)
        self.assertEqual(name, "Unknown")
        self.assertGreater(distance, 0.6)

    def test_encoding_round_trip(self) -> None:
        """Saving and loading encodings should preserve records."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "encodings.pkl"
            data = [("Alice", np.zeros(128))]
            save_encodings(data, str(path))
            loaded = load_encodings(str(path))
            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0][0], "Alice")


class DatabaseTests(unittest.TestCase):
    """Tests for SQLite persistence helpers."""

    def setUp(self) -> None:
        """Create a temporary SQLite database for each test."""
        self.tmpdir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.db_path = Path(self.tmpdir.name) / "access_logs.db"
        init_db(str(self.db_path))

    def tearDown(self) -> None:
        """Remove the temporary database directory after each test."""
        self.tmpdir.cleanup()

    def test_init_db_creates_table(self) -> None:
        """UT-03: init_db should create the access_logs table."""
        self.assertTrue(self.db_path.exists())
        rows = get_logs(db_path=str(self.db_path))
        self.assertEqual(rows, [])

    def test_log_event_inserts_row(self) -> None:
        """UT-04: log_event should insert a retrievable row."""
        log_event("Alice", "Granted", db_path=str(self.db_path))
        rows = get_logs(db_path=str(self.db_path))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["name"], "Alice")
        self.assertEqual(rows[0]["status"], "Granted")

    def test_get_summary_counts_rows(self) -> None:
        """Summary should reflect inserted rows."""
        log_event("Alice", "Granted", db_path=str(self.db_path))
        log_event("Unknown", "Denied", db_path=str(self.db_path))
        summary = get_summary(db_path=str(self.db_path))
        self.assertGreaterEqual(summary["total_today"], 2)
        self.assertGreaterEqual(summary["granted_today"], 1)
        self.assertGreaterEqual(summary["denied_today"], 1)


class AccessControlTests(unittest.TestCase):
    """Tests for cooldown and alert rate limiting."""

    def test_can_log_respects_cooldown(self) -> None:
        """UT-05: can_log should reject repeated logs inside the cooldown window."""
        now = [100.0]
        controller = AccessController(
            confirmation_frames=1,
            cooldown_sec=30,
            time_provider=lambda: now[0],
        )
        self.assertTrue(controller.can_log("Alice"))
        self.assertFalse(controller.can_log("Alice"))
        now[0] = 131.0
        self.assertTrue(controller.can_log("Alice"))


class AlertTests(unittest.TestCase):
    """Tests for alert cooldown behavior."""

    def test_can_alert_respects_cooldown(self) -> None:
        """UT-06: can_alert should toggle after the cooldown interval."""
        now = [100.0]
        manager = AlertManager(
            bot_token="",
            chat_id="",
            cooldown_sec=60,
            time_provider=lambda: now[0],
        )
        self.assertTrue(manager.can_alert())
        self.assertFalse(manager.can_alert())
        now[0] = 161.0
        self.assertTrue(manager.can_alert())


if __name__ == "__main__":
    unittest.main()
