import time
from hardware import init_display, RotaryEncoder, Event, Value
from ui import TextView, ListView, GraphView
from common import State


class MainMenu:
    def __init__(self, display, rotary_encoder, debug=False):
        # init hardware
        self.display = display
        self.rotary_encoder = rotary_encoder
        # init ui
        self.list_view = ListView(self.display, ["HR Measure",
                                                   "HRV Analysis",
                                                   "Kubios Analysis",
                                                   "History"], debug=debug)
        self.debug = debug

    def enter(self):
        print("MainMenu enter") if self.debug else None
        self.display.fill(0)
        self.list_view.refresh()
        self.list_view.show()

    def _select_menu(self):
        event, value = self.rotary_encoder.on_rotate()
        if event == Event.EVENT:
            if value == Value.CLOCKWISE:
                self.list_view.select_next()
            elif value == Value.COUNTER_CLOCKWISE:
                self.list_view.select_previous()
            # self.option_list.show() # no need when auto show enabled

    def _next_state(self):
        event, value = self.rotary_encoder.on_press()
        if event == Event.EVENT and value == Value.PRESS:
            selected_index = self.list_view.get_selected_index()
            if selected_index == 0:
                return State.HR
            elif selected_index == 1:
                return State.HRV
            elif selected_index == 2:
                return State.KUBIOS
            elif selected_index == 3:
                return State.HISTORY
            else:
                print("Error: invalid index")
                return State.MENU
        else:
            return State.MENU

    def execute(self):
        self._select_menu()
        return self._next_state()
