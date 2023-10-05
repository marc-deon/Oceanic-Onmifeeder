#! /usr/bin/env python3
import socket
import curses
from sys import argv
from socket_convenience import *
from chatroom import Chatroom

# Holepunch server address and port
SERVER_ADDR = ("highlyderivative.games", 4800)
# Username to use as a key for holepunching. Will be phased out later for something more secure.
USER = "poseidon"


def PeerHandshake(sock:socket.socket, ourPublic:str, peerPublic:str, peerLocal:str, tentativePort:int):
    """Connect to a peer at either their public/local IP and a tentative Port"""

    print("Connecting to peer")
    sock.settimeout(10)

    # We must figure out whether to use the public or local IP for the peer
    actual = ""
    # We can try to contact the peer over this tentative port, but we may have to switch
    port = tentativePort

    ourLocal = GetLocalIp()

    attempts = 0
    while attempts < 5:
        try:
            # Try to contact peer on internet
            utf8send(sock, f"IAM {ourPublic} {GetSocketPort(sock)}", peerPublic, port)
            # Try to contact peer on local network
            utf8send(sock, f"IAM {ourLocal} {GetSocketPort(sock)}", peerLocal, port)

            # Listen for message from peer
            msg, _, p = utf8get(sock, True)

            match msg:
                # Peer heard our IAM and is responding!
                case ["YOUARE"]:
                    # Send one final YOUARE back to them
                    port = p
                    utf8send(sock, "YOUARE", actual, port)
                    break

                # Peer has made contact with us
                case ["IAM", ip, p]:
                    if ip == peerPublic:
                        actual = peerPublic
                    elif ip == peerLocal:
                        actual = peerLocal
                    else:
                        # This is a third-party trying to connect
                        print("That's my purse!")
                        exit(1)

                    port = p
                    utf8send(sock, "YOUARE", actual, port)

                case _:
                    pass

        except socket.timeout:
            print("timeout")
            continue
        except KeyboardInterrupt:
            exit(0)
        finally:
            attempts += 1

    if not actual:
        print("couldn't find friend :(")
        exit(1)

    return actual, port
    


if argv[1] == "host":
    sock = CreateSocket(20)

    # Request a spot in the holepunch server
    utf8send(sock, f"HOST {GetLocalIp()} {USER}", SERVER_ADDR)
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
                case ["EXPECT", ourpublic, public, local, port]:
                    # Find the true IP and port of our peer (maybe do security stuff?)
                    ip, port = PeerHandshake(sock, ourpublic, public, local, port)
                    
                    # Start demo chatroom
                    cr = Chatroom(sock, ip, port)
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
    # Send message to holepunch server
    utf8send(sock, f"CONN {GetLocalIp()} {USER}", SERVER_ADDR)

    # Listen for response
    msg, addr, port = utf8get(sock, True)
    match msg:
        # Recieved message with our peer's info
        case ["CONNTO", ourpublic, local, public, port]:
            ip, port = PeerHandshake(sock, ourpublic, public, local, port)
            # Start demo chatroom
            cr = Chatroom(sock, ip, port)
            curses.wrapper(cr.main)
            
        case _:
            print("Invalid message", msg)
