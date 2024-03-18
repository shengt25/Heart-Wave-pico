class State:
    MENU = 0
    HR = 1
    HRV, HRV_MEASURING, HRV_DONE = range(2, 5)
    KUBIOS, KUBIOS_MEASURING, KUBIOS_DONE, KUBIOS_FAIL = range(5, 9)
    HISTORY, HISTORY_VIEW = range(9, 11)
