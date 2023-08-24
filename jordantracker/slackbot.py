# automatic slack posting of Jordan Tracker
import csv
import os
import slack
from jordantracker import config



def file_path(filename: str) -> str:
    cwd = os.path.dirname(os.path.realpath(__file__))
    parent_directory = os.path.dirname(cwd)
    file_path = os.path.join(parent_directory, parent_directory+filename)

    return file_path


def get_current_checkin() -> tuple[str, str, str]:
    csv_data = []
    csv_file_path = file_path('/location.csv')

    with open(csv_file_path, "r", encoding="utf-8", errors="ignore") as f:
       csv_reader = csv.reader(f, delimiter='\t')
       for row in csv_reader:
           csv_data.append(row)
           
    latest_update = csv_data[-1]
    
    date = latest_update[1]
    gps = latest_update[2]
    loc_link = latest_update[3]

    return date, gps, loc_link

def should_post(previous_checkin, current_checkin) -> bool:

    if current_checkin > previous_checkin:
        return True

def get_previous_checkin() -> str:

    text_file = file_path('/previous_checkin.txt')
    with open(text_file, 'r', encoding='utf-8') as previous_checkin_file:
        previous_checkin = previous_checkin_file.read()

    return previous_checkin

def post_location() -> None:
    
    current_checkin, gps, loc_link = get_current_checkin()
    previous_checkin = get_previous_checkin()

    if should_post(previous_checkin, current_checkin):
        client = slack.WebClient(token=config.SLACK_TOKEN)
        client.chat_postMessage(channel='#jordan-tracker',text='I was last here: ' + gps + '\nat this time: ' + current_checkin + '\n' + loc_link)
        with open(file_path('/previous_checkin.txt'), 'w', encoding='utf-8') as previous_checkin_text_fp:
         previous_checkin_text_fp.writelines(current_checkin)
