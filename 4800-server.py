#! /usr/bin/env python3

################################################################################
## 4800-server.py
##
## Last updated 2023-09-28
##
## Program to run on cloud server.
## Primarily concerned with holepunching between app and embedded.
## Also has some functionality that should be moved to embedded later.
##
################################################################################

import cv2
import imutils
import base64
import socket
#import json

HOST_IP = '4800.highlyderivative.games'
HOST_PORT = 4800
socket_address = (HOST_IP, HOST_PORT)

BUFF_SIZE = 65536
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUFF_SIZE)
server_socket.bind(socket_address)
print('Listening at:',socket_address)

username_to_ip_dict = {}

# https://bford.info/pub/net/p2pnat/ See especially section 3.2

def HolePunchTest():
    # > REG username localIp
    # < OK
    #
    # > PUNCH username
    # < PUNCHING ip port

    while True:
        msg, client_addr = server_socket.recvfrom(BUFF_SIZE)
        msg = msg.decode("utf8")
        msg = msg.strip() # Remove newlines
        print(client_addr, "said:", msg)
        msg = msg.split(" ")

        match msg:
            case ["REG", username, localIp]:
                #                               Public          Local    Port
                username_to_ip_dict[username] = client_addr[0], localIp, client_addr[1]
                # FIXME: instead of bytes(), use string.encode()
                server_socket.sendto(bytes("OK", "utf8"), client_addr)
                print(username_to_ip_dict)

            case ["PUNCH", username]:
                if username in username_to_ip_dict:
                    public, local, port = username_to_ip_dict[username]
                    response = f"PUNCHING {public} {local} {port}"
                    print("responding with", response)
                    server_socket.sendto(bytes(response, "utf8"), client_addr)
                else:
                    response = f"UNKNOWN USERNAME {username}"
                    print("responding with", response)
                    server_socket.sendto(bytes(response, "utf8"), client_addr)

            case _:
                server_socket.sendto(bytes("Invalid", "utf8"), client_addr)

        #server_socket.sendto(bytes("I hear you", "utf8"), client_addr)

def VideoTest():
    vid = cv2.VideoCapture("take_it_yeesy.mp4") # replace 'rocket.mp4' with 0 for webcam
    WIDTH = 400

    while True:
        print('waiting for connection')
        msg, client_addr = server_socket.recvfrom(BUFF_SIZE)
        print('GOT connection from', client_addr)

        while True:
            # wait for next message from client
            msg, client_addr = server_socket.recvfrom(BUFF_SIZE)

            # Read next frame
            nextFrameValid, frame = vid.read()

            # Loop the placeholder video file
            if not nextFrameValid:
                break

            # Resize
            frame = imutils.resize(frame,width=WIDTH)

            # Encode as jpeg
            encoded, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            # Send to application
            server_socket.sendto(bytes(buffer), client_addr)

        # Loop the placeholder video file
        vid = cv2.VideoCapture("take_it_yeesy.mp4")

#VideoTest()
HolePunchTest()
