import array


class TextView:
    def __init__(self, display, x: int, y: int, text=""):
        self._display = display
        self._x = x
        self._y = y
        self._text = text
        self._changed = None
        self.refresh()

    def refresh(self):
        self._changed = True

    def show(self):
        self._display.text(self._text, self._x, self._y) if self._changed else None

    def clear(self):
        self._display.text(self._text, self._x, self._y, 0)

    def update_text(self, text, auto_update=True):
        self._text = text
        if auto_update:
            self.refresh()


class ListView:
    def __init__(self, display, items: list[str], spacing=2, y=0, debug=False):
        self._display = display
        self._items = items
        self._y = y
        self._spacing = spacing
        self._font_size = 7
        self._debug = debug
        self._arrow_h = array.array('H', [3, 0, 0, 5, 6, 5])
        self._arrow_l = array.array('H', [0, 0, 6, 0, 3, 5])

        # dynamic init
        self._changed = None
        self._selected_index = None
        self._view_index_range = None
        self._slider_height = None
        self.refresh()

    def refresh(self):
        self._changed = True
        self._selected_index = 0
        row_per_page = self._get_view_range()
        self._view_index_range = (0, row_per_page - 1)
        self._slider_height = int(row_per_page / len(self._items) * 35 + 5)
        print(f"view range: {self._view_index_range}") if self._debug else None

    def _get_view_range(self):
        row_per_page = int((self._display.get_height() - self._y) / (self._font_size + self._spacing))
        if row_per_page * (self._font_size + self._spacing) + self._font_size < self._display.get_height() - self._y:
            row_per_page += 1
        print(f"row_per_page: {row_per_page}, items_count: {len(self._items)}") if self._debug else None
        return row_per_page

    def update_items(self, items):
        self._items = items
        self.refresh()

    def _clear_old(self):
        self._display.fill_rect(0, self._y, 128, 64, 0)

    def _draw_scroll_bar(self):
        view_index_l, view_index_h = self._view_index_range
        row_per_page = self._get_view_range()
        slider_y = round(
            view_index_l / (len(self._items) - row_per_page) * (46 - self._slider_height - self._y) + self._y + 9)
        self._display.line(124, self._y + 9, 124, 54, 1)
        self._display.fill_rect(123, slider_y, 3, self._slider_height, 1)
        if view_index_l != 0:  # draw arrow when not on first page
            self._display.poly(121, self._y, self._arrow_h, 1, 1)
        if view_index_l != len(self._items) - row_per_page:  # draw arrow when on last page
            self._display.poly(121, 58, self._arrow_l, 1, 1)

    def show(self):
        if self._changed:
            view_index_l, view_index_h = self._view_index_range
            view_index_h = min(view_index_h, len(self._items) - 1)  # limit the upper bound one page can show
            print(f"selected: {self._selected_index}") if self._debug else None
            for print_index in range(view_index_l, view_index_h + 1):
                print(f"showing index: {print_index} / {len(self._items) - 1}") if self._debug else None
                if print_index == self._selected_index:
                    self._display.text(">" + self._items[print_index], 0,
                                       self._y + (print_index - view_index_l) * (self._font_size + self._spacing))
                else:
                    self._display.text(" " + self._items[print_index], 0,
                                       self._y + (print_index - view_index_l) * (self._font_size + self._spacing))
            row_per_page = self._get_view_range()
            if row_per_page < len(self._items):  # draw scroll bar when one page is not enough
                self._draw_scroll_bar()
            self._display.show()
            self._changed = False

    def select_next(self, auto_show=True):
        self._clear_old()
        if self._selected_index + 1 <= len(self._items) - 1:
            self._selected_index += 1

        view_index_l, view_index_h = self._view_index_range
        if self._selected_index > view_index_h:
            self._view_index_range = (view_index_l + 1, view_index_h + 1)
            print(self._view_index_range) if self._debug else None

        self._changed = True
        if auto_show:
            self.show()

    def select_previous(self, auto_show=True):
        self._clear_old()
        if self._selected_index - 1 >= 0:
            self._selected_index -= 1

        view_index_l, view_index_h = self._view_index_range
        if self._selected_index < view_index_l:
            self._view_index_range = (view_index_l - 1, view_index_h - 1)
            print(self._view_index_range) if self._debug else None

        self._changed = True
        if auto_show:
            self.show()

    def get_selected_index(self):
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
        self._speed = speed
        # init
        self._range_h_default = 36000
        self._range_l_default = 28000
        # dynamic init
        self._x = None
        self._range_h = None
        self._range_l = None
        self._range_h_temp = None
        self._range_l_temp = None
        self._last_x = None
        self._last_y = None
        self.refresh()

    def refresh(self):
        self._x = self._box_x + 1
        self._range_h = self._range_h_default
        self._range_l = self._range_l_default
        self._range_h_temp = self._range_h_default
        self._range_l_temp = self._range_l_default
        self._last_x = -1
        self._last_y = -1

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

    def _g_update_range(self, value, new_period=False):
        if new_period:
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
            self._g_update_range(value, new_period=True)
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


class MainMenuView:
    pass
    # todo: implement the main menu view with icons and text
