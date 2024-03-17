class TextView:
    def __init__(self, display, x: int, y: int, text=""):
        self._display = display
        self._x = x
        self._y = y
        self._text = text

    def show(self):
        self._display.text(self._text, self._x, self._y)

    def clear(self):
        self._display.text(self._text, self._x, self._y, 0)

    def update_text(self, text, auto_show=True):
        self._text = text
        if auto_show:
            self.show()


# todo preliminary implementation
class OptionView:
    def __init__(self, display, options: list[str], spacing=2, x=0, y=0, debug=False):
        self._display = display
        self._options = options
        self._x = x
        self._y = y
        self._spacing = spacing
        self._selected_index = 0
        self._font_size = 6
        self._changed = True
        self._debug = debug

    # todo: boundary and scrolling

    def _clear_old(self):
        if self._debug:
            print(f"clear, id: {self._selected_index}")
        for i, option in enumerate(self._options):
            if i == self._selected_index:
                self._display.text(">" + option, self._x, self._y + i * self._font_size * self._spacing, 0)
            else:
                self._display.text(" " + option, self._x, self._y + i * self._font_size * self._spacing, 0)

    def show(self):
        if self._changed:
            if self._debug:
                print(f"show, id=: {self._selected_index}")
            for i, option in enumerate(self._options):
                if i == self._selected_index:
                    self._display.text(">" + option, self._x, self._y + i * self._font_size * self._spacing)
                else:
                    self._display.text(" " + option, self._x, self._y + i * self._font_size * self._spacing)
            self._display.show()
            self._changed = False

    def next(self, auto_show=True):
        self._clear_old()
        self._selected_index += 1
        self._changed = True
        if auto_show:
            self.show()

    def previous(self, auto_show=True):
        self._clear_old()
        self._selected_index -= 1
        self._changed = True
        if auto_show:
            self.show()

    def enter(self):
        return self._selected_index


class GraphView:
    def __init__(self, display, box_x=0, box_y=10, box_w=128, box_h=40, speed=1, show_box=False, debug=False):
        # parse parameters
        self._display = display
        self._box_x = box_x
        self._box_y = box_y
        self._box_w = box_w
        self._box_h = box_h
        self._show_box = show_box
        self._debug = debug

        # init
        self._x = self._box_x + 1
        self._range_h_default = 36000
        self._range_l_default = 28000
        self._range_h = self._range_h_default
        self._range_l = self._range_l_default
        self._range_h_temp = self._range_h_default
        self._range_l_temp = self._range_l_default
        self._last_x = -1
        self._last_y = -1
        self._speed = speed

    def _g_clean_ahead(self):
        # function usage: fill_rect(x, y, w, h, color)
        # if: within the box's width
        # else: exceed the box's width: clean the part inside box, take the rest at the start and clean it
        clean_width = int(self._box_w / 4)
        if self._x + clean_width < self._box_x + self._box_w:
            self._display.fill_rect(self._x + 1, self._box_y + 1, clean_width - 2, self._box_h - 2, 0)
        else:
            exceed_width = self._x + clean_width - self._box_w - self._box_x
            self._display.fill_rect(self._x + 1, self._box_y + 1, clean_width - exceed_width - 2, self._box_h - 2,
                                    0)
            self._display.fill_rect(self._box_x + 1, self._box_y + 1, exceed_width - 2, self._box_h - 2, 0)

    def _g_update_range(self, value, new=False):
        if new:
            # apply new range every new graph
            self._range_h = self._range_h_temp
            self._range_l = self._range_l_temp
            # reset the temp range
            self._range_h_temp = self._range_l_default
            self._range_l_temp = self._range_h_default
        else:
            # shirk the range
            if self._range_h_temp < value < self._range_h_default:
                self._range_h_temp = value
            if self._range_l_temp > value > self._range_l_default:
                self._range_l_temp = value

    def _g_normalize(self, value):
        # use default when range is negative or zero
        if self._range_h <= self._range_l:
            return int((value - self._range_l) * self._box_h / (self._range_h_default - self._range_l_default))
        else:
            return int((value - self._range_l) * self._box_h / (self._range_h - self._range_l))

    def _g_convert_coord(self, value):
        new_value = - value + self._box_h + self._box_y
        return new_value

    def _g_draw_box(self):
        self._display.rect(self._box_x, self._box_y, self._box_w, self._box_h, 1)

    def _draw_graph(self, value):
        # loop x inside the box
        if self._box_x + 1 < self._x + self._speed < self._box_x + self._box_w - 1:
            self._x += self._speed
            self._g_update_range(value)
        else:
            # bring x to the start and reset last point
            self._x = self._box_x + 1
            self._last_x = -1
            self._last_y = -1
            self._g_update_range(value, new=True)
        # before drawing
        self._g_clean_ahead()
        normalized_value = self._g_normalize(value)
        y = self._g_convert_coord(normalized_value)
        # limit y inside the box
        if y > self._box_y + self._box_h - 2:
            y = self._box_y + self._box_h - 2
        elif y <= self._box_y:
            y = self._box_y + 1
        # ignore drawing with invalid last point
        if self._last_x != -1 and self._last_y != -1:
            self._display.line(self._last_x, self._last_y, self._x, y, 1)
        # update last point
        self._last_x = self._x
        self._last_y = y
        self._display.show()

        if self._debug:
            print(f"raw: {value}, norm:{normalized_value}, xy: {self._x}, {y}")
            print(f"upper_t: {self._range_h_temp}, lower_t: {self._range_l_temp}")
            print(f"upper: {self._range_h}, lower: {self._range_l}\n")

    def show(self, value):
        if self._show_box:
            self._g_draw_box()
        self._draw_graph(value)
