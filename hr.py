from hardware import EncoderEvent
from utils import print_log
import time
from state import State


class HREntry(State):
    # start the measurement after triggering threshold is reached
    def __init__(self, state_machine):
        super().__init__(state_machine)
        self._start_threshold = 200  # threshold that triggers measurement automatically when finger is placed
        self._heading_text = "HR Measure"
        self._hr_text = "-- BPM"

    def enter(self):
        print_log(self._heading_text)
        self._view.add_text(text="Put finger on ", y=14, vid="info1")
        self._view.add_text(text="sensor to start", y=24, vid="info2")
        self._view.add_text(text=self._heading_text, y=0, invert=True, vid="heading")  # 'invert' gives it a background
        self._view.add_text(text=self._hr_text, y=64 - 8, vid="hr")
        self._display.set_update()

    def loop(self):
        value = self._heart_sensor.read()
        if value < self._start_threshold:
            self._view.remove_by_id("info1")
            self._view.remove_by_id("info2")
            self.exit()
            return
        # keep watching rotary encoder press event
        event = self._rotary_encoder.get_event()
        if event == EncoderEvent.PRESS:
            self._view.remove_by_id("info1")
            self._view.remove_by_id("info2")
            self._state_machine.set(State.Main_Menu)

    def exit(self):
        self._state_machine.set(HRMeasure)


class HRMeasure(State):
    def __init__(self, state_machine):
        super().__init__(state_machine)
        # data
        self._last_graph_update_time = time.ticks_ms()
        self._hr_display_list = []
        self._ibi_fifo = self._ibi_calculator.get_ibi_fifo()
        # ui placeholder
        self._text_hr = None
        self._graph = None
        # settings
        self._hr_update_interval = 5  # number of sample needed to update the HR display

    def enter(self):
        # the entry point of the HR menu
        print_log("HR: enter")
        # clear data
        self._ibi_calculator.reinit()
        self._hr_display_list.clear()
        self._last_graph_update_time = time.ticks_ms()
        # ui
        self._text_hr = self._view.select_by_id("hr")
        self._graph = self._view.add_graph(y=14, h=64 - 14 - 12, vid="graph")
        # set up timer interrupt at last (to reduce the chance of data building up), and set next state to measure
        self._heart_sensor.start()

    def loop(self):
        # this function was assigned to the state machine, and called repeatedly in a loop
        # until the rotary encoder event tells to enter another state

        self._ibi_calculator.run()  # keep calling calculator
        # monitor and get data from ibi fifo, calculate hr and put into list
        if self._ibi_fifo.has_data():
            ibi = self._ibi_fifo.get()
            self._hr_display_list.append(int(60000 / ibi))

        # for every _hr_update_interval samples, calculate the median value and update the HR display
        if len(self._hr_display_list) >= self._hr_update_interval:
            median_hr = sorted(self._hr_display_list)[len(self._hr_display_list) // 2]
            # use set_text method to update the text, view (screen) will auto refresh
            self._text_hr.set_text(str(median_hr) + " BPM")
            self._hr_display_list.clear()

        # update graph, it reads current value from sensor directly. no need to use sensor_fifo
        # only update screen every 40ms, to save the CPU time
        if time.ticks_diff(time.ticks_ms(), self._last_graph_update_time) > 40:
            self._last_graph_update_time = time.ticks_ms()
            value = self._heart_sensor.read()
            self._graph.set_value(value)

        # keep watching rotary encoder press event
        event = self._rotary_encoder.get_event()
        if event == EncoderEvent.PRESS:
            self._view.remove_all()
            self._heart_sensor.stop()
            self._state_machine.set(State.Main_Menu)
