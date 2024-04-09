from hardware import HeartSensor, ENCODER_EVENT
from common import State
from ui import GraphView


class HR:
    def __init__(self, hardware, state_machine, view, debug=False):
        # init hardware
        self._heart_sensor = hardware.heart_sensor
        self._rotary_encoder = hardware.rotary_encoder
        # init ui
        self._view = view
        self._graph = None
        self._text_heading = None
        self._text_hr = None
        self._text_exit = None

        # other
        self._state_machine = state_machine
        self._debug = debug

    def enter(self):
        print("HR enter") if self._debug else None

        self._view.clear()
        self._graph = self._view.set_graph_view()
        self._text_heading = self._view.set_text_view()
        self._text_hr = self._view.set_text_view()
        self._text_exit = self._view.set_text_view()

        self._text_heading.update("Heart Rate", 0, 0)
        self._text_hr.update("0", 0, 10)
        self._text_exit.update("Press to exit", 0, 20)

        self._state_machine.set(self._run)

    def _run(self):
        event, value = self._heart_sensor.read()
        # self._graph.set(value)
        # rotary encoder press event
        event = self._rotary_encoder.get_event()
        if event == ENCODER_EVENT.PRESS:
            self._state_machine.set(self._exit)

    def _exit(self):
        self._view.unload_all()
        self._state_machine.set(self._state_machine.main_menu.enter)
