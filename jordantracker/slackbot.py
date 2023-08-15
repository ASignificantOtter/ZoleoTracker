#automatic slack posting of Jordan Tracker
from jordantracker import config
import slack
import csv
import os


def file_path() -> str: 
    cwd = os.path.dirname(os.path.realpath(__file__))
    parent_directory = os.path.dirname(cwd)
    csv_file_path = os.path.join(parent_directory, parent_directory+"/location.csv")

    return csv_file_path


def import_csv(csv_file_path) -> tuple[str, str, str]:
    csv_data = []

    with open(csv_file_path, "r", encoding="utf-8", errors="ignore") as f:
       csv_reader = csv.reader(f, delimiter='\t')
       for row in csv_reader:
           csv_data.append(row)
           
    latest_update = csv_data[-1]
    
    date = latest_update[1]
    gps = latest_update[2]
    map = latest_update[3]

    return date, gps, map


def post_location() -> None:

    csv_file = file_path()
    date, gps, map = import_csv(csv_file)
   
    client = slack.WebClient(token=config.SLACK_TOKEN)
    client.chat_postMessage(channel='#jordan-tracker',text='I was last here: ' + gps + '\nat this time: ' + date + '\n' + map)

    


