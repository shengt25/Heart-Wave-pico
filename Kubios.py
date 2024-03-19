class Kubios:
    def __init__(self, display, event_manager):
        # init hardware
        self._display = display
        self._event_manager = event_manager
        # init ui
        self._graph_view = None

    def execute(self):
        print("KubiosState")