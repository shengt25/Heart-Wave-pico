from machine import Pin, I2C, ADC
from ssd1306 import SSD1306_I2C


class HeartSensor:
    def __init__(self, pin=26):
        self._adc = ADC(Pin(pin))

    def read(self):
        return self._adc.read_u16()


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
