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


def log_print(debug, msg):
    if debug:
        timestamp = time.ticks_ms()
        print(f"{timestamp}: {msg}")


class StateMachine:
    def __init__(self, hardware, view):
        self._state = None
        self.main_menu = MainMenu(hardware, self, view)
        self.hr = HR(hardware, self, view)
        self.hrv = HRV(hardware, self, view)
        self.kubios = Kubios(hardware, self)
        self.history = History(hardware, self)

    def set(self, state):
        self._state = state

    def run(self):
        self._state()


if __name__ == "__main__":
    hardware = Hardware()
    view = View(hardware.display)
    # display_timer = Piotimer(freq=30, callback=display_timer_callback)
    state_machine = StateMachine(hardware, view)
    state_machine.set(state_machine.main_menu.enter)

    while True:
        state_machine.run()
        view.update()
