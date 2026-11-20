
import socket
import json
from sensors import get_sensor_data

def start_server():
    address = socket.getaddrinfo("0.0.0.0", 80)[0][-1]

    server = socket.socket()
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(address)
    server.listen(2)

    print("HTTP server running on port 80")

    while True:
        client, addr = server.accept()

        try:
            request = client.recv(1024).decode()
            parts = request.split()
            if len(parts) < 2:
                continue
            path = parts[1].split("?")[0]

            if path == "/api/status":
                data = get_sensor_data()
                body = json.dumps(data)
                status = "200 OK"
            else:
                body = json.dumps({
                    "message": "Smart LPG Monitoring API",
                    "endpoint": "/api/status"
                })
                status = "200 OK"

            response = (
                "HTTP/1.1 " + status + "\r\n"
                "Content-Type: application/json\r\n"
                "Access-Control-Allow-Origin: *\r\n"
                "Connection: close\r\n"
                "\r\n" + body
            )

            client.sendall(response.encode())

        except Exception as e:
            print("Server error:", e)

        finally:
            client.close()
