"""Minimal HX711 driver (bit-bang, channel A, gain 128) for Pico / Pico 2 W.

Used only by the scripts in this folder. Plain and boring on purpose.
"""
from machine import Pin, disable_irq, enable_irq
from time import sleep_ms, sleep_us, ticks_ms, ticks_diff


class HX711:
    def __init__(self, dt_pin, sck_pin):
        self.dt = Pin(dt_pin, Pin.IN)
        self.sck = Pin(sck_pin, Pin.OUT, value=0)
        self.reset()

    def reset(self):
        # SCK high for >60 us powers the chip down, low again wakes it up.
        self.sck.value(1)
        sleep_us(100)
        self.sck.value(0)
        sleep_ms(500)  # first reading after wake-up takes a while

    def is_ready(self):
        return self.dt.value() == 0

    def read_raw(self, timeout_ms=1000):
        """Return one signed 24-bit reading, or None if the chip never got ready."""
        start = ticks_ms()
        while not self.is_ready():
            if ticks_diff(ticks_ms(), start) > timeout_ms:
                return None
            sleep_ms(1)

        value = 0
        irq = disable_irq()  # keep SCK high-time well under 60 us
        try:
            for _ in range(24):
                self.sck.value(1)
                value = (value << 1) | self.dt.value()
                self.sck.value(0)
            # 25th pulse -> next conversion uses channel A, gain 128
            self.sck.value(1)
            self.sck.value(0)
        finally:
            enable_irq(irq)

        if value & 0x800000:
            value -= 0x1000000
        return value

    def read_avg(self, n=10):
        """Average of n good readings, or None if none worked."""
        total = 0
        good = 0
        for _ in range(n):
            r = self.read_raw()
            if r is not None:
                total += r
                good += 1
        if good == 0:
            raise OSError("HX711: no good readings")
        return total / good