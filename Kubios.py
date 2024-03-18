class Kubios:
    def __init__(self, display, rotary_encoder):
        # init hardware
        self.display = display
        self.rotary_encoder = rotary_encoder
        # init ui
        self.graph_view = None

    def execute(self):
        print("KubiosState")