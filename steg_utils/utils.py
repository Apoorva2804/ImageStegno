import os
import numpy as np
import hashlib
from .magic_lsb import generate_magic_square
from .image_ops import split_blue_blocks, combine_blue_blocks

# ------------------------------
# Blue-block shuffling helpers
# ------------------------------
def make_shuffled_blue(blue: np.ndarray, perm):
    """
    Shuffle blue channel's 4 quadrant blocks according to perm (length 4, values 0..3).
    """
    blocks = split_blue_blocks(blue)
    if len(perm) != 4 or not all(p in range(4) for p in perm):
        raise ValueError(f"Invalid permutation {perm}, must be list of 4 values from 0–3.")
    shuffled = [blocks[perm[i]] for i in range(4)]
    return combine_blue_blocks(shuffled, blue.shape)

def unshuffle_to_visual(blue_after_embed: np.ndarray, perm):
    """
    Inverse of make_shuffled_blue: place blocks back in their original visual quadrants.
    """
    blocks = split_blue_blocks(blue_after_embed)
    unshuffled = [None] * 4
    for i, p in enumerate(perm):
        unshuffled[p] = blocks[i]
    return combine_blue_blocks(unshuffled, blue_after_embed.shape)

# ------------------------------
# Basic text <-> bytes utilities
# ------------------------------
def text_to_bytes(s: str) -> bytes:
    """
    If 's' is a path to an existing file, read its bytes.
    Otherwise, treat 's' as literal text and UTF-8 encode it.
    """
    if os.path.exists(s):
        with open(s, "rb") as f:
            return f.read()
    return s.encode("utf-8")

def bytes_to_text(b: bytes) -> str:
    """Convert bytes back to string (UTF-8 with fallback)."""
    try:
        return b.decode("utf-8")
    except Exception:
        return b.decode("latin1", errors="replace")

# ------------------------------
# Key-based permutation (for 4 blocks)
# ------------------------------
def generate_perm_from_key(key: str):
    """
    Deterministic permutation of 4 indices [0,1,2,3] derived from key.
    """
    seed = int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], "big")
    rng = np.random.default_rng(seed)
    return rng.permutation(4).tolist()

# ------------------------------
# Magic-square-based visiting order
# ------------------------------
def generate_magic_indices(size: int):
    """
    Generate a magic-square-based visiting order for `size` pixels,
    tiling if necessary so it covers the whole channel.
    """
    n = int(np.floor(np.sqrt(size)))
    if n % 2 == 0:
        n -= 1
    if n < 3:
        n = 3  # smallest odd magic square we support

    base_magic = generate_magic_square(n).flatten() - 1  # 0-based
    indices = []
    while len(indices) < size:
        indices.extend(base_magic.tolist())
    return np.array(indices[:size])

# ------------------------------
# LSB embedding / extraction
# ------------------------------
def embed_payload_in_channel(channel: np.ndarray, payload: bytes, bits_per_pixel: int = 2) -> np.ndarray:
    if bits_per_pixel < 1 or bits_per_pixel > 4:
        raise ValueError("bits_per_pixel must be between 1 and 4.")

    flat = channel.flatten().astype(np.uint8)
    total_bits = len(payload) * 8
    capacity_bits = flat.size * bits_per_pixel
    if total_bits > capacity_bits:
        raise ValueError(f"Payload too large: need {total_bits} bits, have {capacity_bits} bits.")

    bits = np.unpackbits(np.frombuffer(payload, dtype=np.uint8))
    indices = generate_magic_indices(flat.size)

    new_flat = flat.copy()
    bit_idx = 0
    for idx in indices:
        for b in range(bits_per_pixel):
            if bit_idx >= total_bits:
                break
            mask = np.uint8(~(1 << b) & 0xFF)  # ✅ safe for uint8
            new_flat[idx] = np.uint8(new_flat[idx] & mask)
            new_flat[idx] = np.uint8(new_flat[idx] | ((bits[bit_idx] & 1) << b))
            bit_idx += 1
        if bit_idx >= total_bits:
            break

    return new_flat.reshape(channel.shape)

def extract_bits_from_channel(channel: np.ndarray, num_bits: int, bits_per_pixel: int = 2) -> bytes:
    """
    Extract exactly num_bits from the channel's LSBs using the same visiting order.
    Returns a bytes object constructed from those bits.
    """
    if bits_per_pixel < 1 or bits_per_pixel > 4:
        raise ValueError("bits_per_pixel must be between 1 and 4.")

    flat = channel.flatten().astype(np.uint8)
    indices = generate_magic_indices(flat.size)

    bits = []
    bit_idx = 0
    for idx in indices:
        for b in range(bits_per_pixel):
            if bit_idx >= num_bits:
                break
            bits.append((flat[idx] >> b) & 1)
            bit_idx += 1
        if bit_idx >= num_bits:
            break

    bits_arr = np.array(bits, dtype=np.uint8)
    pad = (-len(bits_arr)) % 8
    if pad:
        bits_arr = np.concatenate([bits_arr, np.zeros(pad, dtype=np.uint8)])
    return np.packbits(bits_arr).tobytes()
