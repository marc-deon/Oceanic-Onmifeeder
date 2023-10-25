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

def utf8send(sock:socket.socket, msg:bytes|str, ip:str, port:int|None=None):
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


def holepunch(sock:socket.socket, mainIp:str, altIp:str, tentativePort:int, altPort:int) -> tuple[str, int]:
        """Handshake function to connect to connect to a main/alt IP."""
        # Enforce these types
        tentativePort, altPort = int(tentativePort), int(altPort)

        # We must figure out whether to use the public or local IP for the peer
        actual = ""
        # We can try to contact the peer over this tentative port, but we may have to switch
        port = tentativePort

        attempts = 0
        while attempts < 5:
            try:
                # Try to contact peer on internet
                utf8send(sock, "HAND1", mainIp, port)

                if altIp:
                    # Try to contact peer on local network
                    utf8send(sock, "HAND1", altIp, port)

                if altPort:
                    utf8send(sock, "HAND1", mainIp, altPort)
                    
                    if altIp:
                        utf8send(sock, "HAND1", altIp, altPort)
                        


                # Listen for message from peer
                msg, ip, p = utf8get(sock, True)

                match msg:
                    # Peer has made contact with us
                    case ["HAND1"]:
                        if ip == mainIp:
                            actual = mainIp

                        elif ip == altIp:
                            actual = altIp

                        else:
                            # This is a third-party trying to connect
                            print("That's my purse!", ip)
                            continue

                        port = p
                        utf8send(sock, f"HAND2 {actual} {port}", actual, port)

                    # Peer heard our IAM and is responding!
                    case ["HAND2"]:
                        # Send one final YOUARE back to them
                        port = p
                        actual = ip
                        utf8send(sock, f"HAND2 {actual} {port}", actual, port)
                        break

                    case _:
                        print("Malformed message")
                        exit(1)

            except socket.timeout:
                print("timeout")
                continue

            except KeyboardInterrupt:
                exit(0)

            finally:
                attempts += 1

        if not actual:
            print("Failed to connect")
            raise TimeoutError()

        return actual, port
