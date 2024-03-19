import time
from hardware import init_display, RotaryEncoder, EventTypes
from ui import TextView, ListView, GraphView, MenuView
from common import State


class MainMenu:
    def __init__(self, display, event_manager, debug=False):
        # init hardware
        self._display = display
        self._event_manager = event_manager
        # init ui
        self._menu_view = MenuView(self._display, debug=debug)
        self._debug = debug

    def enter(self):
        print("MainMenu enter") if self._debug else None
        self._display.fill(0)
        self._menu_view.re_init()
        self._menu_view.show()

    def _select_menu(self):
        if self._event_manager.pop(EventTypes.ENCODER_CLOCKWISE):
            self._menu_view.select_next()
        elif self._event_manager.pop(EventTypes.ENCODER_COUNTER_CLOCKWISE):
            self._menu_view.select_previous()

    def _next_state(self):
        if self._event_manager.pop(EventTypes.ENCODER_PRESS):
            selected_index = self._menu_view.get_selected_index()
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
