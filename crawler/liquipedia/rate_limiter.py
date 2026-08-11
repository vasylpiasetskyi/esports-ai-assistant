from collections.abc import Callable


class RateLimiter:
    def __init__(
        self,
        min_interval_seconds: float,
        clock: Callable[[], float],
        sleep_fn: Callable[[float], None],
    ) -> None:
        self._min_interval_seconds = min_interval_seconds
        self._clock = clock
        self._sleep_fn = sleep_fn
        self._last_request_at: float | None = None

    def wait(self) -> None:
        now = self._clock()
        if self._last_request_at is not None:
            elapsed = now - self._last_request_at
            remaining = self._min_interval_seconds - elapsed
            if remaining > 0:
                self._sleep_fn(remaining)
                now = self._clock()
        self._last_request_at = now
