from hardware import HeartSensor, ENCODER_EVENT
from common import State
from ui import GraphView


class HR:
    def __init__(self, hardware, state_machine, debug=False):
        # init hardware
        self._display = hardware.display
        self._heart_sensor = hardware.heart_sensor
        self._rotary_encoder = hardware.rotary_encoder
        # init ui
        self._graph_view = GraphView(self._display)
        # other
        self._state_machine = state_machine
        self._debug = debug

    def enter(self):
        print("HR enter") if self._debug else None
        self._display.fill(0)
        self._graph_view.re_init()
        self._state_machine.set(self._run)

    def _run(self):
        event, value = self._heart_sensor.read()
        self._graph_view.show(value)

        # rotary encoder press event
        event = self._rotary_encoder.get_event()
        if event == ENCODER_EVENT.PRESS:
            self._state_machine.set(self._exit)

    def _exit(self):
        self._state_machine.set(self._state_machine.main_menu.enter)
