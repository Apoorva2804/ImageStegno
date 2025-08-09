from steg_utils.image_ops import load_image, split_rgb, flip_planes
from steg_utils.utils import bits_to_text
from steg_utils.encryption import mle_decrypt
from steg_utils.magic_lsb import generate_magic_square, extract_lsb

# Load the stego image
stego = load_image("output/stego.png")
r, g, b = split_rgb(stego)

# Flip the RGB planes (same way as embedding)
r_f, g_f, b_f = flip_planes(r, g, b)

# Use the same magic square size as in main.py
magic = generate_magic_square(7)  # 7x7 = 49 bits

# Extract 49 LSBs from the flipped red plane
extracted_bits = extract_lsb(r_f, 49, magic)

# Decrypt and convert bits to text
decrypted = mle_decrypt(extracted_bits)
message = bits_to_text(decrypted)

# Output the message
print("🔓 Extracted message:", message)
