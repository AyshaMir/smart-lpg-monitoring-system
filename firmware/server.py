"""Short, bounded, non-blocking HTTP /api/status server.

This serves JSON for a separately hosted dashboard. Accept/recv/send are
non-blocking. Tiny HTTP client state; suitable for prototype LAN use only.
"""
import socket
import json
from timebase import ticks_diff


class StatusServer:
    def __init__(self, port=80):
        self.listener = socket.socket()
        self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener.bind(("0.0.0.0", port))
        self.listener.listen(2)
        self.listener.setblocking(False)
        self.client = None
        self.inbuf = b""
        self.outbuf = b""
        self.connected_at = None
        print("HTTP API listening on port", port)

    def _close_client(self):
        if self.client is not None:
            try:
                self.client.close()
            except OSError:
                pass
        self.client = None
        self.inbuf = b""
        self.outbuf = b""
        self.connected_at = None

    def _response(self, data, request):
        path = request.split(b" ", 2)[1].split(b"?", 1)[0]
        payload = data if path == b"/api/status" else {
            "message": "Smart LPG Monitoring API", "endpoint": "/api/status"
        }
        body = json.dumps(payload).encode()
        header = (b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n"
                  b"Access-Control-Allow-Origin: *\r\nConnection: close\r\n"
                  b"Cache-Control: no-store\r\nContent-Length: " +
                  str(len(body)).encode() + b"\r\n\r\n")
        return header + body

    def poll(self, now_ms, data):
        """Perform at most one small receive/send operation per invocation."""
        if self.client is None:
            try:
                self.client, _ = self.listener.accept()
                self.client.setblocking(False)
                self.connected_at = now_ms
            except OSError:
                return
        if (self.connected_at is not None and
                ticks_diff(now_ms, self.connected_at) > 2000):
            self._close_client()
            return
        try:
            if not self.outbuf:
                try:
                    chunk = self.client.recv(1024)
                except OSError:
                    return
                if not chunk:
                    self._close_client()
                    return
                self.inbuf += chunk
                if len(self.inbuf) > 2048:
                    self._close_client()
                    return
                if b"\r\n" in self.inbuf:
                    request = self.inbuf.split(b"\r\n", 1)[0]
                    if len(request.split(b" ")) < 2:
                        self._close_client()
                        return
                    self.outbuf = self._response(data, request)
            if self.outbuf:
                try:
                    sent = self.client.send(self.outbuf)
                except OSError:
                    return
                if sent is None or sent <= 0:
                    return
                self.outbuf = self.outbuf[sent:]
                if not self.outbuf:
                    self._close_client()
        except Exception as error:
            print("HTTP client error:", error)
            self._close_client()

    def close(self):
        self._close_client()
        self.listener.close()
