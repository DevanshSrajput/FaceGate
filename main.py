"""FaceGate entry point for the live recognition camera loop."""

from __future__ import annotations

import argparse
import sys

from config import CAMERA_INDEX, ENCODINGS_PATH, RECOGNITION_THRESHOLD
from modules.camera import run_camera_loop


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the live recognition loop."""
    parser = argparse.ArgumentParser(description="Start FaceGate live recognition.")
    parser.add_argument(
        "--camera-index",
        type=int,
        default=CAMERA_INDEX,
        help="OpenCV camera index to use.",
    )
    parser.add_argument(
        "--encodings-path",
        default=ENCODINGS_PATH,
        help="Path to the enrolled face encodings pickle file.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=RECOGNITION_THRESHOLD,
        help="Face recognition distance threshold.",
    )
    return parser.parse_args()

def main() -> int:
    """Run the FaceGate live camera recognition loop."""
    args = parse_args()

    try:
        run_camera_loop(
            camera_index=args.camera_index,
            encodings_path=args.encodings_path,
            threshold=args.threshold,
        )
    except (RuntimeError, ValueError) as exc:
        print(f"FaceGate failed: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
