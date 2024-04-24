import time
from hardware import EncoderEvent
from common import print_log


class MainMenu:
    def __init__(self, hardware, state_machine, view):
        # hardware
        self._display = hardware
        self._rotary_encoder = hardware.rotary_encoder
        # ui
        self._view = view
        self._menu_main = None
        # other
        self._selection = 0  # for preserve selected index
        self._state_machine = state_machine

    def enter(self):
        print_log("MainMenu enter")
        self._rotary_encoder.set_rotate_irq(items_count=4, position=self._selection, loop_mode=False)
        self._menu_main = self._view.add_menu()
        self._menu_main.set_selection(self._selection)  # set initial selection to last time
        self._state_machine.set(self._menu_handler)

    def _menu_handler(self):
        event = self._rotary_encoder.get_event()
        if event == EncoderEvent.ROTATE:
            self._selection = self._rotary_encoder.get_position()
            self._menu_main.set_selection(self._selection)
        elif event == EncoderEvent.PRESS:
            if self._selection == 0:
                self._state_machine.set(self._state_machine.hr.enter)
            elif self._selection == 1:
                self._state_machine.set(self._state_machine.hrv.enter)
            elif self._selection == 2:
                self._state_machine.set(self._state_machine.kubios.enter)
            elif self._selection == 3:
                self._state_machine.set(self._state_machine.history.enter)
            else:
                raise ValueError("Invalid selection index")
            self._rotary_encoder.unset_rotate_irq()
            self._view.unload_all()

