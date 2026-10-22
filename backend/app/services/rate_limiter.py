from datetime import datetime, timezone
import threading
from typing import Dict, List

from backend.app.core.config import settings


class InMemoryLoginRateLimiter:
    """
    Thread-safe in-memory rate limiter for tracking failed login attempts.
    Guards against credential stuffing and brute force attacks.
    """

    def __init__(
        self,
        max_attempts: int = settings.LOGIN_RATE_LIMIT_MAX_ATTEMPTS,
        window_seconds: int = settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS,
    ):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._lock = threading.Lock()
        self._attempts: Dict[str, List[float]] = {}

    def _clean_old_attempts(self, key: str, now: float) -> None:
        cutoff = now - self.window_seconds
        if key in self._attempts:
            self._attempts[key] = [t for t in self._attempts[key] if t > cutoff]
            if not self._attempts[key]:
                del self._attempts[key]

    def is_rate_limited(self, key: str) -> bool:
        with self._lock:
            now = datetime.now(timezone.utc).timestamp()
            self._clean_old_attempts(key, now)
            attempts = self._attempts.get(key, [])
            return len(attempts) >= self.max_attempts

    def record_failure(self, key: str) -> None:
        with self._lock:
            now = datetime.now(timezone.utc).timestamp()
            self._clean_old_attempts(key, now)
            if key not in self._attempts:
                self._attempts[key] = []
            self._attempts[key].append(now)

    def reset(self, key: str) -> None:
        with self._lock:
            self._attempts.pop(key, None)

    def clear_all(self) -> None:
        """Helper for test suites."""
        with self._lock:
            self._attempts.clear()


login_rate_limiter = InMemoryLoginRateLimiter()
