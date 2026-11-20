
from machine import Pin
from time import sleep_us, ticks_us, ticks_diff

class HX711:
    def __init__(self, dt_pin=18, sck_pin=19):
        self.dt = Pin(dt_pin, Pin.IN)
        self.sck = Pin(sck_pin, Pin.OUT, value=0)

    def read_raw(self):
        start = ticks_us()

        while self.dt.value() == 1:
            if ticks_diff(ticks_us(), start) > 1000000:
                raise OSError("HX711 timeout")

        value = 0

        for i in range(24):
            self.sck.on()
            sleep_us(1)

            value = (value << 1) | self.dt.value()

            self.sck.off()
            sleep_us(1)

        self.sck.on()
        sleep_us(1)
        self.sck.off()

        if value & 0x800000:
            value -= 0x1000000

        return value
