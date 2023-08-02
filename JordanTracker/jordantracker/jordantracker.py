# Email parser / CSV writer of Jordan's location

import os
import csv
import glob
import pandas as pd


from pathlib import Path
from email import policy
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
        text = msg.get_body(preferencelist=('plain')).get_content()
        file_names.append(name)
        texts.append(text)
        fp.close()

    df_eml = pd.DataFrame([file_names, texts]).T
    df_eml.columns = ['file_name', 'text']
    print(df_eml)
    
    return df_eml, df_eml.columns



def stamp_time(none):
    now = dt.now()
    timestamp = now.strftime("%d/%m/%Y %H:%M:%S")

    return timestamp


if __name__ == '__main__':
    folder_path = os.path.normpath(askdirectory(title='Select Folder'))  
    df_eml, df_eml.columns = parse_email(folder_path)  
    print(df_eml)
    
