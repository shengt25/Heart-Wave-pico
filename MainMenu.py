import time
from hardware import display_init, RotaryEncoder, Event, Value
from ui import TextView, OptionView, GraphView
from common import State


class MainMenu:
    def __init__(self, display, rotary_encoder, debug=False):
        # init hardware
        self.display = display
        self.rotary_encoder = rotary_encoder
        # init ui
        self.option_view = OptionView(self.display, ["HR Measure",
                                                     "HRV Analysis",
                                                     "Kubios Analysis",
                                                     "History"])
        self.debug = debug

    def init(self):
        print("MainMenu enter") if self.debug else None
        self.display.fill(0)
        self.option_view.init()
        self.option_view.show()

    def _select_menu(self):
        status, value = self.rotary_encoder.on_rotate()
        if status == Event.EVENT:
            if value == Value.CLOCKWISE:
                self.option_view.next()
            elif value == Value.COUNTER_CLOCKWISE:
                self.option_view.previous()
            # self.option_list.show() # no need when auto show enabled

    def _next(self):
        status, value = self.rotary_encoder.on_press()
        if status == Event.EVENT and value == Value.PRESS:
            selected_index = self.option_view.get_selected_index()
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
        return self._next()
