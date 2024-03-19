import time
from HR import HR
from HRV import HRV
from MainMenu import MainMenu
from Kubios import Kubios
from History import History
from hardware import init_display, RotaryEncoder, HeartSensor
from common import State


class StateManager:
    def __init__(self, states_dict):
        self.states_dict = states_dict

        # init whole system
        self._current_state_code = None
        self._state = None
        self._next_state_code = State.MENU

    def handle_state(self):
        time.sleep_ms(1)
        if self._current_state_code != self._next_state_code:
            self._current_state_code = self._next_state_code
            self._state = self.states_dict[self._next_state_code]
            self._state.enter()
        self._next_state_code = self._state.execute()


if __name__ == "__main__":
    display = init_display()
    rotary_encoder = RotaryEncoder(debounce_ms=2)
    heart_sensor = HeartSensor()

    states_dict = {State.MENU: MainMenu(display, rotary_encoder, debug=True),
                   State.HR: HR(display, rotary_encoder, heart_sensor, debug=True),
                   State.HRV: HRV(display, rotary_encoder),
                   State.KUBIOS: Kubios(display, rotary_encoder),
                   State.HISTORY: History(display, rotary_encoder)}
    state_manager = StateManager(states_dict)

    while True:
        state_manager.handle_state()
