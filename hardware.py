from machine import Pin, I2C, ADC
from ssd1306 import SSD1306_I2C
import time


class Event:
    EVENT = 1
    NO_EVENT = 0
    ERROR = -1


class Value:
    CLOCKWISE = 1
    COUNTER_CLOCKWISE = -1
    PRESS = 0
    RELEASE = 1
    DEFAULT = 0


# all hardware return: status, value
# status: 0: no event, 1: event, -1: error

class HeartSensor:
    def __init__(self, pin=26):
        self._adc = ADC(Pin(pin))

    def read(self):
        """Return (status, value).
        Status: 1 success; -1: error; value: 0-65535"""
        try:
            value = self._adc.read_u16()
        except:
            return Event.ERROR, 0  # return immediately if error
        return Event.EVENT, value


class RotaryEncoder:
    def __init__(self, clk_pin=10, dt_pin=11, btn_pin=12, debounce_ms=50):
        self._clk = Pin(clk_pin, Pin.IN, Pin.PULL_UP)
        self._dt = Pin(dt_pin, Pin.IN, Pin.PULL_UP)
        self._button = Pin(btn_pin, Pin.IN, Pin.PULL_UP)
        self._last_clk_value = 0
        self._last_button_state = 1  # ground button, 1 for released
        self._debounce_ms = debounce_ms
        self._last_rotate_time = time.ticks_ms()
        self._last_press_time = time.ticks_ms()

    def on_rotate(self):
        """Return (status, value).
        Status: 0: no event, 1: event, -1: error; value: 1: clockwise, -1: counter-clockwise"""
        # init default status = 0: no event
        status = Event.NO_EVENT
        value = Value.DEFAULT
        try:
            clk_value = self._clk.value()
            dt_value = self._dt.value()
        except:
            return Event.ERROR, Value.DEFAULT  # return immediately if error

        current_time = time.ticks_ms()
        if clk_value != self._last_clk_value and current_time - self._last_rotate_time > self._debounce_ms:
            status = Event.EVENT
            value = Value.CLOCKWISE if dt_value != clk_value else Value.COUNTER_CLOCKWISE
            self._last_rotate_time = current_time
            self._last_clk_value = clk_value
        return status, value

    def on_press(self):
        """Return (status, value).
        Status: 0: no event, 1: event, -1: error; value: 0: press, 1: release"""
        status = Event.NO_EVENT
        value = Value.DEFAULT
        try:
            button_state = self._button.value()
        except:
            return Event.ERROR, Value.DEFAULT

        current_time = time.ticks_ms()
        if button_state != self._last_button_state and current_time - self._last_rotate_time > self._debounce_ms:
            # ground button, 1 for released, 0 for pressed
            status = Event.EVENT if button_state == Value.PRESS else Event.NO_EVENT
            self._last_press_time = current_time
            self._last_button_state = button_state
        return status, value


def display_init():
    OLED_SDA = 14  # Data
    OLED_SCL = 15  # Clock
    OLED_WIDTH = 128
    OLED_HEIGHT = 64
    i2c = I2C(1, scl=Pin(OLED_SCL), sda=Pin(OLED_SDA), freq=400000)
    return SSD1306_I2C(OLED_WIDTH, OLED_HEIGHT, i2c)
