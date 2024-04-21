from machine import Pin, I2C, ADC
from ssd1306 import SSD1306_I2C as SSD1306_I2C_
import time
from lib.piotimer import Piotimer
from common import Fifo, Global, print_log


class EncoderEvent:
    NONE = 0
    ROTATE = 1
    PRESS = 2


class Hardware:
    def __init__(self):
        self.display = init_display()
        self.rotary_encoder = RotaryEncoder(btn_debounce_ms=50)
        self.heart_sensor = HeartSensor()


class HeartSensor:
    def __init__(self, pin=26, sampling_rate=250):
        self._adc = ADC(Pin(pin))
        self._sampling_rate = sampling_rate
        self._timer = None
        self.sensor_fifo = Fifo(20)

    def set_timer_irq(self):
        self._timer = Piotimer(freq=self._sampling_rate, callback=self._sensor_handler)

    def unset_timer_irq(self):
        self._timer.deinit()

    def _sensor_handler(self, tid):
        value = self._adc.read_u16()
        self.sensor_fifo.put(value)

    def read(self):
        return self._adc.read_u16()


class RotaryEncoder:
    def __init__(self, clk_pin=10, dt_pin=11, btn_pin=12, btn_debounce_ms=50):
        self._clk = Pin(clk_pin, Pin.IN, Pin.PULL_UP)
        self._dt = Pin(dt_pin, Pin.IN, Pin.PULL_UP)
        self._button = Pin(btn_pin, Pin.IN, Pin.PULL_UP)
        self._btn_debounce_ms = btn_debounce_ms
        self._last_press_time = time.ticks_ms()
        self._event_fifo = Fifo(20, 'h')
        # register press interrupt by default (because every state needs it)
        self._button.irq(trigger=Pin.IRQ_RISING, handler=self._press_handler, hard=True)

        self._items_count = 0
        self._loop_mode = False
        self._position = 0

    def _cal_position(self, value):
        if self._loop_mode:
            self._position = (self._position + value) % self._items_count
        else:
            self._position = max(0, min(self._items_count - 1, self._position + value))

    def _rotate_handler(self, pin):
        if self._clk.value():
            self._event_fifo.put(1)
        else:
            self._event_fifo.put(-1)

    def _press_handler(self, pin):
        current_time = time.ticks_ms()
        if current_time - self._last_press_time > self._btn_debounce_ms:
            self._event_fifo.put(0)
            self._last_press_time = time.ticks_ms()

    def set_rotate_irq(self, items_count, position=0, loop_mode=False):
        """Set irq, max index, current position, and whether loop back or stop at limit."""
        self._items_count = items_count
        self._loop_mode = loop_mode
        self._position = position
        self._dt.irq(trigger=Pin.IRQ_RISING, handler=self._rotate_handler, hard=True)

    def unset_rotate_irq(self):
        self._dt.irq(handler=None)

    def get_position(self):
        """Get the current absolute position of the encoder."""
        print_log("Encoder position:" + str(self._position))
        return self._position

    def get_event(self):
        """Event needs to be got in the main loop and fast, to avoid fifo overflow."""
        if self._event_fifo.has_data():
            while self._event_fifo.has_data():
                value = self._event_fifo.get()
                if value == 0:  # press, clean fifo and exit
                    self._event_fifo.clear()
                    return EncoderEvent.PRESS
                else:  # rotate, value is either -1 or 1
                    self._cal_position(value)
            return EncoderEvent.ROTATE
        else:
            return EncoderEvent.NONE


class SSD1306_I2C(SSD1306_I2C_):
    def __init__(self, width, height, i2c):
        self.width = width
        self.height = height
        self.updated = False
        super().__init__(width, height, i2c)

    def show(self):
        """Only show the screen when update flag marked."""
        if self.updated:
            super().show()
            if Global.print_log:
                print(time.ticks_ms(), "screen updated")
            self.updated = False

    def set_update(self):
        """Mark the screen as updated, call show() in the main loop."""
        self.updated = True

    def clear(self):
        self.fill(0)


def init_display(sda=14, scl=15, width=128, height=64):
    # https://docs.micropython.org/en/latest/esp8266/tutorial/ssd1306.html
    # https://docs.micropython.org/en/latest/library/framebuf.html
    i2c = I2C(1, scl=Pin(scl), sda=Pin(sda), freq=400000)
    return SSD1306_I2C(width, height, i2c)
