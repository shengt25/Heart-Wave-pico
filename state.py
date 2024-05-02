"""
State is a base class for all states.

Every state class must have the following methods:
- enter: called when the state is entered
- loop: called repeatedly until the state is changed

Setting next state:
- If next state is within the same file, use self._state_machine.set(StateName),
  where StateName is the class name of the next state
- If next state is in another file and is XXXEntry state, use self._state_machine.set(State.StateName),
  where StateName is the class name of the next state. StateName here is an int, enum-like
  The reason for this is to avoid circular import
"""


class State:
    Main_Menu = 0
    HR_Entry = 1
    HRV_Entry = 2
    Kubios_Entry = 3
    History_Entry = 4

    def __init__(self, state_machine):
        self._state_machine = state_machine
        self._display = state_machine.display
        self._rotary_encoder = state_machine.rotary_encoder
        self._heart_sensor = state_machine.heart_sensor
        self._ibi_calculator = state_machine.ibi_calculator
        self._view = state_machine.view

    def enter(self):
        raise NotImplementedError("This method must be defined and overridden")

    def loop(self):
        raise NotImplementedError("This method must be defined and overridden")
