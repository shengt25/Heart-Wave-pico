import os
import json
    
def save_system(data):
    directory = "Saved_Values"
    try:
        os.stat(directory)
    except OSError:
        os.mkdir(directory)
    file_name = directory + "/" + data["DATE"] + ".txt"
    with open(file_name,"w") as file:
        json.dump(data,file)
    return True