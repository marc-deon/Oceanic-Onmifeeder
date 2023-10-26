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


def main():
    userdict = {}
    s = CreateSocket()
    s.bind(socket_address)
    print("Listening at", socket_address)
    while True:
        msg, (addr, port) = s.recvfrom(BUFF_SIZE)
        msg = msg.decode('utf8').split(" ")
        match msg:
            case ["HOST", local, username, localport]:
                userdict[username] = local, addr, port, localport
                utf8send(s, f"HOSTING", addr, port)

            case ["FRSH"]:
                #utf8send(s, "OK", addr, port)
                pass

            case ["CONN", local, username, localport]:
                if username in userdict:
                    hostlocal, hostaddr, hostport, hostlocalport = userdict[username]
                    expect = f"EXPECT {addr} {local} {port} {localport}"
                    connto = f"CONNTO {hostaddr} {hostlocal} {hostport} {hostlocalport}"
                    print(expect)
                    print(connto)
                    utf8send(s, expect, hostaddr, hostport)
                    utf8send(s, connto, addr, port)
                    userdict.pop(username)
                else:
                    print("Username", username, "not present")
                    utf8send(s, f"USERNAME_NOT_PRESENT", addr, port)
            case _:
                print("Unknown message", msg)

main()
