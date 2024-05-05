import time
from state import State
from utils import print_log


class MainMenu(State):
    def __init__(self, state_machine):
        # take common resources:
        # state_machine, rotary_encoder, heart_sensor, ibi_calculator, view
        super().__init__(state_machine)
        # ui placeholder
        self._menu = None
        # data
        self._selection = 0  # to preserve selected index, resume when exit and re-enter

    def enter(self, args):
        self._rotary_encoder.set_rotate_irq(items_count=4, position=self._selection, loop_mode=False)
        self._menu = self._view.add_menu()
        self._menu.set_selection(self._selection)  # resume selected index from last time

    def loop(self):
        event = self._rotary_encoder.get_event()
        if event == self._rotary_encoder.EVENT_ROTATE:
            self._selection = self._rotary_encoder.get_position()
            self._menu.set_selection(self._selection)
        elif event == self._rotary_encoder.EVENT_PRESS:
            if self._selection == 0:
                self._state_machine.set_module(self._state_machine.MODULE_HR)
                self._state_machine.set(self._state_machine.STATE_WAIT_MEASURE)
            elif self._selection == 1:
                self._state_machine.set_module(self._state_machine.MODULE_HRV)
                self._state_machine.set(self._state_machine.STATE_WAIT_MEASURE)
            elif self._selection == 2:
                self._state_machine.set_module(self._state_machine.MODULE_KUBIOS)
                self._state_machine.set(self._state_machine.STATE_WAIT_MEASURE)
            elif self._selection == 3:
                self._state_machine.set_module(self._state_machine.MODULE_HISTORY)
                self._state_machine.set(self._state_machine.STATE_HISTORY_LIST)
            else:
                raise ValueError("Invalid selection index")
            self._rotary_encoder.unset_rotate_irq()
            self._view.remove_all()
