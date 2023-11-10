from time import sleep

def _OpenFeedDoor() -> bool:
    return True


def _CloseFeedDoor() -> bool:
    return True


def Feed(feed_time) -> bool:
    """Open and close the feeding door"""
    print("feeding...")
    result = _OpenFeedDoor()
    if not result:
        return False
    
    sleep(feed_time)

    result = _CloseFeedDoor()
    print("fed")
    return result
