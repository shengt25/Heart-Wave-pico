class History:
    def __init__(self, hardware, state_machine, debug=False):
        # init hardware
        self._display = hardware.display
        self._rotary_encoder = hardware.rotary_encoder
        # init ui
        self._graph_view = None
        self._state_machine = state_machine
        self._debug = debug

    def enter(self):
        print("History enter") if self._debug else None
        self._rotary_encoder.set_rotate_irq()
        self._display.fill(0)

    def execute(self):
        print("HistoryState")
