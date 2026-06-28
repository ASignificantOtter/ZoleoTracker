# Config file for the email server and the subject to search for

import os

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

EMAIL_SERVER = 'imap.gmail.com'
CHECKIN_EMAIL_SUBJECT = 'Check-in message from SlothPace'
MESSAGE_FORMAT = '(RFC822)'
EMAIL_FOLDER = 'inbox'

# Database path — override with ZOLEO_DB_PATH env var for non-default locations
DATABASE_PATH = os.environ.get(
    'ZOLEO_DB_PATH',
    os.path.join(_PROJECT_ROOT, 'zoleo.db'),
)

# State file that records the last check-in posted to Slack
PREVIOUS_CHECKIN_FILE = os.path.join(_PROJECT_ROOT, 'previous_checkin.txt')

# Slack channel to post location updates to
SLACK_CHANNEL = '#jordan-tracker'
