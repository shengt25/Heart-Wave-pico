from lib.fifo import Fifo as Fifo_
import time


class GlobalSettings:
    print_log = False
    display_max_refresh_rate = 60
    heart_sensor_pin = 26
    heart_sensor_sampling_rate = 250
    graph_refresh_rate = 60


def print_log(message):
    if GlobalSettings.print_log:
        print(time.ticks_ms(), message)


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

    def clear(self):
        self.tail = self.head

    def get_last_and_clear(self):
        """Get last item from the fifo. If the fifo is empty raises an exception."""
        val = self.data[self.head]
        if self.empty():
            raise RuntimeError("Fifo is empty")
        else:
            self.tail = self.head
        return val
