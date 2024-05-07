from utils import GlobalSettings, load_settings
from state_machine import StateMachine
from save_system import check_home_dir

if __name__ == "__main__":
    # load settings:
    load_settings("settings.json")
    GlobalSettings.print_log = False
    # init state machine
    state_machine = StateMachine()
    # connect wlan
    if GlobalSettings.wifi_auto_connect:
        state_machine.data_network.connect_wlan()
    # start from main menu
    state_machine.set(state_code=state_machine.STATE_MENU)
    # check for save directory
    check_home_dir()
    while True:
        state_machine.run()
