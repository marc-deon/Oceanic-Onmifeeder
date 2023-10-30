#! /usr/bin/env python3

from socket_convenience import utf8get, utf8send, CreateSocket
import enet
from enums import *

BUFF_SIZE = 65536
HOST_IP = 'highlyderivative.games'
HOST_PORT = 4800
socket_address = (HOST_IP, HOST_PORT)

def enet_main():
    userdict = {} # username -> ip ip port port
    hostdict = {} # username -> enet.peer

    enetHost = enet.Host(enet.Address(None, HOST_PORT), peerCount=32)
    while True:
        event = enetHost.service(1000)

        match event.type:
            case enet.EVENT_TYPE_RECEIVE:
                addr = event.peer.address.host
                port = event.peer.address.port
                print("Got message", event.packet.data.decode().split(" "))
                match event.packet.data.decode().split(" "):
                    case ["HOST", local, username, localport]:
                        userdict[username] = local, addr, port, localport
                        hostdict[username] = event.peer
                        event.peer.send(CHANNELS.HOLEPUNCH, enet.Packet(b"HOSTING", enet.PACKET_FLAG_RELIABLE))
                        print("Sent HOSTING")

                    case ["CONN", local, username, localport]:
                        if username in userdict:
                            print("username", username, "IS present")
                            # Get the info to send
                            hostlocal, hostaddr, hostport, hostlocalport = userdict[username]

                            # This gets sent back to the original hoster
                            expect = f"EXPECT {addr} {local} {port} {localport}".encode()
                            print(expect)
                            hostdict[username].send(CHANNELS.HOLEPUNCH, enet.Packet(expect, enet.PACKET_FLAG_RELIABLE))

                            # This gets send to the client who just connected
                            connto = f"CONNTO {hostaddr} {hostlocal} {hostport} {hostlocalport}".encode()
                            print(connto)
                            event.peer.send(CHANNELS.HOLEPUNCH, enet.Packet(connto, enet.PACKET_FLAG_RELIABLE))

                            # Remove info from dictionaries
                            #userdict.pop(username)
                            #hostdict.pop(username).disconnect_later()
                            event.peer.disconnect_later()
                        else:
                            s = "USERNAME_NOT_PRESENT".encode()
                            event.peer.send(CHANNELS.HOLEPUNCH, enet.Packet(s, enet.PACKET_FLAG_RELIABLE))
                            print("Username", username, "not present")
                    case _:
                        s = "Unknown message format".encode()
                        print(s, event.packet.data.decode.split(" "))
                        event.peer.send(CHANNELS.HOLEPUNCH, enet.Packet(s, enet.PACKET_FLAG_RELIABLE))
enet_main()