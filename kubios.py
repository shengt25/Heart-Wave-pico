import time
from utils import print_log, dict2show_items
from state import State
from save_system import save_system


class KubiosAnalysis(State):
    def __init__(self, state_machine):
        super().__init__(state_machine)
        self.time0 = None
        self.ibi_list = []

    def enter(self, args):
        self.ibi_list = args[0]
        self.time0 = time.ticks_ms()
        self._view.add_text(text="Sending data...", y=14, vid="text_kubios_send")

    def loop(self):
        # make sure text is displayed
        if time.ticks_ms() - self.time0 > 200:
            self._state_machine.set(state_code=self._state_machine.STATE_KUBIOS_SEND, args=[self.ibi_list])


class KubiosSend(State):
    def __init__(self, state_machine):
        super().__init__(state_machine)
        self._ibi_list = []
        self._listview_retry = None

    def enter(self, args):
        self._ibi_list = args[0]
        success, result = self._state_machine.data_network.get_kubios_analysis(self._ibi_list)
        if success:
            # success, save and goto show result
            save_system(result)
            self._state_machine.set(state_code=self._state_machine.STATE_SHOW_RESULT, args=[dict2show_items(result)])
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
