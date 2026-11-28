"""Timing helpers for MicroPython and desktop Python."""
import time

_ticks_ms = getattr(time, "ticks_ms", None)
_ticks_us = getattr(time, "ticks_us", None)
_ticks_diff = getattr(time, "ticks_diff", None)


def ticks_ms():
    if _ticks_ms is not None:
        return _ticks_ms()
    return int(getattr(time, "monotonic")() * 1000)


def ticks_us():
    if _ticks_us is not None:
        return _ticks_us()
    return int(getattr(time, "monotonic")() * 1000000)


def ticks_diff(new, old):
    if _ticks_diff is not None:
        return _ticks_diff(new, old)
    return new - old


def due(now, last, period):
    return ticks_diff(now, last) >= period