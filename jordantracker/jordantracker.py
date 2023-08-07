# Email parser / CSV writer of Jordan's location

import os
import csv
import glob
import pandas as pd
import email
import html2text


from pathlib import Path
from email import policy
from email import parser
from email.parser import BytesParser
from datetime import datetime as dt
from tkinter.filedialog import askdirectory

def parse_email(folder_path):
    eml_files = glob.glob(folder_path + '*.eml') # get all .eml files in a list
    file_names = []
    texts = []
    for file in eml_files:
        with open(file, 'rb') as fp:
            name = fp.name  # Get file name
            msg = BytesParser(policy=policy.default).parse(fp)
            #msg_data = email.message_from_bytes(fp, policy=email.policy.default)
        text = msg.get_body().get_content()
        text = html2text.html2text(text)
        
        file_names.append(name)
        texts.append(text)
        fp.close()

    df_eml = pd.DataFrame([file_names, texts]).T
    df_eml.columns = ['file_name', 'text']
    
    return df_eml

def fpath():
    current = os.path.dirname(os.path.realpath(__file__))
    parent = os.path.dirname(current)
    folder_path = os.path.join(parent, 'emails/')
    return folder_path


def stamp_time(none):
    now = dt.now()
    timestamp = now.strftime("%d/%m/%Y %H:%M:%S")

    return timestamp

def tracker():
    folder_path = fpath()
    df_eml = parse_email(folder_path)  
    
    df_eml.to_csv('location.csv', sep='\t', index=False,header=True)
   
    pass

if __name__ == '__main__':
    tracker()
