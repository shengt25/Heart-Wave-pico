import time
from hardware import EncoderEvent
from utils import print_log, pico_rom_stat
from hr import HREntry
from hrv import HRVEntry, HRVMeasure
from state import State


class KubiosEntry(HREntry):
    def __init__(self, state_machine):
        super().__init__(state_machine)
        self._hr_update_interval = 5  # number of sample needed to update the HR display
        self._start_threshold = 200  # threshold that triggers measurement automatically when finger is placed
        self._heading_text = "Kubios Analysis"
        self._hr_text = "-- BPM  30s"

    def exit(self):
        self._state_machine.set(KubiosMeasure)


class KubiosMeasure(HRVMeasure):
    def exit(self):
        self._state_machine.set(KubiosResult, self._ibi_list)


class KubiosResult(State):
    def __init__(self, state_machine, ibi_list):
        super().__init__(state_machine)

    def enter(self):
        print("Kubios Result")
        # todo implement Kubios result

    def loop(self):
        event = self._rotary_encoder.get_event()
        if event == EncoderEvent.PRESS:
            self._state_machine.set(State.Main_Menu)
