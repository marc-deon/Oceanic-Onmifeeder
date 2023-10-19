#! /usr/bin/env python3

###############################################################################
#  Reliable UDP  #
##################
#
# This module offers two classes:
# 1. RudpMessage, which is fairly self explanitory
# 2. RudpConnection, which is a little more out-there.
#
# This module was written to solve two needs:
# 1. Establishment of a reliable (i.e. has acknowledgements) connection over
#    a regular UDP port, with some support for holepunching techniques.
# 2. Division of that connection into virtual ports, so
#    that the holepunching only ever has to be done once.
#
# The main way that this should be used is:
#
#   conn = RudpConnection(...)
#   conn.Connect(...)
#   port = conn.Virtual(localPort, remotePort)
#   
#   try:
#       port.Send("Some message")
#   except RudpTimeout:
#       print("We got no acknowledgement.")
#
#   try:
#       rudp_message = port.Receive()
#       print("message contains", rudp_message.string)
#   except RudpTimeout:
#       print("We got no response.")
#
# I very much hope that this is the final API.
#
###############################################################################

import dataclasses
from dataclasses import dataclass
import json
from socket_convenience import *

class RudpTimeout(Exception): pass
class RudpFailedToConnect(Exception): pass

@dataclass
class RudpMessage:
    srcPort:int
    destPort:int
    system:bool
    id:int
    data:bytes

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
        m = RudpMessage(**x)
        # Since json doesn't support bytes, the data will come in as a string
        m.data = bytes(m.data, 'utf8')
        return m

    @property
    def string(self) -> str:
        """Message data as string"""
        return self.data.decode()


class RudpPort:
    """(Virtual) RUDP port"""
    @property
    def socket(self):
        return self.parent.socket


    def __init__(self, port:int, peerport:int, parent:'RudpConnection') -> 'RudpPort':
        self.port:int = port
        self.peerPort:int = peerport
        self.parent:'RudpConnection' = parent
        self.queue:list[RudpMessage] = []
        self.lastId:int = 0


    def Send(self, msg:str, system:bool=False) -> None:
        """Send a message optionally marked as a system message."""
        # TODO: We should maybe have a private _SendSystem instead for this.
        self.parent.Send(self, msg, system)


    def Receive(self) -> RudpMessage:
        """Wait for message, return it and send an ACK. Also queue message for other ports in the mean time."""

        incoming = False
        # Check queue
        if len(self.queue) > 0:
            incoming = self.queue.pop(0)

        else:
            attempts = 0
            while attempts < self.parent.MAX_ATTEMPTS:
                try:
                    msg, (ip, addr) = self.socket.recvfrom(BUFF_SIZE)
                    if (ip, addr) != self.parent.peer:
                        # This is a stranger, ignore them
                        continue

                    incoming = RudpMessage.Decode(msg)

                    if (not incoming.system) or (incoming.string != "ACK"):
                        # The only time we're not going to send ACK is when the message we receive
                        # it IS a system message AND the message itself is ACK
                        self.parent._SendAck(incoming)

                    if incoming.destPort != self.port:
                        # Add to other port's queue
                        self.parent.ports[incoming.destPort].queue.append(incoming)

                    if not incoming.system:
                        break

                except TimeoutError:
                    attempts += 1

            if attempts == self.parent.MAX_ATTEMPTS:
                raise RudpTimeout()

        assert(incoming)
        return incoming
    

class RudpConnection:
    MAX_ATTEMPTS = 5

    def __init__(self, timeout:int=0, port:int=0, socket=None) -> 'RudpConnection':
        self.socket : socket.socket   = CreateSocket(timeout=timeout, port=port) if socket == None else socket
        self.peer   : tuple[str, int] = None # IP-Port pair
        self.ports  : dict[int, RudpPort] = {0: RudpPort(0, 0, self)}


    def _sendto(self, data, dest):
        """Passthrough to socket's sendto()."""
        self.socket.sendto(data, dest)


    def Send(self, port:RudpPort, msg:str, system:bool=False) -> None:
        """Sends a given string to the connected RUDP socket."""
        
        message = RudpMessage(port.port, port.peerPort, system, port.lastId, msg)

        self._sendto(message.Encode(), self.peer)
        self._WaitForAck(port.lastId, port)
        port.lastId += 1


    def _recvfrom(self) -> tuple[bytes, str, int]:
        """Passthrough to socket's recvfrom(), but ip and addr are separated."""
        msg, (ip, addr) = self.socket.recvfrom(BUFF_SIZE)
        return msg, ip, addr


    def _SendAck(self, incoming:RudpMessage) -> None:
        """Send an acknowledgement message in response to given incoming."""
        ack = RudpMessage(incoming.destPort, incoming.srcPort, True, incoming.id, "ACK").Encode()
        self._sendto(ack, self.peer)


    # TODO: This being completely from Receive() bugs me. There's a good bit of
    # Code shared. Merge? Factor out common?
    def _WaitForAck(self, expectedId:int, virtualPort:RudpPort) -> None:
        """Wait for acknowledgement, in the mean time queueing other received messages. Throw error upon timeout."""

        attempts = 0
        while attempts < self.MAX_ATTEMPTS:
            try:
                msg, addr = self.socket.recvfrom(BUFF_SIZE)
                if addr != self.peer:
                    continue

                incoming = RudpMessage.Decode(msg)

                match [incoming.destPort, incoming.system, incoming.id, incoming.string]:
                    case [virtualPort.port, True, expectedId, "ACK"]:
                        # This is what we were waiting for; leave.
                        return

                    case [0, True, _, "HAND1"]:
                        self._SendAck(incoming)

                    case [0, True, _, "HAND2"]:
                        self._SendAck(incoming)
                        
                    case [virtualPort.port, True, _, _]:
                        # If this IS intended for us, and IS a system message,
                        # but we don't have a specific answer, then panic
                        raise NotImplementedError(incoming.string)

                    case [vport, False, _, _]:
                        # If this is for anyone else and is NOT a system message,
                        # add it to their queue and send an ACK
                        self.ports[vport].queue.append(incoming)
                        self._SendAck(incoming)

                    case [vport, True, _, _]:
                        # if this is for anyone else and IS a system emssage,
                        # add it to their queue and that's it
                        self.ports[incoming.destPort].queue.append(incoming)

                    case _:
                        # What?
                        raise NotImplementedError()

            except TimeoutError:
                attempts += 1

        if attempts == self.MAX_ATTEMPTS:
            raise RudpTimeout()


    def _TryConnect(self, mainIp:str, tentativePort:int, altIp:str, altPort:int) -> None:
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
                #          port, peerPort, system, id, msg
                outgoing = RudpMessage(0, 0, True, 0, f'HAND1').Encode()
                print("sending", outgoing, (mainIp, port))
                sock.sendto(outgoing, (mainIp, port))

                if altIp:
                    # Try to contact peer on local network
                    sock.sendto(outgoing, (altIp, port))

                if altPort:
                    sock.sendto(outgoing, (mainIp, altPort))
                    if altIp:
                        sock.sendto(outgoing, (altIp, altPort))


                # Listen for message from peer
                msg, (ip, p) = sock.recvfrom(BUFF_SIZE)
                msg = RudpMessage.Decode(msg).string.split(" ")
                print("received", msg)

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
                        outgoing = RudpMessage(0, 0, True, 1, "HAND2").Encode()
                        print("sending hand2", outgoing)
                        sock.sendto(outgoing, (actual, port))

                    # Peer heard our IAM and is responding!
                    case ["HAND2"]:
                        # Send one final YOUARE back to them
                        port = p
                        actual = ip
                        outgoing = RudpMessage(0,0, True, 1, "HAND2").Encode()
                        sock.sendto(outgoing, (actual, port))
                        break

                    case _:
                        print("Malformed message")
                        exit(1)
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

        self.peer = actual, port


    def Connect(self, ip:str, altIp:str, initialPort:int, altPort:int) -> None:
        """Connect to peer RUDP."""
        self._TryConnect(ip, initialPort, altIp, altPort)


    def Virtual(self, port:int, peerPort:int) -> RudpPort:
        """Create a virtual RUDP port on this connection and return it."""
        if port in self.ports:
            raise KeyError("Duplicate port number")

        p = self.ports[port] = RudpPort(port, peerPort, self)
        return p