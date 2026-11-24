"""Timer-based LED/buzzer behavior replay; run on Pico, no sleep()."""
from machine import Pin, PWM
from time import ticks_ms, ticks_diff

NORMAL = "NORMAL"
LOW_GAS = "LOW_GAS"
LEAK = "LEAK_DETECTED"

cases = [(100, False), (50, False), (21, False), (20, False),
         (10, False), (80, True), (10, True), (15, False), (50, False)]
green = Pin(13, Pin.OUT, value=0)
yellow = Pin(14, Pin.OUT, value=0)
red = Pin(15, Pin.OUT, value=0)
buzzer = PWM(Pin(16))
buzzer.freq(2000)
buzzer.duty_u16(0)

index = -1
state_since = ticks_ms()
case_since = ticks_ms() - 3000
low_warning_given = False
prev_buzzer = False

try:
    while True:
        now = ticks_ms()
        if ticks_diff(now, case_since) >= 3000:
            index += 1
            if index >= len(cases):
                break
            case_since = now
            pct, leak = cases[index]
            state = LEAK if leak else LOW_GAS if pct <= 20 else NORMAL
            green.value(state == NORMAL)
            yellow.value(state == LOW_GAS)
            red.value(state == LEAK)
            if state != LOW_GAS:
                low_warning_given = False
            low_beep = state == LOW_GAS and not low_warning_given
            if low_beep:
                low_warning_given = True
            state_since = now
            print("LPG:", pct, "Leak:", leak, "State:", state)
        elapsed = ticks_diff(now, state_since)
        if state == LEAK:
            buzzer_on = elapsed % 800 < 250
        elif state == LOW_GAS:
            buzzer_on = low_beep and elapsed < 200
        else:
            buzzer_on = False
        if buzzer_on != prev_buzzer:
            buzzer.duty_u16(30000 if buzzer_on else 0)
            prev_buzzer = buzzer_on
finally:
    green.off()
    yellow.off()
    red.off()
    buzzer.duty_u16(0)
    buzzer.deinit()
