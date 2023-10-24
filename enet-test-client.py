#! /usr/bin/env python3

# https://github.com/aresch/pyenet

from sys import argv
import enet

ourPort, peerPort = int(argv[1]), int(argv[2])

# def TestHost():
#     # Socket, 
#     host = enet.Host(enet.Address("localhost", ourPort), peerCount=1)
    
#     while True:
#         event = host.service(1000)
#         peer = event.peer
#         packet = event.packet
        
#         match event.type:
#             case enet.EVENT_TYPE_NONE:
#                 pass

#             case enet.EVENT_TYPE_CONNECT:
#                 print("new connection", peer.address.host, peer.address.port)
                
#             case enet.EVENT_TYPE_RECEIVE:
#                 print("message received")
#                 print(packet.dataLength)
#                 print(packet.data)
#                 print(event.channelID)
#                 print("Receive end")
                
#             case enet.EVENT_TYPE_DISCONNECT:
#                 print("disconnected")
#                 event.peer.data = None


# def TestClient():
#     host = enet.Host(enet.Address("localhost", ourPort), peerCount=1)
#     peer = host.connect(enet.Address("localhost", peerPort), 1)
#     # PACKET_FLAG_RELIABLE
#     # PACKET_FLAG_UNRELIABLE_FRAGMENT
#     while True:
#         event = host.service(1000)
#         packet = enet.Packet(b"Words words", enet.PACKET_FLAG_RELIABLE)
#         peer.send(0, packet)


# if ourPort < peerPort:
#     TestHost()
#     print("Host ended")
# else:
#     TestClient()
#     print("Client ended")


