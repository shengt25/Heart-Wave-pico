import os
import json
from utils import GlobalSettings

def check_file_nr():
    directory = GlobalSettings.save_directory + "/"
    files = os.listdir(directory)
    num_files = len(files)
    if num_files < GlobalSettings.nr_files:
        return True
    return False
    
def save_system(data):
    directory = GlobalSettings.save_directory
    try:
        os.stat(directory)
        if check_file_nr() == True:
            pass
            #ask user to delete files? Not sure how to go about it.
    except OSError:
        os.mkdir(directory)
    file_name = directory + "/" + data["DATE"] + ".txt"
    with open(file_name,"w") as file:
        json.dump(data,file)
    return True

