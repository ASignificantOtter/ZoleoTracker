# Email parser / CSV writer of Jordan's location

import re
from datetime import datetime
import base64
import email
import imaplib
import html2text
import pandas as pd
from jordantracker import config

def parse_email_server() -> pd.DataFrame:

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
                        

def stamp_time(checkin) -> datetime:

    datetime_format = '%d %b %Y %H:%M:%S'
    timestamp = datetime.strptime(checkin, datetime_format)

    return timestamp

def tracker() -> None:


    df_location = parse_email_server()
    df_location.sort_values(by='checkin', inplace=True)

    df_location.to_csv('location.csv', sep='\t', index=False,header=True)




if __name__ == '__main__':
    tracker()
