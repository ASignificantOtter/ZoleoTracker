from jordantracker import jordantracker
from jordantracker import slackbot

def run():
    jordantracker.tracker()
    slackbot.post_location()


if __name__ == '__main__':
    run()
    