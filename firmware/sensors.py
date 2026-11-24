
"""Non-blocking sensor polling; calibration is intentionally not fabricated."""

from machine import ADC, Pin
from timebase import ticks_ms, ticks_diff
from hx711 import HX711

# GPIO pin assignments
MQ5_PIN = 26
HX711_DT_PIN = 18
HX711_SCK_PIN = 19

# Single MQ-5 leak threshold
LEAK_THRESHOLD_VOLTAGE = 2.50

SENSOR_STALE_MS = 2500

# Enter measured calibration values after calibration.
TARE_RAW = None
COUNTS_PER_KG = None
EMPTY_CYLINDER_KG = None

# Simulated LPG capacity for the water-bucket experiment.
LPG_CAPACITY_KG = 3.0


class SensorManager:
    def __init__(self):
        self.mq5 = ADC(Pin(MQ5_PIN))
        self.hx711 = HX711(HX711_DT_PIN, HX711_SCK_PIN)

        self._last_hx_ms = None

        self.data = {
            "weight_raw": None,
            "gas_kg": None,
            "gas_percent": None,
            "mq5_raw": None,
            "mq5_voltage": None,
            "gas_status": "UNAVAILABLE",
            "leak": None,
            "low_gas": None,
            "days_left": None
        }

    def poll(self, now_ms):
        """Read available sensor data without application-level sleep."""

        # ==================================
        # MQ-5 GAS SENSOR
        # ==================================

        try:
            raw = self.mq5.read_u16()

            voltage = (raw / 65535) * 3.3

            # One threshold for suspected leakage.
            if voltage >= LEAK_THRESHOLD_VOLTAGE:
                gas_status = "POSSIBLE_GAS"
                leak_detected = True
            else:
                gas_status = "BASELINE"
                leak_detected = False

            self.data["mq5_raw"] = raw
            self.data["mq5_voltage"] = round(voltage, 2)
            self.data["gas_status"] = gas_status
            self.data["leak"] = leak_detected

        except Exception as error:
            print("MQ-5 read failed:", error)

            self.data["mq5_raw"] = None
            self.data["mq5_voltage"] = None
            self.data["gas_status"] = "UNAVAILABLE"
            self.data["leak"] = None

        # ==================================
        # HX711 LOAD CELL
        # ==================================

        try:
            raw_weight = self.hx711.read_raw()

            if raw_weight is not None:
                self._last_hx_ms = now_ms
                self.data["weight_raw"] = raw_weight

                # Only calculate weight when calibrated.
                if (
                    TARE_RAW is not None
                    and COUNTS_PER_KG not in (None, 0)
                    and EMPTY_CYLINDER_KG is not None
                    and LPG_CAPACITY_KG > 0
                ):
                    total_kg = (
                        raw_weight - TARE_RAW
                    ) / COUNTS_PER_KG

                    gas_kg = max(
                        0,
                        min(
                            LPG_CAPACITY_KG,
                            total_kg - EMPTY_CYLINDER_KG
                        )
                    )

                    self.data["gas_kg"] = round(
                        gas_kg, 2
                    )

                    self.data["gas_percent"] = round(
                        (gas_kg / LPG_CAPACITY_KG) * 100,
                        1
                    )

                else:
                    # Weight calibration is still pending.
                    self.data["gas_kg"] = None
                    self.data["gas_percent"] = None

            # Check whether the HX711 data is too old.
            if (
                self._last_hx_ms is None
                or ticks_diff(
                    now_ms,
                    self._last_hx_ms
                ) > SENSOR_STALE_MS
            ):
                self.data["weight_raw"] = None
                self.data["gas_kg"] = None
                self.data["gas_percent"] = None

        except Exception as error:
            print("HX711 read failed:", error)

            self.data["weight_raw"] = None
            self.data["gas_kg"] = None
            self.data["gas_percent"] = None

        # ==================================
        # LOW LPG DETECTION
        # ==================================

        gas_percent = self.data["gas_percent"]

        if gas_percent is not None:
            self.data["low_gas"] = gas_percent <= 20
        else:
            self.data["low_gas"] = None

        return self.data


def get_sensor_data():
    """Legacy one-shot diagnostic."""
    return SensorManager().poll(ticks_ms())
