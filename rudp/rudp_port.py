# from .rudp_connection import RudpConnection
from .rudp_message import RudpMessage
from .rudp_exceptions import RudpTimeout
from socket_convenience import BUFF_SIZE


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