from main_menu import MainMenu
from hr import HR
from hrv import HRV
from kubios import Kubios
from history import History
from hardware import Hardware
from ui import View
from utils import GlobalSettings
from data_processing import IBICalculator


class StateMachine:
    def __init__(self):
        self._state = None
        self._hardware = Hardware(display_refresh_rate=40, sensor_pin=26, sensor_sampling_rate=250)
        self._view = View(self._hardware.display)
        self._ibi_calculator = IBICalculator(self._hardware.heart_sensor.get_sensor_fifo(),
                                             self._hardware.heart_sensor.get_sampling_rate())
        self.main_menu = MainMenu(self._hardware, self, self._view)
        self.hr = HR(self._hardware, self, self._view, self._ibi_calculator)
        self.hrv = HRV(self._hardware, self, self._view, self._ibi_calculator)
        self.kubios = Kubios(self._hardware, self, self._view, self._ibi_calculator)
        self.history = History(self._hardware, self, self._view)

    def set(self, state):
        """Set the state of the state machine."""
        self._state = state

    def run(self):
        """Run the state machine, call this in main loop."""
        self._state()  # do the 'backend' job
        self._view.refresh()  # refresh the display


if __name__ == "__main__":
    # settings:
    GlobalSettings.print_log = False

    state_machine = StateMachine()
    state_machine.set(state_machine.main_menu.enter)  # set the initial state

    while True:
        state_machine.run()
