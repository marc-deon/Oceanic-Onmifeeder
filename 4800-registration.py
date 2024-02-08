#! /usr/bin/env python3

################################################################################
## 4800-registration.py
##
## Program for users to register accounts on the server.
##
################################################################################

# import socket_convenience
import enet
import json
import random
from datetime import datetime

SERVER_IP = 'highlyderivative.games'
SERVER_PORT = 4800


enetHost:enet.Host = None
enetHost = enet.Host(enet.Address(None, 0), peerCount=1)


   
def get_user_pass():
    while not (username := input("Username: ").strip()):
        pass
    while not (password := input("Password: ").strip()):
        pass
    return username, password

def register() -> bool:
    print("reg")
    username, password = get_user_pass()    
    hpServerPeer = enetHost.connect(enet.Address(SERVER_IP, SERVER_PORT), 1)

    while True:
        event = enetHost.service(500)
        if event.type == enet.EVENT_TYPE_CONNECT:
            s = f"REGISTER {username} {password}".encode()
            hpServerPeer.send(0, enet.Packet(s, enet.PACKET_FLAG_RELIABLE))
        if event.type == enet.EVENT_TYPE_RECEIVE:
            message = event.packet.decode().split()
            if message == "REGISTRATION OK":
                print("Registration successful")
                return True
            else:
                print("Registration error:", message)
                return True

# TODO: Receive json instead of simple string
def login() -> bool:
    print("logi")
    username, password = get_user_pass()    
    hpServerPeer = enetHost.connect(enet.Address(SERVER_IP, SERVER_PORT), 1)

    while True:
        event = enetHost.service(500)
        if event.type == enet.EVENT_TYPE_CONNECT:
            s = f"LOGIN {username} {password}".encode()
            hpServerPeer.send(0, enet.Packet(s, enet.PACKET_FLAG_RELIABLE))
        if event.type == enet.EVENT_TYPE_RECEIVE:
            message = event.packet.decode().split()
            if message == "LOGIN OK":
                print("Login successful")
                return True
            else:
                print("Login error:", message)
                return True 


def main() -> None:
    options = [
        ("Register for account", register),
        ("Test login", login),
        ("Exit", lambda: False)
    ]  

    while True:

        for i, option in enumerate(options):
            print(f"{i+1}) {option[0]}")

        i = int(input("> ").strip()) - 1
        result = options[i][1]()
        if not result:
            break

main()

