from time import sleep
from threading import Thread
import schedule
from datetime import timedelta

def _OpenFeedDoor() -> bool:
    print("OPENING FEED DOOR")
    return True


def _CloseFeedDoor() -> bool:
    print("CLOSING FEED DOOR")
    return True


def Feed(feed_time) -> bool:
    """Open and close the feeding door"""
    _OpenFeedDoor()
    feed_time = timedelta(seconds=feed_time)

    # Junk second
    schedule.every().second.until(feed_time).do(_afterFeed).tag("feed")
    return True


def _afterFeed():
    _CloseFeedDoor()
    return schedule.CancelJob

