import os
import json
from utils import GlobalSettings


def delete_oldest_file():
    """Delete the oldest file in the directory, one file only.
    With current file names setting, the oldest file is the first file in the sort() list."""
    directory = GlobalSettings.save_directory + "/"
    files = os.listdir(directory)
    files.sort()
    os.remove(directory + files[0])


def check_file_nr():
    directory = GlobalSettings.save_directory + "/"
    files = os.listdir(directory)
    num_files = len(files)
    if num_files < GlobalSettings.files_limit:
        return True
    return False

def check_home_dir():
    directory = GlobalSettings.save_directory
    try:
        os.stat(directory)
        if not check_file_nr():
            delete_oldest_file()
            # ask user to delete files? Not sure how to go about it.
        # I'm gonna data will be automatically deleted when the number of files exceeds the limit.
        # The limit can be described in the user manual. By calculation, this limit could be even 7000.
    except OSError:
        os.mkdir(directory)
    
def save_system(data):
    check_home_dir()
    directory = GlobalSettings.save_directory
    filename = data["DATE"].replace(":", ".")
    # format: DD.MM.YY hh:mm:ss,
    # only last two digits for year, because screen is too small to display 4
    # but seconds are important to distinguish files saved in the same minute, when measuring multiple times fast
    # seconds will be cut off in listview, also because of the small screen
    file_name = directory + "/" + filename + ".txt"
    with open(file_name, "w") as file:
        json.dump(data, file)
    return True


def load_history_list():
    directory = GlobalSettings.save_directory + "/"
    files = os.listdir(directory)
    return files


def load_history_data(file_name):
    directory = GlobalSettings.save_directory + "/"
    path = directory + file_name
    with open(path, 'r') as file:
        data = json.load(file)
    return data
