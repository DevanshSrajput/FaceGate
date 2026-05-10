"""Access control decisions with multi-frame confirmation and cooldowns."""

from __future__ import annotations

import time
from collections.abc import Callable

from config import ACCESS_COOLDOWN_SEC, CONFIRMATION_FRAMES


TimeProvider = Callable[[], float]


class AccessController:
    """Maintain recognition confirmation state and per-user access cooldowns."""

    def __init__(
        self,
        confirmation_frames: int = CONFIRMATION_FRAMES,
        cooldown_sec: int = ACCESS_COOLDOWN_SEC,
        time_provider: TimeProvider = time.monotonic,
    ) -> None:
        """Initialize access-control state."""
        if confirmation_frames < 1:
            raise ValueError("confirmation_frames must be at least 1.")
        if cooldown_sec < 0:
            raise ValueError("cooldown_sec cannot be negative.")

        self.confirmation_frames = confirmation_frames
        self.cooldown_sec = cooldown_sec
        self._time_provider = time_provider
        self._candidate_name: str | None = None
        self._candidate_count = 0
        self._last_logged_at: dict[str, float] = {}

    def decide(self, name: str, distance: float) -> tuple[str, str]:
        """Return GRANTED for confirmed known users, otherwise DENIED Unknown."""
        if name == "Unknown":
            self._candidate_name = None
            self._candidate_count = 0
            return "DENIED", "Unknown"

        if name == self._candidate_name:
            self._candidate_count += 1
        else:
            self._candidate_name = name
            self._candidate_count = 1

        if self._candidate_count >= self.confirmation_frames:
            return "GRANTED", name

        return "DENIED", "Unknown"

    def can_log(self, name: str) -> bool:
        """Return True when the named user is outside the access cooldown window."""
        now = self._time_provider()
        last_logged_at = self._last_logged_at.get(name)

        if last_logged_at is None or now - last_logged_at >= self.cooldown_sec:
            self._last_logged_at[name] = now
            return True

        return False

    def confirmation_count(self, name: str) -> int:
        """Return the current consecutive confirmation count for a candidate user."""
        if name != self._candidate_name:
            return 0
        return self._candidate_count

    def reset(self) -> None:
        """Clear all confirmation and cooldown state."""
        self._candidate_name = None
        self._candidate_count = 0
        self._last_logged_at.clear()
