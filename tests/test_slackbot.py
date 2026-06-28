from zoleotracker import slackbot


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
