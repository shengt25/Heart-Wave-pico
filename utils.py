import time
import os
import gc
import machine


class GlobalSettings:
    print_log = False
    nr_files = 3
    save_directory = "Saved_Values"


def print_log(message):
    if GlobalSettings.print_log:
        print(time.ticks_ms(), message)


def pico_stat():
    """Return a tuple of used ram, free ram, total ram, free storage, all in KB.
    Note: If the result is going to be printed out in Thonny, the ram usage is inaccurate.
    Because every time Thonny prints to the console, it uses some memory as print history buffer.
    Those part of memory will be freed automatically after buffer is full.
    The result is accurate when running on the board itself."""
    ram_free = gc.mem_free()
    ram_used = gc.mem_alloc()
    ram_total = ram_free + ram_used
    s = os.statvfs('/')
    storage_free = s[0] * s[3] / 1024
    return ram_used, ram_free, ram_total, storage_free


def pico_rom_stat():
    """Return free storage in KB. The total storage is 2MB, but approx 832KB is usable with MicroPython firmware."""
    s = os.statvfs('/')
    storage_free = s[0] * s[3] / 1024
    return storage_free
