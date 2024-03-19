import time
from hardware import init_display, RotaryEncoder, EventTypes
from ui import TextView, ListView, GraphView
from common import State


class MainMenu:
    def __init__(self, display, rotary_encoder, event_manager, debug=False):
        # init hardware
        self._display = display
        self._rotary_encoder = rotary_encoder
        self._event_manager = event_manager
        # init ui
        self._list_view = ListView(self._display, ["HR Measure",
                                                   "HRV Analysis",
                                                   "Kubios Analysis",
                                                   "History"], debug=debug)
        self._debug = debug

    def enter(self):
        print("MainMenu enter") if self._debug else None
        self._display.fill(0)
        self._list_view.re_init()
        self._list_view.show()

    def _select_menu(self):
        if self._event_manager.pop(EventTypes.ENCODER_CLOCKWISE):
            self._list_view.select_next()
        elif self._event_manager.pop(EventTypes.ENCODER_COUNTER_CLOCKWISE):
            self._list_view.select_previous()

    def _next_state(self):
        if self._event_manager.pop(EventTypes.ENCODER_PRESS):
            selected_index = self._list_view.get_selected_index()
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
