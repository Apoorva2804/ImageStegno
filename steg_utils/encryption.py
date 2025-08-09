def mle_encrypt(bits, key='10101010'):
    xor_bits = ''.join(str(int(b) ^ int(key[i % len(key)])) for i, b in enumerate(bits))
    rotated = xor_bits[-5:] + xor_bits[:-5]  # simple rotation
    return rotated

def mle_decrypt(bits, key='10101010'):
    unrotated = bits[5:] + bits[:5]
    original = ''.join(str(int(b) ^ int(key[i % len(key)])) for i, b in enumerate(unrotated))
    return original
