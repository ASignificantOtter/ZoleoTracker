#automatic slack posting of Jordan Tracker
from jordantracker import config
import slack
from flask import Flask
from slackeventsapi import SlackEventAdapter

SLACK_TOKEN = config.SLACK_TOKEN
SIGNING_SECRET = config.SIGNING_SECRET

app = Flask(__name__)
slack_event_adapter = SlackEventAdapter(SIGNING_SECRET, '/slack/events', app)

def hello():
    
    client = slack.WebClient(token=SLACK_TOKEN)
    client.chat_postMessage(channel='#jordan-tracker',text='Hello World with hidden secrets')

    pass

if __name__ == "__main__":
    app.run(debug=True)

