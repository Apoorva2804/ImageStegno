import numpy as np

def generate_magic_square(n):
    if n % 2 == 0:
        raise ValueError("Only odd-order magic squares supported")
    magic = np.zeros((n, n), dtype=int)
    i, j = 0, n // 2
    for num in range(1, n*n + 1):
        magic[i, j] = num
        i2, j2 = (i-1) % n, (j+1)%n
        if magic[i2, j2]:
            i += 1
        else:
            i, j = i2, j2
    return magic

def embed_lsb(img_plane, bits, magic):
    flat = img_plane.flatten()
    idxs = magic.flatten() - 1  # magic values start at 1

    # Make sure idxs are valid
    idxs = [i for i in idxs if 0 <= i < len(flat)]

    usable_len = min(len(bits), len(idxs))
    for i in range(usable_len):
        pos = idxs[i]
        flat[pos] = (int(flat[pos]) & ~1) | int(bits[i])

    return flat.reshape(img_plane.shape)



def extract_lsb(img_plane, bit_len, magic):
    flat = img_plane.flatten()
    idxs = magic.flatten() - 1
    bits = ''.join([str(flat[i] & 1) for i in idxs[:bit_len]])
    return bits
