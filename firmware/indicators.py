
"""Non-blocking LED and buzzer controller for Smart LPG.

Receives alert decisions from alerts.py.
No sleep() calls.

GPIO assignments are provisional until lab verification.
"""

from typing import Protocol


class LEDDevice(Protocol):
    def off(self) -> None: ...
    def value(self, new_value: int, /) -> None: ...


class BuzzerDevice(Protocol):
    def duty_u16(self, value: int, /) -> None: ...
    def deinit(self) -> None: ...


class IndicatorController:

    def __init__(
        self,
        green_pin=13,
        yellow_pin=14,
        red_pin=15,
        buzzer_pin=16,
        green: LEDDevice | None = None,
        yellow: LEDDevice | None = None,
        red: LEDDevice | None = None,
        buzzer: BuzzerDevice | None = None
    ):
        provided = (green, yellow, red, buzzer)

        if all(device is None for device in provided):
            # Real Pico hardware
            from machine import Pin, PWM

            self.green: LEDDevice = Pin(
                green_pin, Pin.OUT, value=0
            )
            self.yellow: LEDDevice = Pin(
                yellow_pin, Pin.OUT, value=0
            )
            self.red: LEDDevice = Pin(
                red_pin, Pin.OUT, value=0
            )

            physical_buzzer = PWM(Pin(buzzer_pin))
            physical_buzzer.freq(2000)
            self.buzzer: BuzzerDevice = physical_buzzer

        elif (
            green is not None
            and yellow is not None
            and red is not None
            and buzzer is not None
        ):
            # Simulated devices for desktop testing
            self.green = green
            self.yellow = yellow
            self.red = red
            self.buzzer = buzzer

        else:
            raise ValueError(
                "Provide all four simulated devices or none."
            )

        self.current_led = None
        self.buzzer_active = False
        self.all_off()

    def all_off(self):
        """Turn off all LEDs and the buzzer."""

        self.green.off()
        self.yellow.off()
        self.red.off()
        self.buzzer.duty_u16(0)

        self.current_led = None
        self.buzzer_active = False

    def update(self, alert):
        """Apply decisions from AlertController.update()."""

        led = alert["led"]
        buzzer_on = alert["buzzer_on"]

        if led not in ("green", "yellow", "red", None):
            raise ValueError("Invalid LED selection")

        if led != self.current_led:
            self.green.value(1 if led == "green" else 0)
            self.yellow.value(1 if led == "yellow" else 0)
            self.red.value(1 if led == "red" else 0)
            self.current_led = led

        if buzzer_on != self.buzzer_active:
            self.buzzer.duty_u16(
                30000 if buzzer_on else 0
            )
            self.buzzer_active = buzzer_on

    def close(self):
        """Turn off and release the hardware."""

        self.all_off()
        self.buzzer.deinit()
