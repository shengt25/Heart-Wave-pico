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

    def get_previous(self, step):
        """Get data that counting 'step' from the current data to the past"""
        if step >= self.size:
            raise RuntimeError("Step is larger than the fifo size")
        elif step + self.count() > self.size:
            raise RuntimeError("Data is already overwritten")
        else:
            ptr = ((self.tail - step) + self.size) % self.size
            return self.data[ptr]


class IBICalculator:
    def __init__(self, sensor_fifo, sampling_rate, min_hr=40, max_hr=180):
        self._sensor_fifo = sensor_fifo
        # init ibi array
        self.ibi_fifo = Fifo(20, 'H')
        self._sampling_rate = sampling_rate
        self._window_side_length = int(sampling_rate * 0.75)
        self._window_size = self._window_side_length * 2 + 1
        self._max_ibi = 60 / min_hr * 1000
        self._min_ibi = 60 / max_hr * 1000

        self._debounce_samples = 10
        self._count = 0
        self._sum = 0
        self._max = 0
        self._last_thr_index = 0
        self._thr_index = 0
        self._last_peak_index = 0
        self._peak_index = 0

        self.state = self._state_wait

    def reinit(self):
        self._count = 0
        self._sum = 0
        self._max = 0
        self._last_thr_index = 0
        self._thr_index = 0
        self._last_peak_index = 0
        self._peak_index = 0

    def _state_wait(self):
        while self._sensor_fifo.has_data():
            if self._thr_index < self._window_size:  # borrow _thr_index to count the number of data points
                self._sum += self._sensor_fifo.get()
                self._thr_index += 1
            else:
                self._thr_index = 0
                self.state = self._state_below_thr
                break

    def _cal_threshold(self):
        self._sum -= self._sensor_fifo.get_previous(self._window_size)
        self._sum += self._sensor_fifo.get()
        threshold = int(self._sum / self._window_size)
        threshold = threshold + (threshold >> 6)
        value = self._sensor_fifo.get_previous(self._window_side_length)
        print(value, threshold)
        return value, threshold

    def _state_below_thr(self):
        while self._sensor_fifo.has_data():
            value, threshold = self._cal_threshold()
            self._thr_index += 1
            if value > threshold:
                self._last_peak_index = self._peak_index
                self._last_thr_index = self._thr_index
                self._max = 0
                self._thr_index = 0
                self._peak_index = 0
                # print("above thr")
                self.state = self._state_above_thr
                return

    def _state_above_thr(self):
        while self._sensor_fifo.has_data():
            value, threshold = self._cal_threshold()
            self._thr_index += 1
            if value > threshold and value > self._max:
                self._max = value
                self._peak_index = self._thr_index

            if value < threshold:

                # if self._max == 0:
                #     print("max is 0")
                # if self._peak_index == 0:
                #     print("peak index is 0")

                if self._last_peak_index == 0:
                    # print("below thr, not calculating")
                    self.state = self._state_below_thr
                    return
                else:
                    data_points = self._last_thr_index - self._last_peak_index + self._peak_index
                    ibi = int(data_points * 1000 / self._sampling_rate)
                    if self._min_ibi < ibi < self._max_ibi:
                        self.ibi_fifo.put(ibi)
                    else:
                        self._peak_index = 0
                # print("below thr")
                self.state = self._state_below_thr
                return

    def run(self):
        self.state()
