from utils import print_log
import time
from state import State


class HREntry(State):
    """Entry point for any measurement: HR, HRV, Kubios"""

    def __init__(self, state_machine):
        super().__init__(state_machine)
        # settings
        self._start_threshold = 200  # threshold that triggers the start of measurement when finger is placed

    def enter(self, args):
        # take arguments: heading_text, hr_text
        heading_text, hr_text = args[0], args[1]
        self._view.add_text(text="Put finger on ", y=14, vid="info1")
        self._view.add_text(text="sensor to start", y=24, vid="info2")
        self._view.add_text(text=heading_text, y=0, invert=True, vid="heading")  # 'invert' gives it a background
        self._view.add_text(text=hr_text, y=64 - 8, vid="hr")

    def loop(self):
        # check finger on sensor
        value = self._heart_sensor.read()
        if value < self._start_threshold:
            # keep heading and hr text, remove the rest
            self._view.remove_by_id("info1")
            self._view.remove_by_id("info2")
            # HR -> HR Measure, HRV
            if self._state_machine.current_module == self._state_machine.MODULE_HR:
                self._state_machine.set(state_code=self._state_machine.STATE_HR_MEASURE)
            # HRV -> HRV Measure
            elif self._state_machine.current_module == self._state_machine.MODULE_HRV:
                self._state_machine.set(state_code=self._state_machine.STATE_HRV_MEASURE)
            # Kubios -> HRV Measure (same state, but module code will distinguish)
            elif self._state_machine.current_module == self._state_machine.MODULE_KUBIOS:
                self._state_machine.set(state_code=self._state_machine.STATE_HRV_MEASURE)
            return
        # handle rotary encoder event: press
        event = self._rotary_encoder.get_event()
        if event == self._rotary_encoder.EVENT_PRESS:
            # keep heading and hr text, remove the rest
            self._view.remove_by_id("info1")
            self._view.remove_by_id("info2")
            self._state_machine.set(state_code=self._state_machine.STATE_MENU)
            return


class HRMeasure(State):
    def __init__(self, state_machine):
        super().__init__(state_machine)
        # data
        self._last_graph_update_time = time.ticks_ms()
        self._hr_display_list = []
        self._ibi_fifo = self._ibi_calculator.get_ibi_fifo()
        # placeholders for ui
        self._textview_hr = None
        self._graphview = None
        # settings
        self._hr_update_interval = 5  # number of sample

    def enter(self, args):
        # re-init data
        self._last_graph_update_time = time.ticks_ms()
        self._hr_display_list.clear()
        self._ibi_calculator.reinit()  # remember to reinit the calculator before use every time
        # ui
        # assigned to self.xxx, no need to select_by_id in loop()
        self._textview_hr = self._view.select_by_id("hr")
        self._graphview = self._view.add_graph(y=14, h=64 - 14 - 12, vid="graph")
        self._heart_sensor.start()  # start lastly to reduce the chance of data piling, maybe not needed

    def loop(self):
        self._ibi_calculator.run()  # keep calling calculator: sensor_fifo -> ibi_fifo
        # monitor and get data from ibi fifo, calculate hr and put into list
        if self._ibi_fifo.has_data():
            ibi = self._ibi_fifo.get()
            self._hr_display_list.append(int(60000 / ibi))

        # for every _hr_update_interval samples, calculate the median value and update the HR display
        if len(self._hr_display_list) >= self._hr_update_interval:
            median_hr = sorted(self._hr_display_list)[len(self._hr_display_list) // 2]
            # use set_text method to update the text, view (screen) will auto refresh
            self._textview_hr.set_text(str(median_hr) + " BPM")
            self._hr_display_list.clear()

        # update graph, reads value from sensor directly. no need to use sensor_fifo
        # maximum update interval 40ms, to save the CPU time
        if time.ticks_diff(time.ticks_ms(), self._last_graph_update_time) > 40:
            self._last_graph_update_time = time.ticks_ms()
            value = self._heart_sensor.read()
            self._graphview.set_value(value)

        # keep watching rotary encoder press event
        event = self._rotary_encoder.get_event()
        if event == self._rotary_encoder.EVENT_PRESS:
            self._heart_sensor.stop()
            self._view.remove_all()
            self._state_machine.set(state_code=self._state_machine.STATE_MENU)
            return
