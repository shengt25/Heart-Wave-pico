from lib.fifo import Fifo as Fifo_
from utils import print_log
from math import sqrt
    

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

    def get_history(self, step):
        """Get history data that counting 'step' samples from the current to the past
        If the data is already overwritten, raises an exception."""
        if step >= self.size:
            raise RuntimeError("Step is larger than the fifo size")
        elif step + self.count() > self.size:
            raise RuntimeError("Data is already overwritten")
        else:
            ptr = ((self.tail - step) + self.size) % self.size
            return self.data[ptr]


class IBICalculator:
    def __init__(self, sensor_fifo, sampling_rate, min_hr=40, max_hr=180):
        # hardware
        self._sensor_fifo = sensor_fifo
        # init parameters
        self._sampling_rate = sampling_rate
        self._window_side_length = int(sampling_rate * 0.75)
        self._window_size = self._window_side_length * 2 + 1
        self._max_ibi = 60 / min_hr * 1000
        self._min_ibi = 60 / max_hr * 1000
        # data
        self._ibi_fifo = Fifo(20, 'H')
        self._sum = 0
        self._max = 0
        self._last_rising_edge_diff = 0
        self._rising_edge_diff = 0
        self._last_peak_index = 0
        self._peak_index = 0
        # settings
        self._debounce_window = 10
        self._debounce_count = 0
        self._simple_version = False  # see comments in _state_below_threshold_simple
        # first state
        self.state = self._state_wait

    """public methods"""

    def reinit(self):
        """Reinitialize the variables to start a new calculation"""
        self._ibi_fifo.clear()
        self._sum = 0
        self._max = 0
        self._last_rising_edge_diff = 0
        self._rising_edge_diff = 0
        self._last_peak_index = 0
        self._peak_index = 0
        self.state = self._state_wait

    def get_ibi_fifo(self):
        return self._ibi_fifo

    def run(self):
        self.state()

    """private methods"""

    def _get_threshold_and_value(self):
        """Get the value at the center of the window in fifo history, and calculate the threshold"""
        self._sum -= self._sensor_fifo.get_history(self._window_size)
        self._sum += self._sensor_fifo.get()
        threshold = int(self._sum / self._window_size)
        threshold = threshold + (threshold >> 6)  # threshold + threshold * 1.5625%
        value = self._sensor_fifo.get_history(self._window_side_length)  # get the value at the center of the window
        return value, threshold

    def _state_wait(self):
        """Wait for the data to fill the first window size, which is 1.5 seconds data"""
        while self._sensor_fifo.has_data():
            # borrow _rising_edge_diff to count the number of data points
            if self._rising_edge_diff < self._window_size:
                self._sum += self._sensor_fifo.get()
                self._rising_edge_diff += 1
            else:
                self._rising_edge_diff = 0
                if self._simple_version:
                    self.state = self._state_below_threshold_simple
                else:
                    self.state = self._state_below_threshold
                break

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
                self._max = 0
                self._rising_edge_diff = 0
                self._peak_index = 0
                self.state = self._state_above_threshold
                return

    def _state_above_threshold(self):
        # The while loop is to consume all the data in the fifo at once,
        # not a real "while loop" that will block the system
        while self._sensor_fifo.has_data():
            value, threshold = self._get_threshold_and_value()
            self._rising_edge_diff += 1
            if value > threshold and value > self._max:
                self._max = value
                self._peak_index = self._rising_edge_diff

            if value < threshold:
                # last peak is invalid, not calculating but go back and wait for next threshold
                if self._last_peak_index == 0 or self._last_rising_edge_diff == 0:
                    self.state = self._state_below_threshold
                    return
                else:
                    data_points = self._last_rising_edge_diff - self._last_peak_index + self._peak_index
                    ibi = int(data_points * 1000 / self._sampling_rate)
                    if self._min_ibi < ibi < self._max_ibi:
                        self._ibi_fifo.put(ibi)
                    # no need to reset peak_index and rising_edge_diff,
                    # because they will be assigned to last_peak_index and last_rising_edge_diff in the next state
                self.state = self._state_below_threshold
                return

    def _state_below_threshold_simple(self):
        """
        Another simpler version without debounce mechanism. The ibi validation will filter out the invalid data points,
        but it does meaningless calculation for the invalid data points
        Unused, for backup only"""
        # The while loop is to consume all the data in the fifo at once,
        # not a real "while loop" that will block the system
        while self._sensor_fifo.has_data():
            value, threshold = self._get_threshold_and_value()
            self._rising_edge_diff += 1

            if value > threshold:
                self._debounce_count = 0
                self._last_peak_index = self._peak_index
                self._last_rising_edge_diff = self._rising_edge_diff
                self._max = 0
                self._rising_edge_diff = 0
                self._peak_index = 0
                self.state = self._state_above_threshold_simple
                return

    def _state_above_threshold_simple(self):
        """
        Another simpler version without debounce mechanism. The ibi validation will filter out the invalid data points,
        but it does meaningless calculation for the invalid data points
        Unused, for backup only"""
        # The while loop is to consume all the data in the fifo at once,
        # not a real "while loop" that will block the system
        while self._sensor_fifo.has_data():
            value, threshold = self._get_threshold_and_value()
            self._rising_edge_diff += 1
            if value > threshold and value > self._max:
                self._max = value
                self._peak_index = self._rising_edge_diff

            if value < threshold:
                # last peak is invalid, not calculating but go back and wait for next threshold
                data_points = self._last_rising_edge_diff - self._last_peak_index + self._peak_index
                ibi = int(data_points * 1000 / self._sampling_rate)
                if self._min_ibi < ibi < self._max_ibi:
                    self._ibi_fifo.put(ibi)
                self.state = self._state_below_threshold_simple
                return
            
class HRVCalculator:
    def __init__(self,IBI_list):
        self._IBI_list = IBI_list
        
    def _calculate_results(self):
        #HR
        average_HR = 0
        for HR in self._IBI_list:
            average_HR	+= HR
        average_HR /= len(self._IBI_list)
        average_HR = 60000 / average_HR
        
        #PPI
        minimum = 9999999
        maximum = 0
        for beat in self._IBI_list:
            if beat > maximum:
                maximum = beat
            if beat < minimum:
                minimum = beat
        PPI = maximum - minimum
        
        #RMSSD
        average = 0
        for i in range(1,len(self._IBI_list),1):
            difference = (self._IBI_list[i] - self._IBI_list[i-1]) ** 2
            average += difference
        average /= len(self._IBI_list) - 1
        RMSSD = sqrt(average)
        
        mean_val = 0
        for i in self._IBI_list:
            mean_val += i
        mean_val /= len(self._IBI_list)
        variance = 0
        for i in self._IBI_list:
            variance += (i-mean_val)**2
        variance /= (len(self._IBI_list)-1)
        variance = variance** 0.5
        SDNN = variance
        
        #I could've probably done this all in one go but I decided not to give anybody who will read this nightmares.
        return round(average_HR,2),round(PPI,2),round(RMSSD,2),round(SDNN,2)
        
        
            