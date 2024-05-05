from hardware import Display, RotaryEncoder, HeartSensor
from data_processing import IBICalculator
from view import View
from data_network import DataNetwork
from main_menu import MainMenu
from hr import WaitMeasure, BasicMeasure
from hrv import AdvanceMeasure, AdvanceMeasureCheck, HRVAnalysis
from kubios import KubiosAnalysis
from history import HistoryList, ShowResult


class StateMachine:
    # enum for each module and state
    MODULE_MENU = 0
    MODULE_HR = 1
    MODULE_HRV = 2
    MODULE_KUBIOS = 3
    MODULE_HISTORY = 4
    MODULE_SETTINGS = 5

    STATE_MENU = 6
    STATE_WAIT_MEASURE = 7
    STATE_BASIC_MEASURE = 8
    STATE_ADVANCE_MEASURE = 9
    STATE_ADVANCE_MEASURE_CHECK = 10
    STATE_HRV_ANALYSIS = 11
    STATE_KUBIOS_ANALYSIS = 12
    STATE_HISTORY_LIST = 15
    STATE_SHOW_RESULT = 16
    STATE_SETTINGS = 17
    STATE_SETTINGS_INFO = 18
    STATE_SETTINGS_WIFI = 19
    STATE_SETTINGS_MQTT = 20
    STATE_SETTINGS_ABOUT = 21

    # map the state code to each class
    state_dict = {STATE_MENU: MainMenu,
                  STATE_WAIT_MEASURE: WaitMeasure,
                  STATE_BASIC_MEASURE: BasicMeasure,
                  STATE_ADVANCE_MEASURE: AdvanceMeasure,
                  STATE_ADVANCE_MEASURE_CHECK: AdvanceMeasureCheck,
                  STATE_HRV_ANALYSIS: HRVAnalysis,
                  STATE_KUBIOS_ANALYSIS: KubiosAnalysis,
                  STATE_HISTORY_LIST: HistoryList,
                  STATE_SHOW_RESULT: ShowResult}

    def __init__(self):
        self.display = Display(refresh_rate=40)
        self.rotary_encoder = RotaryEncoder(btn_debounce_ms=50)
        self.heart_sensor = HeartSensor(pin=26, sampling_rate=250)
        self.ibi_calculator = IBICalculator(self.heart_sensor.get_sensor_fifo(), self.heart_sensor.get_sampling_rate())
        self.view = View(self.display)
        self.data_network = DataNetwork()
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
