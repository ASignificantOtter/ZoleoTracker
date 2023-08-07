# Email parser / CSV writer of Jordan's location

import os
import csv
import glob
import pandas as pd
import email
import html2text
import re
from datetime import datetime


from pathlib import Path
from email import policy
from email import parser
from email.parser import BytesParser
from datetime import datetime as dt

def parse_email(folder_path):
    eml_files = glob.glob(folder_path + '*.eml') # get all .eml files in a list
    file_names = []
    texts = []
    locations = []
    checkins = []
    links = []

    for file in eml_files:
        with open(file, 'rb') as fp:
            name = fp.name  # Get file name
            msg = BytesParser(policy=policy.default).parse(fp)
        text = msg.get_body().get_content()
        text = html2text.html2text(text)
       
        try:
            location = re.search(r"My location is (.+)", text).group(1)
        except AttributeError:
            location = re.search(r"My location is (.+)", text)
        
        try:
            checkin = re.search(r"sent at: (.+) \(UTC\)", text).group(1)
        except AttributeError:
            checkin = re.search(r"sent at: (.+) \(UTC\)", text)

        checkin = stamp_time(checkin)

        try:
            link = str(re.search(r"View on map \]\((.+)\)", text).group(1))
        except AttributeError:
            link = str(re.search(r"View on map \]\((.+)\)", text))

        
        
        file_names.append(name)
        texts.append(text)
        locations.append(location)
        checkins.append(checkin)
        links.append(link)
        fp.close()

    df_location = pd.DataFrame([file_names, checkins, locations, links]).T
    df_location.columns = ['file name', 'check-in', 'location', 'link']
    
    return df_location

def fpath():
    current = os.path.dirname(os.path.realpath(__file__))
    parent = os.path.dirname(current)
    folder_path = os.path.join(parent, 'emails/')
    return folder_path


def stamp_time(checkin):
    now = dt.now()
    curtime = now.strftime("%d %b %Y %H:%M:%S")
    
    #examplestr = '30 Jul 2023 17:26:53'
    datetime_format = '%d %b %Y %H:%M:%S'
    timestamp = datetime.strptime(checkin, datetime_format)

    return timestamp

def tracker():
    folder_path = fpath()
    df_location = parse_email(folder_path) 
    df_location.to_csv('location.csv', sep='\t', index=False,header=True)
   
    pass

if __name__ == '__main__':
    tracker()
