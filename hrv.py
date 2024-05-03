import time
from utils import print_log, pico_rom_stat
from save_system import save_system
import machine
from state import State
from data_processing import calculate_hrv


class HRVMeasure(State):
    def __init__(self, state_machine):
        super().__init__(state_machine)
        # data
        self._last_graph_update_time = time.ticks_ms()
        self._last_countdown_update_time = -1
        self._hr = 0
        self._hr_display_list = []
        self._ibi_list = []
        self._time_left = 30
        self._ibi_fifo = self._ibi_calculator.get_ibi_fifo()
        # ui placeholder
        self._textview_hr = None
        self._graphview = None
        # settings
        self._hr_update_interval = 5  # number of sample

    def enter(self, args):
        # re-init data
        self._last_graph_update_time = time.ticks_ms()
        self._last_countdown_update_time = -1
        self._hr = 0
        self._hr_display_list = []
        self._ibi_list = []
        self._time_left = 30
        self._ibi_calculator.reinit()
        # ui elements
        self._graphview = self._view.add_graph(y=14, h=64 - 14 - 12)
        self._textview_hr = self._view.select_by_id("hr")
        self._heart_sensor.start()

    def loop(self):
        self._ibi_calculator.run()  # keep calling calculator
        # monitor and get data from ibi fifo, calculate hr and put into list
        if self._ibi_fifo.has_data():
            ibi = self._ibi_fifo.get()
            self._hr_display_list.append(int(60000 / ibi))
            self._ibi_list.append(ibi)
            # if counting down not started, start it when the first ibi is received
            if self._last_countdown_update_time == 0:
                self._last_countdown_update_time = time.ticks_ms()

        # update hr every 5 samples
        if len(self._hr_display_list) >= self._hr_update_interval:
            self._hr = sorted(self._hr_display_list)[len(self._hr_display_list) // 2]
            # use set_text method to update the text, view (screen) will auto refresh
            if self._hr == 0:
                self._textview_hr.set_text("-- BPM  " + str(self._time_left) + "s")
            else:
                self._textview_hr.set_text(str(self._hr) + " BPM  " + str(self._time_left) + "s")
            self._hr_display_list.clear()

        # update graph
        if time.ticks_diff(time.ticks_ms(), self._last_graph_update_time) > 40:
            self._last_graph_update_time = time.ticks_ms()
            value = self._heart_sensor.read()
            self._graphview.set_value(value)

        # counting down and update hr text(timer started when the first ibi is received)
        if (self._last_countdown_update_time != 0 and self._time_left > 0 and
                time.ticks_diff(time.ticks_ms(), self._last_countdown_update_time) >= 1000):
            self._time_left -= 1
            self._last_countdown_update_time = time.ticks_ms()
            if self._hr == 0:
                self._textview_hr.set_text("-- BPM  " + str(self._time_left) + "s")
            else:
                self._textview_hr.set_text(str(self._hr) + " BPM  " + str(self._time_left) + "s")

        # exit when time's up
        if self._time_left <= 0:
            self._heart_sensor.stop()
            self._view.remove(self._graphview)
            self._view.remove(self._textview_hr)
            self._state_machine.set(state_code=self._state_machine.STATE_HRV_RESULT_CHECK, args=[self._ibi_list])
            return

        # rotary encoder event: press
        event = self._rotary_encoder.get_event()
        if event == self._rotary_encoder.EVENT_PRESS:
            self._heart_sensor.stop()
            self._view.remove_all()
            self._state_machine.set(self._state_machine.STATE_MENU)
            return


class HRVResultCheck(State):
    def __init__(self, state_machine):
        super().__init__(state_machine)
        self._listview_retry = None
        self._selection = 0

    def enter(self, args):
        ibi_list = args[0]
        self._selection = 0
        # data not enough, retry or exit
        if len(ibi_list) < 10:
            self._view.add_text(text="Not enough data", y=14, vid="info1")
            self._listview_retry = self._view.add_list(items=["Try again", "Exit"], y=34)
            self._rotary_encoder.set_rotate_irq(items_count=2, position=0)
        else:
            # data ok, show result, or go to kubios
            if self._state_machine.current_module == self._state_machine.MODULE_HRV:
                self._state_machine.set(state_code=self._state_machine.STATE_HRV_RESULT_SHOW, args=[ibi_list])
            elif self._state_machine.current_module == self._state_machine.MODULE_KUBIOS:
                self._state_machine.set(state_code=self._state_machine.STATE_KUBIOS_SEND, args=[ibi_list])

    def loop(self):
        """if check not enough, then goes here"""
        event = self._rotary_encoder.get_event()
        if event == self._rotary_encoder.EVENT_ROTATE:
            self._selection = self._rotary_encoder.get_position()
            self._listview_retry.set_selection(self._selection)
        elif event == self._rotary_encoder.EVENT_PRESS:
            self._rotary_encoder.unset_rotate_irq()
            self._view.remove_all()
            if self._selection == 0:
                self._state_machine.set(state_code=self._state_machine.STATE_HR_ENTRY)
            elif self._selection == 1:

                self._state_machine.set(state_code=self._state_machine.STATE_MENU)
            else:
                raise ValueError("Invalid selection index")


class HRVResultShow(State):
    def __init__(self, state_machine):
        super().__init__(state_machine)

    def enter(self, args):
        # calculating result
        ibi_list = args[0]
        hr, ppi, rmssd, sdnn = calculate_hrv(ibi_list)

        # create new list elements
        self._view.add_list(items=["HR: " + str(hr) + " BPM", "PPI: " + str(ppi) + " ms",
                                   "RMSSD: " + str(rmssd) + " ms", "SDNN: " + str(sdnn) + " ms"],
                            y=14, read_only=True)

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
        if event == self._rotary_encoder.EVENT_PRESS:
            # remove all ui elements and exit to main menu
            self._view.remove_all()
            self._state_machine.set(self._state_machine.STATE_MENU)
