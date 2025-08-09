def text_to_bits(text):
    return ''.join(format(ord(c), '08b') for c in text)

def bits_to_text(bits):
    chars = [bits[i:i+8] for i in range(0, len(bits), 8)]
    return ''.join([chr(int(b, 2)) for b in chars if len(b) == 8])

def pad_bits(bitstring, multiple):
    pad_len = (multiple - len(bitstring) % multiple) % multiple
    return bitstring + '0' * pad_len
