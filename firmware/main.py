
from wifi import connect_wifi
from server import start_server

WIFI_SSID = "HU-Portal"
WIFI_PASSWORD = "Habib786&*^"

def main():
    print("Smart LPG Monitoring System")

    ip = connect_wifi(WIFI_SSID, WIFI_PASSWORD)

    if ip:
        print("API: http://" + ip + "/api/status")
        start_server()
    else:
        print("Server not started: Wi-Fi unavailable")

main()
