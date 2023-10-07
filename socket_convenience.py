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
    return s.getsockname()[1]

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


####
##
####
import dataclasses
from dataclasses import dataclass
import enum
import base64
import json

@dataclass
class RudpSegment:
    id:int
    system:bool
    data:bytearray

    def Encode(self) -> bytes:
        """Message -> dict -> json -> base64 (utf8)"""
        # return base64.b64encode(json.dumps(dataclasses.asdict(self)).encode())
        return json.dumps(dataclasses.asdict(self)).encode()

    @classmethod
    def Decode(self, msg) -> 'RudpSegment':
        """Message <- dict <- json <- base64 (utf8)"""
        # return RudpSegment(**json.loads(base64.b64decode(msg)))
        if not msg:
            return None
        x = json.loads(msg)
        return RudpSegment(**x)


class State(enum.Enum):
    CLOSED      = enum.auto()
    CONNECTED   = enum.auto()
    REGRESSED   = enum.auto()

class RUDP:
    """Reliable UDP port"""

    MAX_ATTEMPTS = 5

    def __init__(self, timeout:int=0, port:int=0) -> 'RUDP':
        self.state = State.CLOSED
        self.socket = CreateSocket(timeout=timeout, port=port)
        self.peer = None # IP-Port pair
        self.lastId = -1

    
    def utf8sendto(self, msg, ip:str, port:int) -> None:
        utf8send(self.socket, msg, ip, port)

    
    def utf8get(self, split:bool=False) -> tuple[str, str, int]:
        return utf8get(self.socket, split)

    
    def _sendto(self, msg, ip:str, port:int=None) -> None:
        if port:
            ip = ip, port
        self.socket.sendto(msg, (ip,port))


    def _HandleSystem(self, incoming):
        match incoming.data:
            case "ACK":
                return
            case "DISCONNECT":
                self.state = State.CLOSED
            case "REGRESS":
                self.state = State.REGRESSED


    def receive(self, strict=True) -> RudpSegment:
        """Recieve data from peer (unless not strict) and send an acknowledgement."""

        for attempts in range(self.MAX_ATTEMPTS):
            try:
                msg, (ip, port) = self.socket.recvfrom(BUFF_SIZE)
                break
            except socket.timeout:
                pass
            
        if attempts == self.MAX_ATTEMPTS:
            return False


        if strict:
            if ip != self.peer[0] or port != self.peer[1]:
                return None
        try:
            incoming = RudpSegment.Decode(msg)
        except json.decoder.JSONDecodeError:
            return None

        if incoming.system:
            self._HandleSystem(incoming)

        if incoming.system and incoming.data == "ACK":
            return incoming

        ack = RudpSegment(incoming.id, True, "ACK").Encode()
        self.socket.sendto(ack, self.peer)
        return incoming


    def send(self, message, system:bool=False) -> bool:
        self.lastId += 1
        message = RudpSegment(self.lastId, system, message)
        encoded = message.Encode()

        sendAttempts = 0
        while sendAttempts < self.MAX_ATTEMPTS:
            try:
                sendAttempts += 1
                # Send message
                self.socket.sendto(encoded, self.peer)

                getAttempts = 0
                while getAttempts < self.MAX_ATTEMPTS:
                    # Wait for acknowledgement
                    response = self.receive()

                    if not response:
                        continue

                    if not response.system:
                        continue

                    if response.id != message.id:
                        continue

                    if response.data != "ACK":
                        continue
                    return True

            except socket.timeout:
                print("Timeout")
                if sendAttempts >= self.MAX_ATTEMPTS:
                    return False
                sendAttempts += 1

        
        
    def _PeerHandshake(self, peerPublic:str, peerLocal:str, tentativePort:int) -> tuple[str, int]:
        """Connect to a peer at either their public/local IP and a tentative Port"""

        sock = self.socket

        # We must figure out whether to use the public or local IP for the peer
        actual = ""
        # We can try to contact the peer over this tentative port, but we may have to switch
        port = tentativePort


        attempts = 0
        while attempts < 5:
            try:
                # Try to contact peer on internet
                utf8send(sock, f'IAM {GetSocketPort(sock)}', peerPublic, port)

                if peerLocal:
                    # Try to contact peer on local network
                    utf8send(sock, f'IAM {GetSocketPort(sock)}', peerLocal, port)

                # Listen for message from peer
                msg, ip, p = utf8get(sock, True)

                match msg:
                    # Peer heard our IAM and is responding!
                    case ["YOUARE"]:
                        # Send one final YOUARE back to them
                        port = p
                        actual = ip
                        utf8send(sock, "YOUARE", actual, port)
                        break

                    # Peer has made contact with us
                    case ["IAM", _p]:
                        if ip == peerPublic:
                            actual = peerPublic
                        elif ip == peerLocal:
                            actual = peerLocal
                        else:
                            # This is a third-party trying to connect
                            print("That's my purse!", ip, peerPublic)
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
            return False

        return actual, int(port)

    def connect(self, ip:str, initialPort:int, altIp:str = None) -> bool:
        result = self._PeerHandshake(ip, altIp, initialPort)
        
        if not result:
            return False
        
        self.peer = result

        self.send("CONNECTING", True)
        msg = self.receive()
        if (not msg.system) or (msg.data != 'CONNECTING' and msg.data != 'ACK'):
            self.peer = None
            return False

        self.state = State.CONNECTED
        return True

    
    def disconnect(self) -> None:
        self.state = State.CLOSED
        self.send("DISCONNECT", True)
    
    def regress(self) -> socket.socket:
        """Disable usage as RELIABLE UDP, but return regular UDP socket"""
        self.state = State.REGRESSED
        self.send("REGRESS", True)
        return self.socket


if __name__ == "__main__":

    def _test(sock:RUDP, ip:str, port:int, label:str):
        result = sock.connect(ip, port)
        

        print(sock.send("Hello world!"))
    
        while sock.receive().data == "ACK":
            print("ACK")

        print("blah")



    from sys import argv
    from threading import Thread
    if "rudp" in argv:
        sockA = RUDP(timeout=0.1, port=4801)
        sockB = RUDP(timeout=0.1, port=4802)
        tA = Thread(target=_test, args=(sockA, '127.0.0.1', 4802, "A"))
        tB = Thread(target=_test, args=(sockB, '127.0.0.1', 4801, "B"))

        tA.start()
        tB.start()
        
        
