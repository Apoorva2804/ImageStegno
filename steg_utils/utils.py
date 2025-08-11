import hashlib
import random
from typing import List
from .magic_lsb import generate_magic_square


def text_to_bytes(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


def bytes_to_text(b: bytes) -> str:
    try:
        return b.decode("utf-8")
    except Exception:
        return b.decode("latin1", errors="replace")


def generate_perm_from_key(key: str) -> List[int]:
    """
    Deterministic permutation of 4 block indices derived from key.
    Returns a permutation list of [0,1,2,3] shuffled by a seed derived from key.
    """
    seed = int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], "big")
    rnd = random.Random(seed)
    perm = [0, 1, 2, 3]
    rnd.shuffle(perm)
    return perm


def bytes_to_bitlist(b: bytes) -> List[int]:
    bits = []
    for byte in b:
        for i in range(8):
            bits.append((byte >> (7 - i)) & 1)
    return bits


def bitlist_to_bytes(bits: List[int]) -> bytes:
    out = bytearray()
    for i in range(0, len(bits), 8):
        byte = 0
        chunk = bits[i:i + 8]
        # pad last chunk with zeros if needed
        while len(chunk) < 8:
            chunk.append(0)
        for bit in chunk:
            byte = (byte << 1) | int(bit)
        out.append(byte & 0xFF)
    return bytes(out)


def embed_payload_in_channel(channel, payload_bytes: bytes, bits_per_pixel: int = 4):
    """
    Embed payload_bytes into channel's LSBs using bits_per_pixel per pixel.
    channel: 2D numpy uint8 array
    returns modified channel
    """
    import numpy as np
    flat = channel.flatten().astype(int)
    bits = bytes_to_bitlist(payload_bytes)
    total_bits = len(bits)
    capacity = flat.size * bits_per_pixel
    if total_bits > capacity:
        raise ValueError(f"Not enough capacity: need {total_bits} bits, have {capacity} bits.")
    new_flat = flat.copy()
    bit_idx = 0
    for i in range(flat.size):
        if bit_idx >= total_bits:
            break
        k = min(bits_per_pixel, total_bits - bit_idx)
        # take next k bits (msb-first in chunk)
        chunk_val = 0
        for j in range(k):
            chunk_val = (chunk_val << 1) | bits[bit_idx + j]
        # mask out lower k bits in pixel and set
        mask = (~((1 << k) - 1)) & 0xFF
        new_flat[i] = (new_flat[i] & mask) | chunk_val
        bit_idx += k
    return new_flat.reshape(channel.shape).astype("uint8")


def extract_bits_from_channel(channel, num_bits: int, bits_per_pixel: int = 4):
    """
    Extract num_bits from channel using bits_per_pixel per pixel (in same order as embed).
    Returns a bytes object constructed from extracted bits (msb-first per byte).
    """
    import numpy as np
    flat = channel.flatten().astype(int)
    bits = []
    bit_idx = 0
    for i in range(flat.size):
        if bit_idx >= num_bits:
            break
        k = min(bits_per_pixel, num_bits - bit_idx)
        val = flat[i] & ((1 << k) - 1)
        # reconstruct k bits in msb->lsb order:
        for j in range(k):
            bit = (val >> (k - 1 - j)) & 1
            bits.append(bit)
        bit_idx += k
    return bitlist_to_bytes(bits)
