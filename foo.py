#! /usr/bin/env python3

from rudp import RudpConnection, RudpTimeout
from sys import argv

localPort = 1
remotePort = 1

a1 = int(argv[1])
a2 = int(argv[2])

conn = RudpConnection(1, a1)
conn.Connect('127.0.0.1', None, a2, None)

port = conn.Virtual(localPort, remotePort)

def SendTest(message):
    try:
        port.Send(message)
    except RudpTimeout:
        print("We got no acknowledgement.")

def ReceiveTest():
    try:
        rudp_message = port.Receive()
        print("message contains", rudp_message.string)
    except RudpTimeout:
        print("We got no response.")

if a1 < a2:
    SendTest("Hello, I'm Alice")
    ReceiveTest()
else:
    ReceiveTest()
    SendTest("Hello, I'm Bob")