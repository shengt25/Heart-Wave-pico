import time
import array
from lib.fifo import Fifo as Fifo_
from common import print_log


class Fifo(Fifo_):
    def __init__(self, size, typecode='H'):
        super().__init__(size, typecode)

    def count(self):
        count = ((self.head - self.tail) + self.size) % self.size
        return count

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


class DualBuffer:
    def __init__(self, size, typecode='H'):
        self._buffer1 = array.array(typecode)
        self._buffer2 = array.array(typecode)
        for i in range(size):
            self._buffer1.append(0)
            self._buffer2.append(0)
        self._active_buffer = self._buffer1
        self._ptr = 0
        self._switched = False

    def put(self, value):
        self._active_buffer[self._ptr] = value
        self._ptr += 1
        if self._ptr == len(self._active_buffer):
            self._ptr = 0
            self._active_buffer = self._buffer2 if self._active_buffer == self._buffer1 else self._buffer1
            if not self._switched:
                self._switched = True
            else:
                raise RuntimeError("DualBuffer: buffer overflow")

    def is_switched(self):
        return self._switched

    def get_previous_buffer(self):
        if self._active_buffer == self._buffer1:
            return self._buffer2
        else:
            return self._buffer1

    def get_buffer(self):
        if self._switched:
            self._switched = False
            if self._active_buffer == self._buffer1:
                return self._buffer2
            else:
                return self._buffer1
        else:
            raise RuntimeError("DualBuffer: buffer not switched yet")

