"""STEP 2 - get TARE_RAW and COUNTS_PER_KG. Run after loadcell_check.py says GOOD.

Needs one object of known weight (e.g. a 1 kg water bottle - weigh it on a
kitchen scale first). Put the platform/bucket on the cell BEFORE starting if
it will always be there; it gets zeroed out as part of the tare.
Nothing here needs typing - it just gives you time to do each step.
"""
from time import sleep
from hx711 import HX711

DT_PIN = 18
SCK_PIN = 19
KNOWN_WEIGHT_KG = 1.545   # <-- change to the real weight you will use

hx = HX711(DT_PIN, SCK_PIN)


def countdown(msg, seconds):
    print(msg)
    for s in range(seconds, 0, -1):
        print("  %d..." % s)
        sleep(1)


countdown("1) Empty platform only. Don't touch. Measuring tare in", 5)
tare = hx.read_avg(30)
print("   tare =", tare)

countdown("2) Put the %.3f kg weight on now. Measuring in" % KNOWN_WEIGHT_KG, 10)
loaded = hx.read_avg(30)
print("   loaded =", loaded)

if tare is None or loaded is None or loaded == tare:
    raise SystemExit("Calibration failed - run loadcell_check.py again.")

counts_per_kg = (loaded - tare) / KNOWN_WEIGHT_KG

countdown("3) Take the weight off, then check zero in", 5)
zero_check = hx.read_avg(30)
if zero_check is None:
    raise SystemExit("No reading after removing the weight - check wiring.")
print("   weight after removing = %.3f kg (should be ~0)" % ((zero_check - tare) / counts_per_kg))
print("\nPaste these into firmware/sensors.py:")
print("TARE_RAW = %d" % round(tare))
print("COUNTS_PER_KG = %.1f" % counts_per_kg)
print("(EMPTY_CYLINDER_KG = weight of the empty cylinder/bucket you set up)")

print("\nLive weight (Ctrl+C to stop):")
while True:
    r = hx.read_raw()
    if r is not None:
        print("%.3f kg" % ((r - tare) / counts_per_kg))
    sleep(0.5)