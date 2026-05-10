"""Face detection, encoding, matching, and annotation utilities."""

from __future__ import annotations

import os
import pickle
from typing import Iterable

import cv2
import face_recognition
import numpy as np

from config import DETECTION_MODEL, FRAME_SCALE


EncodingRecord = tuple[str, np.ndarray]
FaceLocation = tuple[int, int, int, int]


def load_encodings(path: str) -> list[EncodingRecord]:
    """Load serialized face encoding records from a pickle file."""
    if not os.path.exists(path):
        return []

    with open(path, "rb") as file_obj:
        data = pickle.load(file_obj)

    if not isinstance(data, list):
        raise ValueError("Encoding file must contain a list of (name, encoding) pairs.")

    return data


def save_encodings(data: list[EncodingRecord], path: str) -> None:
    """Serialize face encoding records to a pickle file."""
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)

    with open(path, "wb") as file_obj:
        pickle.dump(data, file_obj)


def detect_faces(frame: np.ndarray) -> list[FaceLocation]:
    """Detect faces in a BGR OpenCV frame and return scaled frame locations."""
    small_frame = cv2.resize(frame, (0, 0), fx=FRAME_SCALE, fy=FRAME_SCALE)
    rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
    small_locations = face_recognition.face_locations(
        rgb_small_frame,
        model=DETECTION_MODEL,
    )

    scale = 1 / FRAME_SCALE
    return [
        (
            int(top * scale),
            int(right * scale),
            int(bottom * scale),
            int(left * scale),
        )
        for top, right, bottom, left in small_locations
    ]


def encode_faces(frame: np.ndarray, locations: list[FaceLocation]) -> list[np.ndarray]:
    """Compute 128-dimensional face encodings for detected face locations."""
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return face_recognition.face_encodings(rgb_frame, known_face_locations=locations)


def match_face(
    encoding: np.ndarray,
    known_encodings: Iterable[EncodingRecord],
    threshold: float,
) -> tuple[str, float]:
    """Return the best matching enrolled name and distance for one face encoding."""
    records = list(known_encodings)
    if not records:
        return "Unknown", float("inf")

    names = [name for name, _ in records]
    encodings = [known_encoding for _, known_encoding in records]
    distances = face_recognition.face_distance(encodings, encoding)
    best_index = int(np.argmin(distances))
    best_distance = float(distances[best_index])

    if best_distance < threshold:
        return names[best_index], best_distance

    return "Unknown", best_distance


def annotate_frame(
    frame: np.ndarray,
    locations: list[FaceLocation],
    names: list[str],
    statuses: list[str],
) -> np.ndarray:
    """Draw face boxes and labels on a BGR frame in-place and return the frame."""
    for (top, right, bottom, left), name, status in zip(locations, names, statuses):
        normalized_status = status.upper()
        is_granted = normalized_status.startswith(("GRANTED", "GRANT", "AUTHORIZED"))
        color = (0, 180, 0) if is_granted else (0, 0, 255)
        label = f"{name} - {status}"

        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        cv2.rectangle(frame, (left, bottom - 24), (right, bottom), color, cv2.FILLED)
        cv2.putText(
            frame,
            label,
            (left + 6, bottom - 7),
            cv2.FONT_HERSHEY_DUPLEX,
            0.55,
            (255, 255, 255),
            1,
        )

    return frame
