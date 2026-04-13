from zoleotracker import zoleotracker
from zoleotracker import slackbot


def run() -> None:
    zoleotracker.tracker()
    slackbot.post_location()


if __name__ == '__main__':
    run()
