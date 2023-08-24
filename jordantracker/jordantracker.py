# Email parser / CSV writer of Jordan's location

import os
#import csv
import glob
import pandas as pd
import html2text
import re
from datetime import datetime
from jordantracker import config

import email
import imaplib
import base64

from email import policy
from email.parser import BytesParser
from datetime import datetime as dt

def parse_email_server():

    file_names = []
    texts = []
    locations = []
    checkins = []
    links = []

    mail = imaplib.IMAP4_SSL(config.EMAIL_SERVER)
    mail.login(config.EMAIL_ACCOUNT, config.EMAIL_PASSWORD)
    mail.select('inbox')
    status, data = mail.search(None, 'ALL')
    mail_ids = []
    for block in data:
        mail_ids += block.split()

    for i in mail_ids:
        status, data = mail.fetch(i, '(RFC822)')
        for response_part in data:
            if isinstance(response_part, tuple):
                message = email.message_from_bytes(response_part[1])
                #mail_from = message['from']
                mail_subject = message['subject']
                if mail_subject == 'Check-in message from SlothPace':

                    if message.is_multipart():
                        mail_content = ''

                        for part in message.get_payload():
                            if part.get_content_type() == 'text/plain':
                                mail_content += part.get_payload()
                                mail_content = base64.b64decode(mail_content)
                                mail_content_text = mail_content.decode(errors='ignore')
                                text = html2text.html2text(mail_content_text)
                        

                    else:
                        mail_content = message.get_payload()
                        mail_content = base64.b64decode(mail_content)
                        mail_content_text = mail_content.decode(errors='ignore')
                        text = html2text.html2text(mail_content_text)
                    
        
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

        
        file_names.append(mail_subject)
        texts.append(text)
        locations.append(location)
        checkins.append(checkin)
        links.append(link)
    df_location = pd.DataFrame([file_names, checkins, locations, links]).T
    df_location.columns = ['file', 'checkin', 'location', 'link']
    
    return df_location
                        


def parse_email_file(folder_path):
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
    df_location.columns = ['file', 'checkin', 'location', 'link']
    
    return df_location

def fpath():
    current = os.path.dirname(os.path.realpath(__file__))
    parent = os.path.dirname(current)
    folder_path = os.path.join(parent, 'emails/')

    return folder_path


def stamp_time(checkin):

    datetime_format = '%d %b %Y %H:%M:%S'
    timestamp = datetime.strptime(checkin, datetime_format)

    return timestamp

def tracker():

    #df_location_old = parse_email_file(fpath())
    df_location = parse_email_server()
    df_location.sort_values(by='checkin', inplace=True)

    df_location.to_csv('location.csv', sep='\t', index=False,header=True)
    #df_location_old.to_csv('location_old.csv', sep='\t', index=False,header=True)



if __name__ == '__main__':
    tracker()
