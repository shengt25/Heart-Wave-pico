from hardware import HeartSensor, EncoderEvent
from common import print_log
import time


class HR:
    def __init__(self, hardware, state_machine, view):
        # hardware
        self._heart_sensor = hardware.heart_sensor
        self._rotary_encoder = hardware.rotary_encoder
        # ui
        self._view = view
        self._graph = None
        self._textview_heading = None
        self._textview_exit = None
        # other
        self._state_machine = state_machine

    def enter(self):
        print_log("HR: enter")
        self._state_machine.set(self._measure_enter)

    def _measure_enter(self):
        print_log("HR: measure")
        # ui
        self._graph = self._view.add_graph()
        self._graph.set_attributes(box_y=10, box_h=40)

        self._textview_heading = self._view.add_text()
        self._textview_heading.set_attributes(y=0, invert=True)
        self._textview_heading.set_text("Heart Rate")

        self._textview_exit = self._view.add_text()
        self._textview_exit.set_attributes(y=64 - 10)
        self._textview_exit.set_text("Press to exit")

        # other
        self._heart_sensor.set_timer_irq()
        self._state_machine.set(self._measure)

    def _measure(self):
        # data process
        while self._heart_sensor.sensor_fifo.has_data():
            compute_value = self._heart_sensor.sensor_fifo.get()

        # data graph
        value = self._heart_sensor.read()
        self._graph.set_value(value)

        # rotary encoder press event
        event = self._rotary_encoder.get_event()
        if event == EncoderEvent.PRESS:
            self._view.deactivate_all()
            self._heart_sensor.unset_timer_irq()
            self._state_machine.set(self._state_machine.main_menu.enter)
