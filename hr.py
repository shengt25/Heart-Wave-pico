from hardware import EncoderEvent
from utils import print_log
import time


class HR:
    def __init__(self, hardware, state_machine, view, ibi_calculator):
        # hardware
        self._heart_sensor = hardware.heart_sensor
        self._rotary_encoder = hardware.rotary_encoder
        # other
        self._ibi_calculator = ibi_calculator
        self._state_machine = state_machine
        self._last_graph_update_time = time.ticks_ms()
        # data
        self._hr_list = []
        self._ibi_fifo = self._ibi_calculator.get_ibi_fifo()
        # ui
        self._view = view
        # create ui elements
        self._graph = None
        self._text_heading = None
        self._text_line1 = None
        self._text_line2 = None
        self._text_hr = None
        # settings
        self._hr_update_interval = 5  # number of sample needed to update the HR display
        self._start_threshold = 200  # value threshold to start HR measurement automatically when finger is placed

    def enter(self):
        # the entry point of the HR menu
        print_log("HR: enter")
        self._state_machine.set(self._state_waiting_init)

    def _state_waiting_init(self):
        self._text_heading = self._view.add_text(text="HR Measure", y=0, invert=True)  # 'invert' gives it a background
        self._text_hr = self._view.add_text(text="-- BPM", y=64 - 8)

        self._text_line1 = self._view.add_text(text="Put finger on ", y=14)
        self._text_line2 = self._view.add_text(text="sensor to start", y=24)
        self._state_machine.set(self._state_waiting)

    def _state_waiting(self):
        # keep watching the sensor value, if it's below the threshold, start the measurement
        value = self._heart_sensor.read()
        if value < self._start_threshold:
            self._text_line1.remove()
            self._text_line2.remove()
            self._state_machine.set(self._state_measure_init)

        # keep watching rotary encoder press event
        event = self._rotary_encoder.get_event()
        if event == EncoderEvent.PRESS:
            self._text_line1.remove()
            self._state_machine.set(self._state_machine.main_menu.enter)

    def _state_measure_init(self):
        # the entry point of the measure state, initialize variables here before entering
        # ui
        self._graph = self._view.add_graph(y=14, h=64 - 14 - 12)
        # other
        self._heart_sensor.set_timer_irq()
        self._ibi_calculator.reinit()
        self._state_machine.set(self._state_measure)

    def _state_measure(self):
        # this function was assigned to the state machine, and called repeatedly in a loop
        # until the rotary encoder event tells to enter another state

        self._ibi_calculator.run()  # keep calling calculator
        # monitor and get data from IBI FIFO, calculate hr and put into list
        if self._ibi_fifo.has_data():
            ibi = self._ibi_fifo.get()
            self._hr_list.append(int(60000 / ibi))

        # for every _hr_update_interval samples, calculate the median value and update the HR display
        if len(self._hr_list) >= self._hr_update_interval:
            median_hr = sorted(self._hr_list)[len(self._hr_list) // 2]
            self._text_hr.set_text(str(median_hr) + " BPM")  # use set_text to update the text
            self._hr_list.clear()

        # update graph, it reads current value from sensor directly. no need to use sensor_fifo
        # only update screen every 40ms, to save the CPU time
        if time.ticks_ms() - self._last_graph_update_time > 40:
            self._last_graph_update_time = time.ticks_ms()
            value = self._heart_sensor.read()
            self._graph.set_value(value)

        # keep watching rotary encoder press event
        event = self._rotary_encoder.get_event()
        if event == EncoderEvent.PRESS:
            self._view.remove_all()
            self._heart_sensor.unset_timer_irq()
            self._state_machine.set(self._state_machine.main_menu.enter)
