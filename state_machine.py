from hardware import Display, RotaryEncoder, HeartSensor
from data_processing import IBICalculator
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
        self.view = View(self.display)
        self.args = None
        self.kwargs = None
        self._states = {}
        self._state = None
        self._switched = False

    def get_state(self, state_class, *args, **kwargs):
        if state_class not in self._states:
            self._states[state_class] = state_class(self, *args, **kwargs)
        return self._states[state_class]

    def preload_states(self, state_class_list):
        for state_class in state_class_list:
            self.get_state(state_class)

    def set(self, state, *args, **kwargs):
        # if args or kwargs are provided, store them for the next state.enter()
        if isinstance(state, int):
            state = self._map_entry_state(state)
        self._state = self.get_state(state, *args, **kwargs)
        self._switched = True

    def run(self):
        if self._switched:
            self._state.enter()
            self._switched = False
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
