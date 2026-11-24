"""Timer-based sensor diagnostic; run on Pico, stop with Ctrl+C."""
from timebase import ticks_ms, ticks_diff
from sensors import SensorManager

manager = SensorManager()
last = ticks_ms() - 500
while True:
    now = ticks_ms()
    if ticks_diff(now, last) >= 500:
        last = now
        print(manager.poll(now))
