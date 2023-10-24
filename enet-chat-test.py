#! /usr/bin/env python3
# https://github.com/aresch/pyenet

from sys import argv

hostOrConnect = argv[1]
username = argv[2]

import enet
import enet_chatroom
import curses
import socket_convenience as sc

# Holepunch server address and port
SERVER_ADDR = ("highlyderivative.games", 4800)
# Username to use as a key for holepunching. Will be phased out later for something more secure.
HOLEPUNCH_CODE = "poseidon"

# Create a socket, open a random port
hp_sock = sc.CreateSocket()
sc.utf8send(hp_sock, "FRSH", SERVER_ADDR)
ourport = sc.GetSocketPort(hp_sock)

if hostOrConnect == "host":
    # Request a spot in the holepunch server
    sc.utf8send(hp_sock, f"HOST {sc.GetLocalIp()} {HOLEPUNCH_CODE} {ourport}", SERVER_ADDR)
    msg = sc.utf8get(hp_sock, True)[0]

    while True:
        try:
            msg = sc.utf8get(hp_sock, True)[0]

            match msg:
                case ["HOSTING", public]:
                    print("Hosting at...", sc.GetLocalIp(), public)

                case ["EXPECT", clientaddr, clientlocal, clientport, clientlocalport]:
                    # Find our peer
                    peerIp, peerPort = sc.holepunch(hp_sock, clientaddr, clientlocal, clientport, clientlocalport)
                    # We don't need this anymore
                    hp_sock.close()
                    # enet stuff
                    host = enet.Host(enet.Address(None, ourport), peerCount=2)
                    peer = host.connect(enet.Address(peerIp, peerPort), channelCount=1)
                    # Start chatroom
                    cr = enet_chatroom.Chatroom(host, peer, 0, username)
                    curses.wrapper(cr.main)
                    break

                case ["OK"]:
                    pass

                case ["HAND1"]:
                    # Holepunching junk; it's fine
                    pass

                case _:
                    print("Invalid response", msg)

        except TimeoutError:
            # Refresh the port
            sc.utf8send(hp_sock, "FRSH", SERVER_ADDR)
            continue

if hostOrConnect == "connect":

    # Send message to holepunch server
    sc.utf8send(hp_sock, f"CONN {sc.GetLocalIp()} {HOLEPUNCH_CODE} {ourport}", SERVER_ADDR)

    # Listen for response
    while True:
        msg, addr, port = sc.utf8get(hp_sock, True)
        match msg:
            # Recieved message with our peer's info
            case ["CONNTO", hostaddr, hostlocal, hostport, hostlocalport]:
                # Find our peer
                peerIp, peerPort = sc.holepunch(hp_sock, hostaddr, hostlocal, hostport, hostlocalport)
                # We don't need this anymore
                hp_sock.close()
                # enet stuff
                host = enet.Host(enet.Address(None, ourport), peerCount=2)
                peer = host.connect(enet.Address(peerIp, peerPort), channelCount=1)
                # Start chatroom
                cr = enet_chatroom.Chatroom(host, peer, 0, username)
                curses.wrapper(cr.main)
                break

            case ["HAND1"]:
                # Holepunching junk; it's fine
                pass
            
            case _:
                print("Invalid message", msg)