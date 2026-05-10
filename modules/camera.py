"""OpenCV camera capture and live face recognition utilities."""

from __future__ import annotations

import os
import threading
import time
from collections.abc import Callable
from datetime import datetime

import cv2
import numpy as np

from config import CAMERA_INDEX, ENCODINGS_PATH, INTRUDERS_DIR, RECOGNITION_THRESHOLD
from modules.access_control import AccessController
from modules.alert import AlertManager
from modules.database import init_db, log_event
from modules.face_engine import (
    EncodingRecord,
    annotate_frame,
    detect_faces,
    encode_faces,
    load_encodings,
    match_face,
)


FrameCallback = Callable[[np.ndarray], None]


def build_intruder_image_path(
    intruders_dir: str = INTRUDERS_DIR,
    timestamp: datetime | None = None,
) -> str:
    """Build a timestamped intruder image path and avoid overwriting existing files."""
    capture_time = timestamp or datetime.now()
    base_name = capture_time.strftime("intruder_%Y%m%d_%H%M%S")
    candidate = os.path.join(intruders_dir, f"{base_name}.jpg")
    counter = 1

    while os.path.exists(candidate):
        candidate = os.path.join(intruders_dir, f"{base_name}_{counter}.jpg")
        counter += 1

    return candidate


def save_intruder_image(
    frame: np.ndarray,
    intruders_dir: str = INTRUDERS_DIR,
) -> str | None:
    """Save an annotated intruder frame as a JPEG and return the file path."""
    try:
        os.makedirs(intruders_dir, exist_ok=True)
        image_path = build_intruder_image_path(intruders_dir)
        saved = cv2.imwrite(image_path, frame)
        if not saved:
            raise OSError(f"OpenCV failed to write image to {image_path}.")
        return image_path
    except (cv2.error, OSError) as exc:
        print(f"Intruder image capture failed: {exc}")
        return None


def log_access_decisions(
    names: list[str],
    statuses: list[str],
    access_controller: AccessController,
    annotated_frame: np.ndarray,
    alert_manager: AlertManager | None = None,
) -> None:
    """Persist access decisions from a classified frame without crashing the loop."""
    for name, status in zip(names, statuses):
        normalized_status = status.upper()
        try:
            if normalized_status.startswith("GRANTED") and access_controller.can_log(name):
                log_event(name, "Granted")
            elif normalized_status.startswith("DENIED"):
                image_path = save_intruder_image(annotated_frame)
                log_event("Unknown", "Denied", image_path=image_path)
                if alert_manager is not None:
                    alert_manager.dispatch_intruder_alert(image_path)
        except (RuntimeError, ValueError) as exc:
            print(f"Access event logging skipped: {exc}")


def classify_frame(
    frame: np.ndarray,
    known_encodings: list[EncodingRecord],
    threshold: float = RECOGNITION_THRESHOLD,
    access_controller: AccessController | None = None,
) -> tuple[list[tuple[int, int, int, int]], list[str], list[str]]:
    """Detect and classify every visible face in a frame."""
    locations = detect_faces(frame)
    encodings = encode_faces(frame, locations) if locations else []
    names: list[str] = []
    statuses: list[str] = []

    for encoding in encodings:
        name, distance = match_face(encoding, known_encodings, threshold)
        if access_controller is None:
            status = "GRANTED" if name != "Unknown" else "DENIED"
            display_name = name
        else:
            decision, display_name = access_controller.decide(name, distance)
            if decision == "GRANTED":
                status = "GRANTED"
            elif name != "Unknown":
                count = access_controller.confirmation_count(name)
                status = f"VERIFYING {count}/{access_controller.confirmation_frames}"
                display_name = name
            else:
                status = "DENIED"

        names.append(display_name)
        statuses.append(f"{status} {distance:.2f}")

    return locations, names, statuses


def open_camera(camera_index: int = CAMERA_INDEX) -> cv2.VideoCapture:
    """Open an OpenCV video capture device and validate it is available."""
    capture = cv2.VideoCapture(camera_index)
    if not capture.isOpened():
        capture.release()
        raise RuntimeError(f"Unable to open camera index {camera_index}.")
    return capture


def run_camera_loop(
    camera_index: int = CAMERA_INDEX,
    encodings_path: str = ENCODINGS_PATH,
    threshold: float = RECOGNITION_THRESHOLD,
    window_name: str = "FaceGate Live Recognition",
    stop_event: threading.Event | None = None,
    frame_callback: FrameCallback | None = None,
) -> None:
    """Run the live webcam recognition loop until the user quits or stop_event is set."""
    known_encodings = load_encodings(encodings_path)
    if not known_encodings:
        print(f"No enrolled encodings found at {encodings_path}. Unknown faces will be denied.")

    try:
        init_db()
    except RuntimeError as exc:
        print(f"Database initialization skipped: {exc}")

    access_controller = AccessController()
    alert_manager = AlertManager()
    capture = open_camera(camera_index)
    print("FaceGate live recognition started. Press Q or ESC to stop.")

    try:
        while stop_event is None or not stop_event.is_set():
            ok, frame = capture.read()
            if not ok:
                print("Camera frame read failed; retrying...")
                time.sleep(0.2)
                continue

            locations, names, statuses = classify_frame(
                frame,
                known_encodings,
                threshold,
                access_controller,
            )
            annotated = annotate_frame(frame, locations, names, statuses)
            log_access_decisions(names, statuses, access_controller, annotated, alert_manager)

            if frame_callback is not None:
                frame_callback(annotated)

            cv2.imshow(window_name, annotated)
            key = cv2.waitKey(1) & 0xFF
            if key in {27, ord("q"), ord("Q")}:
                break
    finally:
        access_controller.reset()
        capture.release()
        cv2.destroyAllWindows()


def recognize_once(
    frame: np.ndarray,
    encodings_path: str = ENCODINGS_PATH,
    threshold: float = RECOGNITION_THRESHOLD,
) -> tuple[np.ndarray, list[str], list[str]]:
    """Classify a single frame and return an annotated copy with names and statuses."""
    known_encodings = load_encodings(encodings_path)
    annotated = frame.copy()
    access_controller = AccessController(confirmation_frames=1)
    locations, names, statuses = classify_frame(
        annotated,
        known_encodings,
        threshold,
        access_controller,
    )
    annotate_frame(annotated, locations, names, statuses)
    return annotated, names, statuses
