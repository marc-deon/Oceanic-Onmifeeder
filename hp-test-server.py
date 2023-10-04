#! /usr/bin/env python3

from sys import argv
import socket

BUFF_SIZE = 65536
HOST_IP = 'highlyderivative.games'
HOST_PORT = 4800
socket_address = (HOST_IP, HOST_PORT)

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



def UPNP():
    userdict = {}
    s = CreateSocket()
    s.bind(socket_address)
    while True:
        msg, (addr, port) = s.recvfrom(BUFF_SIZE)
        msg = msg.decode('utf8').split(" ")
        match msg:
            case ["HOST", username]:
                userdict[username] = addr, port
                utf8send(s, f"HOSTING", addr, port)
            case ["CONN", username]:
                if username in userdict:
                    hostaddr, hostport = userdict[username]
                    utf8send(s, f"EXPECT {addr} {port}", hostaddr, hostport)
                    utf8send(s, f"CONNTO {hostaddr} {hostport}", addr, port)
                else:
                    utf8send(s, f"USERNAME_NOT_PRESENT", addr, port)
            case _:
                pass
    pass


if "upnp" in argv:
    UPNP()
    exit(0)



# List of valid messages
#
# HOST local-ip > HOSTING trmXXXX
# CONN local-ip trmXXXX > OK pub-ip local-ip port
# FRSH > OK

userdict = {}

while True:
    sock = CreateSocket()
    sock.bind(socket_address)
    print('Listening at:', socket_address)

    msg, addr = sock.recvfrom(BUFF_SIZE)
    port = addr[1]
    msg = msg.decode("utf8").split(" ")
    match msg:
        case ["HOST", localIp]:
            trm = "trm1234"
            userdict[trm] = addr[0], localIp, port
            utf8send(sock, f"HOSTING {trm} {port}" , addr)

        case ["CONN", clientLocal, trm]:
            hostPublic, hostLocal, hostPort = userdict[trm]
            clientPublic = addr[0]
            utf8send(sock, f"EXPECT {clientPublic} {clientLocal} {port}", hostPublic, hostPort)
            utf8send(sock, f"OK {hostPublic} {hostLocal} {hostPort}", addr)

        case ["FRSH"]:
            utf8send(sock, "REFRESHOK", addr)

        case _:
            print(f"invalid message [{msg}]")
            utf8send(sock, f"INVALID MESSAGE", addr)
