from machine import Pin, I2C, ADC
from ssd1306 import SSD1306_I2C
import time
from lib.fifo import Fifo


class ENCODER_EVENT:
    NONE = 0
    CLOCKWISE = 1
    COUNTER_CLOCKWISE = 2
    PRESS = 3


class Hardware:
    def __init__(self):
        self.display = init_display()
        self.rotary_encoder = RotaryEncoder(rotate_debounce_ms=10, btn_debounce_ms=50)
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
    def __init__(self, clk_pin=10, dt_pin=11, btn_pin=12, rotate_debounce_ms=10, btn_debounce_ms=50):
        self._clk = Pin(clk_pin, Pin.IN, Pin.PULL_UP)
        self._dt = Pin(dt_pin, Pin.IN, Pin.PULL_UP)
        self._button = Pin(btn_pin, Pin.IN, Pin.PULL_UP)
        self._debounce_ms = rotate_debounce_ms
        self._btn_debounce_ms = btn_debounce_ms
        self._last_rotate_time = time.ticks_ms()
        self._last_press_time = time.ticks_ms()
        self._set_rotate_irq = True
        self._fifo = Fifo(10)
        # register interrupt
        self._clk.irq(trigger=Pin.IRQ_RISING, handler=self._rotate_irq, hard=True)
        self._button.irq(trigger=Pin.IRQ_RISING, handler=self._press_irq, hard=True)

    def _rotate_irq(self, p):
        current_time = time.ticks_ms()
        if current_time - self._last_rotate_time > self._debounce_ms:
            if self._dt.value():
                self._fifo.put(ENCODER_EVENT.COUNTER_CLOCKWISE)
            else:
                self._fifo.put(ENCODER_EVENT.CLOCKWISE)
            self._last_rotate_time = time.ticks_ms()

    def _press_irq(self, p):
        current_time = time.ticks_ms()
        if current_time - self._last_press_time > self._btn_debounce_ms:
            self._fifo.put(ENCODER_EVENT.PRESS)
            self._last_press_time = time.ticks_ms()

    def set_rotate_irq(self):
        if not self._set_rotate_irq:
            self._clk.irq(trigger=Pin.IRQ_RISING, handler=self._rotate_irq, hard=True)
            self._set_rotate_irq = True

    def unset_rotate_irq(self):
        if self._set_rotate_irq:
            self._clk.irq(handler=None)
            self._set_rotate_irq = False

    def get_event(self):
        if not self._fifo.empty():
            return self._fifo.get()
        else:
            return ENCODER_EVENT.NONE


class MySSD1306_I2C(SSD1306_I2C):
    def __init__(self, width, height, i2c):
        self.width = width
        self.height = height
        super().__init__(width, height, i2c)

    def get_height(self):
        return self.height

    def get_width(self):
        return self.width

    def power_off(self):
        self.poweroff()

    def power_on(self):
        self.poweron()

    def clear(self):
        self.fill(0)


def init_display(sda=14, scl=15, width=128, height=64):
    # https://docs.micropython.org/en/latest/esp8266/tutorial/ssd1306.html
    # https://docs.micropython.org/en/latest/library/framebuf.html
    i2c = I2C(1, scl=Pin(scl), sda=Pin(sda), freq=400000)
    return MySSD1306_I2C(width, height, i2c)

# class RotaryEncoder:
#     def __init__(self, clk_pin=10, dt_pin=11, btn_pin=12, debounce_ms=5, rotate_timeout=200, rotate_trigger_count=3):
#         self._clk = Pin(clk_pin, Pin.IN, Pin.PULL_UP)
#         self._dt = Pin(dt_pin, Pin.IN, Pin.PULL_UP)
#         self._button = Pin(btn_pin, Pin.IN, Pin.PULL_UP)
#         self._last_button_state = 1  # ground button, 1 for released
#         self._debounce_ms = debounce_ms
#         self._last_rotate_time = time.ticks_ms()
#         self._last_press_time = time.ticks_ms()
#         self._rotate_timeout = rotate_timeout
#         self._rotate_trigger_count = rotate_trigger_count
#         self._set_rotate_irq = True
#         self._fifo = Fifo(10)
#         # register interrupt
#         self._clk.irq(trigger=Pin.IRQ_RISING, handler=self._rotate_irq, hard=True)
#         self._button.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self._press_irq, hard=True)
#
#     def _rotate_irq(self, p):
#         current_time = time.ticks_ms()
#         if current_time - self._last_rotate_time > self._rotate_timeout:
#             self._rotate_step = 0
#
#         if self._rotate_step >= self._rotate_trigger_count:
#             self._fifo.put(EventTypes.ENCODER_CLOCKWISE)
#             self._rotate_step = 0
#
#         if self._rotate_step <= -self._rotate_trigger_count:
#             self._fifo.put(EventTypes.ENCODER_COUNTER_CLOCKWISE)
#             self._rotate_step = 0
#
#         if current_time - self._last_rotate_time > self._debounce_ms:
#             if self._dt.value():
#                 self._rotate_step -= 1
#             else:
#                 self._rotate_step += 1
#             self._last_rotate_time = time.ticks_ms()
