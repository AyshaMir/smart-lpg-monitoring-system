
import network
import socket
import json
import time

wifi = network.WLAN(network.STA_IF)

if not wifi.isconnected():
    print("Connect to Wi-Fi first!")
else:
    ip = wifi.ifconfig()[0]

    server = socket.socket()
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", 80))
    server.listen(1)

    print("Server running at http://" + ip)

    while True:
        client, address = server.accept()
        request = client.recv(1024)

        data = {
            "gas_kg": 2.4,
            "gas_percent": 80,
            "mq5": 12000,
            "leak": False,
            "days_left": 12
        }

        response = json.dumps(data)

        client.send(
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: application/json\r\n"
            "Access-Control-Allow-Origin: *\r\n"
            "Connection: close\r\n\r\n"
        )
        client.send(response)
        client.close()
