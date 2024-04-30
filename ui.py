import array
from icon import icon_hr, icon_hrv, icon_kubios, icon_history
import framebuf
from utils import print_log


class View:
    """Create text, list elements: add_text, add_list"""

    def __init__(self, display):
        self._display = display
        self.width = display.width
        self.height = display.height
        self._text_views = []
        self._list_views = []
        self._graph_views = []
        self._menu_views = []

    def add_text(self, text, y, invert=False):
        # find available view and return it
        for text_view in self._text_views:
            if not text_view.is_active():
                text_view.reinit(text, y, invert)
                print_log(f"re-use text view, total: {len(self._text_views)}")
                return text_view
        # no available text view, create a new one
        new_text_view = TextView(self._display, text, y, invert)
        self._text_views.append(new_text_view)
        print_log(f"new text view created, total: {len(self._text_views)}")
        return new_text_view

    def add_list(self, items, y, spacing=2, read_only=False):
        # find available view and return it
        for list_view in self._list_views:
            if not list_view.is_active():
                list_view.reinit(items, y, spacing, read_only)
                print_log(f"re-use list view, total: {len(self._list_views)}")
                return list_view
        # no available list view, create a new one
        new_list_view = ListView(self._display, items, y, spacing, read_only)
        self._list_views.append(new_list_view)
        print_log(f"new list view created, total: {len(self._list_views)}")
        return new_list_view

    def add_graph(self, x=0, y=12, w=128, h=40, speed=1, show_box=False):
        # find available graph view and return it
        for graph_view in self._graph_views:
            if not graph_view.is_active():
                graph_view.reinit(x, y, w, h, speed, show_box)
                print_log(f"re-use graph view, total: {len(self._graph_views)}")
                return graph_view
        # if no available view, create a new one
        new_graph_view = GraphView(self._display, x, y, w, h, speed, show_box)
        self._graph_views.append(new_graph_view)
        print_log(f"new graph view created, total: {len(self._graph_views)}")
        return new_graph_view

    def add_menu(self):
        for menu_view in self._menu_views:
            if not menu_view.is_active():
                print_log(f"re-use menu view, total: {len(self._menu_views)}")
                return menu_view
        new_menu_view = MenuView(self._display)
        self._menu_views.append(new_menu_view)
        print_log(f"new menu view created, total: {len(self._menu_views)}")
        return new_menu_view

    def refresh(self):
        self._display.refresh()

    def remove_all(self):
        for text_view in self._text_views:
            text_view.remove()
        for list_view in self._list_views:
            list_view.remove()
        for graph_view in self._graph_views:
            graph_view.remove()
        for menu_view in self._menu_views:
            menu_view.remove()
        self._display.clear()


class TextView:
    """Text elements: set_text, remove"""

    def __init__(self, display, text, y, invert=False):
        self._display = display
        self._font_height = display.FONT_HEIGHT
        self._is_active = False

        # attributes
        self._text = text
        self._y = y
        self._invert = invert
        self._activate()

    def reinit(self, text, y, invert=False):
        self._text = text
        self._y = y
        self._invert = invert
        self._activate()

    def remove(self):
        self._clear_old()
        self._is_active = False

    def is_active(self):
        return self._is_active

    def set_text(self, text):
        assert self._is_active is True, "Trying to update inactive TextView"
        self._clear_old()
        self._text = text
        self._update_framebuffer()

    def _activate(self):
        self._update_framebuffer()
        self._is_active = True

    def _clear_old(self):
        if self._invert:
            self._display.fill_rect(0, self._y, self._display.width, self._font_height + 2, 0)
        else:
            self._display.fill_rect(0, self._y, self._display.width, self._font_height, 0)
        self._display.set_update()

    def _update_framebuffer(self):
        if self._invert:
            self._display.fill_rect(0, self._y, self._display.width, self._font_height + 2, 1)
            self._display.text(self._text, 0, self._y + 1, 0)
        else:
            self._display.text(self._text, 0, self._y, 1)
        self._display.set_update()


class ListView:
    """List elements: set_items, set_selection, set_page, remove.
    get_page, get_max_page, get_selection, get_max_selection.
    Note: current selection is got from rotary encoder get_position() method, which is absolute position
    ListView don't have a current_selection attribute or method, it's managed by the caller(rotary encoder user)."""

    def __init__(self, display, items, y, spacing=2, read_only=False):
        self._display = display
        self._font_height = display.FONT_HEIGHT
        self._arrow_top = array.array('H', [3, 0, 0, 5, 6, 5])  # coordinates array of the poly vertex
        self._arrow_bottom = array.array('H', [0, 0, 6, 0, 3, 5])
        self._is_active = False

        self._page = 0
        self._items_per_page = 0
        self._show_scrollbar = False
        self._scrollbar_top = 0
        self._scrollbar_bottom = 0
        self._slider_min_height = 2
        self._slider_height = 0
        self._slider_top = 0
        self._slider_bottom = 0
        self._items = None

        # attributes
        self._read_only = read_only
        self._y = y
        self._spacing = spacing
        self.set_items(items)  # IMPORTANT: set_items must be the last one, because it requires the above attributes
        self._activate()

    def reinit(self, items, y, spacing=2, read_only=False):
        self._y = y
        self._spacing = spacing
        self._read_only = read_only
        self.set_items(items)  # IMPORTANT: set_items must be the last one, because it requires the above attributes
        self._activate()

    def remove(self):
        self._clear_old()
        self._is_active = False

    def is_active(self):
        return self._is_active

    def get_page(self):
        return self._page

    def get_max_page(self):
        return len(self._items) - self._items_per_page

    def get_max_selection(self):
        return len(self._items) - 1

    def set_selection(self, selection):
        if selection < 0 or selection > len(self._items) - 1:
            raise ValueError("Invalid selection index")
        self._clear_old()
        # update page start index
        if selection < self._page:
            self._page = selection
        elif selection > self._page + self._items_per_page - 1:
            self._page = selection - (self._items_per_page - 1)
        self._update_framebuffer(selection)

    def set_page(self, page):
        if page < 0 or page > len(self._items) - self._items_per_page:
            raise ValueError("Invalid page index")
        self._page = page
        self.set_selection(self._page)

    def set_items(self, items):
        self._clear_old()
        self._items = items

        # set items per page
        items_per_page = int((self._display.height - self._y) / (self._font_height + self._spacing))
        if items_per_page * (self._font_height + self._spacing) + self._font_height < self._display.height - self._y:
            items_per_page += 1
        if items_per_page > len(self._items):
            items_per_page = len(self._items)
        print_log(f"List view item per page: {items_per_page}, total: {len(self._items)}")
        self._items_per_page = items_per_page

        # set scrollbar
        if self._items_per_page < len(self._items):
            self._show_scrollbar = True
            self._scrollbar_top = self._y + 5 + 3  # 5 is height of arrow, 3 is margin between arrow and scrollbar
            self._scrollbar_bottom = self._display.height - 5 - 3
            self._slider_top = self._scrollbar_top + 1  # offset 1 pixel from scrollbar outline
            self._slider_bottom = self._scrollbar_bottom - 1
            self._slider_height = int(self._items_per_page / len(self._items) * (
                    self._slider_bottom - self._slider_top - self._slider_min_height) + self._slider_min_height)
        else:
            self._show_scrollbar = False

        self._page = 0  # set view index to first item
        self.set_selection(0)

    def _activate(self):
        self._update_framebuffer(0)
        self._is_active = True

    def _clear_old(self):
        self._display.fill_rect(0, self._y, self._display.width, self._display.height - self._y, 0)
        self._display.set_update()

    def _draw_scrollbar(self):
        scrollbar_width = 5
        slider_width = scrollbar_width - 2
        assert self._items_per_page < len(self._items), "No need to draw scroll bar"

        slider_y = round(self._page / (len(self._items) - self._items_per_page) * (
                self._slider_bottom - self._slider_top - self._slider_height) + self._slider_top)
        # scrollbar outline
        self._display.rect(self._display.width - scrollbar_width - 1, self._scrollbar_top, scrollbar_width,
                           self._scrollbar_bottom - self._scrollbar_top, 1)
        # scrollbar slider
        self._display.fill_rect(self._display.width - slider_width - 2, slider_y, slider_width,
                                self._slider_height, 1)

        if self._page == 0:  # draw arrow on top, 7 is the width of the arrow
            self._display.poly(self._display.width - 7, self._y, self._arrow_top, 1, 0)
        else:
            self._display.poly(self._display.width - 7, self._y, self._arrow_top, 1, 1)

        if self._page == len(self._items) - self._items_per_page:  # draw arrow on bottom, 6 is the height of the arrow
            self._display.poly(self._display.width - 7, self._display.height - 6, self._arrow_bottom, 1, 0)
        else:
            self._display.poly(self._display.width - 7, self._display.height - 6, self._arrow_bottom, 1, 1)

    def _update_framebuffer(self, selection):
        for i in range(self._page, self._page + self._items_per_page):
            print_log(f"List view showing: {i} / {len(self._items) - 1}")
            if self._read_only:
                self._display.text(self._items[i], 0, self._y + (i - self._page) * (self._font_height + self._spacing))
            else:
                if i == selection:
                    self._display.text(">" + self._items[i], 0,
                                       self._y + (i - self._page) * (self._font_height + self._spacing))
                else:
                    self._display.text(" " + self._items[i], 0,
                                       self._y + (i - self._page) * (self._font_height + self._spacing))
        if self._show_scrollbar:
            self._draw_scrollbar()
        self._display.set_update()


class GraphView:
    def __init__(self, display, x=0, y=12, w=128, h=40, speed=1, show_box=False):
        # init
        self._display = display
        self._range_h_default = 16384
        self._range_l_default = 0
        self._range_update_period = 20
        self._is_active = True

        # attributes
        self._box_x = x
        self._box_y = y
        self._box_w = w
        self._box_h = h
        self._show_box = show_box
        self._speed = speed

        self._x = self._box_x + 1
        self._range_h = self._range_h_default
        self._range_l = self._range_l_default
        self._range_h_temp = self._range_h_default
        self._range_l_temp = self._range_l_default
        self._last_x = -1
        self._last_y = -1
        self._activate()

    def reinit(self, x=0, y=12, w=128, h=40, speed=1, show_box=False):
        self._box_x = x
        self._box_y = y
        self._box_w = w
        self._box_h = h
        self._show_box = show_box
        self._speed = speed

        self._x = self._box_x + 1
        self._range_h = self._range_h_default
        self._range_l = self._range_l_default
        self._range_h_temp = self._range_h_default
        self._range_l_temp = self._range_l_default
        self._last_x = -1
        self._last_y = -1
        self._activate()

    def remove(self):
        self._display.fill_rect(self._box_x, self._box_y, self._box_w, self._box_h, 0)
        self._is_active = False

    def is_active(self):
        return self._is_active

    def set_value(self, value):
        self._update_framebuffer(value)

    def _activate(self):
        self._is_active = True

    def _clear_ahead(self):
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

    def _normalize(self, value):
        # use default when range is negative or zero
        if self._range_h <= self._range_l:
            return int((value - self._range_l) * self._box_h / (self._range_h_default - self._range_l_default))
        else:
            return int((value - self._range_l) * self._box_h / (self._range_h - self._range_l))

    def _convert_coord(self, value):
        new_value = - value + self._box_h + self._box_y
        return new_value

    def _draw_outline_box(self):
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

        # update range
        if self._x % self._range_update_period == 0:
            self._range_h = self._range_h_temp
            self._range_l = self._range_l_temp
            # reset the temp range
            self._range_h_temp = self._range_l_default
            self._range_l_temp = self._range_h_default

        # shirk the range
        if self._range_h_temp < value < self._range_h_default:
            self._range_h_temp = value
        if self._range_l_temp > value > self._range_l_default:
            self._range_l_temp = value

        self._clear_ahead()
        normalized_value = self._normalize(value)
        y = self._convert_coord(normalized_value)

        # limit y inside the box
        if y > self._box_y + self._box_h - 2:
            y = self._box_y + self._box_h - 2
        elif y <= self._box_y:
            y = self._box_y + 1

        # draw, ignore drawing with invalid last point
        if self._last_x != -1 and self._last_y != -1:
            self._display.line(self._last_x, self._last_y, self._x, y, 1)
        if self._show_box:
            self._draw_outline_box()

        # update last point
        self._last_x = self._x
        self._last_y = y

        # self._display.set_update()
        self._display.set_update(force=True)


class MenuView:
    def __init__(self, display):
        self._icon_buf_hr = framebuf.FrameBuffer(icon_hr, 32, 32, framebuf.MONO_VLSB)
        self._icon_buf_hrv = framebuf.FrameBuffer(icon_hrv, 32, 32, framebuf.MONO_VLSB)
        self._icon_buf_kubios = framebuf.FrameBuffer(icon_kubios, 32, 32, framebuf.MONO_VLSB)
        self._icon_buf_history = framebuf.FrameBuffer(icon_history, 32, 32, framebuf.MONO_VLSB)

        self._display = display
        self._is_active = True
        self._activate()

    def remove(self):
        self._display.fill(0)
        self._is_active = False

    def is_active(self):
        return self._is_active

    def set_selection(self, selection):
        self._update_framebuffer(selection)

    def _activate(self):
        self._update_framebuffer(0)
        self._is_active = True

    def _update_framebuffer(self, selection):
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
        self._display.set_update()
