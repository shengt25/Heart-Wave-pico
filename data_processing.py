from lib.fifo import Fifo as Fifo_
from utils import print_log
from math import sqrt
import array


class Fifo(Fifo_):
    def __init__(self, size, typecode='H'):
        super().__init__(size, typecode)

    def count(self):
        count = ((self.head - self.tail) + self.size) % self.size
        return count

    def clear(self):
        self.tail = self.head

    def peek_history(self, step):
        """Get history data that counting 'step' samples from the current to the past
        If the data is already overwritten, raises an exception."""
        if step >= self.size:
            raise RuntimeError("Step is larger than the fifo size")
        elif step + self.count() > self.size:
            raise RuntimeError("Data has been overwritten")
        else:
            ptr = ((self.tail - step) + self.size) % self.size
            return self.data[ptr]


class Deque:
    """A circular deque implementation using array"""

    def __init__(self, size, typecode='H'):
        self.size = size
        self.buffer = array.array(typecode)
        for i in range(size):
            self.buffer.append(0)
        self.tail = 0
        self.head = 0
        self.count = 0

    def append_right(self, value):
        if self.count == self.size:
            raise Exception("Deque is full")
        self.buffer[self.head] = value
        self.head = (self.head + 1) % self.size
        self.count += 1

    def append_left(self, value):
        if self.count == self.size:
            raise Exception("Deque is full")
        self.tail = (self.tail - 1) % self.size
        self.buffer[self.tail] = value
        self.count += 1

    def pop_right(self):
        if self.count == 0:
            raise Exception("Deque is empty")
        self.head = (self.head - 1) % self.size
        value = self.buffer[self.head]
        self.count -= 1
        return value

    def pop_left(self):
        if self.count == 0:
            raise Exception("Deque is empty")
        value = self.buffer[self.tail]
        self.tail = (self.tail + 1) % self.size
        self.count -= 1
        return value

    def peek_right(self):
        if self.count == 0:
            raise Exception("Deque is empty")
        return self.buffer[(self.head - 1) % self.size]

    def peek_left(self):
        if self.count == 0:
            raise Exception("Deque is empty")
        return self.buffer[self.tail]

    def peek(self, index):
        if index >= self.count:
            raise Exception("Index out of range")
        return self.buffer[(self.tail + index) % self.size]

    def has_data(self):
        return self.count > 0

    def clear(self):
        self.tail = 0
        self.head = 0
        self.count = 0


class SlidingWindow:
    def __init__(self, size, typecode='H'):
        self.size = size
        self.deque_max = Deque(size, typecode)
        self.deque_min = Deque(size, typecode)
        self.current_window = Deque(size, typecode)
        self.sum = 0

    def push(self, value):
        if self.current_window.count == self.size:
            expiring_value = self.current_window.pop_left()
            if expiring_value == self.deque_max.peek_left():
                self.deque_max.pop_left()
            if expiring_value == self.deque_min.peek_left():
                self.deque_min.pop_left()
            self.sum -= expiring_value

        while self.deque_max.has_data() and self.deque_max.peek_right() < value:
            self.deque_max.pop_right()
        while self.deque_min.has_data() and self.deque_min.peek_right() > value:
            self.deque_min.pop_right()
        self.deque_max.append_right(value)
        self.deque_min.append_right(value)
        self.current_window.append_right(value)
        self.sum += value

    def get_max(self):
        return self.deque_max.peek_left() if self.deque_max else None

    def get_min(self):
        return self.deque_min.peek_left() if self.deque_min else None

    def get_average(self):
        return self.sum / self.current_window.count if self.current_window.count > 0 else None

    def get_mid_index_value(self):
        return self.current_window.peek(self.current_window.count // 2)

    def is_window_filled(self):
        return self.current_window.count == self.size

    def clear(self):
        self.deque_max.clear()
        self.deque_min.clear()
        self.current_window.clear()
        self.sum = 0

    def has_data(self):
        return self.current_window.has_data()


class IBICalculator:
    def __init__(self, sensor_fifo, sampling_rate, sliding_window, min_hr=40, max_hr=180):
        # data store and output
        self.ibi_fifo = Fifo(20, 'H')
        # hardware
        self._sensor_fifo = sensor_fifo
        # init parameters
        self._sampling_rate = sampling_rate
        self._sliding_window = sliding_window
        self._max_ibi = 60 / min_hr * 1000
        self._min_ibi = 60 / max_hr * 1000
        # data
        self._last_rising_edge_diff = 0
        self._rising_edge_diff = 0
        self._peak = 0
        self._last_peak_index = 0
        self._peak_index = 0
        # settings
        self._debounce_window = 10
        self._debounce_count = 0
        # first state
        self._state = self._state_below_threshold

    """public methods"""

    def reinit(self):
        """Reinitialize the variables to start a new calculation"""
        self._sliding_window.clear()
        self.ibi_fifo.clear()
        self._peak = 0
        self._last_rising_edge_diff = 0
        self._rising_edge_diff = 0
        self._last_peak_index = 0
        self._peak_index = 0
        self._state = self._state_below_threshold

    def run(self):
        self._state()

    """private methods"""

    def _get_threshold_and_value(self):
        """Get the value at the center of the window in fifo history, and calculate the threshold"""
        self._sliding_window.push(self._sensor_fifo.get())
        threshold = self._sliding_window.get_average() + (
                self._sliding_window.get_max() - self._sliding_window.get_min()) * 0.4
        value = self._sliding_window.get_mid_index_value()
        return value, threshold

    def _state_below_threshold(self):
        # The while loop is to consume all the data in the fifo at once,
        # not a real "while loop" that will block the system
        while self._sensor_fifo.has_data():
            value, threshold = self._get_threshold_and_value()
            self._rising_edge_diff += 1
            if value > threshold:
                self._debounce_count += 1  # above threshold, start to debounce
            else:
                self._debounce_count = 0  # reset count if below threshold within the debounce window

            # if the debounce window is reached, reset the debounce count and prepare to go to above threshold state
            if self._debounce_count > self._debounce_window:
                self._debounce_count = 0
                self._last_peak_index = self._peak_index
                self._last_rising_edge_diff = self._rising_edge_diff
                self._peak = 0
                self._rising_edge_diff = 0
                self._peak_index = 0
                self._state = self._state_above_threshold
                return

    def _state_above_threshold(self):
        # The while loop is to consume all the data in the fifo at once,
        # not a real "while loop" that will block the system
        while self._sensor_fifo.has_data():
            value, threshold = self._get_threshold_and_value()
            self._rising_edge_diff += 1
            if value > threshold and value > self._peak:
                self._peak = value
                self._peak_index = self._rising_edge_diff

            if value < threshold:
                # last peak is invalid, not calculating but go back and wait for next threshold
                if self._last_peak_index == 0 or self._last_rising_edge_diff == 0:
                    self._state = self._state_below_threshold
                    return
                else:
                    data_points = self._last_rising_edge_diff - self._last_peak_index + self._peak_index
                    ibi = int(data_points * 1000 / self._sampling_rate)
                    if self._min_ibi < ibi < self._max_ibi:
                        self.ibi_fifo.put(ibi)
                    # no need to reset peak_index and rising_edge_diff,
                    # because they will be assigned to last_peak_index and last_rising_edge_diff in the next state
                self._state = self._state_below_threshold
                return


def calculate_hrv(IBI_list):
    # HR
    average_HR = 0
    for HR in IBI_list:
        average_HR += HR
    average_HR /= len(IBI_list)
    average_HR = 60000 / average_HR

    # PPI
    minimum = 9999999
    maximum = 0
    for beat in IBI_list:
        if beat > maximum:
            maximum = beat
        if beat < minimum:
            minimum = beat
    PPI = maximum - minimum

    # RMSSD
    average = 0
    for i in range(1, len(IBI_list), 1):
        difference = (IBI_list[i] - IBI_list[i - 1]) ** 2
        average += difference
    average /= len(IBI_list) - 1
    RMSSD = sqrt(average)

    mean_val = 0
    for i in IBI_list:
        mean_val += i
    mean_val /= len(IBI_list)
    variance = 0
    for i in IBI_list:
        variance += (i - mean_val) ** 2
    variance /= (len(IBI_list) - 1)
    variance = variance ** 0.5
    SDNN = variance

    # I could've probably done this all in one go but I decided not to give anybody who will read this nightmares.
    return round(average_HR, 2), round(PPI, 2), round(RMSSD, 2), round(SDNN, 2)
