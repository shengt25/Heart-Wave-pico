from machine import Pin, I2C, ADC
from ssd1306 import SSD1306_I2C as SSD1306_I2C_
import time
from lib.fifo import Fifo as Fifo_


class Fifo(Fifo_):
    def __init__(self, size, typecode='H', debug=False):
        super().__init__(size, typecode)
        self.debug = debug

    def count(self):
        count = ((self.head - self.tail) + self.size) % self.size
        return count

    def get(self):
        if self.debug:
            print(f"time: {time.ticks_ms()}, fifo count:{self.count()}")
        return super().get()


class ENCODER_EVENT:
    NONE = 0
    CLOCKWISE = 1
    COUNTER_CLOCKWISE = 2
    PRESS = 3


class Hardware:
    def __init__(self):
        self.display = init_display()
        self.rotary_encoder = RotaryEncoder(btn_debounce_ms=50)
        self.heart_sensor = HeartSensor()


class HeartSensor:
    def __init__(self, pin=26):
        self._adc = ADC(Pin(pin))

    def read(self):
        """Return (True/False=success/fail, value)."""
        try:
            value = self._adc.read_u16()
        except:
            return False, 0  # return immediately if error
        return True, value


class RotaryEncoder:
    def __init__(self, clk_pin=10, dt_pin=11, btn_pin=12, btn_debounce_ms=50):
        self._clk = Pin(clk_pin, Pin.IN, Pin.PULL_UP)
        self._dt = Pin(dt_pin, Pin.IN, Pin.PULL_UP)
        self._button = Pin(btn_pin, Pin.IN, Pin.PULL_UP)
        self._btn_debounce_ms = btn_debounce_ms
        self._last_press_time = time.ticks_ms()
        self._has_rotate_irq = False
        self._fifo = Fifo(100)
        # register interrupt
        self._button.irq(trigger=Pin.IRQ_RISING, handler=self._press_handler, hard=True)
        self.set_rotate_irq()

    def _rotate_handler(self, pin):
        if self._clk.value():
            self._fifo.put(ENCODER_EVENT.CLOCKWISE)
        else:
            self._fifo.put(ENCODER_EVENT.COUNTER_CLOCKWISE)

    def _press_handler(self, pin):
        current_time = time.ticks_ms()
        if current_time - self._last_press_time > self._btn_debounce_ms:
            self._fifo.put(ENCODER_EVENT.PRESS)
            self._last_press_time = time.ticks_ms()

    def set_rotate_irq(self):
        if not self._has_rotate_irq:
            self._dt.irq(trigger=Pin.IRQ_RISING, handler=self._rotate_handler, hard=True)
            self._has_rotate_irq = True

    def unset_rotate_irq(self):
        if self._has_rotate_irq:
            self._dt.irq(handler=None)
            self._has_rotate_irq = False

    def get_event(self):
        if not self._fifo.empty():
            return self._fifo.get()
        else:
            return ENCODER_EVENT.NONE


class SSD1306_I2C(SSD1306_I2C_):
    def __init__(self, width, height, i2c):
        self.width = width
        self.height = height
        super().__init__(width, height, i2c)

    def update(self):
        self.show()
        print(time.ticks_ms(), "screen updated")

    def clear(self):
        self.fill(0)


def init_display(sda=14, scl=15, width=128, height=64):
    # https://docs.micropython.org/en/latest/esp8266/tutorial/ssd1306.html
    # https://docs.micropython.org/en/latest/library/framebuf.html
    i2c = I2C(1, scl=Pin(scl), sda=Pin(sda), freq=400000)
    return SSD1306_I2C(width, height, i2c)
