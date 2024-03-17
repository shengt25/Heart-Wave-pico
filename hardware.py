from machine import Pin, I2C, ADC
from ssd1306 import SSD1306_I2C
import time


class HeartSensor:
    def __init__(self, pin=26):
        self._adc = ADC(Pin(pin))

    def read(self):
        return self._adc.read_u16()


class RotaryEncoder:
    def __init__(self, clk_pin=10, dt_pin=11, btn_pin=12, debounce_ms=50):
        self._clk = Pin(clk_pin, Pin.IN, Pin.PULL_UP)
        self._dt = Pin(dt_pin, Pin.IN, Pin.PULL_UP)
        self._button = Pin(btn_pin, Pin.IN, Pin.PULL_UP)
        self._last_clk_value = 0
        self._last_button_state = 1
        self._debounce_ms = debounce_ms
        self._last_rotate_time = time.ticks_ms()
        self._last_press_time = time.ticks_ms()

    def read(self):
        """Return 1 for clockwise, -1 for counter-clockwise, 2 for button press, 0 for no action."""
        current_time = time.ticks_ms()
        clk_value = self._clk.value()
        dt_value = self._dt.value()
        button_state = self._button.value()

        # rotate, ignore when button is pressed
        if clk_value != self._last_clk_value and button_state == 1 and current_time - self._last_rotate_time > self._debounce_ms:
            if dt_value != clk_value:  # clockwise
                value = 1
            else:  # counter-clockwise
                value = -1
            self._last_rotate_time = current_time
            self._last_clk_value = clk_value
            return value

        # button
        if button_state != self._last_button_state and current_time - self._last_rotate_time > self._debounce_ms:
            if button_state == 0:
                value = 2
            else:
                value = 0
            self._last_press_time = current_time
            self._last_button_state = button_state
            return value
        # always 0 when no action
        return 0


# todo separate the rotary encoder and selector, and move selector maybe? it is not hardware
class Selector:
    def __init__(self, clk_pin=10, dt_pin=11, number=1, resolution=5):
        self.clk = Pin(clk_pin, Pin.IN, Pin.PULL_UP)
        self.dt = Pin(dt_pin, Pin.IN, Pin.PULL_UP)
        self.last_encoder_clk_value = 0
        self.value = 0
        self.value_max = 0
        self.number = number
        self.resolution = resolution
        # init items count, max value
        self.set_number(number)

    def read(self):
        clk_value = self.clk.value()
        dt_value = self.dt.value()
        if clk_value != self.last_encoder_clk_value:
            if dt_value != clk_value and self.value < self.value_max:  # clockwise
                self.value += 1
            if dt_value == clk_value and self.value > 0:  # counter-clockwise
                self.value -= 1
        self.last_encoder_clk_value = clk_value
        return int(self.value / self.resolution)

    def read_raw(self):
        return self.value

    def set_number(self, number):
        if number > 0:
            self.number = number
            self.value_max = number * self.resolution - 1
            if self.value > self.value_max:
                self.value = self.value_max
            return True
        else:
            return False


def display_init():
    OLED_SDA = 14  # Data
    OLED_SCL = 15  # Clock
    OLED_WIDTH = 128
    OLED_HEIGHT = 64
    i2c = I2C(1, scl=Pin(OLED_SCL), sda=Pin(OLED_SDA), freq=400000)
    return SSD1306_I2C(OLED_WIDTH, OLED_HEIGHT, i2c)
