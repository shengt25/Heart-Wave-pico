from lib.fifo import Fifo as Fifo_
import time


class Global:
    print_log = False


def print_log(message):
    if Global.print_log:
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
