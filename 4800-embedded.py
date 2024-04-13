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
import sensor_control
from dataclasses import dataclass, field, asdict
from typing import List
import socket_convenience as sc
from enums import *
import schedule
from datetime import datetime
import message_queue

SERVER_IP = 'highlyderivative.games'
SERVER_PORT = 4800
WEBCAM_WIDTH = 320


@dataclass()
class Settings:
    # Keep these secret
    _username:str        = "poseidon"
    _salted_password:str = ""


    # Safe to give to app
    last_feed: List[int]     = field(default_factory=lambda: [1980, 1, 1, 0, 0]) # year, month, day, hour, minute
    feed_time: List[int]     = field(default_factory=lambda: [8, 0]) # Time of day, hour and minute
    feed_length:float        = 1                                     # seconds
    temp_warning:List[float] = field(default_factory=lambda: [10, 99]) # low, high
    ph_warning:List[float]   = field(default_factory=lambda: [1, 14]) # low, high

    @property
    def hp_key(self):
        return self._username

    def asdict(self) -> dict:
        return asdict(self)

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
        with open("4800-settings.json", 'r') as f:
            settings = Settings(**json.load(f))
    except:
        settings = Settings()
        print("Error: using default settings")


def SaveSettings(message) -> bool:
    """Save embedded settings to file"""
    print("Saving settings...")
    # Update according to message
    settings.feed_time = message["feed_time"]
    print("feed time is now", message['feed_time'])
    settings.feed_length = message["feed_length"]
    settings.temp_warning = message["temp_warning"]
    settings.ph_warning = message["ph_warning"]
    print("  Updated struct")
    UpdateSchedule()

    # Write to file
    try:
        with open ("4800-settings.json", 'w') as f:
            f.write(json.dumps(settings.asdict(), indent=2))
            print("  Wrote to file")
    except Exception as e:
        print("Save error", e)
        return False
    print("Saved settings")
    return True


def UpdateSchedule():
    schedule.clear("settings")
    time = f"{settings.feed_time[0]:02d}:{settings.feed_time[1]:02d}"
    schedule.every().day.at(time).do(FeedServo).tag("settings")


# TODO(#7): Implement servo control
def FeedServo() -> None:
    """Open and close the feed door"""
    # if not empty?
    t = datetime.now()
    settings.last_feed = [t.year, t.month, t.day, t.hour, t.minute]
    servo_control.Feed(settings.feed_length)


def HandleControl(message:bytes) -> None:
    """Deal with the bulk of ENet message, i.e. managing settings and manual feeding"""
    ## Message format TBD, but maybe something like this?
    ## GET_SETTINGS -> OK, dict
    ## MANUAL_FEED -> OK
    ## SET_FEED_TIME {TIME} -> OK
    ## SET_TEMP_WARNING {LOW} {HIGH} -> OK
    ## SET_PH_WARNING {LOW} {HIGH} -> OK
    global settings

    response = None
    message = json.loads(message.decode())
    print("Control message", message)

    match message["message_type"]:
        # Send relevent settings back to the app
        case MESSAGE.GET_SETTINGS:
            # Don't wanna return *all* the settings...
            response = {
                "error": ERROR.OK,
                "message_type": MESSAGE.GET_SETTINGS,
                "feed_time": settings.feed_time,
                "feed_length": settings.feed_length,
                "temp_warning": settings.temp_warning,
                "ph_warning": settings.ph_warning
            }
            print(response)

        # Manually trigger feeding
        case MESSAGE.MANUAL_FEED_OPEN:
            # ok =
            FeedServo()
            #if ok:
            #    response = {'error': ERROR.OK, "message_type": MESSAGE.MANUAL_FEED}
            #else:
            #    response = {'error': ERROR.FEED_ERROR, "message_type": MESSAGE.MANUAL_FEED}


        # Set a daily feed time
        case MESSAGE.SET_FEED_TIME:
            # Expects 24 HH:MM
            # Split into hours and minutes, convert to integers
            time = map(int, message["time"].split(":"))
            
            if len(time) != 2:
                response = {'error': ERROR.MALFORMED_TIME,"message_type": MESSAGE.SET_FEED_TIME,}

            if time[0] < 0 or time[0] > 23 or time[1] < 0 or time[1] > 59:
                response = {'error': ERROR.INVALID_TIME,"message_type": MESSAGE.SET_FEED_TIME,}
            else:
                settings.feed_time = time
                response = {'error':ERROR.OK,"message_type": MESSAGE.SET_FEED_TIME,}
                UpdateSchedule()


        # Set how long the door should be open for feeding
        case MESSAGE.SET_FEED_LENGTH:
            seconds = float(message["seconds"])
            if seconds <= 0:
                response = {'error': ERROR.INVALID_LENGTH,"message_type": MESSAGE.SET_FEED_LENGTH,}
            else:
                settings.feed_length = seconds


        # Set minimum and maximum temperature warnings
        case MESSAGE.SET_TEMP_WARNING:
            low, high = message["low"], message["high"]
            if high <= low:
                # Exact error string shown to user will be handled on clientside
                response = {'error': ERROR.TEMP_MINMAX,"message_type":MESSAGE.SET_TEMP_WARNING}
            else:
                settings.temp_warning = low, high
                response = {'error':ERROR.OK,"message_type":MESSAGE.SET_TEMP_WARNING}


        # Set minimum and maximum pH warnings
        case MESSAGE.SET_PH_WARNING:
            low, high = message["low"], message["high"]
            if high <= low:
                # Exact error string shown to user will be handled on clientside
                response = {'error': ERROR.PH_MINMAX, "message_type":MESSAGE.SET_PH_WARNING}
            else:
                # Do the thing
                settings.ph_warning = low, high
                response = {'error':ERROR.OK,"message_type":MESSAGE.SET_PH_WARNING}


        # Reset settings
        case MESSAGE.RESET_SETTINGS:
            settings = Settings()
            response = {'error':ERROR.OK,"message_type":MESSAGE.RESET_SETTINGS}
        

        # Save settings
        case MESSAGE.SAVE_SETTINGS:
            print("message type was save settings")
            if SaveSettings(message):
                response = {'error':ERROR.OK, 'message_type':MESSAGE.SAVE_SETTINGS}
            else:
                response = {'error':ERROR.SAVE_ERROR, 'message_type':MESSAGE.SAVE_SETTINGS}
    
    if response:
        response["channel"] = CHANNELS.CONTROL
        message_queue.Add(response)

def ReadPh() -> float:
    return sensor_control.read_ph()

def ReadTemperature() -> float:
    return sensor_control.read_temp()


# TODO(#8): Implement stats (temp, ph) reading from hardware
useRandomStats = False
def HandleStats(message:bytes) -> None:
    """Return current temp, ph"""
    
    if useRandomStats:
        temp = random.randint(75, 80)
        ph =  7 + 2 * random.random() - 1
    else: # todo
        temp = ReadTemperature()
        ph =  ReadPh()

    m = {'message_type':MESSAGE.GET_STATS, 'error': ERROR.OK, 'temp': temp, 'ph': ph, 'last_feed': settings.last_feed, "channel": CHANNELS.STATS}
    message_queue.Add(m)


demo_vid = None
def HandleVideo(message:bytes, use_demo:bool=True) -> bytes:
    """Capture a video frame from the webcam and prepare it to be send to the app"""
    global demo_vid

    if use_demo:
        if not demo_vid:
            demo_vid = cv2.VideoCapture("take_it_yeesy.mp4")
        vid = demo_vid
    else:
        if not demo_vid:
            # demo_vid = cv2.VideoCapture(0, cv2.CAP_V4L) # RPI webcam = 1, USB webcam = 0? -1 for auto?
            #demo_vid = cv2.VideoCapture('/dev/video0', cv2.CAP_FFMPEG)
            # TODO: We really, really want to read directly from the file.
            demo_vid = cv2.VideoCapture('udp://127.0.0.1:6969', cv2.CAP_FFMPEG)
        vid = demo_vid

    if not vid.isOpened():
        return None

    # Read next frame
    nextFrameValid, frame = vid.read()

    if not nextFrameValid:
        if use_demo:
            # Loop
            demo_vid = cv2.VideoCapture("take_it_yeesy.mp4")
            return HandleVideo(message, use_demo)
        return None

    # Resize
    #frame = imutils.resize(frame,width=WEBCAM_WIDTH)

    # Encode as jpeg
    encoded, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 20])
    return bytes(buffer)


# TODO(#12): RegisterForHolepunch()->None should probably be adapted into HandleHolepunch(bytes)->str, enable reconnection
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
    


def HandleHolepunch(b:bytes) -> None:
    message = b.decode().split(" ")
    print("handling holepunch", message)
    match message:
        case ["EXPECT", addr, local, port, localport]:
            enetHost.connect(enet.Address(addr, int(port)), channelCount=CHANNELS.MAX)
            print("local", local)
            #if len(local.split(".")) > 4:
            #    pass
            #else:
            enetHost.connect(enet.Address(local, int(localport)), channelCount=CHANNELS.MAX)
            print("expecting", addr, local, int(port), int(localport))
        case _:
            print("Unknown HP format")


# TODO: Let's not bother for senior project, but in theory this should instead
# be passed along through the functions called in Service()
mobile_peer = None


def Service() -> None:
    """Main loop"""
    global mobile_peer
    schedule.run_pending()
    event = enetHost.service(1000)
    if False:
        if event.type == enet.EVENT_TYPE_RECEIVE:
            channel = CHANNELS(event.channelID)
            if event.channelID != CHANNELS.HOLEPUNCH:
                return
    response:bytes = None             # What we will respond with, if anything.
                                      # For the most part None; this is handled
                                      # by message_queue, except for video.
    channel:int = None                # What channel to send the response on
    flags = enet.PACKET_FLAG_RELIABLE # Flags to send with the response
    if event.type == enet.EVENT_TYPE_CONNECT:
        print("connect event")
        mobile_peer = event.peer
    elif event.type == enet.EVENT_TYPE_DISCONNECT:
        print("disconnect from", event.peer.address)
        if event.peer == mobile_peer:
            mobile_peer = None

    match event.type:
        case enet.EVENT_TYPE_CONNECT:
            print("connect event to", event.peer)
        case enet.EVENT_TYPE_RECEIVE:
            channel = CHANNELS(event.channelID)
            match channel:
                case CHANNELS.HOLEPUNCH:
                    # print("Got channel", channel.name, "data", event.packet.data)
                    HandleHolepunch(event.packet.data)
                
                case CHANNELS.CONTROL:
                    # print("Got channel", channel.name, "data", event.packet.data)
                    HandleControl(event.packet.data)
                    #response = HandleControl(event.packet.data)
                    #response = json.dumps(response).encode()
                
                case CHANNELS.STATS:
                    # print("Got channel", channel.name, "data", event.packet.data)
                    HandleStats(event.packet.data)
                    #response = json.dumps(response).encode()
                
                case CHANNELS.VIDEO:
                    # print("Got channel", channel.name, "data", event.packet.data)
                    response = HandleVideo(event.packet.data)
                    #print("got video req", response)
                    flags = enet.PACKET_FLAG_UNRELIABLE_FRAGMENT | enet.PACKET_FLAG_UNSEQUENCED
                case _:
                    print("unknown channel", event.packet.data)

    if response:
        event.peer.send(channel, enet.Packet(response, flags))

def flush_queue():
    flags = enet.PACKET_FLAG_RELIABLE # Flags to send with the response
    if mobile_peer:
        while not message_queue.Empty():
            message = message_queue.Get()
            channel = message.pop('channel')
            s = json.dumps(message).encode()
            mobile_peer.send(channel, enet.Packet(s, flags))
    else:
        message_queue.clear()

def main() -> None:
    LoadSettings()
    UpdateSchedule() # Set initial schedule
    RegisterForHolepunch()
    while True:
        sensor_control.service()
        Service()
        flush_queue()


main()
