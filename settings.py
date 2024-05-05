import time
from utils import print_log, pico_stat, pico_rom_stat
from state import State


class Settings(State):
    def __init__(self, state_machine):
        super().__init__(state_machine)
        self._selection = 0  # to preserve selected index, resume when exit and re-enter
        self._page = 0  # to preserve page index, resume when exit and re-enter
        self._listview_settings_list = None

    def enter(self, args):
        self._view.remove_all()  # clear screen
        self._view.add_text(text="Settings", y=0, invert=True)
        self._listview_settings_list = self._view.add_list(items=["Back", "About", "Debug Info", "Connect Wi-Fi",
                                                                  "Connect MQTT", "???"], y=14)
        self._listview_settings_list.set_page(self._page)
        self._listview_settings_list.set_selection(self._selection)
        self._rotary_encoder.set_rotate_irq(items_count=6, position=self._selection)

    def loop(self):
        event = self._rotary_encoder.get_event()
        if event == self._rotary_encoder.EVENT_ROTATE:
            self._listview_settings_list.set_selection(self._rotary_encoder.get_position())
        elif event == self._rotary_encoder.EVENT_PRESS:
            self._selection = self._rotary_encoder.get_position()
            self._page = self._listview_settings_list.get_page()
            self._rotary_encoder.unset_rotate_irq()
            self._view.remove_all()
            if self._selection == 0:
                self._state_machine.set(state_code=self._state_machine.STATE_MENU)
            elif self._selection == 1:
                self._state_machine.set(state_code=self._state_machine.STATE_SETTINGS_ABOUT)
            elif self._selection == 2:
                self._state_machine.set(state_code=self._state_machine.STATE_SETTINGS_DEBUG_INFO)
            elif self._selection == 3:
                self._state_machine.set(state_code=self._state_machine.STATE_SETTINGS_WIFI)
            elif self._selection == 4:
                self._state_machine.set(state_code=self._state_machine.STATE_SETTINGS_MQTT)
            elif self._selection == 5:
                pass
            else:
                raise ValueError("Invalid selection index")


class SettingsAbout(State):
    def __init__(self, state_machine):
        super().__init__(state_machine)
        self._listview_about = None

    def enter(self, args):
        self._view.remove_all()  # clear screen
        self._view.add_text(text="About", y=0, invert=True)
        show_items = ["[HeartWave Pico]",
                      "Sheng Tai", "Alex Pop", "Vitalii Virronen",
                      "Made by Group3"]
        self._listview_about = self._view.add_list(items=show_items, y=14, read_only=True)

    def loop(self):
        event = self._rotary_encoder.get_event()
        if event == self._rotary_encoder.EVENT_PRESS:
            self._view.remove_all()
            self._state_machine.set(state_code=self._state_machine.STATE_SETTINGS)


class SettingsDebugInfo(State):
    def __init__(self, state_machine):
        super().__init__(state_machine)
        self._listview_info = None

    def enter(self, args):
        self._view.remove_all()  # clear screen
        self._view.add_text(text="Debug Info", y=0, invert=True)
        # system info
        ram_used, ram_free, ram_total, storage_free = pico_stat()
        # network
        if self._data_network.is_wlan_connected():
            wlan_status = "Connected"
            wlan_ip = self._data_network.get_wlan_ip()
        else:
            wlan_status = "Not connected"
            wlan_ip = "IP: N/A"
        if self._data_network.is_mqtt_connected():
            mqtt_connected = "Connected"
            mqtt_broker_ip = self._data_network.get_mqtt_broker_ip()
        else:
            mqtt_connected = "Not connected"
            mqtt_broker_ip = "IP: N/A"
        # state info
        state_count = len(self._state_machine.get_states_info())
        # view info
        active_view, inactive_view = self._view.get_stat()
        show_items = ["[RAM]", f"Used:{ram_used}KB", f"Free:{ram_free}KB", f"Total:{ram_total}KB",
                      "",
                      "[Storage]", f"Free:{storage_free}KB",
                      "",
                      "[Wi-Fi]", wlan_status, wlan_ip,
                      "",
                      "[MQTT]", mqtt_connected, mqtt_broker_ip,
                      "",
                      "[State in RAM]", str(state_count),
                      "",
                      "[View]", f"Active:{len(active_view) + 1}", f"Inactive:{len(inactive_view)}"]
        # active_view plus 1 because the view next line not yet activated
        self._listview_info = self._view.add_list(items=show_items, y=14, read_only=True)
        self._rotary_encoder.set_rotate_irq(items_count=self._listview_info.get_page_max() + 1, position=0)

    def loop(self):
        event = self._rotary_encoder.get_event()
        if event == self._rotary_encoder.EVENT_ROTATE:
            self._listview_info.set_page(self._rotary_encoder.get_position())
        elif event == self._rotary_encoder.EVENT_PRESS:
            self._rotary_encoder.unset_rotate_irq()
            self._view.remove_all()
            self._state_machine.set(state_code=self._state_machine.STATE_SETTINGS)


class SettingsWifi(State):
    def __init__(self, state_machine):
        super().__init__(state_machine)
        self._textview_info = None
        self._textview_ip = None
        self._last_check_time = 0

    def enter(self, args):
        self._view.remove_all()  # clear screen
        self._view.add_text(text="Wi-Fi", y=0, invert=True)
        self._textview_info = self._view.add_text(text="", y=14)
        self._textview_ip = self._view.add_text(text="", y=24)

    def loop(self):
        if time.ticks_diff(time.ticks_ms(), self._last_check_time) > 1000:
            self._last_check_time = time.ticks_ms()
            if self._data_network.is_wlan_connected():
                wlan_status = "Connected"
                wlan_ip = self._data_network.get_wlan_ip()
            else:
                wlan_status = "Connecting..."
                wlan_ip = "IP: N/A"
                self._data_network.connect_wlan()
            self._textview_info.set_text(wlan_status)
            self._textview_ip.set_text(wlan_ip)
        event = self._rotary_encoder.get_event()
        if event == self._rotary_encoder.EVENT_PRESS:
            self._view.remove_all()
            self._state_machine.set(state_code=self._state_machine.STATE_SETTINGS)


class SettingsMqtt(State):
    def __init__(self, state_machine):
        super().__init__(state_machine)
        self._textview_info = None
        self._textview_ip = None

    def enter(self, args):
        self._view.remove_all()  # clear screen
        self._view.add_text(text="MQTT", y=0, invert=True)
        self._textview_info = self._view.add_text(text="", y=14)
        self._textview_ip = self._view.add_text(text="", y=24)
        # try to connect at first run
        if not self._data_network.is_mqtt_connected():
            self._textview_info.set_text("Connecting...")
            self._textview_ip.set_text("IP: N/A")
            self._display.show()
            # force update display directly, because the next line blocks the program!
            self._rotary_encoder.unset_button_irq()  # just in case user press button a lot while sending
            self._data_network.connect_mqtt()
            self._rotary_encoder.set_button_irq()
        # update status
        if not self._data_network.is_mqtt_connected():
            self._textview_info.set_text("Failed")
            self._textview_ip.set_text("IP: N/A")
        else:
            self._textview_info.set_text("Connected")
            self._textview_ip.set_text(self._data_network.get_broker_ip())

    def loop(self):
        event = self._rotary_encoder.get_event()
        if event == self._rotary_encoder.EVENT_PRESS:
            self._view.remove_all()
            self._state_machine.set(state_code=self._state_machine.STATE_SETTINGS)
