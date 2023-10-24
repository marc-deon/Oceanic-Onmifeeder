#! /usr/bin/env python3
import cv2
import socket
from sys import argv
import rudp
import imutils
from time import sleep

def serve_video(sock:rudp.RudpPort):
    vid = cv2.VideoCapture("take_it_yeesy.mp4") # replace 'rocket.mp4' with 0 for webcam
    WIDTH = 300

    while True:
        while True:
            # msg = sock.Receive()
            sleep(1/24)
            # Read next frame
            nextFrameValid, frame = vid.read()

            # Loop the placeholder video file
            if not nextFrameValid:
                break

            # Resize
            frame = imutils.resize(frame,width=WIDTH)

            # Encode as jpeg
            buffer = cv2.imencode('.jpeg', frame, [cv2.IMWRITE_JPEG_QUALITY, 90])[1]
            # Send to application
            b = buffer.tobytes()
            # b = b'HELLO WORLD'
            print(b[:10])
            sock.Send(b)

        # Loop the placeholder video file
        vid = cv2.VideoCapture("take_it_yeesy.mp4")

def receive_video(sock:rudp.RudpPort):
    import numpy
    while True:
        msg = sock.Receive()
        frame = numpy.frombuffer(bytes.fromhex(msg.string), dtype='byte')
        frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)

        print("frame", frame)
        cv2.imshow('frame', frame)
        # 30fps...ish
        if cv2.waitKey(1) & 0xFF == 'q':
            break
    pass


if argv[1] == 'host':
    conn = rudp.RudpConnection(1, 4801)
    conn.Connect('127.0.0.1', None, 4802, None)
    port = conn.Virtual(1, 1, True)
    serve_video(port)

elif argv[1] == 'connect':
    conn = rudp.RudpConnection(1, 4802)
    conn.Connect('127.0.0.1', None, 4801, None)
    port = conn.Virtual(1, 1, True)
    receive_video(port)
