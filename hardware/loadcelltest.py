
from machine import Pin
from time import sleep, sleep_us, ticks_us, ticks_diff

dt = Pin(27, Pin.IN)
sck = Pin(26, Pin.OUT, value=0)


def read_hx711():
    start = ticks_us()

    # Wait until HX711 has data ready
    while dt.value() == 1:
        if ticks_diff(ticks_us(), start) > 1000000:
            raise OSError("HX711 not responding")

    value = 0

    # Read 24 bits
    for i in range(24):
        sck.on()
        sleep_us(1)

        value = (value << 1) | dt.value()

        sck.off()
        sleep_us(1)

    # 25th pulse selects channel A, gain 128
    sck.on()
    sleep_us(1)
    sck.off()

    # Convert signed 24-bit reading
    if value & 0x800000:
        value -= 0x1000000

    return value


print("Starting HX711 raw reading test...")

while True:
    try:
        reading = read_hx711()
        print("Raw reading:", reading)
    except OSError as error:
        print(error)

    sleep(0.5)
