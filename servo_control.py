from time import sleep
from threading import Thread

def _OpenFeedDoor() -> bool:
    return True


def _CloseFeedDoor() -> bool:
    return True


def Feed(feed_time) -> bool:
    """Open and close the feeding door"""
    t = Thread(target=_feed, args=[feed_time])
    t.run()
    print("returning from Feed")
    return True


def _feed(feed_time) -> bool:
    print("feeding...")
    result = _OpenFeedDoor()
    if not result:
        return False
    print("sleeping")   
    sleep(0)
    sleep(feed_time)
    print("end sleep")

    result = _CloseFeedDoor()
    print("fed")
    return result
