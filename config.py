"""Configuration values for the FaceGate access control system."""

from __future__ import annotations

import os

from dotenv import load_dotenv


load_dotenv()

RECOGNITION_THRESHOLD = float(os.getenv("RECOGNITION_THRESHOLD", "0.6"))
CONFIRMATION_FRAMES = int(os.getenv("CONFIRMATION_FRAMES", "3"))
ACCESS_COOLDOWN_SEC = int(os.getenv("ACCESS_COOLDOWN_SEC", "30"))
ALERT_COOLDOWN_SEC = int(os.getenv("ALERT_COOLDOWN_SEC", "60"))
CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", "0"))
FRAME_SCALE = float(os.getenv("FRAME_SCALE", "0.25"))
DB_PATH = os.getenv("DB_PATH", "./data/access_logs.db")
ENCODINGS_PATH = os.getenv("ENCODINGS_PATH", "./data/encodings.pkl")
INTRUDERS_DIR = os.getenv("INTRUDERS_DIR", "./intruders/")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
DETECTION_MODEL = os.getenv("DETECTION_MODEL", "hog")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", "")
