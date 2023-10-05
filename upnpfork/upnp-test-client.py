#! /usr/bin/env python3

import socket
#import miniupnpc

import curses
import threading
import os


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

def CreateSocket(timeout=0):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUFF_SIZE)
    if timeout:
        s.settimeout(timeout)
    return s

def utf8send(sock, msg, ip, port=None):
    if port == None:
        ip, port = ip
    print(f"""\
    sock ({type(sock)}) {sock},
    msg  ({type(msg)}) {msg},
    ip   ({type(ip)}) {ip},
    port ({type(port)}) {port}
    """)
    sock.sendto(msg.encode("utf8"), (ip, int(port)))


def utf8get(sock, split=True):
    msg, (addr, port) = s.recvfrom(BUFF_SIZE)
    msg = msg.decode("utf8")
    if split:
        msg = msg.split(" ")
    return msg, addr, port

BUFF_SIZE = 65536
SERVER_IP = 'highlyderivative.games'
SERVER_PORT = 4800
USER = 'poseidon'


#import random
#PORT = random.randint(4801, 65535)

#upnp = miniupnpc.UPnP()
#upnp.discoverdelay = 10
#upnp.discover()
#upnp.selectigd()
#                                 External    Protocol    Internal-host   Internal    Description   Remote-host
#openrequest = upnp.addportmapping(PORT,       'UDP',      upnp.lanaddr,   PORT,       'testing',    '')

#if not openrequest:
#    print("Router would not open port")
#    exit(1)
#
from sys import argv

def iam(s, hostaddr, hostport):
    attempts = 0
    s.settimeout(10)

    while attempts < 5:
        attempts += 1
        try:
            utf8send(s, f"IAM", hostaddr, hostport)
            msg, addr, port = utf8get(s, False)
            if msg == "YOUARE":
                print("Recieved YOUARE")
                print(":)")
                curses.wrapper(chatroom, s, s, addr, port)
                exit(0)

            if msg == "IAM":
                print("recieved IAM, sending YOUARE")
                utf8send(s, "YOUARE", hostaddr, hostport)

        except socket.timeout:
            print("Timeout", attempts)


if "host" in argv:
    s = CreateSocket()
    #s.bind(('', PORT))
    utf8send(s, f"HOST {USER}", SERVER_IP, SERVER_PORT)
    msg, addr, port = utf8get(s, False)
    if msg == "HOSTING":
        msg, addr, port = utf8get(s)
        match msg:
            case ["EXPECT", clientaddr, clientport]:
                iam(s, clientaddr, clientport)

            case _:
                pass

    else:
        pass

elif "connect" in argv:
    s = CreateSocket()
    #s.bind(('', PORT))
    utf8send(s, f"CONN {USER}", SERVER_IP, SERVER_PORT)
    msg, addr, port = utf8get(s)
    match msg:
        case ["CONNTO", hostaddr, hostport]:
            iam(s, hostaddr, hostport)


        case ["USERNAME_NOT_PRESENT"]:
            print("Username not present in server")

        case _:
            print("Unknown message", msg)
