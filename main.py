import os
import cv2
from steg_utils.image_ops import load_image, split_rgb, flip_planes, merge_rgb
from steg_utils.utils import text_to_bits
from steg_utils.encryption import mle_encrypt
from steg_utils.magic_lsb import generate_magic_square, embed_lsb

# Ensure output directory exists
if not os.path.exists("output"):
    os.makedirs("output")

# Load cover image
img = load_image("input/cover.png")
r, g, b = split_rgb(img)

# Flip RGB planes
r_f, g_f, b_f = flip_planes(r, g, b)

# Load secret message
with open("input/secret.txt", "r") as f:
    secret = f.read()

# Convert to bits and encrypt
bits = text_to_bits(secret)
enc = mle_encrypt(bits)

# Use a 7x7 magic square (49 bits = 6 characters)
magic = generate_magic_square(7)
enc_trimmed = enc[:49]

# Embed into Red channel
r_embed = embed_lsb(r_f.copy(), enc_trimmed, magic)

# Merge and save output
final_img = merge_rgb(r_embed, g_f, b_f)
cv2.imwrite("output/stego.png", final_img)

print(" Stego image saved as output/stego.png")
