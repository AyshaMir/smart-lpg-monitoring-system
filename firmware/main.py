"""Smart LPG main loop

Do not run this entry point on desktop CPython.
"""
from timebase import ticks_ms, ticks_diff
from wifi import WiFiManager
from server import StatusServer
from sensors import SensorManager
from alerts import AlertController
from indicators import IndicatorController

try:
    from wificred import WIFI_SSID, WIFI_PASSWORD
except ImportError:
    raise RuntimeError("Create firmware/wificred.py from secrets.example.py")

SENSOR_PERIOD_MS = 200
INDICATOR_PERIOD_MS = 20
WIFI_PERIOD_MS = 1000
PRINT_PERIOD_MS = 1000


def main():
    indicators = IndicatorController()
    alerts = AlertController()
    sensors = SensorManager()
    wifi = WiFiManager(WIFI_SSID, WIFI_PASSWORD)
    server = None
    data = sensors.data
    now = ticks_ms()
    last_sensor = None
    last_indicator = None
    last_wifi = None
    last_print = None
    fresh_sample = False
    last_ip = None
    try:
        while True:
            now = ticks_ms()
            if last_sensor is None or ticks_diff(now, last_sensor) >= SENSOR_PERIOD_MS:
                last_sensor = now
                data = sensors.poll(now)
                fresh_sample = True

            if last_print is None or ticks_diff(now, last_print) >= PRINT_PERIOD_MS:
                last_print = now

                print("MQ-5 Voltage:", data["mq5_voltage"], "V")
                print("MQ-5 Status:", data["gas_status"])
                print("Leak Detected:", data["leak"])
                print("------------------------")

            if last_indicator is None or ticks_diff(now, last_indicator) >= INDICATOR_PERIOD_MS:
                last_indicator = now
                result = alerts.update(data["gas_percent"], data["leak"],
                                       now, fresh_sample=fresh_sample)
                fresh_sample = False
                indicators.update(result)
                data["alert_state"] = result["state"]

            if last_wifi is None or ticks_diff(now, last_wifi) >= WIFI_PERIOD_MS:
                last_wifi = now
                ip = wifi.update(now)
                if ip != last_ip:
                    print("Wi-Fi:", ip if ip else "disconnected")
                    last_ip = ip
                if ip and server is None:
                    try:
                        server = StatusServer()
                        print("API: http://" + ip + "/api/status")
                    except OSError as error:
                        print("Server init failed:", error)
                if not ip and server is not None:
                    server.close()
                    server = None

            if server is not None:
                server.poll(now, data)
    finally:
        indicators.close()
        if server is not None:
            server.close()


if __name__ == "__main__":
    main()
