"""MQ-5 periodic diagnostic. Run on Pico; no sleep()."""
from machine import ADC, Pin
from time import ticks_ms, ticks_diff

mq5 = ADC(Pin(26))
last = ticks_ms() - 1000
print("Starting MQ-5 sensor test...")
while True:
    now = ticks_ms()
    if ticks_diff(now, last) >= 1000:
        last = now
        raw = mq5.read_u16()
        print("MQ-5 Raw:", raw, "| ADC Voltage:", round(raw * 3.3 / 65535, 2), "V")
