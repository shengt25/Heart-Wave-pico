from hardware import Display, RotaryEncoder, HeartSensor
from data_processing import IBICalculator
from view import View
from main_menu import MainMenu
from hr import HREntry, HRMeasure
from hrv import HRVMeasure, HRVResultCheck, HRVResultShow
from kubios import KubiosSend
from history import HistoryList, HistoryData
from state import State


class StateMachine:
    # enum for each module and state
    MODULE_MENU = 0
    MODULE_HR = 1
    MODULE_HRV = 2
    MODULE_KUBIOS = 3
    MODULE_HISTORY = 4

    STATE_MENU = 5
    STATE_HR_ENTRY = 6
    STATE_HR_MEASURE = 7
    STATE_HRV_MEASURE = 8
    STATE_HRV_RESULT_CHECK = 9
    STATE_HRV_RESULT_SHOW = 10
    STATE_KUBIOS_SEND = 11
    STATE_HISTORY_LIST = 12
    STATE_HISTORY_DATA = 13

    # map the state code to each class
    state_dict = {STATE_MENU: MainMenu,
                  STATE_HR_ENTRY: HREntry,
                  STATE_HR_MEASURE: HRMeasure,
                  STATE_HRV_MEASURE: HRVMeasure,
                  STATE_HRV_RESULT_CHECK: HRVResultCheck,
                  STATE_HRV_RESULT_SHOW: HRVResultShow,
                  STATE_HISTORY_LIST: HistoryList,
                  STATE_HISTORY_DATA: HistoryData,
                  STATE_KUBIOS_SEND: KubiosSend}

    def __init__(self):
        self.display = Display(refresh_rate=40)
        self.rotary_encoder = RotaryEncoder(btn_debounce_ms=50)
        self.heart_sensor = HeartSensor(pin=26, sampling_rate=250)
        self.ibi_calculator = IBICalculator(self.heart_sensor.get_sensor_fifo(), self.heart_sensor.get_sampling_rate())
        self.view = View(self.display)
        self.current_module = self.MODULE_MENU
        self._args = None
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

    def set(self, state_code, args=None):
        # store additional arguments for the next state.enter()
        if args is not None and not isinstance(args, list):
            raise ValueError("args must be a list")
        try:
            self._args = args
            state = self.state_dict[state_code]
            self._state = self.get_state(state)
            self._switched = True
        except KeyError:
            raise ValueError("Invalid state code to switch to")

    def run(self):
        if self._switched:
            self._switched = False
            self._state.enter(self._args)
            return
            # skip loop() in the first run, because state can be changed again during enter()
        self._state.loop()
        self.view.refresh()

    def set_module(self, module):
        """The module is used to determine the next state accordingly,
        it's set up only by the main menu"""
        self.current_module = module
