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


class StateMachine:
    def __init__(self, hardware, view):
        self._state = None
        self._view = view
        self._hardware = hardware
        self.main_menu = MainMenu(hardware, self, view)
        self.hr = HR(hardware, self, view)
        self.hrv = HRV(hardware, self, view)
        self.kubios = Kubios(hardware, self, view)
        self.history = History(hardware, self, view)

    def set(self, state):
        self._state = state

    def run(self):
        self._state()


if __name__ == "__main__":
    # settings:
    GlobalSettings.print_log = True
    GlobalSettings.display_max_refresh_rate = 60
    GlobalSettings.heart_sensor_pin = 26
    GlobalSettings.heart_sensor_sampling_rate = 250
    GlobalSettings.graph_refresh_rate = 30

    hardware = Hardware()
    view = View(hardware.display)
    state_machine = StateMachine(hardware, view)
    state_machine.set(state_machine.main_menu.enter)

    while True:
        state_machine.run()
        view.refresh()
