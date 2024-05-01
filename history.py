from utils import print_log
from hardware import EncoderEvent
import os
from utils import GlobalSettings
import json
"""
1. _state_xxx_init
   1.1 initialize variables, create ui elements, set up interrupt/timer, etc
   1.2 goto to _state_xxx immediately
2. _state_xxx_loop
   1.1 during loop, check for event: keep looping, or exit
   1.2 before leave, remember to remove unneeded ui elements, interrupt/timer etc"""


class History:
    def __init__(self, hardware, state_machine, view):
        # hardware
        self._display = hardware.display
        self._rotary_encoder = hardware.rotary_encoder
        # ui
        self._view = view
        self._list_history_list = None
        self._text_heading = None

        # other
        self._history_dates = None
        self._history_data = None
        self._selection = 0
        self._page = 0
        self._state_machine = state_machine

    def enter(self):
        print_log("History: enter")
        self._text_heading = self._view.add_text(text="History", y=0, invert=True)
        self._selection = 0  # reset selected index
        self._page = 0  # reset view index start
        self._state_machine.set(self._state_show_list_init)

    def _load_history_list(self):
        # The first item is always "back", append dates after it
        self._history_dates = ["back"]
        files = os.listdir(GlobalSettings.save_directory + "/")
        self._history_dates.extend(files)
        

    def _load_data(self):
        # data is defined: date, time, HR, PPI, RMSSD, SDNN, SNS, PNS
        path = GlobalSettings.save_directory + "/"+ self._history_dates[self._selection]
        with open(path,'r') as file:
            json_data = json.load(file)
        self._history_data = [str(json_data["DATE"]),"0",str(json_data["HR"]),str(json_data["PPI"]),str(json_data["RMSSD"]),str(json_data["SDNN"]),"0","0"]

    def _state_show_list_init(self):
        # load data
        self._load_history_list()
        # create ui elements
        self._list_history_list = self._view.add_list(items=self._history_dates, y=14)
        self._list_history_list.set_page(self._page)
        self._list_history_list.set_selection(self._selection)
        # other
        self._rotary_encoder.set_rotate_irq(items_count=len(self._history_dates), position=self._selection,
                                            loop_mode=False)
        self._state_machine.set(self._state_show_list_loop)

    def _state_show_list_loop(self):
        event = self._rotary_encoder.get_event()
        if event == EncoderEvent.ROTATE:
            self._selection = self._rotary_encoder.get_position()
            self._list_history_list.set_selection(self._selection)
        elif event == EncoderEvent.PRESS:
            self._page = self._list_history_list.get_page()  # save current page for switching back
            if self._selection == 0:
                self._rotary_encoder.unset_rotate_irq()
                self._view.remove_all()
                self._state_machine.set(self._state_machine.main_menu.enter)
            else:
                self._rotary_encoder.unset_rotate_irq()
                self._list_history_list.remove()
                self._state_machine.set(self._state_show_data_init)

    def _state_show_data_init(self):
        # load data
        self._load_data()
        # create ui elements
        self._list_history_list = self._view.add_list(items=self._history_data, y=14, read_only=True)
        # other
        self._rotary_encoder.set_rotate_irq(items_count=self._list_history_list.get_max_page() + 1)
        self._state_machine.set(self._state_show_data_loop)

    def _state_show_data_loop(self):
        event = self._rotary_encoder.get_event()
        if event == EncoderEvent.ROTATE:
            self._list_history_list.set_page(self._rotary_encoder.get_position())
        elif event == EncoderEvent.PRESS:
            # back to list, remove listview, unset rotate encoder irq
            self._list_history_list.remove()
            self._rotary_encoder.unset_rotate_irq()
            self._state_machine.set(self._state_show_list_init)
