from Cryptodome.Cipher import ChaCha20
import hashlib, zstandard
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=4)


@lru_cache(maxsize=None)
def Nonce_Generator(data):
    hash_object = hashlib.sha256(data)
    sha256 = hash_object.digest()

    nonce = bytearray(12)

    for i in range(12):
        nonce[i] = (sha256[i] + sha256[i + 12]) & 0xff
        if i < 8:
            nonce[i] = (nonce[i] + sha256[i + 24]) & 0xff

    return nonce


def ChaCha20_Encrypter(data, key, nonce):
    cipher = ChaCha20.new(key=key, nonce=nonce)
    return cipher.encrypt(memoryview(data))


def ChaCha20_Decrypter(data, key, nonce):
    cipher = ChaCha20.new(key=key, nonce=nonce)
    return cipher.decrypt(memoryview(data))


cctx = zstandard.ZstdCompressor(level=21)


def ZstdCompressor(data):
    return cctx.compress(memoryview(data))


ZStandardDcmp = zstandard.ZstdDecompressor()


def ZstdDecompressor(data):
    stream_reader = ZStandardDcmp.stream_reader(data)
    decompressedTXTData = stream_reader.read()
    stream_reader.close()
    return decompressedTXTData


def From_BigUint(data):
    data_bytes = bytes(data)  # Convert the list of bytes to a bytes object
    amount = int.from_bytes(data_bytes[1:len(data_bytes)], byteorder='big')

    return amount
