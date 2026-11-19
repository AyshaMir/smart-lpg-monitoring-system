
from machine import Pin, PWM
from time import sleep

green = Pin(13, Pin.OUT)
yellow = Pin(14, Pin.OUT)
red = Pin(15, Pin.OUT)

buzzer = PWM(Pin(16))
buzzer.freq(2000)
buzzer.duty_u16(0)

low_warning_given = False


def all_off():
    green.off()
    yellow.off()
    red.off()
    buzzer.duty_u16(0)


def beep(duration=0.2):
    buzzer.duty_u16(30000)
    sleep(duration)
    buzzer.duty_u16(0)


def check_status(gas_percent, leak):
    global low_warning_given

    print("LPG:", gas_percent, "% | Leak:", leak)

    all_off()

    # Highest priority: gas leak
    if leak:
        print("STATUS: GAS LEAK!")

        for i in range(5):
            red.on()
            beep(0.3)
            red.off()
            sleep(0.4)

    # Low LPG: 20% or below
    elif gas_percent <= 20:
        print("STATUS: LOW LPG")
        yellow.on()

        if not low_warning_given:
            beep(0.2)
            low_warning_given = True

        sleep(2)

    # Normal LPG
    else:
        print("STATUS: NORMAL")
        green.on()
        low_warning_given = False
        sleep(2)


tests = [
    (100, False),
    (50, False),
    (21, False),
    (20, False),
    (10, False),
    (80, True),
    (10, True),
    (15, False),
    (50, False)
]

try:
    print("Starting LPG warning tests...")

    for gas_percent, leak in tests:
        check_status(gas_percent, leak)
        sleep(1)

    print("All tests completed!")

except KeyboardInterrupt:
    print("Test interrupted.")

finally:
    all_off()
    buzzer.deinit()
