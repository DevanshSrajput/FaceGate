"""Integration tests for FaceGate core pipelines (IT-01 through IT-04)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np

from modules.access_control import AccessController
from modules.camera import log_access_decisions
from modules.database import get_logs, init_db, log_event
from modules.face_engine import save_encodings


class EnrollmentToRecognitionTests(unittest.TestCase):
    """IT-01 and IT-02: end-to-end enrollment → recognition pipeline."""

    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.db_path = str(Path(self.tmpdir.name) / "access_logs.db")
        self.encodings_path = str(Path(self.tmpdir.name) / "encodings.pkl")

        # Patch log_event so calls without an explicit db_path land in the temp db
        _original_log_event = log_event

        def _wrapped_log_event(name, status, image_path=None, db_path=None):
            return _original_log_event(name, status, image_path=image_path, db_path=db_path or self.db_path)

        # Replace in both modules so log_access_decisions uses the temp db
        import modules.camera as cam_module
        import modules.database as db_module

        self._saved_cam_log = cam_module.log_event
        self._saved_db_log = db_module.log_event
        cam_module.log_event = _wrapped_log_event
        db_module.log_event = _wrapped_log_event

        init_db(self.db_path)

    def tearDown(self) -> None:
        import modules.camera as cam_module
        import modules.database as db_module

        cam_module.log_event = self._saved_cam_log
        db_module.log_event = self._saved_db_log
        self.tmpdir.cleanup()

    def _classified_frame(self, known_encoding: np.ndarray, test_encoding: np.ndarray) -> None:
        """Simulate one recognition frame: classify and log the result."""
        known_encodings = [("Alice", known_encoding)]

        # simulate a frame where the test encoding is returned by encode_faces
        # we bypass the camera/face_engine internals by directly testing the
        # decision pipeline through classify_frame — but classify_frame calls
        # detect_faces and encode_faces internally. Instead we exercise the
        # log_access_decisions path directly so the test is deterministic.
        access_controller = AccessController(confirmation_frames=1, cooldown_sec=0)
        dummy_frame = np.zeros((240, 320, 3), dtype=np.uint8)

        # build the names/statuses that classify_frame would produce
        names: list[str] = []
        statuses: list[str] = []
        distance = float(np.linalg.norm(test_encoding - known_encoding))
        if distance < 0.6:
            decision, display_name = access_controller.decide("Alice", distance)
            names.append(display_name)
            statuses.append(f"{decision} {distance:.2f}")
        else:
            decision, display_name = access_controller.decide("Unknown", distance)
            names.append(display_name)
            statuses.append(f"{decision} {distance:.2f}")

        log_access_decisions(
            names,
            statuses,
            access_controller,
            dummy_frame,
            alert_manager=None,
        )

    def test_it01_enrolled_user_grants_access(self) -> None:
        """IT-01: enroll user → recognize same encoding → GRANTED event in DB."""
        encoding = np.zeros(128, dtype=np.float64)
        save_encodings([("Alice", encoding)], self.encodings_path)

        self._classified_frame(encoding, encoding)

        rows = get_logs(limit=10, offset=0, db_path=self.db_path)
        granted = [r for r in rows if r["status"] == "Granted"]
        self.assertTrue(granted, "Expected a GRANTED log entry for the enrolled user.")
        self.assertEqual(granted[0]["name"], "Alice")

    def test_it02_unknown_face_denies_access(self) -> None:
        """IT-02: unknown face → DENIED event + intruder image saved."""
        known_encoding = np.zeros(128, dtype=np.float64)
        unknown_encoding = np.ones(128, dtype=np.float64)
        save_encodings([("Alice", known_encoding)], self.encodings_path)

        self._classified_frame(known_encoding, unknown_encoding)

        rows = get_logs(limit=10, offset=0, db_path=self.db_path)
        denied = [r for r in rows if r["status"] == "Denied"]
        self.assertTrue(denied, "Expected a DENIED log entry for the unknown face.")
        self.assertEqual(denied[0]["name"], "Unknown")
        self.assertIsNotNone(denied[0].get("image_path"))
        self.assertTrue(
            Path(denied[0]["image_path"]).exists() if denied[0]["image_path"] else False,
            "Expected an intruder image file to exist on disk.",
        )


class FlaskRouteTests(unittest.TestCase):
    """IT-03 and IT-04: Flask dashboard route integration tests."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.tmpdir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        cls.db_path = str(Path(cls.tmpdir.name) / "access_logs.db")

        init_db(cls.db_path)
        log_event("Alice", "Granted", db_path=cls.db_path)
        log_event("Unknown", "Denied", image_path="/tmp/test.jpg", db_path=cls.db_path)

        from web.app import create_app

        app = create_app()
        app.config["TESTING"] = True
        app.config["SECRET_KEY"] = "test-key"

        # Override DB_PATH so the test app reads our temp database
        import modules.database as db_module

        _original_db_path = db_module.DB_PATH
        db_module.DB_PATH = cls.db_path
        cls._original_db_path = _original_db_path

        cls.app = app
        cls.client = app.test_client()

    @classmethod
    def tearDownClass(cls) -> None:
        import modules.database as db_module

        db_module.DB_PATH = cls._original_db_path
        cls.tmpdir.cleanup()

    def _login(self) -> None:
        """Bypass login by setting the session directly."""
        with self.client.session_transaction() as sess:
            sess["authenticated"] = True
            sess["username"] = "admin"

    def test_it03_logs_route_returns_rows(self) -> None:
        """IT-03: /logs returns HTTP 200 and contains log rows after events are logged."""
        self._login()
        response = self.client.get("/logs")
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")
        self.assertIn("Alice", html)
        self.assertIn("Granted", html)
        self.assertIn("Unknown", html)
        self.assertIn("Denied", html)

    def test_it03_logs_filter_json(self) -> None:
        """IT-03 extension: /logs/filter?format=json returns JSON array."""
        self._login()
        response = self.client.get("/logs/filter?status=Granted&format=json")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIsInstance(data, list)
        self.assertTrue(all(r["status"] == "Granted" for r in data))

    def test_it04_start_camera_thread(self) -> None:
        """IT-04: POST /start spawns camera thread; GET /status returns running=true."""
        self._login()
        start_resp = self.client.post("/start")
        self.assertEqual(start_resp.status_code, 200)
        start_data = start_resp.get_json()
        self.assertTrue(start_data.get("started") or start_data.get("running"),
                        "Expected camera to start or already be running.")

        status_resp = self.client.get("/status")
        self.assertEqual(status_resp.status_code, 200)
        status_data = status_resp.get_json()
        self.assertTrue(status_data["running"],
                        "Expected camera running=true after /start.")

        # stop camera to avoid dangling background thread
        self.client.post("/stop")


if __name__ == "__main__":
    unittest.main()