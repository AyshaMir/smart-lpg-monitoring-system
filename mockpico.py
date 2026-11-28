
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import json
import time

PORT = 8000
START_TIME = time.time()

class MockPicoHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path != "/api/status":
            self.send_error(404, "Not found")
            return

        params = parse_qs(parsed.query)
        mode = params.get("mode", ["normal"])[0].lower()

        # Simulate 0.01 kg consumed every second.
        elapsed = time.time() - START_TIME
        weight = max(0.3, round(2.4 - elapsed * 0.01, 2))
        voltage = 1.2
        leak = False

        if mode == "leak":
            voltage = 2.7
            leak = True

        elif mode == "low":
            weight = 0.6

        elif mode == "fault":
            data = {
                "gas_kg": None,
                "gas_percent": None,
                "mq5_voltage": None,
                "gas_status": "UNAVAILABLE",
                "leak": None,
                "alert_state": "FAULT",
                "days_left": None
            }
            self.respond(data)
            return

        percent = round(weight / 3.0 * 100, 1)

        if leak:
            state = "LEAK_DETECTED"
        elif percent <= 20:
            state = "LOW_GAS"
        else:
            state = "NORMAL"

        data = {
            "gas_kg": weight,
            "gas_percent": percent,
            "mq5_voltage": voltage,
            "gas_status": "POSSIBLE_GAS" if leak else "BASELINE",
            "leak": leak,
            "low_gas": percent <= 20,
            "alert_state": state,
            "days_left": None
        }

        self.respond(data)
    def respond(self, data):
        data["simulated"] = True
        payload = json.dumps(data).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()

        self.wfile.write(payload)


if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", PORT), MockPicoHandler)

    print("Mock Pico running!")
    print(f"API: http://127.0.0.1:{PORT}/api/status")
    print("Press Ctrl+C to stop.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
        print("\nServer stopped.")
