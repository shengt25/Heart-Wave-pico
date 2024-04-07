import time

from MainMenu import MainMenu
from HR import HR
from HRV import HRV
from Kubios import Kubios
from History import History
from hardware import Hardware
from ui import View
from common import State


class StateMachine:
    def __init__(self):
        self._state = None
        self.main_menu = None
        self.hr = None
        self.hrv = None
        self.kubios = None
        self.history = None

    def init_states(self, main_menu, hr, hrv, kubios, history):
        self.main_menu = main_menu
        self.hr = hr
        self.hrv = hrv
        self.kubios = kubios
        self.history = history

    def set(self, state):
        self._state = state

    def run(self):
        time.sleep_ms(1)
        self._state()


if __name__ == "__main__":
    debug = True

    hardware = Hardware()
    state_machine = StateMachine()
    state_machine.init_states(MainMenu(hardware, state_machine, debug=True),
                              HR(hardware, state_machine, debug=True),
                              HRV(hardware, state_machine, debug=True),
                              Kubios(hardware, state_machine, debug=True),
                              History(hardware, state_machine, debug=True))

    state_machine.set(state_machine.main_menu.enter)

    while True:
        state_machine.run()
