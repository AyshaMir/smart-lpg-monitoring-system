"""Non-blocking sensor polling; calibration is intentionally not fabricated."""
from machine import ADC, Pin
from timebase import ticks_ms, ticks_diff
from hx711 import HX711

MQ5_PIN = 26
HX711_DT_PIN = 18  # PROVISIONAL: verify in lab
HX711_SCK_PIN = 19  # PROVISIONAL: verify in lab
WARNING_VOLTAGE = 2.40  # Provisional CSV-derived threshold, not a certified limit
HIGH_VOLTAGE = 2.60     # Provisional higher-response band
SENSOR_STALE_MS = 2500

# Enter measured calibration values after next lab; otherwise weight remains None.
TARE_RAW = None
COUNTS_PER_KG = None
EMPTY_CYLINDER_KG = None
LPG_CAPACITY_KG = 3.0  # Existing dashboard assumption; verify in lab


class SensorManager:
    def __init__(self):
        self.mq5 = ADC(Pin(MQ5_PIN))
        self.hx711 = HX711(HX711_DT_PIN, HX711_SCK_PIN)
        self._last_hx_ms = None
        self.data = {
            "weight_raw": None, "gas_kg": None, "gas_percent": None,
            "mq5_raw": None, "mq5_voltage": None, "gas_status": "UNAVAILABLE",
            "leak": None, "low_gas": None, "days_left": None
        }

    def poll(self, now_ms):
        """Read MQ-5 and HX711 if ready; return snapshot. Never sleep."""
        try:
            raw = self.mq5.read_u16()
            voltage = raw * 3.3 / 65535
            status = ("HIGH_RESPONSE" if voltage >= HIGH_VOLTAGE else
                      "POSSIBLE_GAS" if voltage >= WARNING_VOLTAGE else "BASELINE")
            self.data["mq5_raw"] = raw
            self.data["mq5_voltage"] = round(voltage, 2)
            self.data["gas_status"] = status
            self.data["leak"] = status != "BASELINE"
        except Exception as error:
            print("MQ-5 read failed:", error)
            self.data["mq5_raw"] = None
            self.data["mq5_voltage"] = None
            self.data["gas_status"] = "UNAVAILABLE"
            self.data["leak"] = None

        try:
            raw_weight = self.hx711.read_raw()
            if raw_weight is not None:
                self._last_hx_ms = now_ms
                self.data["weight_raw"] = raw_weight
                if (TARE_RAW is not None and COUNTS_PER_KG not in (None, 0)
                        and EMPTY_CYLINDER_KG is not None
                        and LPG_CAPACITY_KG > 0):
                    total_kg = (raw_weight - TARE_RAW) / COUNTS_PER_KG
                    gas_kg = max(0, min(LPG_CAPACITY_KG,
                                        total_kg - EMPTY_CYLINDER_KG))
                    self.data["gas_kg"] = round(gas_kg, 2)
                    self.data["gas_percent"] = round(100 * gas_kg / LPG_CAPACITY_KG, 1)
                else:
                    self.data["gas_kg"] = None
                    self.data["gas_percent"] = None
            if (self._last_hx_ms is None or
                    ticks_diff(now_ms, self._last_hx_ms) > SENSOR_STALE_MS):
                self.data["weight_raw"] = None
                self.data["gas_kg"] = None
                self.data["gas_percent"] = None
        except Exception as error:
            print("HX711 read failed:", error)
            self.data["weight_raw"] = None
            self.data["gas_kg"] = None
            self.data["gas_percent"] = None
        pct = self.data["gas_percent"]
        self.data["low_gas"] = pct <= 20 if pct is not None else None
        return self.data


def get_sensor_data():
    """Legacy one-shot diagnostic; creates an instance each call."""
    return SensorManager().poll(ticks_ms())
