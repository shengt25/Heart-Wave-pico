import time

from MainMenu import MainMenu
from HR import HR
from HRV import HRV
from Kubios import Kubios
from History import History
from hardware import Hardware
from ui import View
from common import State
from lib.piotimer import Piotimer


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
        self._state()


if __name__ == "__main__":
    debug = True

    hardware = Hardware()
    state_machine = StateMachine()
    view = View(hardware.display, debug=debug)


    def display_timer_callback(tid):
        view.show()


    # display_timer = Piotimer(freq=30, callback=display_timer_callback)

    state_machine.init_states(MainMenu(hardware, state_machine, view, debug=True),
                              HR(hardware, state_machine, view, debug=True),
                              HRV(hardware, state_machine, debug=True),
                              Kubios(hardware, state_machine, debug=True),
                              History(hardware, state_machine, debug=True))

    state_machine.set(state_machine.main_menu.enter)

    while True:
        # xtime.sleep_ms(1)
        state_machine.run()
        view.show()
