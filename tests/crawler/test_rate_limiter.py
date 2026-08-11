from crawler.liquipedia.rate_limiter import RateLimiter


class FakeClock:
    def __init__(self, start: float = 0.0) -> None:
        self.time = start

    def __call__(self) -> float:
        return self.time


def test_first_call_does_not_sleep():
    clock = FakeClock(start=100.0)
    sleep_calls: list[float] = []
    limiter = RateLimiter(min_interval_seconds=2.0, clock=clock, sleep_fn=sleep_calls.append)

    limiter.wait()

    assert sleep_calls == []


def test_second_call_too_soon_sleeps_remaining_time():
    clock = FakeClock(start=100.0)
    sleep_calls: list[float] = []

    def fake_sleep(seconds: float) -> None:
        sleep_calls.append(seconds)
        clock.time += seconds

    limiter = RateLimiter(min_interval_seconds=2.0, clock=clock, sleep_fn=fake_sleep)

    limiter.wait()
    clock.time += 0.5
    limiter.wait()

    assert sleep_calls == [1.5]


def test_second_call_after_interval_does_not_sleep():
    clock = FakeClock(start=100.0)
    sleep_calls: list[float] = []
    limiter = RateLimiter(min_interval_seconds=2.0, clock=clock, sleep_fn=sleep_calls.append)

    limiter.wait()
    clock.time += 3.0
    limiter.wait()

    assert sleep_calls == []
