#! /usr/bin/env python3
import socket
from socket import socket as Socket

BUFF_SIZE = 65536
HP_SERVER = ("highlyderivative.games", 4800)

def CreateSocket(timeout=0, port=0):
    s = Socket(socket.AF_INET, socket.SOCK_DGRAM)
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
        s = Socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('192.255.255.255', 1))
        _local_ip = s.getsockname()[0]
        s.close()
    return _local_ip

def GetSocketPort(s):
    return int(s.getsockname()[1])

def utf8send(sock:Socket, msg:bytes|str, ip:str, port:int|None=None):
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


def holepunch(sock:Socket, mainIp:str, altIp:str, tentativePort:int, altPort:int) -> tuple[str, int, str, int]:
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
                    case ["HAND2", oa, op]:
                        # Send one final YOUARE back to them
                        port = p
                        actual = ip
                        ourActual = oa
                        ourPort = int(op)
                        utf8send(sock, f"HAND2 {actual} {port}", actual, port)
                        break

                    case _:
                        print("Malformed message", msg)
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

        return actual, port, ourActual, ourPort

def register_for_holepunch(key:str, port:int=0) -> Socket:
    """As a host, register with holepunch server"""
    # Create a socket, open a random port
    hp_sock = CreateSocket(port=port)
    utf8send(hp_sock, "FRSH", HP_SERVER)
    ourPort = GetSocketPort(hp_sock)

    # Request a spot in the holepunch server
    utf8send(hp_sock, f"HOST {GetLocalIp()} {key} {ourPort}", HP_SERVER)
    msg = utf8get(hp_sock, True)[0]
    return hp_sock

def wait_for_holepunch(hp_sock:Socket) -> tuple[str, int, str, int]:
    """As a host, wait for holepunch server to find us a client"""
    while True:
        try:
            msg = utf8get(hp_sock, True)[0]

            match msg:
                case ["HOSTING", public]:
                    print("Hosting at...", GetLocalIp(), public)

                case ["EXPECT", clientaddr, clientlocal, clientport, clientlocalport]:
                    # Find our peer
                    peerIp, peerPort, ourIp, ourPort = holepunch(hp_sock, clientaddr, clientlocal, clientport, clientlocalport)
                    # We don't need this anymore
                    hp_sock.close()
                    
                    return peerIp, int(peerPort), ourIp, int(ourPort)
                    
                    # After this function, do something like ...
                    # enet stuff
                    # host = enet.Host(enet.Address(ourIp, ourPort), peerCount=2)
                    # peer = host.connect(enet.Address(peerIp, peerPort), channelCount=1)
                    # Start chatroom
                    # cr = enet_chatroom.Chatroom(host, peer, 0, username)
                    # curses.wrapper(cr.main)

                case ["OK"]:
                    pass

                case ["HAND1"]:
                    # Holepunching junk; it's fine
                    pass

                case _:
                    print("Invalid response", msg)

        except TimeoutError:
            # Refresh the port
            utf8send(hp_sock, "FRSH", HP_SERVER)
            continue

def connect_to_holepunch(key:str, port:int=0) -> tuple[str, int, str, int]:
    """As a client, ask holepunch server to find us a host"""
    # Create a socket, open a random port
    hp_sock = CreateSocket(port=port)
    utf8send(hp_sock, "FRSH", HP_SERVER)
    ourPort = GetSocketPort(hp_sock)

    # Send message to holepunch server
    utf8send(hp_sock, f"CONN {GetLocalIp()} {key} {ourPort}", HP_SERVER)

    # Listen for response
    while True:
        msg, addr, port = utf8get(hp_sock, True)
        match msg:
            # Recieved message with our peer's info
            case ["CONNTO", hostaddr, hostlocal, hostport, hostlocalport]:
                # Find our peer
                peerIp, peerPort, ourIp, ourPort = holepunch(hp_sock, hostaddr, hostlocal, hostport, hostlocalport)
                # We don't need this anymore
                hp_sock.close()

                return peerIp, int(peerPort), ourIp, int(ourPort)
                # After this function, do something like ...
                # enet stuff
                # host = enet.Host(enet.Address(ourIp, ourPort), peerCount=2)
                # peer = host.connect(enet.Address(peerIp, peerPort), channelCount=1)
                # Start chatroom
                # cr = enet_chatroom.Chatroom(host, peer, 0, username)
                # curses.wrapper(cr.main)apper(cr.main)

            case ["HAND1"]:
                # Holepunching junk; it's fine
                pass
            
            case _:
                print("Invalid message", msg)