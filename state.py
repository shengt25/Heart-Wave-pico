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
