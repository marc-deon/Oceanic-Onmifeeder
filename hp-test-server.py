#! /usr/bin/env python3

import socket

BUFF_SIZE = 65536
HOST_IP = '4800.highlyderivative.games'
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
    sock.sendto(msg.encode("utf8"), (ip, port))


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
