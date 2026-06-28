from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest

from zoleotracker import databaseSQL, slackbot


def test_should_post_returns_True_if_date_is_newer():
    previous_checkin = '2023-07-30 17:26:53'
    current_checkin = '2023-08-01 17:26:53'

    assert slackbot.should_post(previous_checkin, current_checkin)


def test_should_post_returns_False_if_date_is_same():
    previous_checkin = '2023-07-30 17:26:53'

    assert not slackbot.should_post(previous_checkin, previous_checkin)


def test_should_post_returns_False_if_date_is_older():
    previous_checkin = '2023-07-30 17:26:53'
    current_bad_checkin = '2023-07-29 17:26:53'

    assert not slackbot.should_post(previous_checkin, current_bad_checkin)


def test_get_current_checkin_returns_latest_row():
    mock_row = databaseSQL.CheckinRow(
        id=1,
        file='subject',
        checkin='2023-08-01 10:00:00',
        location='47.6 N, 122.3 W',
        link='http://maps.example.com',
    )

    @contextmanager
    def mock_db_conn():
        yield MagicMock()

    with patch('zoleotracker.databaseSQL.db_connection', mock_db_conn), \
         patch('zoleotracker.databaseSQL.read_last_row', return_value=[mock_row]):
        date, gps, loc_link = slackbot.get_current_checkin()

    assert date == '2023-08-01 10:00:00'
    assert gps == '47.6 N, 122.3 W'
    assert loc_link == 'http://maps.example.com'


def test_get_current_checkin_raises_when_no_rows():
    @contextmanager
    def mock_db_conn():
        yield MagicMock()

    with patch('zoleotracker.databaseSQL.db_connection', mock_db_conn), \
         patch('zoleotracker.databaseSQL.read_last_row', return_value=[]):
        with pytest.raises(RuntimeError, match="No check-ins found"):
            slackbot.get_current_checkin()


def test_get_slack_client_raises_when_token_missing(monkeypatch):
    monkeypatch.delenv('SLACK_TOKEN', raising=False)

    with pytest.raises(EnvironmentError, match="SLACK_TOKEN"):
        slackbot.get_slack_client()


def test_post_location_calls_slack_when_new_checkin(tmp_path, monkeypatch):
    monkeypatch.setenv('SLACK_TOKEN', 'test-token')
    mock_row = databaseSQL.CheckinRow(
        id=1,
        file='subject',
        checkin='2023-08-01 10:00:00',
        location='47.6 N, 122.3 W',
        link='http://maps.example.com',
    )

    @contextmanager
    def mock_db_conn():
        yield MagicMock()

    mock_client = MagicMock()
    prev_file = tmp_path / 'previous_checkin.txt'

    with patch('zoleotracker.databaseSQL.db_connection', mock_db_conn), \
         patch('zoleotracker.databaseSQL.read_last_row', return_value=[mock_row]), \
         patch('zoleotracker.slackbot.config') as mock_config, \
         patch('zoleotracker.slackbot.get_slack_client', return_value=mock_client):
        mock_config.PREVIOUS_CHECKIN_FILE = str(prev_file)
        mock_config.SLACK_CHANNEL = '#test-channel'

        slackbot.post_location()

    mock_client.chat_postMessage.assert_called_once()
    call_kwargs = mock_client.chat_postMessage.call_args.kwargs
    assert call_kwargs['channel'] == '#test-channel'
    assert '47.6 N, 122.3 W' in call_kwargs['text']


def test_post_location_skips_slack_when_not_new(tmp_path, monkeypatch):
    monkeypatch.setenv('SLACK_TOKEN', 'test-token')
    mock_row = databaseSQL.CheckinRow(
        id=1,
        file='subject',
        checkin='2023-08-01 10:00:00',
        location='47.6 N, 122.3 W',
        link='http://maps.example.com',
    )
    prev_file = tmp_path / 'previous_checkin.txt'
    prev_file.write_text('2023-09-01 00:00:00')  # newer than current_checkin

    @contextmanager
    def mock_db_conn():
        yield MagicMock()

    mock_client = MagicMock()

    with patch('zoleotracker.databaseSQL.db_connection', mock_db_conn), \
         patch('zoleotracker.databaseSQL.read_last_row', return_value=[mock_row]), \
         patch('zoleotracker.slackbot.config') as mock_config, \
         patch('zoleotracker.slackbot.get_slack_client', return_value=mock_client):
        mock_config.PREVIOUS_CHECKIN_FILE = str(prev_file)
        mock_config.SLACK_CHANNEL = '#test-channel'

        slackbot.post_location()

    mock_client.chat_postMessage.assert_not_called()


# --- _upload_map_image ---

def test_upload_map_image_skipped_when_no_api_key():
    mock_client = MagicMock()

    with patch('zoleotracker.slackbot.config') as mock_config:
        mock_config.GOOGLE_MAPS_API_KEY = ''
        mock_config.SLACK_CHANNEL = '#test-channel'
        slackbot._upload_map_image(mock_client, '47.6 N, 122.3 W')

    mock_client.files_upload.assert_not_called()


def test_upload_map_image_uploads_when_api_key_set():
    mock_client = MagicMock()
    fake_image = b'fake-png-bytes'

    with patch('zoleotracker.slackbot.config') as mock_config, \
         patch('zoleotracker.slackbot.maps.parse_gps_coordinates', return_value=(47.6, -122.3)), \
         patch('zoleotracker.slackbot.maps.fetch_map_image', return_value=fake_image):
        mock_config.GOOGLE_MAPS_API_KEY = 'FAKE_KEY'
        mock_config.SLACK_CHANNEL = '#test-channel'
        slackbot._upload_map_image(mock_client, '47.6 N, 122.3 W')

    mock_client.files_upload.assert_called_once()
    call_kwargs = mock_client.files_upload.call_args.kwargs
    assert call_kwargs['channels'] == '#test-channel'
    assert call_kwargs['content'] == fake_image


def test_upload_map_image_logs_warning_on_parse_error():
    mock_client = MagicMock()

    with patch('zoleotracker.slackbot.config') as mock_config, \
         patch('zoleotracker.slackbot.maps.parse_gps_coordinates', side_effect=ValueError("bad")):
        mock_config.GOOGLE_MAPS_API_KEY = 'FAKE_KEY'
        mock_config.SLACK_CHANNEL = '#test-channel'
        # Should not raise; warning is logged instead
        slackbot._upload_map_image(mock_client, 'bad coords')

    mock_client.files_upload.assert_not_called()


def test_post_location_uploads_map_image_when_new_checkin(tmp_path, monkeypatch):
    monkeypatch.setenv('SLACK_TOKEN', 'test-token')
    mock_row = databaseSQL.CheckinRow(
        id=1,
        file='subject',
        checkin='2023-08-01 10:00:00',
        location='47.6 N, 122.3 W',
        link='http://maps.example.com',
    )

    @contextmanager
    def mock_db_conn():
        yield MagicMock()

    mock_client = MagicMock()
    prev_file = tmp_path / 'previous_checkin.txt'

    with patch('zoleotracker.databaseSQL.db_connection', mock_db_conn), \
         patch('zoleotracker.databaseSQL.read_last_row', return_value=[mock_row]), \
         patch('zoleotracker.slackbot.config') as mock_config, \
         patch('zoleotracker.slackbot.get_slack_client', return_value=mock_client), \
         patch('zoleotracker.slackbot._upload_map_image') as mock_upload:
        mock_config.PREVIOUS_CHECKIN_FILE = str(prev_file)
        mock_config.SLACK_CHANNEL = '#test-channel'

        slackbot.post_location()

    mock_upload.assert_called_once_with(mock_client, '47.6 N, 122.3 W')
