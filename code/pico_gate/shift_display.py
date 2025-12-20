# driver for 74HC595 and multiplexing

from machine import Pin, Timer
import segment_font

class ShiftDisplay:
    def __init__(self, data_pin, clock_pin, latch_pin, digit_pins, common_anode=False, digit_active_high=None):
        self.data = Pin(data_pin, Pin.OUT)
        self.clock = Pin(clock_pin, Pin.OUT)
        self.latch = Pin(latch_pin, Pin.OUT)
        self.digits = [Pin(p, Pin.OUT) for p in digit_pins]
        self.common_anode = common_anode

        if digit_active_high is None:
            # default behavior:
            # common cathode (False) -> active high digits (True)
            # common anode (True) -> active low digits (False)
            self.digit_active_high = not common_anode
        else:
            self.digit_active_high = digit_active_high
        
        self.buffer = [segment_font.BLANK] * 4
        self.timer = Timer()
        self.current_digit = 0
        
        # multiplexing at 500Hz
        self.timer.init(freq=500, mode=Timer.PERIODIC, callback=self._refresh)

    def _shift_out(self, byte_val):
        # shift out 8 bits, MSB first so Q0=LSB (Segment A)
        # iterate 7 down to 0
        for i in range(7, -1, -1):
            bit = (byte_val >> i) & 1
            self.data.value(bit)
            self.clock.value(1)
            self.clock.value(0)
            
    def _refresh(self, t):
        # Turn off all digits to prevent ghosting
        # Common Anode: High is OFF (if driving base via PNP/logic) or Low is ON?
        # Usually for Common Cathode digits: Pin LOW = OFF, Pin HIGH = ON
        # For Common Anode digits: Pin HIGH = OFF, Pin LOW = ON
        
        off_state = 1 if self.common_anode else 0
        on_state = 0 if self.common_anode else 1
        
        for d in self.digits:
            d.value(off_state) 
            
        # latch data for current digit
        self.latch.value(0)
        val = self.buffer[self.current_digit]
        
        # so invert bits if common anode
        if self.common_anode:
            val = ~val & 0xFF
            
        self._shift_out(val)
        self.latch.value(1)
        
        # turn on current digit
        self.digits[self.current_digit].value(on_state)
        
        # move to next digit
        self.current_digit = (self.current_digit + 1) % 4

    def show_full(self):
        self.buffer = segment_font.WORD_FULL

    def clear(self):
        self.buffer = [segment_font.BLANK] * 4

    def deinit(self):
        self.timer.deinit()
        off_state = 1 if self.common_anode else 0
        for d in self.digits:
            d.value(off_state)