from hardware import Display, RotaryEncoder, HeartSensor
from data_processing import IBICalculator, HRVCalculator
from view import View
from main_menu import MainMenu
from hr import HREntry
from hrv import HRVEntry
from kubios import KubiosEntry
# from history import HistoryEntry
from state import State


class StateMachine:
    def __init__(self):
        self.display = Display(refresh_rate=40)
        self.rotary_encoder = RotaryEncoder(btn_debounce_ms=50)
        self.heart_sensor = HeartSensor(pin=26, sampling_rate=250)
        self.ibi_calculator = IBICalculator(self.heart_sensor.get_sensor_fifo(), self.heart_sensor.get_sampling_rate())
        self.hrv_calculator = HRVCalculator()
        self.view = View(self.display)
        self._args = None
        self._kwargs = None
        self._states = {}
        self._state = None
        self._switched = False

    def get_state(self, state_class):
        if state_class not in self._states:
            self._states[state_class] = state_class(self)  # pass self to state class, to give property access
        return self._states[state_class]

    def preload_states(self, state_class_list):
        for state_class in state_class_list:
            self.get_state(state_class)

    def set(self, state, *args, **kwargs):
        # Store additional arguments for the next state.enter()
        self._args = args
        self._kwargs = kwargs
        if isinstance(state, int):
            state = self._map_entry_state(state)
        self._state = self.get_state(state)
        self._switched = True

    def run(self):
        if self._switched:
            self._switched = False
            if not self._args and not self._kwargs:
                self._state.enter()
                return
            if self._args and not self._kwargs:
                self._state.enter(*self._args)
                return
            if self._kwargs and not self._args:
                self._state.enter(**self._kwargs)
                return
            if self._args and self._kwargs:
                self._state.enter(*self._args, **self._kwargs)
                return
            # skip loop() in the first run, because state can be changed again during enter()
        self._state.loop()
        self.view.refresh()

    def _map_entry_state(self, state_int):
        if state_int == State.Main_Menu:
            return MainMenu
        elif state_int == State.HR_Entry:
            return HREntry
        elif state_int == State.HRV_Entry:
            return HRVEntry
        elif state_int == State.Kubios_Entry:
            return KubiosEntry
        # elif state_int == State.History_Entry:
        #     return HistoryEntry
        else:

            raise ValueError("Invalid state int")
