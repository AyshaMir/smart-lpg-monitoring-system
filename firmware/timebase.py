"""Wrap-safe monotonic time helpers (MicroPython or desktop CPython)."""
try:
    import time as _time
    _ticks_ms = _time.ticks_ms
    _ticks_us = _time.ticks_us
    _ticks_diff = _time.ticks_diff
except AttributeError:
    import time as _time
    _ticks_ms = None
    _ticks_us = None
    _ticks_diff = None


def ticks_ms():
    if _ticks_ms is not None:
        return _ticks_ms()
    return int(_time.monotonic() * 1000)


def ticks_us():
    if _ticks_us is not None:
        return _ticks_us()
    return int(_time.monotonic() * 1000000)


def ticks_diff(new, old):
    if _ticks_diff is not None:
        return _ticks_diff(new, old)
    return new - old


def due(now, last, period):
    return ticks_diff(now, last) >= period
