from hardware import HeartSensor, EncoderEvent
from common import GlobalSettings,print_log
import time
from data_processing import peak_detector
from array import array

class HR:
    def __init__(self, hardware, state_machine, view):
        # hardware
        self._heart_sensor = hardware.heart_sensor
        self._rotary_encoder = hardware.rotary_encoder
        # ui
        self._view = view
        self._graph = None
        self._textview_heading = None
        self._textview_info = None
        # other
        self._state_machine = state_machine
        
        #data processing
        self.time_sample = 0
        self.value_array = array('i')

    def enter(self):
        print_log("HR: enter")
        self._state_machine.set(self._measure_enter)

    def _measure_enter(self):
        # ui
        self._textview_heading = self._view.add_text(text="HR Measure", y=0, invert=True)
        self._graph = self._view.add_graph(y=14, h=64 - 14 - 12, show_box=False)
        self._textview_info = self._view.add_text(text="--- BPM", y=64 - 8)

        # other
        self._heart_sensor.set_timer_irq()
        self._state_machine.set(self._measure)

    def _measure(self):
        
        # data process
        while self._heart_sensor.sensor_fifo.has_data():
            compute_value = self._heart_sensor.sensor_fifo.get()
            self.value_array.append(compute_value)
            self.time_sample+=1
            if self.time_sample%750 == 0:
                peak_detector(self.value_array,3,GlobalSettings.heart_sensor_sampling_rate)
                self.value_array = array('i')
            
        # data graph
        value = self._heart_sensor.read()
        self._graph.set_value(value)

        # rotary encoder press event
        event = self._rotary_encoder.get_event()
        if event == EncoderEvent.PRESS:
            self._view.deactivate_all()
            self._heart_sensor.unset_timer_irq()
            self._state_machine.set(self._state_machine.main_menu.enter)
