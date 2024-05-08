from utils import print_log
from utils import GlobalSettings
from state import State
from save_system import load_history_list, load_history_data


class ShowHistory(State):
    def __init__(self, state_machine):
        super().__init__(state_machine)
        self._selection = 0  # to preserve selected index, resume when exit and re-enter
        self._page = 0  # to preserve page index, resume when exit and re-enter
        self._history_dates = []
        # ui
        self._listview_history_list = None

    def enter(self, args):
        # load data
        self._history_dates.clear()
        self._history_dates.append("Back")
        files = load_history_list()
        self._history_dates.extend(files)
        # ui
        self._view.add_text(text="History", x=0, y=0, invert=True)
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
                # set state to show data, and pass the data
                data = load_history_data(self._history_dates[self._selection])
                show_items = dict2show_items(data, show_datetime=True)
                self._state_machine.set(state_code=self._state_machine.STATE_SHOW_RESULT,
                                        args=[show_items])


class ShowResult(State):
    def __init__(self, state_machine):
        super().__init__(state_machine)
        self._listview_result = None

    def enter(self, args):
        show_items = args[0]
        self._listview_result = self._view.add_list(items=show_items, y=14, read_only=True)
        if self._listview_result.need_scrollbar():
            self._rotary_encoder.set_rotate_irq(items_count=self._listview_result.get_page_max() + 1, position=0)

    def loop(self):
        # keep watching rotary encoder press event
        event = self._rotary_encoder.get_event()
        if event == self._rotary_encoder.EVENT_ROTATE:
            self._listview_result.set_page(self._rotary_encoder.get_position())
        if event == self._rotary_encoder.EVENT_PRESS:
            self._rotary_encoder.unset_rotate_irq()
            # from measurement, go to main menu
            if (self._state_machine.current_module == self._state_machine.MODULE_HRV or
                    self._state_machine.current_module == self._state_machine.MODULE_KUBIOS):
                self._state_machine.set(state_code=self._state_machine.STATE_MENU)
                self._view.remove_all()
            # from history, go back to history list
            elif self._state_machine.current_module == self._state_machine.MODULE_HISTORY:
                self._view.remove(self._listview_result)
                self._state_machine.set(state_code=self._state_machine.STATE_SHOW_HISTORY)
            else:
                raise ValueError("Undefined result showing module")


def dict2show_items(dict_data, show_datetime=False):
    list_data = []
    # history data: date time first
    if show_datetime:
        list_data = ["Date:" + str(dict_data["DATE"][:8]),
                     "Time:" + str(dict_data["DATE"][9:17])]
    # normal data: in the middle
    list_data.extend(["HR:" + str(dict_data["HR"]),
                      "IBI:" + str(dict_data["IBI"]),
                      "RMSSD:" + str(dict_data["RMSSD"]),
                      "SDNN:" + str(dict_data["SDNN"])])
    # kubios data: at the end
    if "SNS" in dict_data:
        list_data.extend(["SNS:" + str(dict_data["SNS"]),
                          "PNS:" + str(dict_data["PNS"]),
                          "Stress:" + str(dict_data["STRESS"])])
    # compare with local calculation when done kubios, for testing purpose
    if "HR_LOCAL" in dict_data:
        list_data.extend(["",
                          "[local result]",
                          "HR:" + str(dict_data["HR_LOCAL"]),
                          "IBI:" + str(dict_data["IBI_LOCAL"]),
                          "RMSSD:" + str(dict_data["RMSSD_LOCAL"]),
                          "SDNN:" + str(dict_data["SDNN_LOCAL"])])

    return list_data
