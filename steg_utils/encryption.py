import hashlib


def _key_stream(key: str, length: int) -> bytes:
    """
    Expand SHA-256(key) to a keystream of requested length by repeating hash bytes.
    Deterministic for a given key.
    """
    kb = hashlib.sha256(key.encode()).digest()
    reps = (length + len(kb) - 1) // len(kb)
    return (kb * reps)[:length]


def _left_circular_shift(byte: int, shift: int = 1) -> int:
    return ((byte << shift) & 0xFF) | ((byte >> (8 - shift)) & ((1 << shift) - 1))


def _right_circular_shift(byte: int, shift: int = 1) -> int:
    return ((byte >> shift) & (0xFF >> shift)) | ((byte << (8 - shift)) & 0xFF)


def mle_encrypt(plain: bytes, key: str) -> bytes:
    """
    Implements the MLEA variant described in the paper:
    - For each byte:
      * left-circular-shift by 1 -> b_shift
      * split into B1 (upper 4 bits) and B2 (lower 4 bits)
      * mask = B1 ; B2 = B2 XOR mask  (XOR is its own inverse)
      * combined = (B2 << 4) | B1
    - Then XOR combined bytes with keystream derived from key
    """
    out = bytearray()
    for b in plain:
        b_shift = ((b << 1) & 0xFF) | ((b >> 7) & 0x01)
        B1 = (b_shift >> 4) & 0x0F
        B2 = b_shift & 0x0F
        B2 = B2 ^ B1  # flip lower nibble wherever upper nibble bits are 1
        combined = ((B2 & 0x0F) << 4) | (B1 & 0x0F)
        out.append(combined)
    ks = _key_stream(key, len(out))
    cipher = bytes([o ^ ks[i] for i, o in enumerate(out)])
    return cipher


def mle_decrypt(cipher: bytes, key: str) -> bytes:
    """
    Reverse of mle_encrypt.
    """
    ks = _key_stream(key, len(cipher))
    interm = bytes([c ^ ks[i] for i, c in enumerate(cipher)])
    out = bytearray()
    for cb in interm:
        B2_enc = (cb >> 4) & 0x0F
        B1 = cb & 0x0F
        # reverse XOR: B2_original = B2_enc ^ B1  (XOR is symmetric)
        B2_orig = B2_enc ^ B1
        b_shift = ((B1 & 0x0F) << 4) | (B2_orig & 0x0F)
        # right circular shift by 1 to recover original byte
        b_orig = ((b_shift >> 1) & 0x7F) | ((b_shift & 0x01) << 7)
        out.append(b_orig & 0xFF)
    return bytes(out)
