import time


class GlobalSettings:
    print_log = False


def print_log(message):
    if GlobalSettings.print_log:
        print(time.ticks_ms(), message)
