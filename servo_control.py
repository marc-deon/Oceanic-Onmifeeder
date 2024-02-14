from time import sleep
from threading import Thread
import RPi.GPIO as GPIO

#####################################################################
#  FILE API  #
##############
#
# Public:
#   bool Feed(feed_time:int)
#
# Private:
#   bool _OpenFeedDoor()
#   None _CloseFeedDoor(feed_time)
#
#####################################################################


def _OpenFeedDoor() -> bool:
    """Private: Physically open door"""
    # TODO: Open door here
    print("OPENING FEED DOOR")
    return True


# TODO: Rework messaging system to allow for this to 'return' a success
def _CloseFeedDoor(feed_time:int) -> None:
    """Private: Wait, and physically close door"""

    # This for loop could be replaced to support float feed times
    print("feeding for", feed_time, "...")
    for i in range(feed_time):
        print(("tock" if i%2 else "tick") + "...")
        # Wait
        sleep(1)

    # TODO: Open door here
    print("CLOSING FEED DOOR")



def Feed(feed_time:int) -> bool:
    """Public: Open and close the feeding door in new thread"""
    
    # Open door
    ok = _OpenFeedDoor()
    # Open new thread to close door
    t = Thread(target=_CloseFeedDoor, args=(feed_time,))
    t.start()
    # Return that we've succeeded in at least opening the door
    return ok
