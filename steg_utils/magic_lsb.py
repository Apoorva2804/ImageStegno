import numpy as np

def generate_magic_square(n: int) -> np.ndarray:
    """
    Generate an n x n magic square as a NumPy array.
    Works for odd, doubly even (n % 4 == 0), and singly even (n % 2 == 0 but not multiple of 4).
    (Kept from your original implementation.)
    """
    if n < 3:
        raise ValueError("Magic square not possible for n < 3")

    if n % 2 == 1:
        magic = np.zeros((n, n), dtype=int)
        i, j = 0, n // 2
        for num in range(1, n * n + 1):
            magic[i, j] = num
            i, j = (i - 1) % n, (j + 1) % n
            if magic[i, j] != 0:
                i, j = (i + 2) % n, (j - 1) % n
        return magic

    elif n % 4 == 0:
        magic = np.arange(1, n * n + 1).reshape(n, n)
        mask = np.full((n, n), False)
        for i in range(n):
            for j in range(n):
                if (i % 4 == j % 4) or ((i % 4 + j % 4) == 3):
                    mask[i, j] = True
        magic[mask] = n * n + 1 - magic[mask]
        return magic

    else:
        half = n // 2
        sub_square = generate_magic_square(half)
        magic = np.zeros((n, n), dtype=int)
        add = [0, 2 * half * half, 3 * half * half, half * half]
        quadrants = [(0, 0), (0, half), (half, 0), (half, half)]
        for k, (r, c) in enumerate(quadrants):
            magic[r:r+half, c:c+half] = sub_square + add[k]
        k = (n - 2) // 4
        for i in range(half):
            for j in range(k):
                magic[i, j], magic[i+half, j] = magic[i+half, j], magic[i, j]
                magic[i, j+n-k], magic[i+half, j+n-k] = magic[i+half, j+n-k], magic[i, j+n-k]
        for i in range(half):
            magic[i, k], magic[i+half, k] = magic[i+half, k], magic[i, k]
        return magic


# -------------------------
# Bit/LSB utilities
# -------------------------
def bytes_to_bits(data: bytes) -> np.ndarray:
    """
    Convert bytes to a flat bit array (MSB-first for each byte).
    Returns an ndarray of dtype uint8 containing 0/1 bits.
    """
    if len(data) == 0:
        return np.zeros((0,), dtype=np.uint8)
    bits = np.unpackbits(np.frombuffer(data, dtype=np.uint8))
    # np.unpackbits yields MSB-first per byte by default, which we want.
    return bits.astype(np.uint8)

def bits_to_bytes(bits: np.ndarray) -> bytes:
    """
    Convert a flat bit array (length multiple of 8) back to bytes.
    bits expected as numpy array of dtype uint8 with values 0/1 in MSB-first ordering.
    """
    if len(bits) == 0:
        return b""
    if len(bits) % 8 != 0:
        # pad with zeros at the end (least significant bits) - this behavior must be consistent with extraction
        pad_len = 8 - (len(bits) % 8)
        bits = np.concatenate([bits, np.zeros(pad_len, dtype=np.uint8)])
    byte_arr = np.packbits(bits)
    return byte_arr.tobytes()

def embedding_capacity(blocks: list, lsb_count: int) -> int:
    """Return total embedding capacity in bits for a list of blocks given lsb_count."""
    total_pixels = sum([b.size for b in blocks])
    return total_pixels * int(lsb_count)

def embed_bits_in_blocks(blocks: list, bits: np.ndarray, lsb_count: int = 1) -> list:
    """
    Embed bit-stream into provided blocks (list of 2D numpy arrays) using LSB substitution.
    - blocks: [BC1, BC2, BC3, BC4] (each uint8 2D)
    - bits: numpy array of 0/1 bits (MSB-first from bytes_to_bits)
    - lsb_count: number of LSBs per pixel to use (1..4 recommended)
    Returns modified_blocks (deep copies).
    """
    if lsb_count < 1 or lsb_count > 8:
        raise ValueError("lsb_count must be between 1 and 8")

    bits = bits.astype(np.uint8)
    capacity = embedding_capacity(blocks, lsb_count)
    if bits.size > capacity:
        raise ValueError(f"Too many bits to embed ({bits.size}) for capacity {capacity}")

    # Flatten blocks in the canonical order BC1->BC2->BC3->BC4, row-major
    flat_pixels = np.concatenate([b.flatten() for b in blocks]).astype(np.uint8)
    mask_clear = (~((1 << lsb_count) - 1)) & 0xFF  # mask to clear LSBs
    # Create array of the per-pixel values to write (0..(2^lsb_count-1))
    # Group bits into chunks of lsb_count, MSB-first within each chunk
    if bits.size == 0:
        return [flat_pixels[0: b.size].reshape(b.shape).astype(np.uint8) for b in blocks]

    # pad bits to full chunks
    remainder = bits.size % lsb_count
    if remainder != 0:
        pad = lsb_count - remainder
        bits = np.concatenate([bits, np.zeros(pad, dtype=np.uint8)])

    bits_reshaped = bits.reshape(-1, lsb_count)  # each row is a chunk of lsb_count bits
    # convert each chunk to integer (MSB-first)
    chunk_values = np.packbits(bits_reshaped, axis=1, bitorder='big').flatten()
    # When lsb_count < 8, packbits returns values in high bits; we need to right-shift
    if lsb_count < 8:
        shift = 8 - lsb_count
        chunk_values = (chunk_values >> shift) & ((1 << lsb_count) - 1)
    # Now place chunk_values into the first N pixels
    num_chunks = chunk_values.size
    flat_pixels[:num_chunks] = ((flat_pixels[:num_chunks] & mask_clear) | chunk_values).astype(np.uint8)

    # reconstruct blocks
    out_blocks = []
    idx = 0
    for b in blocks:
        n = b.size
        out_block = flat_pixels[idx:idx+n].reshape(b.shape).astype(np.uint8)
        out_blocks.append(out_block)
        idx += n
    return out_blocks

def extract_bits_from_blocks(blocks: list, bit_count: int, lsb_count: int = 1) -> np.ndarray:
    """
    Extract bit_count bits from blocks in the canonical order BC1->BC2->BC3->BC4.
    Returns a numpy array of bits (uint8, MSB-first within each byte).
    """
    capacity = embedding_capacity(blocks, lsb_count)
    if bit_count > capacity:
        raise ValueError(f"Requested {bit_count} bits but capacity is {capacity}")

    flat_pixels = np.concatenate([b.flatten() for b in blocks]).astype(np.uint8)
    needed_chunks = (bit_count + lsb_count - 1) // lsb_count
    chunk_values = (flat_pixels[:needed_chunks] & ((1 << lsb_count) - 1)).astype(np.uint8)

    # Convert each chunk value into lsb_count bits (MSB-first)
    bits_list = []
    for val in chunk_values:
        chunk_bits = np.unpackbits(np.array([val], dtype=np.uint8))
        # chunk_bits is 8 bits; take the most significant lsb_count bits from left side of 8-bit pack
        if lsb_count < 8:
            start = 8 - lsb_count
            chunk_bits = chunk_bits[start:start+lsb_count]
        bits_list.append(chunk_bits)
    if len(bits_list) == 0:
        return np.zeros((0,), dtype=np.uint8)
    bits = np.concatenate(bits_list).astype(np.uint8)
    # truncate to requested bit_count
    bits = bits[:bit_count]
    return bits
