
"""Hardware-independent alert decisions for the Smart LPG system.

Call update() regularly with validated sensor readings and a
monotonic millisecond timestamp (time.ticks_ms() on the Pico).

This module does not control GPIO pins or use blocking sleep().
"""

# Compatible with both MicroPython and desktop Python.
try:
    from time import ticks_diff as _micro_ticks_diff
except ImportError:
    _micro_ticks_diff = None

def elapsed_ms(new, old):
    if _micro_ticks_diff is not None:
        return _micro_ticks_diff(new, old)
    return new - old


NORMAL = "NORMAL"
LOW_GAS = "LOW_GAS"
LEAK_DETECTED = "LEAK_DETECTED"
FAULT = "FAULT"


class AlertController:

    def __init__(
        self,
        clear_samples=3,
        beep_on_ms=250,
        beep_period_ms=800,
        low_beep_ms=200
    ):
        self.clear_samples = clear_samples
        self.beep_on_ms = beep_on_ms
        self.beep_period_ms = beep_period_ms
        self.low_beep_ms = low_beep_ms

        self.state = FAULT
        self._normal_samples = 0
        self._state_since = 0

    def update(self, gas_percent, leak_detected, now_ms):
        """Calculate LED and buzzer outputs without blocking.

        gas_percent:
            0 to 100, or None if unavailable.

        leak_detected:
            True  = suspected leakage
            False = normal gas sensor reading
            None  = gas sensor unavailable

        now_ms:
            Monotonic timestamp in milliseconds.

        Returns:
            {
                "state": str,
                "led": str or None,
                "buzzer_on": bool
            }
        """

        valid_weight = (
            isinstance(gas_percent, (int, float))
            and not isinstance(gas_percent, bool)
            and 0 <= gas_percent <= 100
        )

        # Priority 1: Suspected leakage.
        if leak_detected is True:
            self._normal_samples = 0
            desired = LEAK_DETECTED

        # Never clear an active leak alarm when the MQ-5
        # suddenly stops providing readings.
        elif leak_detected is None and self.state == LEAK_DETECTED:
            self._normal_samples = 0
            desired = LEAK_DETECTED

        # Priority 2: Sensor fault.
        elif leak_detected is None or not valid_weight:
            self._normal_samples = 0
            desired = FAULT

        # Leak recovery requires consecutive normal readings.
        elif self.state == LEAK_DETECTED:
            self._normal_samples += 1

            if self._normal_samples < self.clear_samples:
                desired = LEAK_DETECTED
            else:
                desired = (
                    LOW_GAS if gas_percent <= 20 else NORMAL
                )

        # Priority 3: Cylinder weight status.
        else:
            self._normal_samples = 0

            desired = (
                LOW_GAS if gas_percent <= 20 else NORMAL
            )

        # Record when the alert state changes.
        if desired != self.state:
            self.state = desired
            self._state_since = now_ms

        elapsed = max(
            0,
            elapsed_ms(now_ms, self._state_since)
        )

        # Determine LED and buzzer output.
        if self.state == LEAK_DETECTED:
            led = "red"
            buzzer_on = (
                elapsed % self.beep_period_ms
            ) < self.beep_on_ms

        elif self.state == LOW_GAS:
            led = "yellow"
            buzzer_on = elapsed < self.low_beep_ms

        elif self.state == NORMAL:
            led = "green"
            buzzer_on = False

        else:
            # Agreed fault state: all indicators OFF.
            led = None
            buzzer_on = False

        return {
            "state": self.state,
            "led": led,
            "buzzer_on": buzzer_on
        }
