"""HX711 load-cell ADC driver (PIO state machine) for Raspberry Pi Pico W / 2 W.

The PIO program waits for DT to go low, clocks out 24 data bits plus the 25th
pulse (channel A, gain 128) and pushes the sample to the RX FIFO, all in
hardware. Wi-Fi interrupts therefore can't stretch a clock pulse (SCK high for
more than ~60 us powers the HX711 down).

read_raw() NEVER blocks: it returns the newest sample, or None if no new
sample has arrived since the last call. Works with SensorManager unchanged.
"""
import rp2
from machine import Pin
# pyright: reportUndefinedVariable=false, reportCallIssue=false, reportAttributeAccessIssue=false

@rp2.asm_pio(
    sideset_init=rp2.PIO.OUT_LOW,
    in_shiftdir=rp2.PIO.SHIFT_LEFT,
    autopush=False,
)
def _hx711_program():
    wait(0, pin, 0).side(0)        # DT low = conversion ready
    set(x, 23).side(0)             # 24 data bits
    label("bit")
    nop().side(1)[2]               # SCK high
    in_(pins, 1).side(1)           # sample DT
    nop().side(0)[2]               # SCK low
    jmp(x_dec, "bit").side(0)
    nop().side(1)[3]               # 25th pulse: channel A, gain 128
    nop().side(0)[3]
    push(block).side(0)


class HX711:
    def __init__(self, dt_pin, sck_pin, sm_id=0):
        self.dt = Pin(dt_pin, Pin.IN)
        self.sck = Pin(sck_pin, Pin.OUT, value=0)
        self.sm = rp2.StateMachine(
            sm_id,
            _hx711_program,
            freq=2_000_000,
            sideset_base=self.sck,
            in_base=self.dt,
        )
        self.sm.active(1)

    def read_raw(self):
        """Return the newest signed 24-bit sample, or None if nothing new."""
        raw = None
        while self.sm.rx_fifo():      # drain; keep only the newest sample
            raw = self.sm.get()
        if raw is None:
            return None
        raw &= 0xFFFFFF
        if raw & 0x800000:
            raw -= 0x1000000
        return raw

    def close(self):
        self.sm.active(0)
        self.sck.init(Pin.OUT, value=0)