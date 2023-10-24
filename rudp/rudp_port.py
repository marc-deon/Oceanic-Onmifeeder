# from .rudp_connection import RudpConnection
from .rudp_message import RudpMessage
from .rudp_exceptions import RudpTimeout
from socket_convenience import BUFF_SIZE
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from rudp import RudpConnection

class RudpPort:
    """(Virtual) RUDP port"""
    @property
    def socket(self):
        return self.parent.socket


    def __init__(self, port:int, peerport:int, parent:'RudpConnection', stream:bool=False) -> 'RudpPort':
        self.port:int = port
        self.peerPort:int = peerport
        self.parent:'RudpConnection' = parent
        self.queue:list[RudpMessage] = []
        self.lastId:int = 0
        self.stream:bool = stream


    def Send(self, msg:str|bytes) -> None:
        """Send a message optionally marked as a system message."""
        if isinstance(msg,str):
            msg = msg.encode()
        self.parent._Send(self, msg, system=False)


    def _SendSystem(self, msg:str) -> None:
        self.parent._Send(self, msg, system=True)
        pass


    def Receive(self) -> RudpMessage:
        """Wait for message, return it and send an ACK. Also queue message for other ports in the mean time."""
        m = self.parent._Receive(self)
        while m.system:
            m = self.parent._Receive(self)
        return m
        