from hardware import HeartSensor, EncoderEvent
from common import print_log
import time


class HR:
    def __init__(self, hardware, state_machine, view, ibi_calculator):
        # hardware
        self._heart_sensor = hardware.heart_sensor
        self._rotary_encoder = hardware.rotary_encoder
        # ui
        self._view = view
        self._graph = None
        self._text_heading = None
        self._text_info = None
        # other
        self.hr = 0
        self._hr_avg_count = 3
        self._ibi_calculator = ibi_calculator
        self._state_machine = state_machine

        self._last_graph_update_time = time.ticks_ms()

    def enter(self):
        print_log("HR: enter")
        self._state_machine.set(self._measure_enter)

    def _measure_enter(self):
        # ui
        self._text_heading = self._view.add_text(text="HR Measure", y=0, invert=True)
        self._graph = self._view.add_graph(y=14, h=64 - 14 - 12, show_box=False)
        self._text_info = self._view.add_text(text="--- BPM", y=64 - 8)

        # other
        self._heart_sensor.set_timer_irq()
        self._ibi_calculator.reinit()
        self._state_machine.set(self._measure)

    def _measure(self):
        self._ibi_calculator.run()
        if self._ibi_calculator.ibi_fifo.has_data():
            ibi = self._ibi_calculator.ibi_fifo.get()
            hr = int(60000 / ibi)
            self._text_info.set_text(str(hr) + " BPM")
            if self._heart_sensor.sensor_fifo.count() > 500:
                print("Warning: sensor fifo is filling too fast")

        # update graph
        if time.ticks_ms() - self._last_graph_update_time > 40:
            self._last_graph_update_time = time.ticks_ms()
            value = self._heart_sensor.read()
            self._graph.set_value(value)

        # rotary encoder press event
        event = self._rotary_encoder.get_event()
        if event == EncoderEvent.PRESS:
            self._view.deactivate_all()
            self._heart_sensor.unset_timer_irq()
            self._state_machine.set(self._state_machine.main_menu.enter)
