from hardware import HeartSensor, EventTypes
from common import State
from ui import GraphView


class HR:
    def __init__(self, display, heart_sensor, event_manager, debug=False):
        # init hardware
        self._display = display
        self._heart_sensor = heart_sensor
        self._event_manager = event_manager
        # init ui
        self._graph_view = GraphView(self._display)
        self._debug = debug

    def enter(self):
        print("HR enter") if self._debug else None
        self._display.fill(0)
        self._graph_view.re_init()

    def _next_state(self):
        if self._event_manager.pop(EventTypes.ENCODER_PRESS):
            return State.MENU
        else:
            return State.HR

    def execute(self):
        event, value = self._heart_sensor.read()
        self._graph_view.show(value)
        return self._next_state()
