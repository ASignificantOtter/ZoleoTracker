# Automatic Slack posting for Jordan Tracker
import logging
import os
import tempfile

import slack

from zoleotracker import config
from zoleotracker import databaseSQL
from zoleotracker import maps

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


def _upload_map_image(client: slack.WebClient, gps: str) -> None:
    """Fetch a Google Maps Static image for *gps* and upload it to the Slack channel.

    Does nothing if ``GOOGLE_MAPS_API_KEY`` is not configured or coordinate
    parsing fails.
    """
    api_key = config.GOOGLE_MAPS_API_KEY
    if not api_key:
        return

    try:
        lat, lon = maps.parse_gps_coordinates(gps)
        image_bytes = maps.fetch_map_image(lat, lon, api_key)
    except Exception as exc:
        logger.warning("Could not generate map image: %s", exc)
        return

    try:
        client.files_upload(
            channels=config.SLACK_CHANNEL,
            content=image_bytes,
            filename='location_map.png',
            title=f'Map: {gps}',
        )
    except slack.errors.SlackApiError as exc:
        logger.warning("Failed to upload map image to Slack: %s", exc.response['error'])


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

        _upload_map_image(client, gps)

        dir_name = os.path.dirname(config.PREVIOUS_CHECKIN_FILE) or '.'
        with tempfile.NamedTemporaryFile('w', dir=dir_name, delete=False, encoding='utf-8') as tmp:
            tmp.write(current_checkin)
            tmp_path = tmp.name
        os.replace(tmp_path, config.PREVIOUS_CHECKIN_FILE)
