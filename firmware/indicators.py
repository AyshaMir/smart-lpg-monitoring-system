"""Apply alert decisions to LEDs and shared buzzer without sleeping."""
class IndicatorController:
    def __init__(self, green_pin=13, yellow_pin=14, red_pin=12,
                 buzzer_pin=16, green=None, yellow=None, red=None, buzzer=None):
        if green is None and yellow is None and red is None and buzzer is None:
            from machine import Pin, PWM
            self.green = Pin(green_pin, Pin.OUT, value=0)
            self.yellow = Pin(yellow_pin, Pin.OUT, value=0)
            self.red = Pin(red_pin, Pin.OUT, value=0)
            physical_buzzer = PWM(Pin(buzzer_pin))
            physical_buzzer.freq(2000)
            self.buzzer = physical_buzzer
        elif (green is not None and yellow is not None
              and red is not None and buzzer is not None):
            assert green is not None and yellow is not None
            assert red is not None and buzzer is not None
            self.green = green
            self.yellow = yellow
            self.red = red
            self.buzzer = buzzer
        else:
            raise ValueError("Provide either all four simulated devices or none")
        self.current_led = None
        self.buzzer_active = False
        self.all_off()

    def all_off(self):
        self.green.off()
        self.yellow.off()
        self.red.off()
        self.buzzer.duty_u16(0)
        self.current_led = None
        self.buzzer_active = False

    def update(self, alert):
        led = alert["led"]
        buzzer_on = bool(alert["buzzer_on"])
        if led not in ("green", "yellow", "red", None):
            raise ValueError("Invalid LED selection")
        if led != self.current_led:
            self.green.value(1 if led == "green" else 0)
            self.yellow.value(1 if led == "yellow" else 0)
            self.red.value(1 if led == "red" else 0)
            self.current_led = led
        if buzzer_on != self.buzzer_active:
            self.buzzer.duty_u16(30000 if buzzer_on else 0)
            self.buzzer_active = buzzer_on

    def close(self):
        self.all_off()
        self.buzzer.deinit()
