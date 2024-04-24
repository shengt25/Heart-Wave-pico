import array
from icon import icon_hr, icon_hrv, icon_kubios, icon_history
import framebuf
from common import print_log, GlobalSettings
import time


class View:
    def __init__(self, display):
        self._display = display
        self.width = display.width
        self.height = display.height
        self._text_views = []
        self._list_views = []
        self._graph_views = []
        self._menu_views = []

    def add_text(self):
        # find available view and return it
        for text_view in self._text_views:
            if not text_view.is_using:
                text_view.load()
                print_log(f"re-use text view, total: {len(self._text_views)}")
                return text_view
        # no available text view, create a new one
        new_text_view = TextView(self._display)
        new_text_view.load()
        self._text_views.append(new_text_view)
        print_log(f"new text view created, total: {len(self._text_views)}")
        return new_text_view

    def add_list(self):
        # find available view and return it
        for list_view in self._list_views:
            if not list_view.is_using:
                list_view.load()
                print_log(f"re-use list view, total: {len(self._list_views)}")
                return list_view
        # no available list view, create a new one
        new_list_view = ListView(self._display)
        new_list_view.load()
        self._list_views.append(new_list_view)
        print_log(f"new list view created, total: {len(self._list_views)}")
        return new_list_view

    def add_graph(self):
        # find available graph view and return it
        for graph_view in self._graph_views:
            if not graph_view.is_using:
                graph_view.load()
                print_log(f"re-use graph view, total: {len(self._graph_views)}")
                return graph_view
        # if no available view, create a new one
        new_graph_view = GraphView(self._display)
        new_graph_view.load()
        self._graph_views.append(new_graph_view)
        print_log(f"new graph view created, total: {len(self._graph_views)}")
        return new_graph_view

    def add_menu(self):
        for menu_view in self._menu_views:
            if not menu_view.is_using:
                menu_view.load()
                print_log(f"re-use menu view, total: {len(self._menu_views)}")
                return menu_view
        new_menu_view = MenuView(self._display)
        new_menu_view.load()
        self._menu_views.append(new_menu_view)
        print_log(f"new menu view created, total: {len(self._menu_views)}")
        return new_menu_view

    def show(self):
        self._display.show()

    def unload_all(self):
        for text_view in self._text_views:
            text_view.unload()
        for list_view in self._list_views:
            list_view.unload()
        for graph_view in self._graph_views:
            graph_view.unload()
        for menu_view in self._menu_views:
            menu_view.unload()
        self._display.clear()


class TextView:
    def __init__(self, display):
        self._display = display

        # dynamic
        self._x = 0
        self._y = 0
        self._text = ""
        self.is_using = True

    def load(self):
        self.is_using = True
        self._update_framebuffer()

    def unload(self):
        self.is_using = False

    def _clear_old(self):
        self._display.text(self._text, self._x, self._y, 0)
        self._display.set_updated()

    def _update_framebuffer(self):
        self._display.text(self._text, self._x, self._y)
        self._display.set_updated()

    def set_text(self, text):
        assert self.is_using is True, "Trying to update unused TextView"
        self._clear_old()
        self._text = text
        self._update_framebuffer()

    def set_attributes(self, x=None, y=None):
        self._clear_old()
        if x is not None:
            self._x = x
        if y is not None:
            self._y = y
        self._update_framebuffer()


class ListView:
    def __init__(self, display):
        self._display = display
        self._font_size = 7
        self._arrow_h = array.array('H', [3, 0, 0, 5, 6, 5])  # coordinates array of the poly vertex
        self._arrow_l = array.array('H', [0, 0, 6, 0, 3, 5])
        self.is_using = False

        # dynamic
        self._y = 0
        self._spacing = 2
        self._items = []
        self._page = 0
        self._items_per_page = 0

        self._slider_height = 0
        self._show_scroll_bar = False

    def load(self):
        self.is_using = True

    def unload(self):
        self.is_using = False

    def _cal_items_per_page(self):
        items_per_page = int((self._display.height - self._y) / (self._font_size + self._spacing))
        if items_per_page * (self._font_size + self._spacing) + self._font_size < self._display.height - self._y:
            items_per_page += 1
        if items_per_page > len(self._items):
            items_per_page = len(self._items)
        print_log(f"List view item per page: {items_per_page}, total: {len(self._items)}")
        return items_per_page

    def _cal_slider_height(self):
        return int(self._items_per_page / len(self._items) * 35 + 5)  # todo what is 35 and 5 here?

    def _clear_old(self):
        self._display.fill_rect(0, self._y, self._display.width, self._display.height - self._y, 0)
        self._display.set_updated()

    def _draw_scroll_bar(self):
        assert self._items_per_page < len(self._items), "No need to draw scroll bar"
        slider_y = round(self._page / (len(self._items) - self._items_per_page) * (
                46 - self._slider_height - self._y) + self._y + 9)
        self._display.line(124, self._y + 9, 124, 54, 1)  # scroll bar background line
        self._display.fill_rect(123, slider_y, 3, self._slider_height, 1)  # scroll bar slider
        if self._page == 0:  # draw arrow on top
            self._display.poly(121, self._y, self._arrow_h, 1, 0)
        else:
            self._display.poly(121, self._y, self._arrow_h, 1, 1)

        if self._page == len(self._items) - self._items_per_page:  # draw arrow on bottom
            self._display.poly(121, 58, self._arrow_l, 1, 0)
        else:
            self._display.poly(121, 58, self._arrow_l, 1, 1)

    def _update_framebuffer(self, selection):
        for i in range(self._page, self._page + self._items_per_page):
            print_log(f"List view showing: {i} / {len(self._items) - 1}")
            if i == selection:
                self._display.text(">" + self._items[i], 0,
                                   self._y + (i - self._page) * (self._font_size + self._spacing))
            else:
                self._display.text(" " + self._items[i], 0,
                                   self._y + (i - self._page) * (self._font_size + self._spacing))
        if self._show_scroll_bar:
            self._draw_scroll_bar()
        self._display.set_updated()

    def get_page(self):
        return self._page

    def set_selection(self, selection):
        self._clear_old()
        # update page start index
        if selection < self._page:
            self._page = selection
        elif selection > self._page + self._items_per_page - 1:
            self._page = selection - (self._items_per_page - 1)
        self._update_framebuffer(selection)

    def set_page(self, page):
        self._page = page
        self.set_selection(self._page)

    def set_items(self, items):
        self._items = items
        self._items_per_page = self._cal_items_per_page()
        self._show_scroll_bar = True if self._items_per_page < len(self._items) else False
        self._page = 0  # set view index to first item
        self._slider_height = self._cal_slider_height()
        self.set_selection(0)

    def set_attributes(self, y=None, spacing=None):
        self._clear_old()
        if y is not None:
            self._y = y
        if spacing is not None:
            self._spacing = spacing
        self.set_selection(0)


class GraphView:
    def __init__(self, display):
        # init
        self._display = display
        self._range_h_default = 65535
        self._range_l_default = 0
        self._range_update_period = 20
        self.is_using = True
        self._refresh_period = 1000 // GlobalSettings.graph_refresh_rate
        self._last_refresh_time = 0

        # dynamic
        self._box_x = 0
        self._box_y = 10
        self._box_w = 128
        self._box_h = 40
        self._show_box = False
        self._speed = 1

        self._x = None
        self._range_h = None
        self._range_l = None
        self._range_h_temp = None
        self._range_l_temp = None
        self._last_x = None
        self._last_y = None

    def set_attributes(self, box_x=None, box_y=None, box_w=None, box_h=None, speed=None, show_box=None):
        if box_x is not None:
            self._box_x = box_x
        if box_y is not None:
            self._box_y = box_y
        if box_w is not None:
            self._box_w = box_w
        if box_h is not None:
            self._box_h = box_h
        if speed is not None:
            self._speed = speed
        if show_box is not None:
            self._show_box = show_box

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
            self._display.fill_rect(self._x + 1, self._box_y + 1, clean_width - 2, self._box_h - 2, 0)
        else:
            exceed_width = self._x + clean_width - self._box_w - self._box_x
            self._display.fill_rect(self._x + 1, self._box_y + 1, clean_width - exceed_width - 2,
                                    self._box_h - 2, 0)
            self._display.fill_rect(self._box_x + 1, self._box_y + 1, exceed_width - 2, self._box_h - 2, 0)

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
        self._display.rect(self._box_x, self._box_y, self._box_w, self._box_h, 1)

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
            self._display.line(self._last_x, self._last_y, self._x, y, 1)
        if self._show_box:
            self._g_draw_box()
        # update last point
        self._last_x = self._x
        self._last_y = y
        # self._display.set_update()
        self._display.set_update_now()

        # print(f"raw: {value}, norm:{normalized_value}, xy: {self._x}, {y}")
        # print(f"upper_t: {self._range_h_temp}, lower_t: {self._range_l_temp}")
        # print(f"upper: {self._range_h}, lower: {self._range_l}\n")

    def set_value(self, value):
        if time.ticks_ms() - self._last_refresh_time > self._refresh_period:
            self._update_framebuffer(value)
            self._last_refresh_time = time.ticks_ms()


class MenuView:
    def __init__(self, display):
        self._icon_buf_hr = framebuf.FrameBuffer(icon_hr, 32, 32, framebuf.MONO_VLSB)
        self._icon_buf_hrv = framebuf.FrameBuffer(icon_hrv, 32, 32, framebuf.MONO_VLSB)
        self._icon_buf_kubios = framebuf.FrameBuffer(icon_kubios, 32, 32, framebuf.MONO_VLSB)
        self._icon_buf_history = framebuf.FrameBuffer(icon_history, 32, 32, framebuf.MONO_VLSB)

        self._display = display
        self.is_using = True

    def load(self):
        self.is_using = True

    def unload(self):
        self.is_using = False

    def _update_framebuffer(self, text, icon_buf, selection):
        self._display.clear()
        self._display.text(text, int((128 - len(text) * 8) / 2), 38, 1)
        self._display.blit(icon_buf, int((128 - 32) / 2), 0)
        # draw selection indicator
        self._display.rect(42, 61, 2, 2, 1)
        self._display.rect(54, 61, 2, 2, 1)
        self._display.rect(66, 61, 2, 2, 1)
        self._display.rect(78, 61, 2, 2, 1)
        x = 42 + selection * 12
        self._display.fill_rect(x, 60, 4, 4, 1)
        self._display.set_updated()

    def set_selection(self, selection):
        if selection == 0:
            icon_buf = self._icon_buf_hr
            text = "HR Measure"
        elif selection == 1:
            icon_buf = self._icon_buf_hrv
            text = "HRV Analysis"
        elif selection == 2:
            icon_buf = self._icon_buf_kubios
            text = "Kubios Analysis"
        elif selection == 3:
            icon_buf = self._icon_buf_history
            text = "History"
        else:
            raise ValueError("Invalid index")
        self._update_framebuffer(text, icon_buf, selection)
