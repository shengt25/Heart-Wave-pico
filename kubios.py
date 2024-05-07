import time
from utils import print_log, dict2show_items
from state import State
from save_system import save_system


class KubiosAnalysis(State):
    def __init__(self, state_machine):
        super().__init__(state_machine)
        self._ibi_list = []
        self._listview_retry = None

    def enter(self, args):
        self._ibi_list = args[0]
        self._view.add_text(text="Sending data...", y=14, vid="text_kubios_send")
        self._display.show()  # force update display directly, because the next line blocks the program!
        print_log("Sending data...")
        self._rotary_encoder.unset_button_irq()  # just in case user press button a lot while sending
        kubios_success, result = self._state_machine.data_network.get_kubios_analysis(self._ibi_list)
        self._rotary_encoder.set_button_irq()  # resume after process done
        print_log("Result received")
        if kubios_success:
            # success, save and goto show result
            save_system(result)
            show_items = dict2show_items(result)
            # send to mqtt
            mqtt_success = self._state_machine.data_network.mqtt_publish(result)
            if not mqtt_success:
                show_items.extend(["---", "MQTT failed", "Check settings"])
            self._state_machine.set(state_code=self._state_machine.STATE_SHOW_RESULT, args=[show_items])
            self._view.remove_by_id("text_kubios_send")
            return
        else:
            # failed, retry or show HRV result
            self._rotary_encoder.set_rotate_irq(items_count=2, position=0)
            self._view.select_by_id("text_kubios_send").set_text("Failed sending")
            self._listview_retry = self._view.add_list(items=["Try again", "Show HRV result"], y=34)

    def loop(self):
        # send failed, retry or show HRV result
        event = self._rotary_encoder.get_event()
        if event == self._rotary_encoder.EVENT_ROTATE:
            self._listview_retry.set_selection(self._rotary_encoder.get_position())
        if event == self._rotary_encoder.EVENT_PRESS:
            self._state_machine.rotary_encoder.unset_rotate_irq()
            self._view.remove_by_id("text_kubios_send")
            self._view.remove(self._listview_retry)
            if self._rotary_encoder.get_position() == 0:
                self._state_machine.set(state_code=self._state_machine.STATE_KUBIOS_ANALYSIS, args=[self._ibi_list])
            elif self._rotary_encoder.get_position() == 1:
                self._state_machine.set(state_code=self._state_machine.STATE_HRV_ANALYSIS, args=[self._ibi_list])
            else:
                raise ValueError("Invalid selection index")
