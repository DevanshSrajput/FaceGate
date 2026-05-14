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

# Hardcoded credentials for web dashboard (never change)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = "scrypt:32768:8:1$l0ysQ4Sus4Z9E4bx$f81228bf4912f873b7a06e5c5aa20edb0794f3c3157cd7ef49e3d4ce2c0a82f5513f3032836e02739545f065e8b436375b91b4aabace2bd142168ef56d231950"

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_RECIPIENT = os.getenv("SMTP_RECIPIENT", "")
