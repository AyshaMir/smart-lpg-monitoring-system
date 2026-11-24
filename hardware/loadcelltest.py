"""HX711 raw diagnostic using timer-paced polling, not sleep().

Pins 27/26 reflect OLD separate test wiring and CONFLICT with MQ-5 GP26.
Verify wiring before running simultaneously with MQ-5 or main firmware.
"""
from machine import Pin
from time import ticks_ms, ticks_us, ticks_diff

DT_PIN = 27
SCK_PIN = 26

dt = Pin(DT_PIN, Pin.IN)
sck = Pin(SCK_PIN, Pin.OUT, value=0)


def pulse_wait():
    start = ticks_us()
    while ticks_diff(ticks_us(), start) < 2:
        pass  # HX711 timing-critical, approximately 2 us


def read_raw_if_ready():
    if dt.value() != 0:
        return None
    value = 0
    for _ in range(24):
        sck.on()
        pulse_wait()
        value = (value << 1) | dt.value()
        sck.off()
        pulse_wait()
    sck.on()
    pulse_wait()
    sck.off()
    if value & 0x800000:
        value -= 0x1000000
    return value


last = ticks_ms() - 500
print("Starting HX711 raw reading test...")
while True:
    now = ticks_ms()
    if ticks_diff(now, last) >= 500:
        last = now
        reading = read_raw_if_ready()
        print("Raw reading:", reading if reading is not None else "not ready")
