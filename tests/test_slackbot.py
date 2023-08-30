from datetime import datetime
from zoleotracker import slackbot

def test_should_post_returns_True_if_date_is_newer():

    previous_checkin_raw = '30 Jul 2023 17:26:53'
    current_checkin_raw = '01 Aug 2023 17:26:53'
    datetime_format = '%d %b %Y %H:%M:%S'
    
    previous_checkin = datetime.strptime(previous_checkin_raw, datetime_format)
    current_checkin = datetime.strptime(current_checkin_raw, datetime_format)

    assert slackbot.should_post(previous_checkin, current_checkin) 


def test_should_post_returns_False_if_date_is_same():

    previous_checkin_raw = '30 Jul 2023 17:26:53'
    datetime_format = '%d %b %Y %H:%M:%S'
    
    previous_checkin = datetime.strptime(previous_checkin_raw, datetime_format)

    assert not slackbot.should_post(previous_checkin, previous_checkin)
  

def test_should_post_returns_False_if_date_is_older():

    previous_checkin_raw = '30 Jul 2023 17:26:53'
    current_bad_checkin_raw = '29 Jul 2023 17:26:53'
    datetime_format = '%d %b %Y %H:%M:%S'
    
    previous_checkin = datetime.strptime(previous_checkin_raw, datetime_format)
    current_bad_checkin = datetime.strptime(current_bad_checkin_raw, datetime_format)

    assert not slackbot.should_post(previous_checkin, current_bad_checkin)
