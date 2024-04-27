from common import print_log
from hardware import EncoderEvent


class History:
    def __init__(self, hardware, state_machine, view):
        # hardware
        self._display = hardware.display
        self._rotary_encoder = hardware.rotary_encoder
        # ui
        self._view = view
        self._listview_history_list = None
        self._textview_history_heading = None
        self._textview_data_heading = None
        self._textview_data_hr = None
        self._textview_data_hrv = None
        self._textview_data_sdnn = None
        self._textview_data_rmssd = None
        # other
        self._history_list = None
        self._data = None
        self._selection = 0
        self._page = 0
        self._state_machine = state_machine

    def _load_history_list(self):
        # dummy data
        self._history_list = ["back", "2021-01-01", "2021-01-02", "2021-01-03", "2021-01-04", "2021-01-05",
                              "2021-01-06", "2021-01-07", "2021-01-08", "2021-01-09", "2021-01-10"]

    def _load_data(self):
        # dummy data
        self._data = {"date": "2021-01-01", "hr": "60", "hrv": "10", "sdnn": "20", "rmssd": "30"}

    def enter(self):
        print_log("History: enter")
        self._load_history_list()
        self._state_machine.set(self._show_history_enter)

    def _show_history_enter(self):
        # ui
        self._textview_history_heading = self._view.add_text(text="History", y=0, invert=True)
        self._listview_history_list = self._view.add_list(items=self._history_list, y=14)
        self._listview_history_list.set_page(self._page)
        self._listview_history_list.set_selection(self._selection)

        # other
        self._rotary_encoder.set_rotate_irq(items_count=len(self._history_list), position=self._selection,
                                            loop_mode=True)
        self._state_machine.set(self._show_history_handler)

    def _show_history_handler(self):
        event = self._rotary_encoder.get_event()
        if event == EncoderEvent.ROTATE:
            self._selection = self._rotary_encoder.get_position()
            self._listview_history_list.set_selection(self._selection)

        elif event == EncoderEvent.PRESS:
            self._page = self._listview_history_list.get_page()  # save current page for switching back
            if self._selection == 0:
                self._rotary_encoder.unset_rotate_irq()
                self._view.deactivate_all()
                self._state_machine.set(self._state_machine.main_menu.enter)
            else:
                self._rotary_encoder.unset_rotate_irq()
                self._view.deactivate_all()
                self._state_machine.set(self._show_data_enter)

    def _show_data_enter(self):
        print_log("History: history data")
        self._load_data()

        # ui
        self._textview_data_heading = self._view.add_text(text=self._data["date"], y=0, invert=True)
        self._textview_data_hr = self._view.add_text(text="HR: " + self._data["hr"], y=12)
        self._textview_data_hrv = self._view.add_text(text="HRV: " + self._data["hrv"], y=22)
        self._textview_data_sdnn = self._view.add_text(text="SDNN: " + self._data["sdnn"], y=32)
        self._textview_data_rmssd = self._view.add_text(text="RMSSD: " + self._data["rmssd"], y=42)

        # other
        self._state_machine.set(self._show_data_handler)

    def _show_data_handler(self):
        event = self._rotary_encoder.get_event()
        if event == EncoderEvent.PRESS:
            self._view.deactivate_all()
            self._state_machine.set(self._show_history_enter)

    def _exit(self):
        # clean up resources and unset irq
        self._view.deactivate_all()
        self._rotary_encoder.unset_rotate_irq()
        self._display.clear()
        self._selection = 0  # reset selected index
        self._page = 0  # reset view index start
        self._state_machine.set(self._state_machine.main_menu.enter)
