"""Pairing test: gives ONE clear result per wiring. Run it once per wiring.

Uses the 1.545 kg bottle (set BOTTLE_KG). Follow the countdowns:
  1) hands OFF everything -> measures rest value and how much it wanders
  2) put the bottle in the CENTRE of the plate, hands OFF -> measures again
Then compare the 'change' number across the three wirings. The right wiring
gives a much bigger change (and a bigger change-to-noise ratio).
"""
from time import sleep
from hx711 import HX711

DT_PIN = 18
SCK_PIN = 19
BOTTLE_KG = 1.545

hx = HX711(DT_PIN, SCK_PIN)


def countdown(msg, seconds):
    print(msg)
    for s in range(seconds, 0, -1):
        print("  %d..." % s)
        sleep(1)


def measure(n):
    vals = []
    for _ in range(n):
        r = hx.read_raw()
        if r is not None:
            vals.append(r)
    if not vals:
        raise SystemExit("No readings - check wiring.")
    return sum(vals) / len(vals), max(vals) - min(vals)


countdown("1) Empty platform, hands OFF. Measuring rest in", 5)
rest, rest_spread = measure(30)
print("   rest =", int(rest), " wander (max-min) =", rest_spread)

countdown("2) Put the bottle on the centre, hands OFF. Measuring in", 10)
loaded, loaded_spread = measure(30)
print("   loaded =", int(loaded), " wander (max-min) =", loaded_spread)

change = loaded - rest
noise = max(rest_spread, loaded_spread, 1)
print("\n==== RESULT ====")
print("change with bottle:", int(change), "counts")
print("counts per kg:", int(change / BOTTLE_KG))
print("change / wander:", round(abs(change) / noise, 1), "(want 20+)")
if abs(change) < 3 * noise:
    print("Verdict: bottle is lost in the noise - NOT usable.")
elif abs(change) / BOTTLE_KG < 50000:
    print("Verdict: responds, but sensitivity is low - probably not the best wiring.")
else:
    print("Verdict: GOOD - strong, clear response.")