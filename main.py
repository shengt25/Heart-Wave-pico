import time
from HR import HR
from HRV import HRV
from MainMenu import MainMenu
from Kubios import Kubios
from History import History
from hardware import display_init, RotaryEncoder, HeartSensor
from common import State


class Manager:
    def __init__(self, states_dict):
        self.states_dict = states_dict

        # init whole system
        self.current_state = State.MENU
        self.state = self.states_dict[State.MENU]
        self.state.init()

    def handle_state(self):
        time.sleep_ms(5)
        next_state = self.state.execute()
        if self.current_state != next_state:
            self.current_state = next_state
            self.state = self.states_dict[next_state]
            self.state.init()


if __name__ == "__main__":
    display = display_init()
    rotary_encoder = RotaryEncoder(debounce_ms=2)
    heart_sensor = HeartSensor()

    states_dict = {State.MENU: MainMenu(display, rotary_encoder, debug=True),
                   State.HR: HR(display, rotary_encoder, heart_sensor, debug=True),
                   State.HRV: HRV(display, rotary_encoder),
                   State.KUBIOS: Kubios(display, rotary_encoder),
                   State.HISTORY: History(display, rotary_encoder)}
    state_manager = Manager(states_dict)

    while True:
        state_manager.handle_state()
