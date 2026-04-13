# Email parser and database writer for Jordan's location

import base64
import email
import imaplib
import logging
import os
import re
import sys
from datetime import datetime

import html2text
import pandas as pd

from zoleotracker import config
from zoleotracker import databaseSQL
from zoleotracker import slackbot

PLAIN_TEXT = 'text/plain'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def validate_env_vars() -> None:
    required = ['EMAIL_ACCOUNT', 'EMAIL_PASSWORD', 'SLACK_TOKEN']
    missing = [var for var in required if not os.environ.get(var)]
    if missing:
        logger.error("Missing required environment variables: %s", ', '.join(missing))
        sys.exit(1)


# Returns an IMAP4_SSL object connected to the configured email folder.
def get_inbox() -> imaplib.IMAP4_SSL:
    email_account = os.environ.get('EMAIL_ACCOUNT')
    email_password = os.environ.get('EMAIL_PASSWORD')
    assert email_account is not None, "EMAIL_ACCOUNT environment variable is not set"
    assert email_password is not None, "EMAIL_PASSWORD environment variable is not set"
    mail = imaplib.IMAP4_SSL(config.EMAIL_SERVER)
    mail.login(email_account, email_password)
    mail.select(config.EMAIL_FOLDER)
    return mail


# Connects to the email account, searches for check-in emails by subject, and
# parses the checkin time, location, and Google Maps link from each matching email.
# Returns a DataFrame of [file, checkin, location, link].
def parse_email_server() -> pd.DataFrame:
    file_names: list[str] = []
    locations: list[str] = []
    checkins: list[datetime] = []
    links: list[str] = []

    mail = get_inbox()
    _mail_status, inbox = mail.search(None, 'ALL')
    mail_ids: list[bytes] = []
    for mail_block in inbox:
        mail_ids += mail_block.split()

    for i in mail_ids:
        _status, raw_email = mail.fetch(i, config.MESSAGE_FORMAT)
        for response_part in raw_email:
            if not isinstance(response_part, tuple):
                continue

            message = email.message_from_bytes(response_part[1])

            if message['subject'] != config.CHECKIN_EMAIL_SUBJECT:
                continue

            if message.is_multipart():
                mail_content_bytes = b''
                for part in message.get_payload():
                    if part.get_content_type() == PLAIN_TEXT:
                        mail_content_bytes = base64.b64decode(part.get_payload())
                        break
            else:
                mail_content_bytes = base64.b64decode(message.get_payload())

            mail_content_text = mail_content_bytes.decode(errors='ignore')
            text = html2text.html2text(mail_content_text)

            location_match = re.search(r"My location is (.+)", text)
            if location_match is None:
                logger.warning("Could not parse location from email, skipping.")
                continue
            location = location_match.group(1)

            checkin_match = re.search(r"sent at: (.+) \(UTC\)", text)
            if checkin_match is None:
                logger.warning("Could not parse checkin time from email, skipping.")
                continue
            checkin = stamp_time(checkin_match.group(1))

            link_match = re.search(r"View on map \]\((.+)\)", text)
            if link_match is None:
                logger.warning("Could not parse location link from email, skipping.")
                continue
            link = link_match.group(1)

            file_names.append(message['subject'])
            locations.append(location)
            checkins.append(checkin)
            links.append(link)

    df_all_checkins = pd.DataFrame({
        'file': file_names,
        'checkin': checkins,
        'location': locations,
        'link': links,
    })

    return df_all_checkins


def stamp_time(checkin: str) -> datetime:
    datetime_format = '%d %b %Y %H:%M:%S'
    timestamp = datetime.strptime(checkin, datetime_format)
    return timestamp


def tracker() -> None:
    df_all_checkins = parse_email_server()
    # Sort from oldest checkin to latest checkin
    df_all_checkins.sort_values(by='checkin', inplace=True)

    query_values: list[tuple[str, str, str, str]] = [
        (
            str(row.file),
            databaseSQL.checkin_to_str(row.checkin),
            str(row.location),
            str(row.link),
        )
        for row in df_all_checkins.itertuples(index=False)
    ]

    connection = databaseSQL.create_db_connection()
    databaseSQL.create_table_if_not_exists(connection)
    databaseSQL.insert_rows(connection, query_values)
    connection.commit()
    connection.close()


def start() -> None:
    validate_env_vars()
    tracker()
    slackbot.post_location()


if __name__ == '__main__':
    start()
