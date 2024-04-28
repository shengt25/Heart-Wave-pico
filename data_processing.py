import time
from array import array

def ibi_calculator(beat_list):
    try:
        average = 0
        for time in range (1,len(beat_list),1):
            #print(f"IBI {time}. {beat_list[time] - beat_list[time-1]} s")
            average += beat_list[time] - beat_list[time-1]
        average /= len(beat_list) - 1
        print(f"Average heartrate of: {60/average} bpm")
    except:
        print("An exception occurred")

def threshold_finder(minimum,maximum):
    return (minimum + maximum) / 2

def peak_detector(data,time,hertz):
    peak_list = array('f')
    
    last_value = data[0]
    minimum = last_value
    maximum = last_value
    threshold = last_value
    
    last_slope = 0 #0 if negative, 1 if positive slope.
    threshold_check = 0 #0 if under threshold and didn't meet peak, 1 if over threshold and met peak
    
    for time in range(1,hertz * time,1):
        new_value = data[time]
        if new_value <= 36000 and new_value >= 30000:
            if new_value > maximum:
                maximum = new_value
                threshold = threshold_finder(minimum,maximum)
            elif new_value < minimum:
                minimum = new_value
                threshold = threshold_finder(minimum,maximum)
            if new_value > threshold:
                if new_value - last_value <= 0 and last_slope == 1 and threshold_check == 0:
                    peak_list.append(time/250)
                    last_slope = 0
                    threshold_check = 1
                elif new_value - last_value >= 0:
                    last_slope = 1
            else:
                threshold_check = 0
        last_value = new_value
    return ibi_calculator(peak_list)