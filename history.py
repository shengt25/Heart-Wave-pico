from utils import print_log
import os
from utils import GlobalSettings
import json
from state import State
from save_system import load_history_list, load_history_data


class HistoryList(State):
    def __init__(self, state_machine):
        super().__init__(state_machine)
        self._selection = 0  # to preserve selected index, resume when exit and re-enter
        self._page = 0  # to preserve page index, resume when exit and re-enter
        self._history_dates = None
        # ui
        self._listview_history_list = None

    def enter(self, args):
        # load data
        self._history_dates = ["back"]
        files = load_history_list()
        self._history_dates.extend(files)
        # ui
        self._view.add_text(text="History", y=0, invert=True)
        self._listview_history_list = self._view.add_list(items=self._history_dates, y=14, max_text_length=15)
        self._listview_history_list.set_page(self._page)
        self._listview_history_list.set_selection(self._selection)
        # rotary encoder
        self._rotary_encoder.set_rotate_irq(items_count=len(self._history_dates), position=self._selection)

    def loop(self):
        event = self._rotary_encoder.get_event()
        if event == self._rotary_encoder.EVENT_ROTATE:
            self._listview_history_list.set_selection(self._rotary_encoder.get_position())
        elif event == self._rotary_encoder.EVENT_PRESS:
            # save current page and selection for switching back
            self._selection = self._rotary_encoder.get_position()
            self._page = self._listview_history_list.get_page()
            if self._selection == 0:
                # back to main menu
                # set selection and page to 0
                self._selection = 0
                self._page = 0
                self._rotary_encoder.unset_rotate_irq()
                self._view.remove_all()
                self._state_machine.set(state_code=self._state_machine.STATE_MENU)
            else:
                # save selection and page
                self._selection = self._rotary_encoder.get_position()
                self._page = self._listview_history_list.get_page()
                self._rotary_encoder.unset_rotate_irq()
                self._view.remove(self._listview_history_list)
                # set state to show data, and pass the filename
                self._state_machine.set(state_code=self._state_machine.STATE_HISTORY_DATA,
                                        args=[self._history_dates[self._selection]])


class HistoryData(State):
    def __init__(self, state_machine):
        super().__init__(state_machine)
        # ui
        self._listview_history_data = None

    def enter(self, args):
        # pass filename
        json_data = load_history_data(args[0])
        data = ["Date: " + str(json_data["DATE"][:8]), "Time: " + str(json_data["DATE"][9:17]),
                "HR: " + str(json_data["HR"]), "PPI: " + str(json_data["PPI"]),
                "RMSSD: " + str(json_data["RMSSD"]), "SDNN: " + str(json_data["SDNN"])]
        if "SNS" in json_data:
            data.extend(["SNS: " + str(json_data["SNS"]), "PNS: " + str(json_data["PNS"])])
        self._listview_history_data = self._view.add_list(items=data, y=14, read_only=True)
        self._rotary_encoder.set_rotate_irq(items_count=self._listview_history_data.get_page_max() + 1)
        # page index starts from 0, so add 1 to be the count

    def loop(self):
        event = self._rotary_encoder.get_event()
        if event == self._rotary_encoder.EVENT_ROTATE:
            self._listview_history_data.set_page(self._rotary_encoder.get_position())
        elif event == self._rotary_encoder.EVENT_PRESS:
            # back to list, remove listview, unset rotate encoder irq
            self._view.remove(self._listview_history_data)
            self._rotary_encoder.unset_rotate_irq()
            self._state_machine.set(state_code=self._state_machine.STATE_HISTORY_LIST)
