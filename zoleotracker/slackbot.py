# Automatic Slack posting for Jordan Tracker
import os

import slack

from zoleotracker import databaseSQL


# Creates Slack WebClient from environment variable.
def get_slack_client() -> slack.WebClient:
    slack_token = os.environ.get('SLACK_TOKEN')
    client = slack.WebClient(token=slack_token)
    return client


def get_current_checkin() -> tuple[str, str, str]:
    connection = databaseSQL.create_db_connection()
    rows = databaseSQL.read_last_row(connection)
    connection.close()

    if not rows:
        raise RuntimeError("No check-ins found in database.")

    # Row schema: (id, file, checkin, location, link)
    row = rows[0]
    date = str(row[2])
    gps = str(row[3])
    loc_link = str(row[4])

    return date, gps, loc_link


def should_post(previous_checkin: str, current_checkin: str) -> bool:
    return current_checkin > previous_checkin


def get_previous_checkin() -> str:
    previous_checkin_path = 'previous_checkin.txt'
    with open(previous_checkin_path, 'r', encoding='utf-8') as previous_checkin_file:
        previous_checkin = previous_checkin_file.read()
    return previous_checkin


def post_location() -> None:
    current_checkin, gps, loc_link = get_current_checkin()
    previous_checkin = get_previous_checkin()

    if should_post(previous_checkin, current_checkin):
        client = get_slack_client()
        client.chat_postMessage(
            channel='#jordan-tracker',
            text=(
                'Jordan has been making some moves! His last coordinates are: '
                + gps + '\n' + loc_link
            ),
        )
        with open('previous_checkin.txt', 'w', encoding='utf-8') as fp:
            fp.write(current_checkin)
