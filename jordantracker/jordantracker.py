# Email parser / CSV writer of Jordan's location

import re
from datetime import datetime
import base64
import email
import imaplib
import html2text
import pandas as pd
from jordantracker import config
from jordantracker import slackbot

PLAIN_TEXT = 'text/plain'

#returns a IMAP4_SSL class object containing the entire email folder from server
def get_inbox():
    mail = imaplib.IMAP4_SSL(config.EMAIL_SERVER)
    mail.login(config.EMAIL_ACCOUNT, config.EMAIL_PASSWORD)
    mail.select(config.EMAIL_FOLDER)

    return mail

# Connects to email account from config file, searches through specified email folder, 
# looks for check-in emails by subject, parses out the checkin time, location, and google maps link. 
# Returns a dataframe of [email_subject, checkin time, checkin location, location google maps link]
def parse_email_server() -> pd.DataFrame:
 
    file_names = []
    texts = []
    locations = []
    checkins = []
    links = []

    mail = get_inbox()
    mail_status, inbox = mail.search(None, 'ALL')
    mail_ids = []
    # splits out individual email messages from one blob (inbox)
    # iterates through each individual email id, and splits from the full inbox block
    for mail_block in inbox:
        mail_ids += mail_block.split()
    # iterates through email messages using email id as an iterator. 
    for i in mail_ids:
        status, raw_email = mail.fetch(i, config.MESSAGE_FORMAT)
        for response_part in raw_email:
            if isinstance(response_part, tuple):
                message = email.message_from_bytes(response_part[1])

                if message['subject'] == config.CHECKIN_EMAIL_SUBJECT:

                    if message.is_multipart():
                        mail_content = ''

                        for part in message.get_payload():
                            if part.get_content_type() == PLAIN_TEXT:
                                mail_content += part.get_payload()
                                mail_content = base64.b64decode(mail_content)
                                
                    else:
                        mail_content = base64.b64decode(message.get_payload())
                
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

        file_names.append(message['subject'])
        texts.append(text)
        locations.append(location)
        checkins.append(checkin)
        links.append(link)
    df_all_checkins = pd.DataFrame([file_names, checkins, locations, links]).T
    df_all_checkins.columns = ['file', 'checkin', 'location', 'link']
    
    return df_all_checkins
               
def stamp_time(checkin) -> datetime:

    datetime_format = '%d %b %Y %H:%M:%S'
    timestamp = datetime.strptime(checkin, datetime_format)

    return timestamp

def tracker() -> None:

    df_all_checkins = parse_email_server()
    #sorts from oldest checkin to latest checkin
    df_all_checkins.sort_values(by='checkin', inplace=True) 
    df_all_checkins.to_csv('location.csv', sep='\t', index=False,header=True)

def start():
    tracker()
    slackbot.post_location()


if __name__ == '__main__':
    start()