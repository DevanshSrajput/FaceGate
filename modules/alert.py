"""Telegram and email alert dispatch for unauthorized access events."""

from __future__ import annotations

import logging
import os
import smtplib
import threading
import time
from collections.abc import Callable
from datetime import datetime
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests

from config import (
    ALERT_COOLDOWN_SEC,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_RECIPIENT,
    SMTP_USERNAME,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
)


TimeProvider = Callable[[], float]

logging.basicConfig(
    filename="alerts.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)


class AlertManager:
    """Manage Telegram alert cooldowns and asynchronous dispatch."""

    def __init__(
        self,
        bot_token: str = TELEGRAM_BOT_TOKEN,
        chat_id: str = TELEGRAM_CHAT_ID,
        cooldown_sec: int = ALERT_COOLDOWN_SEC,
        time_provider: TimeProvider = time.monotonic,
    ) -> None:
        """Initialize alert configuration and cooldown state."""
        if cooldown_sec < 0:
            raise ValueError("cooldown_sec cannot be negative.")

        self.bot_token = bot_token
        self.chat_id = chat_id
        self.cooldown_sec = cooldown_sec
        self._time_provider = time_provider
        self._last_alert_at: float | None = None
        self._lock = threading.Lock()

    def can_alert(self) -> bool:
        """Return True when the alert cooldown has elapsed."""
        with self._lock:
            now = self._time_provider()
            if self._last_alert_at is None or now - self._last_alert_at >= self.cooldown_sec:
                self._last_alert_at = now
                return True
            return False

    def dispatch_intruder_alert(
        self,
        image_path: str | None,
        timestamp: datetime | None = None,
    ) -> bool:
        """Start a daemon thread to send an intruder alert when cooldown allows."""
        if not self.can_alert():
            logging.info("Alert suppressed by cooldown.")
            return False

        alert_time = timestamp or datetime.now()

        def _send_all() -> None:
            self.send_telegram_alert(image_path, alert_time)
            self.send_email_alert(image_path, alert_time)

        thread = threading.Thread(target=_send_all, daemon=True)
        thread.start()
        return True

    def send_telegram_alert(
        self,
        image_path: str | None,
        timestamp: datetime,
    ) -> bool:
        """Send an unauthorized-access Telegram alert with an optional image."""
        if not self.bot_token or not self.chat_id:
            logging.warning("Telegram alert skipped because token or chat ID is missing.")
            return False

        caption = f"ALERT: Unauthorized access detected at {timestamp.isoformat(timespec='seconds')}. Image attached."
        base_url = f"https://api.telegram.org/bot{self.bot_token}"

        try:
            if image_path and os.path.exists(image_path):
                with open(image_path, "rb") as image_file:
                    response = requests.post(
                        f"{base_url}/sendPhoto",
                        data={"chat_id": self.chat_id, "caption": caption},
                        files={"photo": image_file},
                        timeout=10,
                    )
            else:
                response = requests.post(
                    f"{base_url}/sendMessage",
                    data={"chat_id": self.chat_id, "text": caption},
                    timeout=10,
                )

            response.raise_for_status()
            logging.info("Telegram alert sent successfully.")
            return True
        except (OSError, requests.RequestException) as exc:
            logging.error("Telegram alert failed: %s", exc)
            return False

    def send_email_alert(
        self,
        image_path: str | None,
        timestamp: datetime,
    ) -> bool:
        """Send an intruder alert via SMTP email as a secondary channel."""
        if not SMTP_HOST or not SMTP_USERNAME or not SMTP_PASSWORD or not SMTP_RECIPIENT:
            logging.info("Email alert skipped because SMTP is not configured.")
            return False

        try:
            msg = MIMEMultipart()
            msg["Subject"] = f"FaceGate Alert: Unauthorized access at {timestamp.isoformat(timespec='seconds')}"
            msg["From"] = SMTP_USERNAME
            msg["To"] = SMTP_RECIPIENT

            body = (
                f"ALERT: Unauthorized access was detected at "
                f"{timestamp.isoformat(timespec='seconds')}.\n\n"
                f"The intruder image is attached."
            )
            msg.attach(MIMEText(body, "plain"))

            if image_path and os.path.exists(image_path):
                with open(image_path, "rb") as img_file:
                    image_part = MIMEImage(img_file.read(), name=os.path.basename(image_path))
                    msg.attach(image_part)

            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
                server.starttls()
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.send_message(msg)

            logging.info("Email alert sent successfully to %s.", SMTP_RECIPIENT)
            return True
        except (OSError, smtplib.SMTPException) as exc:
            logging.error("Email alert failed: %s", exc)
            return False


_DEFAULT_ALERT_MANAGER = AlertManager()


def send_telegram_alert(image_path: str | None, timestamp: datetime) -> bool:
    """Send a Telegram alert using the default AlertManager configuration."""
    return _DEFAULT_ALERT_MANAGER.send_telegram_alert(image_path, timestamp)


def can_alert() -> bool:
    """Return whether the default alert manager would allow an alert."""
    return _DEFAULT_ALERT_MANAGER.can_alert()


def send_email_alert(image_path: str | None, timestamp: datetime) -> bool:
    """Send an optional email alert using the default AlertManager configuration."""
    return _DEFAULT_ALERT_MANAGER.send_email_alert(image_path, timestamp)
