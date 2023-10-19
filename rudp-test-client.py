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
from rudp import RudpPort, RudpConnection

# Holepunch server address and port
SERVER_ADDR = ("highlyderivative.games", 4800)
# Username to use as a key for holepunching. Will be phased out later for something more secure.
USER = "poseidon"


if argv[1] == "host":
    sock = CreateSocket(.5)
    #We need to get a port assigned to us, so... this works.
    utf8send(sock, "FRSH", SERVER_ADDR)
    ourport = GetSocketPort(sock)

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
                    conn = RudpConnection(socket=sock)

                    if argv[2] == "local":
                        conn.Connect('127.0.0.1', None, int(clientport), int(clientlocalport))
                    else:
                        conn.Connect(clientaddr, clientlocal, int(clientport), int(clientlocalport))
                    sendsock = conn.Virtual(1, 2)
                    recvsock = conn.Virtual(2, 1)

                    cr = Chatroom(sendsock, recvsock, "Alice")
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
    sock = CreateSocket(.5)
    utf8send(sock, "FRSH", SERVER_ADDR)
    ourport = GetSocketPort(sock)

    # Send message to holepunch server
    utf8send(sock, f"CONN {GetLocalIp()} {USER} {ourport}", SERVER_ADDR)

    # Listen for response
    while True:
        msg, addr, port = utf8get(sock, True)
        match msg:
            # Recieved message with our peer's info
            case ["CONNTO", hostaddr, hostlocal, hostport, hostlocalport]:

                # Start demo chatroom
                conn = RudpConnection(socket=sock)
                sendsock = conn.Virtual(1, 2)
                recvsock = conn.Virtual(2, 1)
                if argv[2] == "local":
                    conn.Connect('127.0.0.1', None, int(hostport), int(hostlocalport))
                else:
                    conn.Connect(hostaddr, hostlocal, int(hostport), int(hostlocalport))

                cr = Chatroom(sendsock, recvsock, "Bob")
                curses.wrapper(cr.main)
                break

            case _:
                print("Invalid message", msg)
