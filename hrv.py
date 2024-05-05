import time
from utils import print_log, get_datetime, dict2show_items
from save_system import save_system
import machine
from state import State
from data_processing import calculate_hrv


class AdvanceMeasure(State):
    def __init__(self, state_machine):
        super().__init__(state_machine)
        # data
        self._last_graph_update_time = None
        self._last_countdown_update_time = None
        self._hr = None
        self._hr_display_list = []
        self._ibi_list = []
        self._time_left = None
        self._ibi_fifo = self._ibi_calculator.get_ibi_fifo()  # ref of ibi fifo
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
        self._hr_display_list.clear()
        self._ibi_list.clear()
        self._time_left = 30
        self._ibi_calculator.reinit()
        # ui elements
        self._graphview = self._view.add_graph(y=14, h=64 - 14 - 12)
        self._textview_hr = self._view.select_by_id("text_hr")  # this element was created in HREntry state
        self._heart_sensor.start()

    def loop(self):
        self._ibi_calculator.run()  # keep calling calculator
        # monitor and get data from ibi fifo, calculate hr and put into list
        if self._ibi_fifo.has_data():
            ibi = self._ibi_fifo.get()
            self._hr_display_list.append(int(60000 / ibi))
            self._ibi_list.append(ibi)

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

        # counting down and update hr text(timer started)
        if self._last_countdown_update_time == -1:
            if len(self._ibi_list) > 2:  # start countdown timer when 2 ibi data received
                self._last_countdown_update_time = time.ticks_ms()
        else:
            if self._time_left > 0 and time.ticks_diff(time.ticks_ms(), self._last_countdown_update_time) >= 1000:
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
            self._state_machine.set(state_code=self._state_machine.STATE_ADVANCE_MEASURE_CHECK, args=[self._ibi_list])
            return

        # rotary encoder event: press
        event = self._rotary_encoder.get_event()
        if event == self._rotary_encoder.EVENT_PRESS:
            self._heart_sensor.stop()
            self._view.remove_all()
            self._state_machine.set(state_code=self._state_machine.STATE_MENU)
            return


class AdvanceMeasureCheck(State):
    def __init__(self, state_machine):
        super().__init__(state_machine)
        self._listview_retry = None

    def enter(self, args):
        ibi_list = args[0]
        if len(ibi_list) > 10:
            # data ok, go to hrv or kubios
            if self._state_machine.current_module == self._state_machine.MODULE_HRV:
                self._state_machine.set(state_code=self._state_machine.STATE_HRV_ANALYSIS, args=[ibi_list])
            elif self._state_machine.current_module == self._state_machine.MODULE_KUBIOS:
                self._state_machine.set(state_code=self._state_machine.STATE_KUBIOS_ANALYSIS, args=[ibi_list])
            else:
                raise ValueError("Invalid module code")
            return
        else:
            self._view.add_text(text="Not enough data", y=14, vid="text_check_error")
            self._listview_retry = self._view.add_list(items=["Try again", "Exit"], y=34)
            self._rotary_encoder.set_rotate_irq(items_count=2, position=0)

    def loop(self):
        """if check not enough, then goes here"""
        event = self._rotary_encoder.get_event()
        if event == self._rotary_encoder.EVENT_ROTATE:
            self._listview_retry.set_selection(self._rotary_encoder.get_position())
        elif event == self._rotary_encoder.EVENT_PRESS:
            self._rotary_encoder.unset_rotate_irq()
            self._view.remove_all()  # main menu needs to be re-created, wait measure also will re-create heading
            if self._rotary_encoder.get_position() == 0:
                self._state_machine.set(state_code=self._state_machine.STATE_WAIT_MEASURE)
            elif self._rotary_encoder.get_position() == 1:
                self._state_machine.set(state_code=self._state_machine.STATE_MENU)
            else:
                raise ValueError("Invalid selection index")


class HRVAnalysis(State):
    def __init__(self, state_machine):
        super().__init__(state_machine)
        self._listview_retry = None

    def enter(self, args):
        ibi_list = args[0]
        hr, ppi, rmssd, sdnn = calculate_hrv(ibi_list)
        # save data
        result = {"DATE": get_datetime(),
                  "HR": str(hr) + "BPM",
                  "PPI": str(ppi) + "ms",
                  "RMSSD": str(rmssd) + "ms",
                  "SDNN": str(sdnn) + "ms"}
        save_system(result)
        show_items = dict2show_items(result)
        # send to mqtt
        mqtt_success = self._state_machine.data_network.mqtt_publish(result)
        if not mqtt_success:
            show_items.extend(["---", "MQTT failed", "Check settings"])
        self._state_machine.set(state_code=self._state_machine.STATE_SHOW_RESULT, args=[show_items])

    def loop(self):
        return
