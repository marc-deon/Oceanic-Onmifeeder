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
import imutils
import json
import random
import servo_control
from dataclasses import dataclass, field
from typing import List
import socket_convenience as sc
from enums import *


SERVER_IP = '4800.highlyderivative.games'
SERVER_PORT = 4800
WEBCAM_WIDTH = 320


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


def HandleControl(message:str) -> dict:
    """Deal with the bulk of ENet message, i.e. managing settings and manual feeding"""
    ## Message format TBD, but maybe something like this?
    ## GET_SETTINGS -> OK, dict
    ## MANUAL_FEED -> OK
    ## SET_FEED_TIME {TIME} -> OK
    ## SET_TEMP_WARNING {LOW} {HIGH} -> OK
    ## SET_PH_WARNING {LOW} {HIGH} -> OK
    response = None

    match message:
        # Send relevent settings back to the app
        case [MESSAGE.GET_SETTINGS]:
            # Don't wanna return *all* the settings...
            response = {
                "error": ERROR.OK,
                "feed_time": settings.feed_time,
                "feed_length": settings.feed_length,
                "temp_warning": settings.temp_warning,
                "ph_warning": settings.ph_warning,
            }


        # Manually trigger feeding
        case [MESSAGE.MANUAL_FEED]:
            ok = FeedServo()
            if ok:
                response = {'error':ERROR.OK}
            else:
                response = {'error': ERROR.FEED_ERROR}


        # Set a daily feed time
        case [MESSAGE.SET_FEED_TIME, time]:
            # Expects 24 HH:MM
            # Split into hours and minutes, convert to integers
            time = map(int, time.split(":"))
            
            if len(time) != 2:
                response = {'error': ERROR.MALFORMED_TIME}

            if time[0] < 0 or time[0] > 23 or time[1] < 0 or time[1] > 59:
                response = {'error': ERROR.INVALID_TIME}
            else:
                settings.feed_time = time
                response = {'error':ERROR.OK}


        # Set how long the door should be open for feeding
        case [MESSAGE.SET_FEED_LENGTH, seconds]:
            seconds = float(seconds)
            if seconds <= 0:
                response = {'error': ERROR.INVALID_LENGTH}
            else:
                settings.feed_length = seconds


        # Set minimum and maximum temperature warnings
        case [MESSAGE.SET_TEMP_WARNING, low, high]:
            low, high = float(low), float(high)
            if high <= low:
                # Exact error string shown to user will be handled on clientside
                response = {'error': ERROR.TEMP_MINMAX}
            else:
                settings.temp_warning = low, high
                response = {'error':ERROR.OK}


        # Set minimum and maximum pH warnings
        case [MESSAGE.SET_PH_WARNING, low, high]:
            low, high = float(low), float(high)
            if high <= low:
                # Exact error string shown to user will be handled on clientside
                response = {'error': ERROR.PH_MINMAX}
            else:
                # Do the thing
                settings.ph_warning = low, high
                response = {'error':ERROR.OK}


        # Reset settings
        case [MESSAGE.RESET_SETTINGS]:
            settings = Settings()
            response = {'error':ERROR.OK}
        

        # Save settings
        case [MESSAGE.SAVE_SETTINGS]:
            SaveSettings()
            response = {'error':ERROR.OK}
    
    return response


# TODO(#8): Implement stats (temp, ph) reading
def HandleStats(message:str) -> dict:
    """Return current temp, ph"""
    temp = random.randint(75, 80)
    ph =  7 + 2 * random.random() - 1
    return {'message_type':MESSAGE.GET_STATS, 'error': ERROR.OK, 'temp': temp, 'ph': ph}


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
    print("registering...")

    # Instantiate enet host, peer; save the host
    global enetHost
    # Bind to all IPv4 addresses, any port?
    enetHost = enet.Host(enet.Address(None, 0), peerCount=32)
    # We might want to save this later for a graceful disconnect or something
    hpServerPeer = None
    enetHost.connect(enet.Address(SERVER_IP, SERVER_PORT), channelCount=CHANNELS.MAX)

    # use enet to register
    s = f"HOST {sc.GetLocalIp()} {settings.hp_key} {enetHost.address.port}".encode()

    # Timeout after a while
    for _ in range(15):
        event = enetHost.service(500)
        if event.type == enet.EVENT_TYPE_NONE:
            pass
        if event.type == enet.EVENT_TYPE_CONNECT:
            hpServerPeer = event.peer
            hpServerPeer.send(CHANNELS.HOLEPUNCH, enet.Packet(s, enet.PACKET_FLAG_RELIABLE))
            print("Connected, sending", s)
        if event.type == enet.EVENT_TYPE_RECEIVE:
            if event.packet.data == b'HOSTING':
                break
    else:
        raise TimeoutError

    print("Done registering")

def HandleHolepunch(b:bytes):
    message = b.decode().split(" ")
    print("handling holepunch", message)
    match message:
        case ["EXPECT", addr, local, port, localport]:
            enetHost.connect(enet.Address(addr, int(port)), channelCount=CHANNELS.MAX)
            enetHost.connect(enet.Address(local, int(localport)), channelCount=CHANNELS.MAX)
            print("expecting", addr, local, int(port), int(localport))
        case _:
            print("Unknown HP format")

def Service() -> None:
    """Main loop"""

    event = enetHost.service(500)
    response:bytes = None
    channel:int = None
    flags = enet.PACKET_FLAG_RELIABLE

    match event.type:
        case enet.EVENT_TYPE_NONE:
            pass

        case enet.EVENT_TYPE_CONNECT:
            print("case enet.EVENT_TYPE_CONNECT")
            pass

        case enet.EVENT_TYPE_DISCONNECT:
            print("case enet.EVENT_TYPE_DISCONNECT")
            pass

        case enet.EVENT_TYPE_RECEIVE:
            channel = CHANNELS(event.channelID)
            match channel:
                case CHANNELS.HOLEPUNCH:
                    response = HandleHolepunch(event.packet.data)
                    response = json.dumps(response).encode()
                case CHANNELS.CONTROL:
                    print("Got CONTROL message")
                    response = HandleControl(event.packet.data)
                    response = json.dumps(response).encode()
                case CHANNELS.STATS:
                    # print("Got STATS message")
                    response = HandleStats(event.packet.data)
                    response = json.dumps(response).encode()
                case CHANNELS.VIDEO:
                    response = HandleVideo(event.packet.data)
                    flags = enet.PACKET_FLAG_UNRELIABLE_FRAGMENT | enet.PACKET_FLAG_UNSEQUENCED

    if response:
        # print("sending response", response)
        event.peer.send(channel, enet.Packet(response, flags))



def main() -> None:
    LoadSettings()
    RegisterForHolepunch()
    while True:
        Service()


main()
