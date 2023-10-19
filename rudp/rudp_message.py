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