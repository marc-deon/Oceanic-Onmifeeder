#! /usr/bin/env python3
import cv2
import enet
import imutils
import socket_convenience as sc
from sys import argv
from time import sleep

hp_key = "poseidon"

sock = sc.register_for_holepunch(hp_key)
peerIp, peerPort, ourIp, ourPort = sc.wait_for_holepunch(sock)

# enet stuff
host = enet.Host(enet.Address(ourIp, ourPort), peerCount=2)
peer = host.connect(enet.Address(peerIp, peerPort), channelCount=1)

# Start chatroom
vid = cv2.VideoCapture("take_it_yeesy.mp4") # replace 'rocket.mp4' with 0 for webcam
WIDTH = 400

# while True:
while True:
    event = host.service(0)
    # match event.type:
    #     case enet.EVENT_TYPE_RECEIVE:
    #         if event.packet.data != b'1':
    #             continue
    
    sleep(1/15)

    # Read next frame
    nextFrameValid, frame = vid.read()

    # Loop the placeholder video file
    if not nextFrameValid:
        break

    # Resize
    frame = imutils.resize(frame,width=WIDTH)

    # Encode as jpeg
    encoded, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
    print(bytes(buffer))
    # Send to application
    packet = enet.Packet(bytes(buffer), enet.PACKET_FLAG_UNSEQUENCED)
    peer.send(0, packet)
