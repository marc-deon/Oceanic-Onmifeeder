#! /usr/bin/env python3

################################################################################
#
# This test file will use regular RPD to connect to the holepunch server,
# then disconnect, then use the same port with Reliable UDP to connect to the peer.
#
################################################################################

# import socket
import curses
from sys import argv
from socket_convenience import *
from rudp_chatroom import Chatroom
from rudp import RUDP

# Holepunch server address and port
SERVER_ADDR = ("highlyderivative.games", 4800)
# Username to use as a key for holepunching. Will be phased out later for something more secure.
USER = "poseidon"


if argv[1] == "host":
    sock = CreateSocket(20)
    utf8send(sock, "FRSH", SERVER_ADDR)
    ourport = GetSocketPort(sock)

    print(93)
    # Request a spot in the holepunch server
    utf8send(sock, f"HOST {GetLocalIp()} {USER} {ourport}", SERVER_ADDR)
    msg, _a, _p = utf8get(sock, True)

    while True:
        try:
            # Listen
            msg, _a, _p = utf8get(sock, split=True)

            match msg:
                # Request for spot succeeded
                case ["HOSTING", public]:
                    print("Hosting at...", GetLocalIp(), public)

                # Server says that a peer is trying to contact us
                case ["EXPECT", clientaddr, clientlocal, clientport, clientlocalport]:
                    print(f"{ourport=}")

                    # Start demo chatroom
                    sock = RUDP(socket=sock)

                    sock.Connect(clientaddr, clientlocal, clientport, clientlocalport, "sendSock")
                    sock.Virtual("recvSock")

                    # Start demo chatroom
                    cr = Chatroom(sock)
                    curses.wrapper(cr.main)

                # Refreshed connection to server
                case ["OK"]:
                    pass

                case _:
                    print("Invalid response", msg)

        except socket.timeout:
            # Refresh the port
            utf8send(sock, "FRSH", SERVER_ADDR)
            continue


elif argv[1] == "connect":
    sock = CreateSocket(20)
    utf8send(sock, "FRSH", SERVER_ADDR)
    ourport = GetSocketPort(sock)

    print(149)
    # Send message to holepunch server
    utf8send(sock, f"CONN {GetLocalIp()} {USER} {ourport}", SERVER_ADDR)

    # Listen for response
    msg, addr, port = utf8get(sock, True)
    match msg:
        # Recieved message with our peer's info
        case ["CONNTO", hostaddr, hostlocal, hostport, hostlocalport]:
            sock = RUDP(socket=sock)

            # Start demo chatroom
            sock.Connect(hostaddr, hostlocal, hostport, hostlocalport, "sendSock")
            sock.Virtual("recvSock")

            cr = Chatroom(sock)
            curses.wrapper(cr.main)

        case _:
            print("Invalid message", msg)
