from machine import ADC, Pin
from time import sleep

# MQ-5 analog output connected to GP26
mq5 = ADC(Pin(26))

print("Starting MQ-5 sensor test...")

while True:
    # Read sensor value
    raw = mq5.read_u16()

    # Convert to Pico ADC input voltage
    voltage = (raw / 65535) * 3.3

    print("MQ-5 Raw:", raw, "| ADC Voltage:", round(voltage, 2), "V")

    sleep(1)