"""Wi-Fi connection state machine; no blocking delay loops."""
import network
from timebase import ticks_diff


class WiFiManager:
    def __init__(self, ssid, password, retry_ms=10000, timeout_ms=10000):
        self.ssid = ssid
        self.password = password
        self.retry_ms = retry_ms
        self.timeout_ms = timeout_ms
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        self.started_at = None
        self.next_attempt_at = None

    def update(self, now_ms):
        """Call periodically (e.g., every 1000 ms)."""
        if self.wlan.isconnected():
            return self.wlan.ifconfig()[0]
        if self.started_at is not None:
            if ticks_diff(now_ms, self.started_at) < self.timeout_ms:
                return None
            try:
                self.wlan.disconnect()
            except OSError:
                pass
            self.started_at = None
            self.next_attempt_at = now_ms
            return None
        if (self.next_attempt_at is None or
                ticks_diff(now_ms, self.next_attempt_at) >= self.retry_ms):
            try:
                self.wlan.connect(self.ssid, self.password)
                self.started_at = now_ms
                self.next_attempt_at = now_ms
            except OSError as error:
                print("Wi-Fi connect error:", error)
                self.next_attempt_at = now_ms
        return None
