from machine import Pin, I2C, ADC
from ssd1306 import SSD1306_I2C
import time


class EventTypes:
    ENCODER_CLOCKWISE = 1 << 0
    ENCODER_COUNTER_CLOCKWISE = 1 << 1
    ENCODER_PRESS = 1 << 2
    # SW1_PRESS = 1<<3
    # SW2_PRESS = 1<<4
    # SW3_PRESS = 1<<5


class EventManager:
    def __init__(self):
        self._event_flag = 0

    def set(self, event_type):
        self._event_flag |= event_type

    def clear(self, event_type):
        self._event_flag &= ~event_type

    def pop(self, event_type):
        if self.get(event_type):
            self.clear(event_type)
            print(event_type)
            return True
        return False

    def get(self, event_type):
        return self._event_flag & event_type

    def clear_all(self):
        self._event_flag = 0
    #
    # def is_set(self):
    #     return self._event_flag != 0


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
    def __init__(self, event_manager, clk_pin=10, dt_pin=11, btn_pin=12, debounce_ms=5, rotate_timeout=200,
                 rotate_step_trigger=3, debug=False):
        self._clk = Pin(clk_pin, Pin.IN, Pin.PULL_UP)
        self._dt = Pin(dt_pin, Pin.IN, Pin.PULL_UP)
        self._button = Pin(btn_pin, Pin.IN, Pin.PULL_UP)
        self._last_clk_value = 0
        self._last_button_state = 1  # ground button, 1 for released
        self._debounce_ms = debounce_ms
        self._last_rotate_time = time.ticks_ms()
        self._last_press_time = time.ticks_ms()

        self._rotate_timeout = rotate_timeout
        self._rotate_step_trigger = rotate_step_trigger
        self._rotate_step = 0

        # register interrupt
        self._event_manager = event_manager
        self._clk.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self._on_rotate)
        self._button.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self._on_press)

    def _on_rotate(self, p):
        try:
            clk_value = self._clk.value()
            dt_value = self._dt.value()
        except:
            return False

        current_time = time.ticks_ms()
        if current_time - self._last_rotate_time > self._rotate_timeout:
            self._rotate_step = 0
        if clk_value != self._last_clk_value and current_time - self._last_rotate_time > self._debounce_ms:
            if dt_value != clk_value:
                self._rotate_step += 1
            else:
                self._rotate_step -= 1
            self._last_rotate_time = current_time
            self._last_clk_value = clk_value

        if self._rotate_step >= self._rotate_step_trigger:
            self._event_manager.set(EventTypes.ENCODER_CLOCKWISE)
            self._rotate_step = 0
        if self._rotate_step <= -self._rotate_step_trigger:
            self._event_manager.set(EventTypes.ENCODER_COUNTER_CLOCKWISE)
            self._rotate_step = 0
        print(self._rotate_step)

        return True

    def _on_press(self, p):
        try:
            button_state = self._button.value()
        except:
            return False
        current_time = time.ticks_ms()
        if button_state != self._last_button_state and current_time - self._last_press_time > self._debounce_ms:
            # ground button, 1 for released, 0 for pressed
            if button_state == 0:
                self._event_manager.set(EventTypes.ENCODER_PRESS)
            self._last_press_time = current_time
            self._last_button_state = button_state
        return True


class MySSD1306_I2C(SSD1306_I2C):
    def __init__(self, width, height, i2c):
        self.width = width
        self.height = height
        super().__init__(width, height, i2c)

    def get_height(self):
        return self.height

    def get_width(self):
        return self.width

    def turnoff(self):
        self.poweroff()


def init_display(sda=14, scl=15, width=128, height=64):
    # https://docs.micropython.org/en/latest/esp8266/tutorial/ssd1306.html
    # https://docs.micropython.org/en/latest/library/framebuf.html
    i2c = I2C(1, scl=Pin(scl), sda=Pin(sda), freq=400000)
    return MySSD1306_I2C(width, height, i2c)
