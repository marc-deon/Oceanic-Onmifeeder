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
    
    sleep(1/30)

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

# # Loop the placeholder video file
# vid = cv2.VideoCapture("take_it_yeesy.mp4")


# def serve_video(sock:sc.Socket):
#     vid = cv2.VideoCapture("take_it_yeesy.mp4") # replace 'rocket.mp4' with 0 for webcam
#     WIDTH = 400

#     while True:
#         while True:
#             # msg = sock.Receive()
#             sleep(1/24)
#             # Read next frame
#             nextFrameValid, frame = vid.read()

#             # Loop the placeholder video file
#             if not nextFrameValid:
#                 break

#             # Resize
#             frame = imutils.resize(frame,width=WIDTH)

#             # Encode as jpeg
#             encoded, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
#             print(bytes(buffer))
#             # Send to application
#             sock.Send(bytes(buffer))

#         # Loop the placeholder video file
#         vid = cv2.VideoCapture("take_it_yeesy.mp4")

# def receive_video(sock:sc.Socket):
#     import numpy
#     while True:
#         msg = sock.Receive()
#         print("received msg with data", msg.data)
#         # numpy.frombuffer()
#         frame = numpy.array(msg.data, dtype='S1')
#         cv2.imdecode(frame, cv2.IMREAD_UNCHANGED)
#         cv2.imshow()
#     pass


# if argv[1] == 'host':
#     conn = rudp.RudpConnection(1, 4801)
#     conn.Connect('127.0.0.1', None, 4802, None)
#     port = conn.Virtual(1, 1, True)
#     serve_video(port)

# elif argv[1] == 'connect':
#     conn = rudp.RudpConnection(1, 4802)
#     conn.Connect('127.0.0.1', None, 4801, None)
#     port = conn.Virtual(1, 1, True)
#     receive_video(port)
