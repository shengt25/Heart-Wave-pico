from hardware import EncoderEvent
from utils import print_log, pico_rom_stat
import time
from data_processing import HRVCalculator
from save_system import save_system
import machine
import utime
from state import State
from hr import HREntry


class HRVEntry(HREntry):
    def __init__(self, state_machine):
        super().__init__(state_machine)
        self._hr_update_interval = 5  # number of sample needed to update the HR display
        self._start_threshold = 200  # threshold that triggers measurement automatically when finger is placed
        self._heading_text = "HRV Analysis"
        self._hr_text = "-- BPM  30s"

    def loop(self):
        value = self._heart_sensor.read()
        if value < self._start_threshold:
            self._view.remove_by_id("info1")
            self._view.remove_by_id("info2")
            self._state_machine.set(HRVMeasure)

        # keep watching rotary encoder press event
        event = self._rotary_encoder.get_event()
        if event == EncoderEvent.PRESS:
            self._view.remove_by_id("info1")
            self._view.remove_by_id("info2")
            self._state_machine.set(State.Main_Menu)


class HRVMeasure(State):
    def __init__(self, state_machine):
        super().__init__(state_machine)
        # data
        self._last_graph_update_time = time.ticks_ms()
        self._last_countdown_update_time = 0
        self._hr = 0
        self._hr_display_list = []
        self._ibi_list = []
        self._time_left = 30
        self._ibi_fifo = self._ibi_calculator.get_ibi_fifo()
        # ui placeholder
        self._text_hr = None
        self._graph = None
        # settings
        self._hr_update_interval = 5

    def enter(self):
        self._ibi_calculator.reinit()  # ibi_fifo will be cleared inside this method
        self._hr = 0
        self._hr_display_list = []
        self._time_left = 30
        self._ibi_list = []
        self._last_graph_update_time = time.ticks_ms()
        self._last_countdown_update_time = 0
        # set up timer interrupt at last (to reduce the chance of data building up), and set next state to measure
        self._graph = self._view.add_graph(y=14, h=64 - 14 - 12)
        self._text_hr = self._view.select_by_id("hr")
        self._heart_sensor.start()

    def loop(self):
        # this function was assigned to the state machine, and called repeatedly in a loop
        # until entering another state

        self._ibi_calculator.run()  # keep calling calculator
        # monitor and get data from ibi fifo, calculate hr and put into list
        if self._ibi_fifo.has_data():
            ibi = self._ibi_fifo.get()
            self._hr_display_list.append(int(60000 / ibi))
            self._ibi_list.append(ibi)
            # if not started counting down, start it when the first ibi is received
            if self._last_countdown_update_time == 0:
                self._last_countdown_update_time = time.ticks_ms()

        # for every _hr_update_interval samples, calculate the median value and update the HR display
        if len(self._hr_display_list) >= self._hr_update_interval:
            self._hr = sorted(self._hr_display_list)[len(self._hr_display_list) // 2]
            # use set_text method to update the text, view (screen) will auto refresh
            if self._hr == 0:
                self._text_hr.set_text("-- BPM  " + str(self._time_left) + "s")
            else:
                self._text_hr.set_text(str(self._hr) + " BPM  " + str(self._time_left) + "s")
            self._hr_display_list.clear()

        # update graph, it reads current value from sensor directly. no need to use sensor_fifo
        # only update screen every 40ms, to save the CPU time
        if time.ticks_diff(time.ticks_ms(), self._last_graph_update_time) > 40:
            self._last_graph_update_time = time.ticks_ms()
            value = self._heart_sensor.read()
            self._graph.set_value(value)

        # after the timer is started, update and check 30s timer every second
        if (self._last_countdown_update_time != 0 and
                time.ticks_diff(time.ticks_ms(), self._last_countdown_update_time) >= 1000):
            self._time_left -= 1
            self._last_countdown_update_time = time.ticks_ms()

            # update or exit when time is up
            if self._time_left > 0:
                if self._hr == 0:
                    self._text_hr.set_text("-- BPM  " + str(self._time_left) + "s")
                else:
                    self._text_hr.set_text(str(self._hr) + " BPM  " + str(self._time_left) + "s")
            else:
                # finished measuring, remove all ui elements except for heading, stop heart sensor and go to next state
                self._view.remove(self._graph)
                self._view.remove(self._text_hr)
                self._heart_sensor.stop()
                self.exit()  # entry point to next state

        # keep watching rotary encoder press event, if pressed during measuring, exit to main menu
        event = self._rotary_encoder.get_event()
        if event == EncoderEvent.PRESS:
            # remove all ui elements, stop heart sensor, and exit to main menu
            self._view.remove_all()
            self._heart_sensor.stop()
            self._state_machine.set(State.Main_Menu)

    def exit(self):
        """This state creates an entry point to next state,
        making kubios module able to easily inherit HRV class and override this method."""
        self._state_machine.set(HRVResult, self._ibi_list)


class HRVResult(State):
    def __init__(self, state_machine, ibi_list):
        super().__init__(state_machine)
        self._ibi_list = ibi_list

    def enter(self):
        # todo
        # calculating result
        HRV_Calculator = HRVCalculator(self._ibi_list)
        hr, ppi, rmssd, sdnn = HRV_Calculator._calculate_results()

        # create new list elements
        self._view.add_list(items=["HR: " + str(hr) + " BPM",
                                   "PPI: " + str(ppi) + " ms",
                                   "RMSSD: " + str(rmssd) + " ms",
                                   "SDNN: " + str(sdnn) + " ms"], y=14, read_only=True)

        # time initialization
        rtc = machine.RTC()
        year, month, day, second, hour, minute, _, _ = rtc.datetime()
        date = "{:02d}.{:02d}.{} {:02d}:{:02d}:{:02d}".format(day, month, year, hour, minute, second)
        results = {
            "DATE": date,
            "HR": hr,
            "PPI": ppi,
            "RMSSD": rmssd,
            "SDNN": sdnn}

        save_system(results)

        print(f"Free storage: {pico_rom_stat()} KB")

    def loop(self):
        # keep watching rotary encoder press event
        event = self._rotary_encoder.get_event()
        if event == EncoderEvent.PRESS:
            # remove all ui elements and exit to main menu
            self._view.remove_all()
            self._state_machine.set(State.Main_Menu)
