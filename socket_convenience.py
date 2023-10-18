#! /usr/bin/env python3
import socket

BUFF_SIZE = 65536
def CreateSocket(timeout=0, port=0):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUFF_SIZE)
    if port:
        s.bind(('0.0.0.0', int(port)))
    if timeout:
        s.settimeout(timeout)
    return s

_local_ip = ""
def GetLocalIp():
    global _local_ip
    if not _local_ip:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('192.255.255.255', 1))
        _local_ip = s.getsockname()[0]
        s.close()
    return _local_ip

def GetSocketPort(s):
    return int(s.getsockname()[1])

def utf8send(sock, msg, ip, port=None):
    if port == None:
        ip, port = ip
    # print(f"""\
    # sock ({type(sock)}) {sock},
    # msg  ({type(msg)}) {msg},
    # ip   ({type(ip)}) {ip},
    # port ({type(port)}) {port}
    # """)
    if isinstance(msg, str):
        msg = msg.encode('utf8')
    sock.sendto(msg, (ip, int(port)))


def utf8get(sock, split=False) -> tuple[str, str, int]:
    msg, (addr, port) = sock.recvfrom(BUFF_SIZE)
    msg = msg.decode("utf8")
    if split:
        msg = msg.split(" ")
    return msg, addr, int(port)



