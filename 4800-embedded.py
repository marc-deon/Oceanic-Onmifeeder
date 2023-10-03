#! /usr/bin/env python3

################################################################################
## 4800-embedded.py
##
## Last updated 2023-09-28
##
## Program to run on embedded fishtank.
##
## Initially connects to server and registers username.
##
## Can then be contacted by APP to be queried for stats and video.
##
################################################################################
## Let's start with a UDP Timeout of ~20 seconds
##
################################################################################

import random
import socket
import time

HOLEPUNCH_TIMEOUT = 20

def CreateSocket(timeout=0):
    BUFF_SIZE = 65536
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    if timeout:
        s.settimeout(timeout)
    return s

def getLocalIp():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('192.255.255.255', 1))
    return s.getsockname()[0]

localIp = getLocalIp()

SERVER_IP = '4800.highlyderivative.games'
SERVER_PORT = 4800
username = "Poseidon"

def Register():
    msg = bytes(f"REG {username} {localIp}", "utf8")
    server_socket = CreateSocket()
    server_socket.sendto(msg, (SERVER_IP, SERVER_PORT))
    ret = server_socket.recvfrom(BUFF_SIZE)
    print(ret)

def GiveCamera():
    pass

def GiveStats():
    temp = random.randint(75, 80)
    ph =  7 + 2 * random.random() - 1

# Listens for connection from server with form:
# PUNCH [ADDR] [PORT]
def AskForHolepunch():
    print("Asking for HP...")
    s = CreateSocket(HOLEPUNCH_TIMEOUT)
    try:
        msg, addr = s.recvfrom(BUFF_SIZE)
        msg = msg.decode("utf8")
        case ["PUNCH", addr, port]:
            print("Got addr:port", addr, int(port))
            return addr, port

        case _:
            print("Invalid msg", msg)

    except socket.timeout:
        print("Giving up ask HP")

    return None, None

def LookForQuery(addr, port):
    print("Looking for Q...")
    try:
        msg, ap = s.recvfrom(BUFF_SIZE)
        # Either address or port do not match
        if ap[0] != addr or ap[1] != port:
            return

    except socket.timeout:
        print("Giving up on Q")


while True:
    if not Register():
        time.sleep(60)

    addr, port = AskForHolepunch()

    if not addr:
        continue

    WaitForQuery(addr, port)





