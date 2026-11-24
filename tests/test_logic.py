"""Desktop-only regression tests. From tests/: python test_logic.py"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "firmware"))
from alerts import AlertController, NORMAL, LOW_GAS, LEAK_DETECTED, FAULT
from indicators import IndicatorController


class LED:
    def __init__(self):
        self.v = 0
    def value(self, x):
        self.v = x
    def off(self):
        self.v = 0


class Buzz:
    def __init__(self):
        self.v = 0
    def duty_u16(self, x):
        self.v = x
    def deinit(self):
        pass


a = AlertController()
leds = [LED() for _ in range(3)]
b = Buzz()
i = IndicatorController(green=leds[0], yellow=leds[1], red=leds[2], buzzer=b)

def run(pct, leak, ms, fresh=True):
    result = a.update(pct, leak, ms, fresh_sample=fresh)
    i.update(result)
    return result

assert run(None, None, 0)["state"] == FAULT
assert run(80, False, 20)["state"] == NORMAL
assert leds[0].v == 1
assert run(20, False, 40)["buzzer_on"]
assert run(20, False, 300)["state"] == LOW_GAS
assert b.v == 0
assert run(20, True, 400)["state"] == LEAK_DETECTED
assert leds[2].v == 1
assert run(20, True, 700, False)["buzzer_on"] is False
assert run(20, False, 800, True)["state"] == LEAK_DETECTED
assert run(20, False, 820, False)["state"] == LEAK_DETECTED
assert run(20, False, 840, False)["state"] == LEAK_DETECTED
assert run(20, False, 1000, True)["state"] == LEAK_DETECTED
assert run(20, False, 1200, True)["state"] == LOW_GAS
assert run(80, True, 1400)["state"] == LEAK_DETECTED
assert run(None, None, 1600)["state"] == LEAK_DETECTED
assert run(80, False, 1800)["state"] == LEAK_DETECTED
assert run(80, False, 2000)["state"] == LEAK_DETECTED
assert run(80, False, 2200)["state"] == NORMAL
assert run(None, False, 2400)["state"] == FAULT
assert [x.v for x in leds] == [0,0,0]
i.close()
print("PASS: 18 alert / indicator regression checks")
