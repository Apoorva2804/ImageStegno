import hashlib

def _key_stream(key: str, length: int) -> bytes:
    """Deterministic keystream derived from SHA-256 of key (repeated)."""
    kb = hashlib.sha256(key.encode()).digest()
    reps = (length + len(kb) - 1) // len(kb)
    return (kb * reps)[:length]

def mle_encrypt(plain: bytes, key: str) -> bytes:
    """
    MLEA-like transform (keystream XOR on top):
    - left circular shift by 1
    - split to two nibbles B1 (upper), B2 (lower)
    - B2 = B2 XOR B1
    - combined = (B2 << 4) | B1
    - XOR with keystream derived from key
    Returns bytes (cipher).
    """
    out = bytearray()
    for b in plain:
        # left circular shift by 1
        b_shift = ((b << 1) & 0xFF) | ((b >> 7) & 0x01)
        B1 = (b_shift >> 4) & 0x0F  # upper nibble
        B2 = b_shift & 0x0F         # lower nibble
        B2 = B2 ^ B1
        combined = ((B2 & 0x0F) << 4) | (B1 & 0x0F)
        out.append(combined & 0xFF)
    ks = _key_stream(key, len(out))
    cipher = bytes([o ^ ks[i] for i, o in enumerate(out)])
    return cipher

def mle_decrypt(cipher: bytes, key: str) -> bytes:
    """
    Reverse of mle_encrypt:
    - XOR keystream
    - split to B2_enc (upper) and B1 (lower)
    - B2_orig = B2_enc XOR B1
    - b_shift = (B1<<4) | B2_orig
    - right circular shift by 1 to get original byte
    """
    ks = _key_stream(key, len(cipher))
    interm = bytes([c ^ ks[i] for i, c in enumerate(cipher)])
    out = bytearray()
    for cb in interm:
        B2_enc = (cb >> 4) & 0x0F
        B1 = cb & 0x0F
        B2_orig = B2_enc ^ B1
        b_shift = ((B1 & 0x0F) << 4) | (B2_orig & 0x0F)
        # right circular shift by 1
        b_orig = ((b_shift >> 1) | ((b_shift & 0x01) << 7)) & 0xFF
        out.append(b_orig)
    return bytes(out)
