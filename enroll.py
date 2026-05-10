"""CLI enrollment script for adding authorized FaceGate users."""

from __future__ import annotations

import argparse
import sys

import cv2

from config import CAMERA_INDEX, ENCODINGS_PATH
from modules.face_engine import detect_faces, encode_faces, load_encodings, save_encodings


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for enrollment."""
    parser = argparse.ArgumentParser(description="Enroll a new authorized FaceGate user.")
    parser.add_argument("name", help="Display name for the authorized user.")
    parser.add_argument(
        "--samples",
        type=int,
        default=1,
        help="Number of face samples to capture for this user.",
    )
    parser.add_argument(
        "--camera-index",
        type=int,
        default=CAMERA_INDEX,
        help="OpenCV camera index to use for capture.",
    )
    parser.add_argument(
        "--encodings-path",
        default=ENCODINGS_PATH,
        help="Path where enrolled encodings are stored.",
    )
    return parser.parse_args()


def capture_sample(camera: cv2.VideoCapture, sample_number: int, total_samples: int):
    """Capture one valid face encoding from the webcam."""
    print(f"Sample {sample_number}/{total_samples}: press SPACE to capture, ESC to cancel.")

    while True:
        ok, frame = camera.read()
        if not ok:
            raise RuntimeError("Unable to read from camera.")

        preview = frame.copy()
        locations = detect_faces(preview)
        statuses = ["READY"] * len(locations)
        names = [f"Face {index + 1}" for index in range(len(locations))]

        from modules.face_engine import annotate_frame

        annotate_frame(preview, locations, names, statuses)
        cv2.imshow("FaceGate Enrollment", preview)

        key = cv2.waitKey(1) & 0xFF
        if key == 27:
            raise KeyboardInterrupt("Enrollment cancelled.")
        if key == 32:
            if len(locations) != 1:
                print("Capture rejected: exactly one face must be visible.")
                continue

            encodings = encode_faces(frame, locations)
            if not encodings:
                print("Capture rejected: face encoding failed.")
                continue

            return encodings[0]


def enroll_user(
    name: str,
    samples: int,
    camera_index: int,
    encodings_path: str,
) -> int:
    """Capture face samples for a user and persist them to the encodings file."""
    if samples < 1:
        raise ValueError("samples must be at least 1.")

    camera = cv2.VideoCapture(camera_index)
    if not camera.isOpened():
        raise RuntimeError(f"Unable to open camera index {camera_index}.")

    saved_count = 0
    try:
        records = load_encodings(encodings_path)
        for sample_number in range(1, samples + 1):
            encoding = capture_sample(camera, sample_number, samples)
            records.append((name, encoding))
            saved_count += 1

        save_encodings(records, encodings_path)
        return saved_count
    finally:
        camera.release()
        cv2.destroyAllWindows()


def main() -> int:
    """Run the enrollment CLI."""
    args = parse_args()

    try:
        saved_count = enroll_user(
            name=args.name,
            samples=args.samples,
            camera_index=args.camera_index,
            encodings_path=args.encodings_path,
        )
    except (KeyboardInterrupt, RuntimeError, ValueError) as exc:
        print(f"Enrollment failed: {exc}", file=sys.stderr)
        return 1

    print(f"Enrollment complete: saved {saved_count} sample(s) for {args.name}.")
    print(f"Encodings file: {args.encodings_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
