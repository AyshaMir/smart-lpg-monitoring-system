
import network
import time

wifi = network.WLAN(network.STA_IF)
wifi.active(True)

wifi.connect("HU-Portal", "Habib786&*^")

for i in range(20):
    if wifi.isconnected():
        break
    time.sleep(1)

if wifi.isconnected():
    print("Wi-Fi connected!")
    print("Pico IP:", wifi.ifconfig()[0])
else:
    print("Connection failed")
