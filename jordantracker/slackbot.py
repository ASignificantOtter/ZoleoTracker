#automatic slack posting of Jordan Tracker
from jordantracker import config
import slack
from flask import Flask
from slackeventsapi import SlackEventAdapter
import csv
import os


SLACK_TOKEN = config.SLACK_TOKEN
SIGNING_SECRET = config.SIGNING_SECRET
client = slack.WebClient(token=SLACK_TOKEN)


app = Flask(__name__)
slack_event_adapter = SlackEventAdapter(SIGNING_SECRET, '/slack/events', app)

def fpath():
    current = os.path.dirname(os.path.realpath(__file__))
    parent = os.path.dirname(current)
    file = os.path.join(parent, parent+"/location.csv")

    return file

file = fpath()

def import_csv(csvfilename):
    with open(csvfilename, "r", encoding="utf-8", errors="ignore") as f:
       csv_reader = csv.reader(f, delimiter='\t')
       for line in csv_reader:
           x = line[1]
           y = line[2]
           z = line[3]
    return x, y, z


def hello():
    
    client.chat_postMessage(channel='#jordan-tracker',text='Hello World with hidden secrets')

    pass

def update_location():

    file = fpath()
    date, gps, map = import_csv(file)
   

    client = slack.WebClient(token=SLACK_TOKEN)
    client.chat_postMessage(channel='#jordan-tracker',text='I was last here: ' + gps + '\nat this time: ' + date + '\n' + map)

    pass

if __name__ == "__main__":
    app.run(debug=True)

