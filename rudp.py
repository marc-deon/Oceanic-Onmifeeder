#! /usr/bin/env python3
import dataclasses
from dataclasses import dataclass
import enum
import json
from socket_convenience import *

@dataclass
class RudpMessage:
    id:int
    system:bool
    data:bytearray

    # TODO: Add base64 back in
    def Encode(self) -> bytes:
        """Message -> dict -> json"""
        # return base64.b64encode(json.dumps(dataclasses.asdict(self)).encode())
        return json.dumps(dataclasses.asdict(self)).encode()

    # TODO: Add base64 back in
    @classmethod
    def Decode(self, msg:bytes) -> 'RudpMessage':
        """Message <- dict <- json"""
        # return RudpSegment(**json.loads(base64.b64decode(msg)))
        x = json.loads(msg.decode())
        return RudpMessage(**x)

    @property
    def string(self) -> str:
        return self.data.decode()

class State(enum.Enum):
    CLOSED      = enum.auto()
    CONNECTED   = enum.auto()
    SENDING     = enum.auto()
    RECIEVING   = enum.auto()
    REGRESSED   = enum.auto()

class RudpInvalidState(Exception):
    pass

class RudpTimeout(Exception):
    pass

class RudpFailedToConnect(Exception):
    pass

class RUDP:
    """Reliable UDP port"""

    MAX_ATTEMPTS = 5

    def _sendto(self, data, dest):
        """Passthrough to socket's sendto()."""
        print(f"sending {data} to {dest}")
        self.socket.sendto(data, dest)

    def __init__(self, timeout:int=0, port:int=0) -> 'RUDP':
        self.state  : State           = State.CLOSED
        self.socket : socket.socket   = CreateSocket(timeout=timeout, port=port)
        self.peer   : tuple[str, int] = None # IP-Port pair
        self.lastId : int             = -1
        self.recvQueue : list[RudpMessage] = []
    

    def _recvfrom(self) -> tuple[bytes, str, int]:
        """Passthrough to socket's recvfrom(), but ip and addr are separated."""
        msg, (ip, addr) = self.socket.recvfrom(BUFF_SIZE)
        return msg, ip, addr


    def Send(self, msg:str, system:bool=False) -> None:
        """Sends a given string to the connected RUDP socket."""
        if self.state != State.CONNECTED:
            raise RudpInvalidState("Can only send while connected!")

        self.lastId += 1
        message = RudpMessage(self.lastId, system, msg)
        
        self._sendto(message.Encode(), self.peer)
        self._WaitForAck(id)


    def _SendAck(self, incoming:RudpMessage) -> None:
        """Send an acknowledgement message in response to given incoming."""
        ack = RudpMessage(incoming.id, True, "ACK").Encode()
        self._sendto(ack, self.peer)


    # TODO: This being completely from Receive() bugs me. There's a good bit of
    # Code shared. Merge? Factor out common?
    def _WaitForAck(self, id:int) -> None:
        """Wait for acknowledgement, in the mean time queueing other received messages. Throw error upon timeout."""
        attempts = 0
        while attempts < self.MAX_ATTEMPTS:
            try:
                msg, addr = self.socket.recvfrom(BUFF_SIZE)
                if addr != self.peer:
                    print("Skipping unknown address", addr, "VS", self.peer)
                    continue

                incoming = RudpMessage.Decode(msg)

                match [incoming.system, incoming.data, incoming.id]:
                    case [True, "ACK", id]:
                        self.state = State.CONNECTED
                        return

                    case [True, "HAND1", _]:
                        pass
                    
                    case [True, "HAND2", _]:
                        pass

                    case [False, _, _]:
                        self.recvQueue.append(incoming)
                        self._SendAck(incoming)
                        


                    case _:
                        raise NotImplementedError()
                    
            except TimeoutError:
                attempts += 1
        
        if attempts == self.MAX_ATTEMPTS:
            raise RudpTimeout()


    def Receive(self) -> RudpMessage:
        """Wait for message from connected socket, return it and send an ACK."""
        if self.state != State.CONNECTED: #and self.state != State.SENDING:
            raise RudpInvalidState("Can only recieve while connected or waiting for send-ack!")

        incoming = False
        # Check queue
        if len(self.recvQueue) > 0:
            incoming = self.recvQueue.pop(0)

        else:
            attempts = 0
            while attempts < self.MAX_ATTEMPTS:
                try:
                    msg, (ip, addr) = self.socket.recvfrom(BUFF_SIZE)
                    if (ip, addr) != self.peer:
                        print("Skipping unknown address", ip, addr, "VS", self.peer)
                        continue

                    incoming = RudpMessage.Decode(msg)
                    if incoming.system:
                        
                        continue

                    else:
                        self._SendAck(incoming)
                        break

                except TimeoutError:
                    attempts += 1
            
            if attempts == self.MAX_ATTEMPTS:
                raise RudpTimeout()

        assert(incoming)
        return incoming


    def _TryConnect(self, mainIp:str, tentativePort:int, altIp:str):
        """Handshake function to connect to connect to a main/alt IP."""
        sock = self.socket
        
        # We must figure out whether to use the public or local IP for the peer
        actual = ""
        # We can try to contact the peer over this tentative port, but we may have to switch
        port = tentativePort
        assert isinstance(port, int)

        attempts = 0
        while attempts < self.MAX_ATTEMPTS:
            try:
                # Try to contact peer on internet
                outgoing = RudpMessage(-1, True, f'HAND1').Encode()
                sock.sendto(outgoing, (mainIp, port))

                if altIp:
                    # Try to contact peer on local network
                    sock.sendto(outgoing, (altIp, port))

                # Listen for message from peer
                msg, (ip, p) = sock.recvfrom(BUFF_SIZE)
                msg = RudpMessage.Decode(msg).data.split(" ")

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
                        outgoing = RudpMessage(-1, True, "HAND2").Encode()
                        sock.sendto(outgoing, (actual, port))

                    # Peer heard our IAM and is responding!
                    case ["HAND2"]:
                        # Send one final YOUARE back to them
                        port = p
                        actual = ip
                        outgoing = RudpMessage(-1, True, "HAND2").Encode()
                        sock.sendto(outgoing, (actual, port))
                        break

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
            print("Failed to connect")
            raise RudpFailedToConnect()

        self.state = State.CONNECTED
        self.peer = actual, port


    def Connect(self, ip:str, initialPort:int, altIp:str=None):
        """Connect to peer RUDP port."""

        match self.state:
            case State.CLOSED:
                try:
                    self._TryConnect(ip, initialPort, altIp)
                except Exception as e:
                    raise e

            case _:
                raise RudpInvalidState("Can only connect from a closed state!")


    def Disconnect(self) -> None:
        self.state = State.CLOSED
        self.Send("DISCONNECT", True)

    def Regress(self) -> socket.socket:
        """Disable usage as RELIABLE UDP, but return regular UDP socket"""
        self.state = State.REGRESSED
        self.Send("REGRESS", True)
        return self.socket
    
################################################################################
################################################################################


if __name__ == "__main__":
    # Testing stuff

    from sys import argv
    ip, port, label = argv[1:]
    print(ip, port, label)
    sock = RUDP(timeout=1, port=port)

    port = 4800 if port == "4801" else 4801


    sock.Connect(ip, port)

    #########
    ## Test A

    if 'm' in label:
        print("Sending math request")
        sock.Send("15+5")
        print(sock.Receive())
    else:
        print("Receiving math request")
        m = sock.Receive()
        ans = sum(int(x) for x in m.data.split("+"))
        sock.Send(str(ans))

    print(sock.state)

    #########
    ## Test B
    # sock.Send(f"I am {label}")
    # m = sock.Receive()
    # print(m)
    # sock.Send(f"Yo fr? You're {m.data.split(' ')[-1]}?")
    # sock.Send(f"That's crazy.")
    # print(sock.Receive())
    # print(sock.Receive())