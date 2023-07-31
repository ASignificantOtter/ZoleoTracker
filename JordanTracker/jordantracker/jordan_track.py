# Email parser / CSV writer of Jordan's location

import os
import csv
import email

from datetime import datetime as dt
from tkinter.filedialog import askdirectory



def helloworld(name):
    print(f'Hi, {name}')
    
    return 0

def parse_email(timestamp, folder_path):
    #grab emaiils in folder newer than latest timestamp in csv

    return 0

def stamp_time(none):
    now = dt.now()
    timestamp = now.strftime("%d/%m/%Y %H:%M:%S")

    return timestamp



if __name__ == '__main__':
    #helloworld('Matt')

    folder_path = os.path.normpath(askdirectory(title='Select Folder'))    
    
