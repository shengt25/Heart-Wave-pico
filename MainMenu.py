import time
from hardware import init_display, RotaryEncoder, ENCODER_EVENT
from ui import TextView, ListView, GraphView, MenuView
from common import State


class MainMenu:
    def __init__(self, hardware, state_machine, view, debug=False):
        # init hardware
        self._display = hardware.display
        self._rotary_encoder = hardware.rotary_encoder
        # init ui
        self._view = view
        self._menu_view = None
        # other
        self._state_machine = state_machine
        self._debug = debug

    def enter(self):
        print("MainMenu enter") if self._debug else None
        self._menu_view = self._view.set_menu_view()
        self._rotary_encoder.set_rotate_irq()
        self._display.clear()
        self._state_machine.set(self._run)

    def _run(self):
        self._view.show()
        event = self._rotary_encoder.get_event()
        if event == ENCODER_EVENT.CLOCKWISE:
            self._menu_view.select_next()
        elif event == ENCODER_EVENT.COUNTER_CLOCKWISE:
            self._menu_view.select_previous()
        elif event == ENCODER_EVENT.PRESS:
            self._state_machine.set(self._exit)

    def _exit(self):
        self._rotary_encoder.unset_rotate_irq()
        self._view.unload_all()

        selected_index = self._menu_view.get_selected_index()
        if selected_index == 0:
            self._state_machine.set(self._state_machine.hr.enter)
        elif selected_index == 1:
            self._state_machine.set(self._state_machine.hrv.enter)
        elif selected_index == 2:
            self._state_machine.set(self._state_machine.kubios.enter)
        elif selected_index == 3:
            self._state_machine.set(self._state_machine.history.enter)
