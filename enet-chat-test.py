#! /usr/bin/env python3
# https://github.com/aresch/pyenet

import curses
import enet
import enet_chatroom
import socket_convenience as sc

from sys import argv

hostOrConnect = argv[1]
username = argv[2]

# Username to use as a key for holepunching. Will be phased out later for something more secure.
HOLEPUNCH_CODE = "poseidon"

if hostOrConnect == "host":
    # Find our peer
    hp_sock = sc.register_for_holepunch(HOLEPUNCH_CODE)
    peerIp, peerPort, ourIp, ourPort = sc.wait_for_holepunch(hp_sock)

if hostOrConnect == "connect":
    # Find our peer
    peerIp, peerPort, ourIp, ourPort = sc.connect_to_holepunch(HOLEPUNCH_CODE)

# enet stuff
host = enet.Host(enet.Address(ourIp, ourPort), peerCount=2)
peer = host.connect(enet.Address(peerIp, peerPort), channelCount=1)
# Start chatroom
cr = enet_chatroom.Chatroom(host, peer, 0, username)
curses.wrapper(cr.main)