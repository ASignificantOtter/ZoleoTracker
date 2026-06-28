import base64
import email.message
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from zoleotracker import config, zoleotracker


def test_stamp_time_parses_valid_date():
    result = zoleotracker.stamp_time("01 Aug 2023 10:00:00")
    assert result == datetime(2023, 8, 1, 10, 0, 0)


def test_stamp_time_raises_on_invalid_format():
    with pytest.raises(ValueError):
        zoleotracker.stamp_time("not-a-date")


def _make_raw_email(subject: str, body: str) -> bytes:
    """Build minimal raw email bytes with a base64-encoded plain-text body.

    Wraps each line in an HTML <p> tag so that html2text preserves line
    boundaries (html2text collapses bare newlines into spaces).
    """
    html_body = ''.join(f'<p>{line}</p>' for line in body.splitlines())
    msg = email.message.Message()
    msg['Subject'] = subject
    msg['Content-Type'] = 'text/plain'
    msg['Content-Transfer-Encoding'] = 'base64'
    msg.set_payload(base64.b64encode(html_body.encode()).decode())
    return msg.as_bytes()


def _mock_imap(raw_email_bytes: bytes) -> MagicMock:
    mock_mail = MagicMock()
    mock_mail.search.return_value = ('OK', [b'1'])
    mock_mail.fetch.return_value = ('OK', [(b'1 (RFC822)', raw_email_bytes)])
    return mock_mail


def test_parse_email_server_skips_non_matching_subject():
    raw = _make_raw_email('Wrong subject', 'body text')
    mock_mail = _mock_imap(raw)

    with patch('zoleotracker.zoleotracker.get_inbox', return_value=mock_mail):
        df = zoleotracker.parse_email_server()

    assert df.empty


def test_parse_email_server_parses_matching_email():
    body = (
        "My location is 47.6 N, 122.3 W\n"
        "sent at: 01 Aug 2023 10:00:00 (UTC)\n"
        "[ View on map ](https://maps.example.com/)\n"
    )
    raw = _make_raw_email(config.CHECKIN_EMAIL_SUBJECT, body)
    mock_mail = _mock_imap(raw)

    with patch('zoleotracker.zoleotracker.get_inbox', return_value=mock_mail):
        df = zoleotracker.parse_email_server()

    assert len(df) == 1
    assert df.iloc[0]['location'] == '47.6 N, 122.3 W'
    assert df.iloc[0]['link'] == 'https://maps.example.com/'


def test_parse_email_server_skips_email_with_missing_fields():
    # Body missing the map link — should be skipped with a warning
    body = (
        "My location is 47.6 N, 122.3 W\n"
        "sent at: 01 Aug 2023 10:00:00 (UTC)\n"
    )
    raw = _make_raw_email(config.CHECKIN_EMAIL_SUBJECT, body)
    mock_mail = _mock_imap(raw)

    with patch('zoleotracker.zoleotracker.get_inbox', return_value=mock_mail):
        df = zoleotracker.parse_email_server()

    assert df.empty


def test_parse_email_server_returns_empty_when_inbox_empty():
    mock_mail = MagicMock()
    mock_mail.search.return_value = ('OK', [b''])

    with patch('zoleotracker.zoleotracker.get_inbox', return_value=mock_mail):
        df = zoleotracker.parse_email_server()

    assert df.empty
