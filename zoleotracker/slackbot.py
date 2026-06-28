# Automatic Slack posting for Jordan Tracker
import logging
import os
import tempfile

import slack

from zoleotracker import config
from zoleotracker import databaseSQL

logger = logging.getLogger(__name__)


# Creates Slack WebClient from environment variable.
def get_slack_client() -> slack.WebClient:
    slack_token = os.environ.get('SLACK_TOKEN')
    if not slack_token:
        raise EnvironmentError("SLACK_TOKEN environment variable is not set")
    return slack.WebClient(token=slack_token)


def get_current_checkin() -> tuple[str, str, str]:
    with databaseSQL.db_connection() as connection:
        rows = databaseSQL.read_last_row(connection)

    if not rows:
        raise RuntimeError("No check-ins found in database.")

    row = rows[0]
    return row.checkin, row.location, row.link


def should_post(previous_checkin: str, current_checkin: str) -> bool:
    return current_checkin > previous_checkin


def get_previous_checkin() -> str:
    try:
        with open(config.PREVIOUS_CHECKIN_FILE, 'r', encoding='utf-8') as previous_checkin_file:
            return previous_checkin_file.read()
    except FileNotFoundError:
        return ''


def post_location() -> None:
    current_checkin, gps, loc_link = get_current_checkin()
    previous_checkin = get_previous_checkin()

    if should_post(previous_checkin, current_checkin):
        client = get_slack_client()
        try:
            client.chat_postMessage(
                channel=config.SLACK_CHANNEL,
                text=(
                    'Jordan has been making some moves! His last coordinates are: '
                    + gps + '\n' + loc_link
                ),
            )
        except slack.errors.SlackApiError as exc:
            logger.error("Failed to post Slack message: %s", exc.response['error'])
            raise

        dir_name = os.path.dirname(config.PREVIOUS_CHECKIN_FILE) or '.'
        with tempfile.NamedTemporaryFile('w', dir=dir_name, delete=False, encoding='utf-8') as tmp:
            tmp.write(current_checkin)
            tmp_path = tmp.name
        os.replace(tmp_path, config.PREVIOUS_CHECKIN_FILE)
