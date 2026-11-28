"""Pure, non-blocking alert state machine. No GPIO calls or sleeps."""
from timebase import ticks_diff

NORMAL = "NORMAL"
LOW_GAS = "LOW_GAS"
LEAK_DETECTED = "LEAK_DETECTED"
FAULT = "FAULT"


class AlertController:
    def __init__(self, clear_samples=3, beep_on_ms=250,
                 beep_period_ms=800, low_beep_ms=200):
        if clear_samples < 1 or beep_period_ms <= 0:
            raise ValueError("Invalid alarm timing")
        self.clear_samples = clear_samples
        self.beep_on_ms = beep_on_ms
        self.beep_period_ms = beep_period_ms
        self.low_beep_ms = low_beep_ms
        self.state = FAULT
        self._normal_samples = 0
        self._state_since = 0

    def update(self, gas_percent, leak_detected, now_ms, fresh_sample=True):
        """Update alarm state and return {state, led, buzzer_on}.

        Set fresh_sample=True ONLY when a new MQ-5 reading is available.
        Call again with False for fast buzzer updates. Missing/invalid readings
        are faults, except an existing leak remains latched until cleared.
        """
        valid_weight = (isinstance(gas_percent, (int, float))
                        and not isinstance(gas_percent, bool)
                        and 0 <= gas_percent <= 100)
        if leak_detected is True:
            self._normal_samples = 0
            desired = LEAK_DETECTED
        elif leak_detected is None and self.state == LEAK_DETECTED:
            self._normal_samples = 0
            desired = LEAK_DETECTED
        elif self.state == LEAK_DETECTED:
            if fresh_sample:
                self._normal_samples += 1
            if self._normal_samples < self.clear_samples:
                desired = LEAK_DETECTED
            else:
                self._normal_samples = 0
                if not valid_weight:
                    desired = FAULT
                else:
                    desired = LOW_GAS if gas_percent <= 20 else NORMAL

        elif leak_detected is None or not valid_weight:
            self._normal_samples = 0
            desired = FAULT

        else:
            self._normal_samples = 0
            desired = LOW_GAS if gas_percent <= 20 else NORMAL

        if desired != self.state:
            self.state = desired
            self._state_since = now_ms
        elapsed = max(0, ticks_diff(now_ms, self._state_since))
        if self.state == LEAK_DETECTED:
            led = "red"
            buzzer_on = (elapsed % self.beep_period_ms) < self.beep_on_ms
        elif self.state == LOW_GAS:
            led = "yellow"
            buzzer_on = elapsed < self.low_beep_ms
        elif self.state == NORMAL:
            led = "green"
            buzzer_on = False
        else:
            led = None
            buzzer_on = False
        return {"state": self.state, "led": led, "buzzer_on": buzzer_on}
