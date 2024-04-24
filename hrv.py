from hardware import HeartSensor
from ui import GraphView


class HRV:
    def __init__(self, hardware, state_machine, view, debug=False):
        # init hardware
        self._display = hardware.display
        self._heart_sensor = hardware.heart_sensor
        self._rotary_encoder = hardware.rotary_encoder
        # init ui
        self._view = view
        self._graph_view = None
        self._state_machine = state_machine
        self._debug = debug

    def enter(self):
        print("HRV enter") if self._debug else None
        self._display.fill(0)
        self._graph_view = self._view.add_graph()
        self._heart_sensor.set_timer_irq()
        self._state_machine.set(self._run)

    def _run(self):
        if self._heart_sensor.sensor_fifo.has_data():
            while self._heart_sensor.sensor_fifo.has_data():
                value = self._heart_sensor.sensor_fifo.get()
                # print(self._heart_sensor.sensor_data.count())
        if self._heart_sensor.display_fifo.has_data():
            while self._heart_sensor.display_fifo.has_data():
                display_value = self._heart_sensor.display_fifo.get()
            self._graph_view.update(display_value)
            print(self._heart_sensor.display_fifo.count())

        event = self._rotary_encoder.get_event()
        if event == ENCODER_EVENT.PRESS:
            self._state_machine.set(self._exit)

    def _exit(self):
        self._state_machine.set(self._state_machine.main_menu.enter)
