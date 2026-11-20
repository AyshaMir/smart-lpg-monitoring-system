
from machine import ADC, Pin

mq5 = ADC(Pin(26))

# Provisional demonstration thresholds
WARNING_VOLTAGE = 2.40
HIGH_VOLTAGE = 2.60

def get_sensor_data():
    raw = mq5.read_u16()
    voltage = (raw / 65535) * 3.3

    if voltage >= HIGH_VOLTAGE:
        gas_status = "HIGH_RESPONSE"
    elif voltage >= WARNING_VOLTAGE:
        gas_status = "POSSIBLE_GAS"
    else:
        gas_status = "BASELINE"

    return {
        "weight_raw": None,
        "gas_kg": None,
        "gas_percent": None,
        "mq5_raw": raw,
        "mq5_voltage": round(voltage, 2),
        "gas_status": gas_status,
        "leak": None,
        "low_gas": None,
        "days_left": None
    }
