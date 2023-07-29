import msgpack
import json


class Packet:
    def __init__(self, data: bytes | dict):
        if isinstance(data, bytes):
            self.raw_data: dict = msgpack.unpackb(data)
        else:
            self.raw_data = data

        if self.raw_data.get('Response', None) is None:
            if self.raw_data.get('Request', None) is None:
                raise Exception("Not a request nor a response, bad packet")
            self.is_request = True
            self.unpacked_data = self.raw_data['Request']
        else:
            self.is_request = False
            self.unpacked_data = self.raw_data['Response']
        self.id = self.unpacked_data['id']
        try:
            self.q = self.unpacked_data['q']
        except KeyError:
            self.r = self.unpacked_data['r']

    # def __getattr__(self, attr: str):
    #     return self.unpacked_data[attr]

    def __str__(self):
        return json.dumps(self.raw_data)

    def __repr__(self):
        return json.dumps(self.raw_data, indent=4)

    # def get_id(self) -> int:
    #     if self.is_request:
    #         return self.unpacked_data['id']
    #     else:
    #         return self.unpacked_data['id']

    def serialize(self) -> bytes:
        return msgpack.packb(self.raw_data)

    def to_model(self):
        if self.raw_data.get('Request', None) is not None:
            if self.q == "Ping":
                return PingRequest(self)
            elif self.q == "GetLastBlock":
                return GetLastBlockRequest(self)
            elif self.q == "NewBlock":
                return NewBlockRequest(self)
            elif self.q == "GetNodes":
                return GetNodesRequest(self)
            elif self.q == "Announce":
                return AnnounceRequest(self)
            elif self.q == "GetAmount":
                return GetAmountRequest(self)
            elif self.q == "GetTransaction":
                return GetTransactionRequest(self)
            elif self.q == "GetBlockByHash":
                return GetBlockByHashRequest(self)
            elif self.q == "GetBlocksByHeights":
                return GetBlocksByHeightsRequest(self)
            elif self.q == "NewTransaction":
                return NewTransactionRequest(self)
            elif self.q == "GetBlockByHeight":
                return GetBlockByHeightRequest(self)
        elif self.raw_data.get('Response', None) is not None:
            if self.r == "Ok":
                return OkResponse(self)
            elif self.r == "Ping":
                return PingResponse(self)
            elif self.r == "GetNodes":
                return GetNodesResponse(self)
            elif self.r == "GetBlock":
                return GetBlockResponse(self)
            elif self.r == "GetAmount":
                return GetAmountResponse(self)
            elif self.r == "SubmitPow":
                return SubmitPowResponse(self)
            elif self.r == "GetBlocks":
                return GetBlocksResponse(self)
            elif self.r == "GetTransaction":
                return GetTransactionResponse(self)


class AnnounceRequest(Packet):
    def __init__(self, pack: Packet):
        super().__init__(pack.raw_data)
        self.addr: bytes = bytes(pack.unpacked_data['addr'])  # pub addr: Vec<u8>


class GetAmountRequest(Packet):
    def __init__(self, pack: Packet):
        super().__init__(pack.raw_data)
        self.address: bytes = bytes(pack.unpacked_data['address'])  # pub address: Vec<u8>


class PingResponse(Packet):
    def __init__(self, pack: Packet):
        super().__init__(pack.raw_data)
        pass


class SubmitPowResponse(Packet):
    def __init__(self, pack: Packet):
        super().__init__(pack.raw_data)
        self.accepted: bool = pack.unpacked_data['accepted']  # pub accepted: bool


class OkResponse(Packet):
    def __init__(self, pack: Packet):
        super().__init__(pack.raw_data)
        pass


class PingRequest(Packet):
    def __init__(self, pack: Packet):
        super().__init__(pack.raw_data)
        pass


class GetLastBlockRequest(Packet):
    def __init__(self, pack: Packet):
        super().__init__(pack.raw_data)
        pass


class NewBlockRequest(Packet):
    def __init__(self, pack: Packet):
        super().__init__(pack.raw_data)
        self.dump: bytes = bytes(pack.unpacked_data['dump'])  # pub dump: Vec<u8>
        self.transactions: bytes = bytes(pack.unpacked_data['transactions'])  # pub transactions: Vec<u8>


class GetNodesRequest(Packet):
    def __init__(self, pack: Packet):
        super().__init__(pack.raw_data)
        pass


class GetNodesResponse(Packet):
    def __init__(self, pack: Packet):
        super().__init__(pack.raw_data)
        try:
            self.ipv4: bytes = bytes(pack.unpacked_data['ipv4'])  # pub ipv4: Option<Vec<u8>>
        except KeyError:
            self.ipv4 = None
        try:
            self.ipv6: bytes = bytes(pack.unpacked_data['ipv6'])  # pub ipv6: Option<Vec<u8>>
        except KeyError:
            self.ipv6 = None


class GetBlockResponse(Packet):
    def __init__(self, pack: Packet):
        super().__init__(pack.raw_data)
        try:
            self.dump: bytes = bytes(pack.unpacked_data['dump'])  # pub dump: Option<Vec<u8>>
        except KeyError:
            self.dump = None


class GetAmountResponse(Packet):
    def __init__(self, pack: Packet):
        super().__init__(pack.raw_data)
        self.amount: bytes = bytes(pack.unpacked_data['amount'])  # pub amount: Vec<u8>


class GetBlockByHashRequest(Packet):
    def __init__(self, pack: Packet):
        super().__init__(pack.raw_data)
        self.hash: bytes = bytes(pack.unpacked_data['hash'])  # pub hash: [u8; 32]


class GetBlockByHeightRequest(Packet):
    def __init__(self, pack: Packet):
        super().__init__(pack.raw_data)
        self.height: int = int(pack.unpacked_data['height'])  # pub height: u64


class GetBlocksByHeightsRequest(Packet):
    def __init__(self, pack: Packet):
        super().__init__(pack.raw_data)
        self.start: int = int(pack.unpacked_data['start'])  # pub start: u64
        self.amount: int = int(pack.unpacked_data['amount'])  # pub amount: u64


class GetBlocksResponse(Packet):
    def __init__(self, pack: Packet):
        super().__init__(pack.raw_data)
        self.blocks: list[bytes] = pack.unpacked_data['blocks']  # pub blocks: Vec<Vec<u8>>
        self.transactions: list[bytes] = pack.unpacked_data['transactions']  # pub transactions: Vec<Vec<u8>>


class GetTransactionRequest(Packet):
    def __init__(self, pack: Packet):
        super().__init__(pack.raw_data)
        self.hash: bytes = bytes(pack.unpacked_data['hash'])  # pub hash: [u8; 32]


class GetTransactionResponse(Packet):
    def __init__(self, pack: Packet):
        super().__init__(pack.raw_data)
        try:
            self.transaction: bytes = bytes(pack.unpacked_data['transaction'])  # pub transaction: Option<Vec<u8>>
        except KeyError:
            self.transaction = None


class NewTransactionRequest(Packet):
    def __init__(self, pack: Packet):
        super().__init__(pack.raw_data)
        self.transaction: bytes = bytes(pack.unpacked_data['transaction'])  # pub transaction: Vec<u8>
