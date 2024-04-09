import array
from icon import icon_hr, icon_hrv, icon_kubios, icon_history
import framebuf


class ViewType:
    TEXT = 0
    LIST = 1
    GRAPH = 2
    MENU = 3


class View:
    def __init__(self, display, debug=False):
        self._display = display
        self.width = display.width
        self.height = display.height
        self._debug = debug
        self._text_views = []
        self._list_views = []
        self._graph_views = []
        self.updated = False
        self.framebuffer = framebuf.FrameBuffer(bytearray(display.width * display.height // 8), display.width,
                                                display.height, framebuf.MONO_HLSB)
        self._main_menu_view = None

    def set_text_view(self):
        for text_view in self._text_views:
            if not text_view.is_using:
                text_view.load()
                return text_view
        # no available text view, create a new one
        new_text_view = TextView(self)
        new_text_view.load()
        self._text_views.append(new_text_view)
        return new_text_view

    def set_list_view(self):
        for list_view in self._list_views:
            if not list_view.is_using:
                list_view.load()
                return list_view
        # no available list view, create a new one
        new_list_view = ListView(self)
        new_list_view.load()
        self._list_views.append(new_list_view)
        return new_list_view

    def set_graph_view(self):
        for graph_view in self._graph_views:
            if not graph_view.is_using:
                graph_view.load()
                return graph_view
        # no available graph view, create a new one
        new_graph_view = GraphView(self)
        new_graph_view.load()
        self._graph_views.append(new_graph_view)
        return new_graph_view

    def set_menu_view(self):
        if self._main_menu_view is not None:
            self._main_menu_view.load()
            return self._main_menu_view
        # no available menu view, create a new one
        self._main_menu_view = MenuView(self)
        self._main_menu_view.load()
        return self._main_menu_view

    def update(self):
        if self.updated:
            self._display.update(self.framebuffer)
            self.updated = False

    def unload_all(self):
        for text_view in self._text_views:
            text_view.unload()
        for list_view in self._list_views:
            list_view.unload()
        for graph_view in self._graph_views:
            graph_view.unload()
        if self._main_menu_view is not None:
            self._main_menu_view.unload()
        self.clear()

    def clear(self):
        self.framebuffer.fill(0)


class TextView:
    def __init__(self, view, x: int = 0, y: int = 0, text=""):
        self._x = x
        self._y = y
        self._text = text
        self._view = view
        self._framebuffer = view.framebuffer
        self.is_using = False

    def load(self):
        self.is_using = True
        self._update_framebuffer()

    def unload(self):
        self.is_using = False

    def _update_framebuffer(self):
        self._framebuffer.text(self._text, self._x, self._y)
        self._view.updated = True

    def update(self, text=None, x=None, y=None):
        if not self.is_using:
            raise Exception("Trying updating unused TextView")
        if text is not None:
            self._text = text
        if x is not None:
            self._x = x
        if y is not None:
            self._y = y
        self.load()  # reload after update


class ListView:
    def __init__(self, view, items: list[str] = None, spacing=2, y=0, debug=False):
        self._view = view
        self._framebuffer = view.framebuffer
        self._items = items
        self._y = y
        self._spacing = spacing
        self._font_size = 7
        self._debug = debug
        self._arrow_h = array.array('H', [3, 0, 0, 5, 6, 5])
        self._arrow_l = array.array('H', [0, 0, 6, 0, 3, 5])
        self.is_using = False

        # dynamic init
        self._selected_index = None
        self._view_index_range = None
        self._slider_height = None

    def load(self):
        self.is_using = True
        if self._items is None:
            self._items = []
        self._selected_index = 0
        row_per_page = self._get_view_range()
        self._view_index_range = (0, row_per_page - 1)  # set init view range to page one
        self._slider_height = int(row_per_page / len(self._items) * 35 + 5)
        print(f"view range: {self._view_index_range}") if self._debug else None
        self._update_framebuffer()

    def unload(self):
        self.is_using = False

    def _get_view_range(self):
        row_per_page = int((self._view.height - self._y) / (self._font_size + self._spacing))
        if row_per_page * (self._font_size + self._spacing) + self._font_size < self._view.height - self._y:
            row_per_page += 1
        print(f"row_per_page: {row_per_page}, items_count: {len(self._items)}") if self._debug else None
        return row_per_page

    def _clear_old(self):
        self._framebuffer.fill_rect(0, self._y, 128, 64, 0)

    def _draw_scroll_bar(self):
        row_per_page = self._get_view_range()
        if row_per_page < len(self._items):  # draw scroll bar when one page is not enough
            view_index_l, view_index_h = self._view_index_range
            slider_y = round(
                view_index_l / (len(self._items) - row_per_page) * (46 - self._slider_height - self._y) + self._y + 9)
            self._framebuffer.line(124, self._y + 9, 124, 54, 1)
            self._framebuffer.fill_rect(123, slider_y, 3, self._slider_height, 1)
            if view_index_l != 0:  # draw arrow when not on first page
                self._framebuffer.poly(121, self._y, self._arrow_h, 1, 1)
            if view_index_l != len(self._items) - row_per_page:  # draw arrow when on last page
                self._framebuffer.poly(121, 58, self._arrow_l, 1, 1)

    def _update_framebuffer(self):
        view_index_l, view_index_h = self._view_index_range
        view_index_h = min(view_index_h, len(self._items) - 1)  # limit the upper bound one page can show
        if self._debug:
            print(f"selected: {self._selected_index}")
        for print_index in range(view_index_l, view_index_h + 1):
            if self._debug:
                print(f"showing index: {print_index} / {len(self._items) - 1}")
            if print_index == self._selected_index:
                self._framebuffer.text(">" + self._items[print_index], 0,
                                       self._y + (print_index - view_index_l) * (
                                               self._font_size + self._spacing))
            else:
                self._framebuffer.text(" " + self._items[print_index], 0,
                                       self._y + (print_index - view_index_l) * (
                                               self._font_size + self._spacing))
        self._draw_scroll_bar()
        self._view.updated = True

    def select_next(self, auto_show=True):
        self._clear_old()
        if self._selected_index + 1 <= len(self._items) - 1:
            self._selected_index += 1
            # scroll page
            view_index_l, view_index_h = self._view_index_range
            if self._selected_index > view_index_h:
                self._view_index_range = (view_index_l + 1, view_index_h + 1)
                print(self._view_index_range) if self._debug else None
                self._update_framebuffer()

    def select_previous(self, auto_show=True):
        self._clear_old()
        if self._selected_index - 1 >= 0:
            self._selected_index -= 1
            # scroll page
            view_index_l, view_index_h = self._view_index_range
            if self._selected_index < view_index_l:
                self._view_index_range = (view_index_l - 1, view_index_h - 1)
                print(self._view_index_range) if self._debug else None
                self._update_framebuffer()

    def get_selected_index(self):
        return self._selected_index

    def update(self, items=None, y=None):
        if items is not None:
            self._items = items
        if y is not None:
            self._y = y
        self.load()  # reload after update


class GraphView:
    def __init__(self, view, box_x=0, box_y=10, box_w=128, box_h=40, speed=1, show_box=False, debug=False):
        # parse parameters
        self._box_x = box_x
        self._box_y = box_y
        self._box_w = box_w
        self._box_h = box_h
        self._show_box = show_box
        self._debug = debug
        self._speed = speed
        # init
        self._view = view
        self._framebuffer = view.framebuffer
        self._range_h_default = 65535
        self._range_l_default = 0
        self._range_update_period = 20
        self.is_using = False

        # dynamic init
        self._x = None
        self._range_h = None
        self._range_l = None
        self._range_h_temp = None
        self._range_l_temp = None
        self._last_x = None
        self._last_y = None

    def load(self):
        self.is_using = True
        self._x = self._box_x + 1
        self._range_h = self._range_h_default
        self._range_l = self._range_l_default
        self._range_h_temp = self._range_h_default
        self._range_l_temp = self._range_l_default
        self._last_x = -1
        self._last_y = -1
        # not updating framebuffer automatically, because of no data

    def unload(self):
        self.is_using = False

    def _g_clean_ahead(self):
        # function usage: fill_rect(x, y, w, h, color)
        # if: within the box's width
        # else: exceed the box's width: clean the part inside box, take the rest at the start and clean it
        clean_width = int(self._box_w / 4)
        if self._x + clean_width < self._box_x + self._box_w:
            self._framebuffer.fill_rect(self._x + 1, self._box_y + 1, clean_width - 2, self._box_h - 2, 0)
        else:
            exceed_width = self._x + clean_width - self._box_w - self._box_x
            self._framebuffer.fill_rect(self._x + 1, self._box_y + 1, clean_width - exceed_width - 2,
                                        self._box_h - 2,
                                        0)
            self._framebuffer.fill_rect(self._box_x + 1, self._box_y + 1, exceed_width - 2, self._box_h - 2,
                                        0)

    def _g_update_range(self, value):
        # shirk the range
        if self._range_h_temp < value < self._range_h_default:
            self._range_h_temp = value
        if self._range_l_temp > value > self._range_l_default:
            self._range_l_temp = value

    def _g_set_new_range(self):
        self._range_h = self._range_h_temp
        self._range_l = self._range_l_temp
        # reset the temp range
        self._range_h_temp = self._range_l_default
        self._range_l_temp = self._range_h_default

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
        self._framebuffer.rect(self._box_x, self._box_y, self._box_w, self._box_h, 1)

    def _update_framebuffer(self, value):
        # loop x inside the box
        if self._box_x + 1 < self._x + self._speed < self._box_x + self._box_w - 1:
            self._x += self._speed
        else:
            # bring x to the start and reset last point
            self._x = self._box_x + 1
            self._last_x = -1
            self._last_y = -1

        if self._x % self._range_update_period == 0:
            self._g_set_new_range()

        # before drawing, data processing
        self._g_update_range(value)
        self._g_clean_ahead()
        normalized_value = self._g_normalize(value)
        y = self._g_convert_coord(normalized_value)
        # limit y inside the box
        if y > self._box_y + self._box_h - 2:
            y = self._box_y + self._box_h - 2
        elif y <= self._box_y:
            y = self._box_y + 1
        # draw, ignore drawing with invalid last point
        if self._last_x != -1 and self._last_y != -1:
            self._framebuffer.line(self._last_x, self._last_y, self._x, y, 1)
        if self._show_box:
            self._g_draw_box()
        # update last point
        self._last_x = self._x
        self._last_y = y
        self._view.updated = True

        if self._debug:
            print(f"raw: {value}, norm:{normalized_value}, xy: {self._x}, {y}")
            print(f"upper_t: {self._range_h_temp}, lower_t: {self._range_l_temp}")
            print(f"upper: {self._range_h}, lower: {self._range_l}\n")
        self._view.updated = True

    def update(self, value):
        self._update_framebuffer(value)


class MenuView:
    def __init__(self, view, debug=False):
        self._icon_buf_hr = framebuf.FrameBuffer(icon_hr, 32, 32, framebuf.MONO_VLSB)
        self._icon_buf_hrv = framebuf.FrameBuffer(icon_hrv, 32, 32, framebuf.MONO_VLSB)
        self._icon_buf_kubios = framebuf.FrameBuffer(icon_kubios, 32, 32, framebuf.MONO_VLSB)
        self._icon_buf_history = framebuf.FrameBuffer(icon_hr, 32, 32, framebuf.MONO_VLSB)

        self._view = view
        self._framebuffer = view.framebuffer
        self._debug = debug
        self._selected_index = 0
        self.is_using = False

    def load(self):
        self.is_using = True
        self._update_framebuffer()

    def unload(self):
        self.is_using = False

    def _get_menu_content(self, index):
        if index == 0:
            return self._icon_buf_hr, "HR Measure"
        elif index == 1:
            return self._icon_buf_hrv, "HRV Analysis"
        elif index == 2:
            return self._icon_buf_kubios, "Kubios Analysis"
        elif index == 3:
            return self._icon_buf_history, "History"
        else:
            return None

    def _draw_dot(self):
        self._framebuffer.rect(42, 61, 2, 2, 1)
        self._framebuffer.rect(54, 61, 2, 2, 1)
        self._framebuffer.rect(66, 61, 2, 2, 1)
        self._framebuffer.rect(78, 61, 2, 2, 1)
        x = 42 + self._selected_index * 12
        self._framebuffer.fill_rect(x, 60, 4, 4, 1)

    def _update_framebuffer(self):
        icon_buf, text = self._get_menu_content(self._selected_index)
        self._framebuffer.fill(0)
        self._framebuffer.text(text, int((128 - len(text) * 8) / 2), 38, 1)
        self._framebuffer.blit(icon_buf, int((128 - 32) / 2), 0)
        self._draw_dot()
        self._view.updated = True

    def select_next(self):
        if self._selected_index + 1 <= 3:
            self._selected_index += 1
            self._update_framebuffer()
            print(f"select next: {self._selected_index}")
        else:
            print(f"select max: {self._selected_index}")

    def select_previous(self):
        if self._selected_index - 1 >= 0:
            self._selected_index -= 1
            self._update_framebuffer()
            print(f"select previous: {self._selected_index}")
        else:
            print(f"select min: {self._selected_index}")

    def get_selected_index(self):
        return self._selected_index
