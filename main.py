import time

from main_menu import MainMenu
from hr import HR
from hrv import HRV
from kubios import Kubios
from history import History
from hardware import Hardware
from ui import View
from lib.piotimer import Piotimer
from common import GlobalSettings
from data_processing import IBICalculator


class StateMachine:
    def __init__(self):
        self._state = None
        self._hardware = Hardware(display_refresh_rate=40, sensor_pin=26, sensor_sampling_rate=250)
        self._view = View(self._hardware.display)
        self._ibi_calculator = IBICalculator(self._hardware.heart_sensor.sensor_fifo,
                                             self._hardware.heart_sensor.get_sampling_rate())
        self.main_menu = MainMenu(self._hardware, self, self._view)
        self.hr = HR(self._hardware, self, self._view, self._ibi_calculator)
        self.hrv = HRV(self._hardware, self, self._view)
        self.kubios = Kubios(self._hardware, self, self._view)
        self.history = History(self._hardware, self, self._view)

    def set(self, state):
        self._state = state

    def run(self):
        self._state()
        self._view.refresh()


if __name__ == "__main__":
    # settings:
    GlobalSettings.print_log = False

    state_machine = StateMachine()
    state_machine.set(state_machine.main_menu.enter)

    while True:
        state_machine.run()
