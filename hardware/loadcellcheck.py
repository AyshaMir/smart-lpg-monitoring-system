"""Live readout. Prints how far the reading moved from the starting value.

Start it with nothing touching the cell, then press / release and watch 'change'.
A working 10 kg cell moves by hundreds of thousands of counts with ~1 kg.
Ctrl+C to stop.
"""
from time import sleep_ms
from hx711 import HX711

DT_PIN = 18
SCK_PIN = 19

hx = HX711(DT_PIN, SCK_PIN)
base = hx.read_avg(10)
print("start value:", base)

while True:
    r = hx.read_raw()
    if r is None:
        print("no response")
    else:
        print("raw %9d   change %9d" % (r, r - base))
    sleep_ms(200)