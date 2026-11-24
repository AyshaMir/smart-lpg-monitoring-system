"""HX711 reader. Never sleeps or waits for data-ready.

Reading the 25 clock pulses is inherently a short, timing-critical synchronous
transaction (a few hundred microseconds). Do not call it from an IRQ callback.
"""
from machine import Pin
from timebase import ticks_us, ticks_diff


def _pulse_spacing_us(minimum_us=2):
    # Only a *microsecond* spin for HX711 electrical pulse timing, not
    # application-level waiting. No sleep()/sleep_us().
    start = ticks_us()
    while ticks_diff(ticks_us(), start) < minimum_us:
        pass


class HX711:
    def __init__(self, dt_pin=18, sck_pin=19):
        self.dt = Pin(dt_pin, Pin.IN)
        self.sck = Pin(sck_pin, Pin.OUT, value=0)

    def ready(self):
        return self.dt.value() == 0

    def read_raw(self):
        if not self.ready():
            return None
        value = 0
        for _ in range(24):
            self.sck.on()
            _pulse_spacing_us()
            value = (value << 1) | self.dt.value()
            self.sck.off()
            _pulse_spacing_us()
        self.sck.on()  # 25th pulse = channel A, gain 128
        _pulse_spacing_us()
        self.sck.off()
        if value & 0x800000:
            value -= 0x1000000
        return value
