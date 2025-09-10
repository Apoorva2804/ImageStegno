import hashlib

def _key_stream(key: str, length: int) -> bytes:
    kb = hashlib.sha256(key.encode()).digest()
    reps = (length + len(kb) - 1) // len(kb)
    return (kb * reps)[:length]

def mle_encrypt(plain: bytes, key: str) -> bytes:
    """
    A light MLEA-like transform:
    - left circular shift by 1
    - split to two nibbles B1 (upper), B2 (lower)
    - B2 = B2 XOR B1
    - combined = (B2 << 4) | B1
    - XOR with keystream derived from key
    """
    out = bytearray()
    for b in plain:
        b_shift = ((b << 1) & 0xFF) | ((b >> 7) & 0x01)
        B1 = (b_shift >> 4) & 0x0F
        B2 = b_shift & 0x0F
        B2 = B2 ^ B1
        combined = ((B2 & 0x0F) << 4) | (B1 & 0x0F)
        out.append(combined)
    ks = _key_stream(key, len(out))
    cipher = bytes([o ^ ks[i] for i, o in enumerate(out)])
    return cipher

def mle_decrypt(cipher: bytes, key: str) -> bytes:
    ks = _key_stream(key, len(cipher))
    interm = bytes([c ^ ks[i] for i, c in enumerate(cipher)])
    out = bytearray()
    for cb in interm:
        B2_enc = (cb >> 4) & 0x0F
        B1 = cb & 0x0F
        B2_orig = B2_enc ^ B1
        b_shift = ((B1 & 0x0F) << 4) | (B2_orig & 0x0F)
        b_orig = ((b_shift >> 1) & 0x7F) | ((b_shift & 0x01) << 7)
        out.append(b_orig & 0xFF)
    return bytes(out)
