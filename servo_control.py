from time import sleep
from threading import Thread
#import RPi.GPIO as GPIO
from gpiozero import AngularServo
from gpiozero import Servo
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

SERVO_PIN = 18

def MoveServo(angle):
    # Might need to adjust
    min_pulse_width = 1/1000 #1.0/1000 # ms -> seconds
    max_pulse_width = 2/1000 # 2.0/1000 # ms -> seconds
    
    servo = AngularServo(SERVO_PIN, min_angle=0, max_angle=180, min_pulse_width=min_pulse_width, max_pulse_width=max_pulse_width)
    servo.angle = angle
    sleep(0.25)
    servo.close()
    

if __name__ == "__main__":
    angle = 0
    while True:
        print("a")
        MoveServo(angle)
        sleep(1)
        angle+=50 % 180
        

def _OpenFeedDoor() -> None:
    """Private: Physically open door"""
    # TODO: Open door here
    print("OPENING FEED DOOR")
    OPEN_ANGLE = 170
    MoveServo(OPEN_ANGLE)
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
    MoveServo(0)

    # Prepare response message
    ok = True
    if ok:
        response = {"error": ERROR.OK, "message_type": MESSAGE.MANUAL_FEED_CLOSE, "channel":CHANNELS.CONTROL}
    else:
        response = {"error": ERROR.FEED_ERROR, "message_type":MESSAGE.MANUAL_FEED_CLOSE, "channel":CHANNELS.CONTROL}
    message_queue.Add(response)




def Feed(feed_time:int) -> None:
    """Public: Open and close the feeding door in new thread"""
    print("feed")
    # Open door
    ok = _OpenFeedDoor()
    
    # Open new thread to (wait and then) close door
    t = Thread(target=_CloseFeedDoor, args=(feed_time,))
    t.start()
