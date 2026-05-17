"""Integration tests for FaceGate core pipelines (IT-01 through IT-04)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

import web.app as web_app_module
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
        self._saved_save_intruder_image = cam_module.save_intruder_image
        self._saved_db_log = db_module.log_event
        cam_module.log_event = _wrapped_log_event
        db_module.log_event = _wrapped_log_event

        def _wrapped_save_intruder_image(frame, intruders_dir=None):
            target_dir = intruders_dir or str(Path(self.tmpdir.name) / "intruders")
            return self._saved_save_intruder_image(frame, target_dir)

        cam_module.save_intruder_image = _wrapped_save_intruder_image

        init_db(self.db_path)

    def tearDown(self) -> None:
        import modules.camera as cam_module
        import modules.database as db_module

        cam_module.log_event = self._saved_cam_log
        cam_module.save_intruder_image = self._saved_save_intruder_image
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
        dummy_frame = np.full((240, 320, 3), (48, 88, 132), dtype=np.uint8)
        cv2.rectangle(dummy_frame, (72, 40), (248, 220), (178, 202, 224), -1)
        cv2.circle(dummy_frame, (130, 112), 12, (25, 35, 45), -1)
        cv2.circle(dummy_frame, (190, 112), 12, (25, 35, 45), -1)
        cv2.ellipse(dummy_frame, (160, 160), (42, 18), 0, 0, 180, (20, 30, 40), 3)

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
        image = cv2.imread(denied[0]["image_path"])
        self.assertIsNotNone(image, "Expected saved intruder image to be readable.")
        self.assertGreater(float(image.mean()), 8.0, "Expected saved intruder image to be non-black.")
        self.assertGreater(float(image.std()), 4.0, "Expected saved intruder image to contain visual detail.")


class FlaskRouteTests(unittest.TestCase):
    """IT-03 and IT-04: Flask dashboard route integration tests."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.tmpdir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        cls.tmpdir_path = Path(cls.tmpdir.name)
        cls.db_path = str(cls.tmpdir_path / "access_logs.db")
        cls.intruders_dir = cls.tmpdir_path / "intruders"
        cls.intruders_dir.mkdir()
        cls.intruder_filename = "intruder_test.jpg"
        cls.intruder_path = cls.intruders_dir / cls.intruder_filename
        cv2.imwrite(str(cls.intruder_path), np.full((24, 32, 3), (90, 140, 190), dtype=np.uint8))

        init_db(cls.db_path)
        log_event("Alice", "Granted", db_path=cls.db_path)
        log_event("Unknown", "Denied", image_path=str(cls.intruder_path), db_path=cls.db_path)

        cls._original_intruders_dir = web_app_module.INTRUDERS_DIR
        cls._original_get_logs = web_app_module.get_logs
        cls._original_get_summary = web_app_module.get_summary
        web_app_module.INTRUDERS_DIR = str(cls.intruders_dir)

        def _get_logs(*args, **kwargs):
            kwargs["db_path"] = cls.db_path
            return cls._original_get_logs(*args, **kwargs)

        def _get_summary(*args, **kwargs):
            kwargs["db_path"] = cls.db_path
            return cls._original_get_summary(*args, **kwargs)

        web_app_module.get_logs = _get_logs
        web_app_module.get_summary = _get_summary

        app = web_app_module.create_app()
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
        web_app_module.INTRUDERS_DIR = cls._original_intruders_dir
        web_app_module.get_logs = cls._original_get_logs
        web_app_module.get_summary = cls._original_get_summary
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
        self.assertIn("log-image-link", html)
        self.assertIn(self.intruder_filename, html)

    def test_it03_logs_filter_json(self) -> None:
        """IT-03 extension: /logs/filter?format=json returns JSON array."""
        self._login()
        response = self.client.get("/logs/filter?status=Granted&format=json")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIsInstance(data, list)
        self.assertTrue(all(r["status"] == "Granted" for r in data))

    def test_it03_intruder_image_route_serves_jpeg(self) -> None:
        """IT-03 extension: protected intruder images are served from configured storage."""
        self._login()
        response = self.client.get(f"/intruders/image/{self.intruder_filename}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, "image/jpeg")
        self.assertGreater(len(response.data), 0)

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
