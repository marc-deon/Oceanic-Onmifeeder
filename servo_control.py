from time import sleep
from threading import Thread
import RPi.GPIO as GPIO
import message_queue
from enums import *

#####################################################################
#  FILE API  #
##############
#
# Public:
#   Feed(feed_time:int) -> None
#
# Private:
#   _OpenFeedDoor() -> None
#   _CloseFeedDoor(feed_time) -> None
#
#####################################################################


def _OpenFeedDoor() -> None:
    """Private: Physically open door"""
    # TODO: Open door here
    print("OPENING FEED DOOR")

    # Prepare response message
    ok = True
    if ok:
        response = {"error": ERROR.OK, "message_type": MESSAGE.MANUAL_FEED_OPEN, "channel":CHANNELS.CONTROL}
    else:
        response = {"error": ERROR.FEED_ERROR, "message_type":MESSAGE.MANUAL_FEED_OPEN, "channel":CHANNELS.CONTROL}
    message_queue.Add(response)


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

    # Prepare response message
    ok = True
    if ok:
        response = {"error": ERROR.OK, "message_type": MESSAGE.MANUAL_FEED_CLOSE, "channel":CHANNELS.CONTROL}
    else:
        response = {"error": ERROR.FEED_ERROR, "message_type":MESSAGE.MANUAL_FEED_CLOSE, "channel":CHANNELS.CONTROL}
    message_queue.Add(response)




def Feed(feed_time:int) -> None:
    """Public: Open and close the feeding door in new thread"""
    
    # Open door
    ok = _OpenFeedDoor()
    
    # Open new thread to (wait and then) close door
    t = Thread(target=_CloseFeedDoor, args=(feed_time,))
    t.start()
