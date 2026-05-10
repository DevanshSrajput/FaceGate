"""Telegram and email alert dispatch for unauthorized access events."""

from __future__ import annotations

import logging
import os
import threading
import time
from collections.abc import Callable
from datetime import datetime

import requests

from config import ALERT_COOLDOWN_SEC, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


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
        thread = threading.Thread(
            target=self.send_telegram_alert,
            args=(image_path, alert_time),
            daemon=True,
        )
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
        """Placeholder for optional SMTP email alert support."""
        logging.info(
            "Email alert not configured for image_path=%s timestamp=%s.",
            image_path,
            timestamp.isoformat(timespec="seconds"),
        )
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
