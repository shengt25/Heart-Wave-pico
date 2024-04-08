class Kubios:
    def __init__(self, hardware, state_machine, debug=False):
        # init hardware
        self._display = hardware.display
        self._heart_sensor = hardware.heart_sensor
        self._rotary_encoder = hardware.rotary_encoder
        # init ui
        self._graph_view = None
        self._state_machine = state_machine
        self._debug = debug

    def enter(self):
        print("Kubios enter") if self._debug else None
        self._rotary_encoder.unset_rotate_irq()
        self._display.fill(0)
        self._graph_view.load()
        self._state_machine.set(self._run)

    def _run(self):
        print("KubiosState")

    def _exit(self):
        self._state_machine.set(self._state_machine.main_menu.enter)
