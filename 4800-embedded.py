#! /usr/bin/env python3

################################################################################
## 4800-embedded.py
##
## Program to run on embedded fishtank feeder.
##
## Initially connects to server and registers username.
##
## Can then be contacted by App to be queried for stats and video.
##
################################################################################

# import socket_convenience
import cv2
import enet
import enum
import imutils
import json
import random
import servo_control
from dataclasses import dataclass, field
from typing import List
import socket_convenience as sc

SERVER_IP = '4800.highlyderivative.games'
SERVER_PORT = 4800
WEBCAM_WIDTH = 320

class CHANNELS(enum.IntEnum):
    HOLEPUNCH = enum.auto()
    CONTROL = enum.auto()
    STATS = enum.auto()
    VIDEO = enum.auto()
    MAX = enum.auto()


class ERROR(enum.IntEnum):
    ERROR = enum.auto()
    OK = enum.auto()
    MALFORMED_TIME = enum.auto()
    INVALID_TIME = enum.auto()
    INVALID_LENGTH = enum.auto()
    TEMP_MINMAX = enum.auto()
    PH_MINMAX = enum.auto()
    FEED_ERROR = enum.auto()


class MESSAGE(enum.IntEnum):
    GET_SETTINGS = enum.auto()
    GET_STATS = enum.auto()
    MANUAL_FEED = enum.auto()
    SET_FEED_TIME = enum.auto()
    SET_FEED_LENGTH = enum.auto()
    SET_TEMP_WARNING = enum.auto()
    SET_PH_WARNING = enum.auto()
    RESET_SETTINGS = enum.auto()
    SAVE_SETTINGS = enum.auto()

@dataclass
class Settings:
    # Keep these secret
    _username:str        = "poseidon"
    _salted_password:str = ""

    # Safe to give to app
    feed_time: List[int]     = field(default_factory=lambda: [0, 0]) # Time of day, hour and minute
    feed_length:float        = 0                                     # seconds
    temp_warning:List[float] = field(default_factory=lambda: [0, 0]) # low, high
    ph_warning:List[float]   = field(default_factory=lambda: [0, 0]) # low, high

    @property
    def hp_key(self):
        return self._username

enetHost:enet.Host = None

settings:Settings


def LoadSettings(force_default=False) -> None:
    """Load embedded settings from file, or use default on error"""
    global settings

    if force_default:
        settings = Settings()
        return

    # Try load from file
    try:
        with open("4800-settings.json") as f:
            settings = Settings(**json.load(f))
    except:
        settings = Settings()
        print("Error: using default settings")


def SaveSettings() -> bool:
    """Save embedded settings to file"""
    # Write to file
    try:
        with open ("4800-settings.json") as f:
            f.write(settings.asdict())
    except:
        return False
    return True


# TODO(#7): Implement servo control
def FeedServo() -> bool:
    """Open and close the feed door"""
    # if not empty?
    return servo_control.Feed()


def HandleControl(message:str) -> str:
    """Deal with the bulk of ENet message, i.e. managing settings and manual feeding"""
    ## Message format TBD, but maybe something like this?
    ## GET_SETTINGS -> OK, dict
    ## MANUAL_FEED -> OK
    ## SET_FEED_TIME {TIME} -> OK
    ## SET_TEMP_WARNING {LOW} {HIGH} -> OK
    ## SET_PH_WARNING {LOW} {HIGH} -> OK
    response = []

    match message:
        # Send relevent settings back to the app
        case [MESSAGE.GET_SETTINGS]:
            # Don't wanna return *all* the settings...
            d = {
                "feed_time": settings.feed_time,
                "feed_length": settings.feed_length,
                "temp_warning": settings.temp_warning,
                "ph_warning": settings.ph_warning,
            }
            response = [ERROR.OK, d]


        case [MESSAGE.GET_STATS]:
            response = [ERROR.OK, HandleStats(message)]


        # Manually trigger feeding
        case [MESSAGE.MANUAL_FEED]:
            ok = FeedServo()
            if ok:
                response = [ERROR.OK]
            else:
                response = [ERROR.ERROR, ERROR.FEED_ERROR]


        # Set a daily feed time
        case [MESSAGE.SET_FEED_TIME, time]:
            # Expects 24 HH:MM
            # Split into hours and minutes, convert to integers
            time = map(int, time.split(":"))
            
            if len(time) != 2:
                response = [ERROR.ERROR, ERROR.MALFORMED_TIME]

            if time[0] < 0 or time[0] > 23 or time[1] < 0 or time[1] > 59:
                response = [ERROR.ERROR, ERROR.INVALID_TIME]
            else:
                settings.feed_time = time
                response = [ERROR.OK]


        # Set how long the door should be open for feeding
        case [MESSAGE.SET_FEED_LENGTH, seconds]:
            seconds = float(seconds)
            if seconds <= 0:
                response = [ERROR.ERROR, ERROR.INVALID_LENGTH]
            else:
                settings.feed_length = seconds


        # Set minimum and maximum temperature warnings
        case [MESSAGE.SET_TEMP_WARNING, low, high]:
            low, high = float(low), float(high)
            if high <= low:
                # Exact error string shown to user will be handled on clientside
                response = [ERROR.ERROR, ERROR.TEMP_MINMAX]
            else:
                settings.temp_warning = low, high
                response = [ERROR.OK]


        # Set minimum and maximum pH warnings
        case [MESSAGE.SET_PH_WARNING, low, high]:
            low, high = float(low), float(high)
            if high <= low:
                # Exact error string shown to user will be handled on clientside
                response = [ERROR.ERROR, ERROR.PH_MINMAX]
            else:
                # Do the thing
                settings.ph_warning = low, high
                response = [ERROR.OK]


        # Reset settings
        case [MESSAGE.RESET_SETTINGS]:
            settings = Settings()
            response = [ERROR.OK]
        

        # Save settings
        case [MESSAGE.SAVE_SETTINGS]:
            SaveSettings()
            response = [ERROR.OK]
    
    return response


# TODO(#8): Implement stats (temp, ph) reading
def HandleStats(message:str) -> str:
    """Return current temp, ph"""
    temp = random.randint(75, 80)
    ph =  7 + 2 * random.random() - 1
    message = json.dumps({'temp': temp, 'ph': ph})
    return message


demo_vid = None
# TODO(#9): Implement webcam streaming fully
def HandleVideo(message:str, use_demo:bool=True) -> bytes:
    """Capture a video frame from the webcam and prepare it to be send to the app"""
    global demo_vid

    if use_demo:
        if not demo_vid:
            demo_vid = cv2.VideoCapture("take_it_yeesy.mp4")
        vid = demo_vid
    else:
         vid = cv2.VideoCapture(0)

    # Read next frame
    nextFrameValid, frame = vid.read()

    if not nextFrameValid:
        if use_demo:
            # Loop
            demo_vid = cv2.VideoCapture("take_it_yeesy.mp4")
            return HandleVideo(message, use_demo)
        return None

    # Resize
    frame = imutils.resize(frame,width=WEBCAM_WIDTH)

    # Encode as jpeg
    encoded, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
    return bytes(buffer)


# TODO(#10): Implement holepunch via ENet
def RegisterForHolepunch() -> None:
    # I think that holepunching should indeed use enet...
    # Simpler to keep the port alive, don't need to FRSH

    # Instantiate enet host, peer; save the host
    global enetHost
    # Bind to all IPv4 addresses, any port?
    enetHost = enet.Host(enet.Address('0.0.0.0', 0), peerCount=2)
    peer = enetHost.connect(enet.Address(SERVER_IP, SERVER_PORT), channelCount=1)
    
    # use enet to register
    enetHost.service(0)
    s = f"HOST {sc.GetLocalIp()} {settings.hp_key} {enetHost.address.port}".encode()
    peer.send(0, enet.Packet(s, enet.PACKET_FLAG_RELIABLE))
    response = enetHost.service(1000)
    if response.type == enet.EVENT_TYPE_NONE:
        raise Exception("Unable to register for holepunch")


def Service() -> None:
    """Main loop"""
    event = enetHost.service(0)
    response = None
    channel = None
    flags = enet.PACKET_FLAG_RELIABLE

    match event.type:
        case enet.EVENT_TYPE_NONE:
            pass

        case enet.EVENT_TYPE_CONNECT:
            pass

        case enet.EVENT_TYPE_DISCONNECT:
            pass

        case enet.EVENT_TYPE_RECEIVE:
            channel = event.channelID
            match channel:
                case CHANNELS.CONTROL:
                    response = HandleControl(event.packet.data)
                case CHANNELS.STATS:
                    response = HandleStats(event.packet.data)
                case CHANNELS.VIDEO:
                    response = HandleVideo(event.packet.data)
                    flags = enet.PACKET_FLAG_UNRELIABLE_FRAGMENT | enet.PACKET_FLAG_UNSEQUENCED

    if response:
        event.peer.send(channel, enet.Packet(response, flags))


def main() -> None:
    LoadSettings()
    RegisterForHolepunch()
    Service()


main()
