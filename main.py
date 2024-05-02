from view import View
from utils import GlobalSettings
from state_machine import StateMachine
from state import State

if __name__ == "__main__":
    # settings:
    GlobalSettings.print_log = False
    GlobalSettings.nr_files = 3
    GlobalSettings.save_directory = "Saved_Values"

    state_machine = StateMachine()
    state_machine.set(State.Main_Menu)  # set the initial state
    while True:
        state_machine.run()
