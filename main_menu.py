import time
from hardware import EncoderEvent
from state import State
from utils import print_log


class MainMenu(State):
    def __init__(self, state_machine):
        super().__init__(state_machine)
        # init
        # ui placeholder
        self._menu = None
        # other
        self._selection = 0  # for preserve selected index

    def enter(self):
        print_log("MainMenu enter")
        self._rotary_encoder.set_rotate_irq(items_count=4, position=self._selection, loop_mode=False)
        self._menu = self._view.add_menu()
        self._menu.set_selection(self._selection)  # resume selected index from last time

    def loop(self):
        event = self._rotary_encoder.get_event()
        if event == EncoderEvent.ROTATE:
            self._selection = self._rotary_encoder.get_position()
            self._menu.set_selection(self._selection)
        elif event == EncoderEvent.PRESS:
            if self._selection == 0:
                self._state_machine.set(State.HR_Entry)
            elif self._selection == 1:
                self._state_machine.set(State.HRV_Entry)
            elif self._selection == 2:
                self._state_machine.set(State.Kubios_Entry)
            elif self._selection == 3:
                self._state_machine.set(State.History_Entry)
            else:
                raise ValueError("Invalid selection index")
            self._rotary_encoder.unset_rotate_irq()
            self._view.remove_all()
