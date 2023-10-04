#! /usr/bin/env python3
import socket
from sys import argv
import curses
import os
import sys
import threading

BUFF_SIZE = 65536
def CreateSocket(timeout=0, port=0):
    s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUFF_SIZE)
    if port:
        s.bind(('', int(port)))
    if timeout:
        s.settimeout(timeout)
    return s

def GetLocalIp():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('192.255.255.255', 1))
    return s.getsockname()[0]

def utf8send(sock, msg, ip, port=None):
    if port == None:
        ip, port = ip
    print(f"sending to {ip}:{port} {msg}")
    sock.sendto(msg.encode("utf8"), (ip, int(port)))

server_addr = ("highlyderivative.games", 4800)


# list of username, message pairs
chatlog = [["System", "Welcome!"]]





def chatroom_listen(rsock, ip, port):
    global chatlog
    while True:
        try:
            msg, addr = rsock.recvfrom(BUFF_SIZE)
            print("recieved", msg)
            msg = msg.decode("utf8")
            chatlog.append(["Them", msg])
            chatlog = chatlog[-10:]

        except socket.timeout:
            pass


def chatroom_send(message, ssock, ip, port):
    chatlog.append(["You", message])
    utf8send(ssock, message, ip, port)


def chatroom(win, rsock, ssock, ip, port):
    currentMessage = ""

    logWindow = win.subwin(12, 70, 0, 0)
    messageWindow = win.subwin(3, 70, 12, 0)
    logWindow.border()
    messageWindow.border()

    curses.noecho()
    curses.halfdelay(1)

    print("Entering chatroom")
    t = threading.Thread(target=chatroom_listen, args=(rsock, ip, port))
    t.start()

    while True:

        try:
            k = win.getkey()

            if k == os.linesep:
                chatroom_send(currentMessage, ssock, ip, port)
                currentMessage = ""

            elif k == "KEY_BACKSPACE":
                currentMessage = currentMessage[:-1]

            elif k == "^[":
                os.system('stty sane')
                exit()

            else:
                currentMessage += k
            curses.doupdate()

        except curses.error:
            pass

        except (KeyboardInterrupt, SystemExit):
            os.system('stty sane')
            exit()

        logWindow.move(1,1)
        for m in chatlog:
            rev = curses.A_REVERSE if m[0] == "Them" else 0
            logWindow.addstr(f"{m[0]}: {m[1]}\n ", rev)
        logWindow.border()

        messageWindow.clear()
        messageWindow.border()
        messageWindow.addstr(1, 1, currentMessage)

        logWindow.refresh()
        messageWindow.refresh()

def connect_to_peer(recv_sock, public, local, port):
    print("Connecting to peer")
    recv_sock.settimeout(5)
    send_sock = CreateSocket(5)

    actual = ""
    attempts = 5
    while attempts > 0:
        try:
            # Try to send to public
            utf8send(send_sock, f"iam {GetLocalIp()}", public, port)
            print(f"sending to {public}:{port}")

            # Try to send to private
            utf8send(send_sock, f"iam {GetLocalIp()}", local, port)
            print(f"sending to {local}:{port}")

            # Recieve
            print(f"Recieving on {recv_sock.getsockname()})")
            msg, addr = recv_sock.recvfrom(BUFF_SIZE)
            msg = msg.decode("utf8")
            if msg == f"iam {local}":
                actual = local
            elif msg == f"iam {public}":
                actual = public
            else:
                print("That's my purse!", msg)
                continue
            attempts -= 1

        except socket.timeout:
            attempts -= 1
            print("timeout")
            continue
        except KeyboardInterrupt:
            exit(0)


    if not actual:
        print("couldn't find friend :(")
        return

    print("Found my friend at", actual, port)

    curses.wrapper(chatroom, recv_sock, send_sock, actual, port)


if argv[1] == "host":
    sock = CreateSocket(20)

    msg = f"HOST {GetLocalIp()}"
    print("sending", msg)
    utf8send(sock, msg, server_addr)
    msg, addr = sock.recvfrom(BUFF_SIZE)
    msg = msg.decode("utf8").split(" ")

    match msg:
        case ["HOSTING", trm, port]:
            print("Hosting at...", trm, sock.getsockname()[1])
            sock.close()
            sock = CreateSocket(port=int(port))
            while True:
                try:
                    msg, addr = sock.recvfrom(BUFF_SIZE)
                    msg = msg.decode("utf8").split(" ")

                    match msg:
                        case ["EXPECT", public, local, port]:
                            connect_to_peer(sock, public, local, port)

                        case ["REFRESHOK"]:
                            print(msg)

                        case _:
                            print("Invalid response", msg)

                except socket.timeout:
                    utf8send(sock, "FRSH", server_addr)
                    continue

        case _:
            print("Hosting failed for some reason", msg)

elif argv[1] == "connect":
    sock = CreateSocket(20)
    trm = argv[2]
    local = GetLocalIp()
    utf8send(sock, f"CONN {local} {trm}", server_addr)
    msg, addr = sock.recvfrom(BUFF_SIZE)
    msg = msg.decode("utf8").split(" ")

    match msg:
        case ["OK", public, local, port]:
            connect_to_peer(sock, public, local, port)
        case _:
            print("Invalid message", msg)

