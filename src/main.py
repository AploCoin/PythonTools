import socket, msgpack
import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import os, random
import x25519
import ecdsa
from hasher import *

# Get the number of CPUs in the system
num_cpus = 61 # os.cpu_count()

# Create ThreadPoolExecutor with the number of workers equal to the number of CPUs
executor = ThreadPoolExecutor(max_workers=num_cpus*1024)
process_executor = ProcessPoolExecutor(max_workers=num_cpus)  # For CPU-intensive tasks


class SocketHandler:
    def __init__(self):
        self.sockert = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.list_nodes = [["0.0.0.0", 5050, False, 0]]  # Ip, Port, Is alive, time
        self.selected_node = []

        # Check exists ip to nodes from  "self.list_nodes"
        self.Checker_Exist_Host()

        self.received_data = {}  # Dictionary to hold received data with ID as key

        self.__data_user = {}
        self.__is_listening = False

    def Checker_Exist_Host(self):
        # Check node
        for i in range(len(self.list_nodes)):
            start = time.time()
            try:
                self.sockert.connect(
                    (self.list_nodes[i][0], self.list_nodes[i][1])
                )
                self.sockert.close()
            except socket.error as msg:
                # Win error solution
                if self.list_nodes[i][0] == "0.0.0.0":
                    self.list_nodes[i][0] = "localhost"
                    try:
                        self.sockert.connect(
                            (self.list_nodes[i][0], self.list_nodes[i][1])
                        )
                        self.sockert.close()
                    except socket.error as msg:
                        self.list_nodes[i][2] = False
                    else:
                        self.list_nodes[i][2] = True

                else:
                    self.list_nodes[i][2] = False

            else:
                self.list_nodes[i][2] = True
            self.sockert.close()
            self.sockert = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.list_nodes[i][3] = float(f"{(time.time() - start):.{6}f}")

            if self.list_nodes[i][2]:
                if not self.selected_node:
                    self.selected_node = self.list_nodes[i]

                if self.selected_node[3] < self.list_nodes[i][3]:
                    self.selected_node = self.list_nodes[i]

    def Connect_To_Nodes(self):
        if not self.selected_node:
            self.Checker_Exist_Host()

        if not self.selected_node:
            return

        self.sockert = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.sockert.connect(
            (self.selected_node[0],  # Host of Node
             self.selected_node[1])  # Port of Node
        )
        data = self.sockert.recv(32)
        private_key = os.urandom(32)
        public_key = x25519.scalar_base_mult(private_key)
        shared_key = x25519.scalar_mult(private_key, data)
        nonce_key = Nonce_Generator(shared_key)
        self.sockert.sendall(public_key)

        self.__data_user = {
            "socket": {
                "connection": self.sockert,
                "selected-node": self.selected_node
            },
            "keys": {
                "server": {
                    "public-key": data
                },
                "client": {
                    "public-key": public_key,
                    "private-key": private_key,
                },
                "maintenance": {
                    "shared-key": shared_key,
                    "nonce-key": nonce_key
                }
            }
        }
        self.__is_listening = True
        executor.submit(self.__listen_for_messages)

    def Close(self):
        self.__is_listening = False

    def __listen_for_messages(self):
        while self.__is_listening:
            try:
                data_size = int.from_bytes(self.sockert.recv(4), "big")
                data = self.sockert.recv(data_size)
                data = ChaCha20_Decrypter(
                    data,
                    self.__data_user["keys"]["maintenance"]["shared-key"],
                    bytes(self.__data_user["keys"]["maintenance"]["nonce-key"])
                )
                data = ZstdDecompressor(data)
                data = msgpack.unpackb(data)

                try:
                    if data["Request"]:
                        pass
                except:
                    request_id = data["Response"]["id"]
                    self.received_data[request_id] = data

            except socket.error as e:
                print(f"Socket error: {e}")
                break

        self.sockert.close()

    def Send_Message(self, message):
        id_req = random.randint(1, 1000000)

        message["Request"]["id"] = id_req

        if self.__data_user == {}:
            raise Exception("No Nodes or not inited")

        sockert = self.__data_user["socket"]["connection"]
        message = msgpack.packb(message)
        message = ZstdCompressor(message)
        message = ChaCha20_Encrypter(
            message,
            self.__data_user["keys"]["maintenance"]["shared-key"],
            bytes(self.__data_user["keys"]["maintenance"]["nonce-key"])
        )

        sockert.send(len(message).to_bytes(4, byteorder="big"))
        sockert.sendall(message)
        return id_req  # Return request ID so that we can use it to get the response

    def Receive_Data(self, request_id, timeout=20):
        start_time = time.time()
        while time.time() - start_time < timeout:
            data = self.received_data.pop(request_id, None)
            if data is not None:
                return data
            time.sleep(0.1)  # Don't hog the CPU

        # If we've reached this point, it means the timeout was hit without receiving the data
        raise Exception(f"Timeout waiting for data with ID {request_id}")

    def Check_Ping(self):
        ping_message = {
            "Request": {
                "q": "Ping"
            }
        }
        start_time = time.time()
        id = self.Send_Message(ping_message)
        self.Receive_Data(id)
        self.__data_user["socket"]["selected-node"][3] = float(f"{(time.time() - start_time):.{6}f}")
        return self.__data_user["socket"]["selected-node"][3]


class Wallet:
    def __init__(self, socks):
        self.sockert = socks
        self.__data = {}

    def Create_Wallet(self):
        private_key = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
        public_key = private_key.get_verifying_key()
        compressed_public_key = public_key.to_string("compressed")

        self.__data = {
            "private-key": private_key,
            "public-key": public_key,
            "wallet-key": compressed_public_key
        }

    def Load_Wallet(self, private_key):
        public_key = private_key.get_verifying_key()
        compressed_public_key = public_key.to_string("compressed")

        self.__data = {
            "private-key": private_key,
            "public-key": public_key,
            "wallet-key": compressed_public_key
        }

    def Check_Balance(self, wallet_addr=None):
        if wallet_addr is None:
            wallet_addr = self.__data["wallet-key"]
        request_id = self.sockert.Send_Message({
            "Request": {
                "q": "GetAmount",
                "address": list(wallet_addr)
            }
        })
        data = self.sockert.Receive_Data(request_id)
        try:
            return [wallet_addr.hex(), From_BigUint(data["Response"]["amount"])]
        except:
            pass

if __name__ == "__main__": 
    handlers = SocketHandler()
    handlers.Connect_To_Nodes()
    handlers.Check_Ping()

    wallet = Wallet(handlers)
    wallet.Create_Wallet()

    print(wallet.Check_Balance())  # bytes.fromhex()

    # Genesis address with 648,999,974,080,000 AploCoins
    default_addr = bytearray([
        3, 27, 132, 197, 86, 123, 18, 100, 64, 153, 93, 62, 213, 170, 186, 5, 101, 215, 30, 24, 52, 96,
        72, 25, 255, 156, 23, 245, 233, 213, 221, 7, 143,
    ])
    default_addr_stats = wallet.Check_Balance(wallet_addr=default_addr)
    print("{:,}".format(default_addr_stats[1]))

    start = time.time()
    for i in range(100):
        wallet = Wallet(handlers)
        wallet.Create_Wallet()
        wallet.Check_Balance()

    print(f"100 wallets need time: {time.time() - start}")
    handlers.Close()