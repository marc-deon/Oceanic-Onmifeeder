import dataclasses
from dataclasses import dataclass
import json

@dataclass
class RudpMessage:
    srcPort:int
    destPort:int
    system:bool
    id:int
    data:bytes

    def __post_init__(self):
        if isinstance(self.data, str):
            self.data = self.data.encode()
            # raise Exception(self.data)

    # TODO: Add base64 back in
    def Encode(self) -> bytes:
        """Message -> dict -> json"""
        d = dataclasses.asdict(self)
        # Json doesn't support bytes, so we need to convert data to a string, and then
        # dump the whole thing into a json string, and then get the bytes from that
        d['data'] = self.string
        return json.dumps(d).encode()

    # TODO: Add base64 back in
    @classmethod
    def Decode(self, msg:bytes) -> 'RudpMessage':
        """Message <- dict <- json"""
        assert isinstance(msg, bytes), "message must be bytes"

        x = json.loads(msg.decode())
        m = RudpMessage(**x)
        # m.data = bytes.fromhex(m.data) #m.data.decode()
        return m

    @property
    def string(self) -> str:
        """Message data as string"""
        return self.data.decode()