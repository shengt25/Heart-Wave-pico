import time
from hardware import EncoderEvent
from utils import print_log
from hrv import HRV

"""
1. _state_xxx_init
   1.1 initialize variables, create ui elements, set up interrupt/timer, etc
   1.2 goto to _state_xxx immediately (this state run only once)
2. _state_xxx_loop
   1.1 during loop, check for event: keep looping, or exit
   1.2 before leave, remember to remove unneeded ui elements, interrupt/timer etc"""

"""Kubios is inherited from HRV, because the only differences are after measurement."""


class Kubios(HRV):
    def __init__(self, hardware, state_machine, view, ibi_calculator):
        super().__init__(hardware, state_machine, view, ibi_calculator)
        self._heading_text = "Kubios Analysis"

    def _state_after_measure(self):
        """Override the parent method as an entry point"""
        self._state_machine.set(self._state_show_result_init)
        # jump to _state_show_result_init for now

    def _state_send_data_init(self):
        pass

    def _state_send_data_loop(self):
        pass

    def _state_receive_data_init(self):
        pass

    def __state_receive_data_loop(self):
        pass

    def _state_show_result_init(self):
        # todo
        # interpreting result
        hr = 0
        ppi = 0
        rmssd = 0
        sdnn = 0
        sns = 0
        pns = 0

        # create new text elements
        self._list_result = self._view.add_list(items=["HR: " + str(hr),
                                                       "PPI: " + str(ppi),
                                                       "RMSSD: " + str(rmssd),
                                                       "SDNN: " + str(sdnn),
                                                       "SNS: " + str(sns),
                                                       "PNS: " + str(pns)], y=14, read_only=True)
        self._rotary_encoder.set_rotate_irq(items_count=self._list_result.get_max_page() + 1)

        # todo
        # save result

        # goto next state (a loop)
        self._state_machine.set(self._state_show_result_loop)

    def _state_show_result_loop(self):
        event = self._rotary_encoder.get_event()
        if event == EncoderEvent.ROTATE:
            self._list_result.set_page(self._rotary_encoder.get_position())
        elif event == EncoderEvent.PRESS:
            # remove all ui elements, unset rotary encoder interrupt, and exit to main menu
            self._view.remove_all()
            self._rotary_encoder.unset_rotate_irq()
            self._state_machine.set(self._state_machine.main_menu.enter)
