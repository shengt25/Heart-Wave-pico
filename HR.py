from hardware import Event, Value, HeartSensor
from common import State
from ui import GraphView


class HR:
    def __init__(self, display, rotary_encoder, heart_sensor, debug=False):
        # init hardware
        self.display = display
        self.rotary_encoder = rotary_encoder
        self.heart_sensor = heart_sensor
        # init ui
        self.graph_view = GraphView(self.display)
        self.debug = debug

    def init(self):
        print("HR enter") if self.debug else None
        self.display.fill(0)
        self.graph_view.init()

    def _next(self):
        status, value = self.rotary_encoder.on_press()
        if status == Event.EVENT and value == Value.PRESS:
            return State.MENU
        else:
            return State.HR

    def execute(self):
        status, value = self.heart_sensor.read()
        self.graph_view.show(value)
        return self._next()
