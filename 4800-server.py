#! /usr/bin/env python3

from socket_convenience import utf8get, utf8send, CreateSocket

BUFF_SIZE = 65536
HOST_IP = 'highlyderivative.games'
HOST_PORT = 4800
socket_address = (HOST_IP, HOST_PORT)

def main():
    userdict = {}
    s = CreateSocket()
    s.bind(socket_address)
    print("Listening at", socket_address)
    while True:
        msg, addr, port = utf8get(s)
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
