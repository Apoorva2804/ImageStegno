import os
from pathlib import Path
from steg_utils import image_ops, encryption, utils

DEFAULT_COVER = Path("input/cover.png")
DEFAULT_SECRET = Path("input/secret.txt")
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# -----------------------------
# Helpers to handle permutations
# -----------------------------

def make_shuffled_blue(blue_channel, perm):
    """
    Return a 'shuffled view' of the blue channel by rearranging its 4 blocks
    into the order dictated by perm. (No changes to pixel values.)
    """
    blocks = image_ops.split_blue_blocks(blue_channel)  # [TL, TR, BL, BR]
    shuffled_blocks = [blocks[perm[i]] for i in range(4)]
    return image_ops.combine_blue_blocks(shuffled_blocks, blue_channel.shape)


def unshuffle_to_visual(blue_channel_after_shuffled_embed, perm):
    """
    After embedding into the shuffled-blue layout, put blocks back to their
    original visual places so the saved image looks normal.
    """
    blocks_after = image_ops.split_blue_blocks(blue_channel_after_shuffled_embed)
    unshuffled_blocks = [None] * 4
    for i, orig_idx in enumerate(perm):
        unshuffled_blocks[orig_idx] = blocks_after[i]
    return image_ops.combine_blue_blocks(unshuffled_blocks, blue_channel_after_shuffled_embed.shape)


# ----------------------------------------
# Core: Embed and Extract (fixed pipeline)
# ----------------------------------------

def embed_text_into_image(cover_path: str, secret_path: str, key: str, bits_per_pixel: int = 2, visual_restore: bool = True):
    """
    Embed secret text into the cover image.
    - We internally flip+transpose for processing consistency.
    - We permute the blue blocks (by key) and embed across that shuffled view.
    - If visual_restore=True, we unshuffle back so the saved image looks normal.
    """
    img = image_ops.load_image(cover_path)
    proc = image_ops.flip_transpose(img)
    r, g, b = image_ops.split_rgb(proc)

    perm = utils.generate_perm_from_key(key)
    shuffled_blue = make_shuffled_blue(b, perm)

    # Read secret, build CalDiff using RED channel
    secret_bytes = utils.text_to_bytes(secret_path)
    red_flat = r.flatten()
    if len(secret_bytes) > red_flat.size:
        raise ValueError("Secret is too large relative to image red-pixel availability.")

    caldiff = bytes(((secret_bytes[i] - int(red_flat[i])) % 256) for i in range(len(secret_bytes)))

    # Encrypt caldiff
    cipher = encryption.mle_encrypt(caldiff, key)

    # payload = 4-byte header (len(cipher), big-endian) + cipher
    header = len(cipher).to_bytes(4, "big")
    payload = header + cipher

    # Capacity check against shuffled view
    capacity_bits = shuffled_blue.size * bits_per_pixel
    required_bits = len(payload) * 8
    if capacity_bits < required_bits:
        raise ValueError(
            f"Insufficient capacity: capacity={capacity_bits} bits, need={required_bits} bits. "
            f"Use larger image / fewer bits_per_pixel / smaller secret."
        )

    # Embed into shuffled blue
    new_shuffled_blue = utils.embed_payload_in_channel(shuffled_blue, payload, bits_per_pixel=bits_per_pixel)

    # Restore visual layout or keep shuffled look
    new_b = unshuffle_to_visual(new_shuffled_blue, perm) if visual_restore else new_shuffled_blue

    # Merge & invert transform and save
    stego_proc = image_ops.merge_rgb(r, g, new_b)
    stego = image_ops.inv_flip_transpose(stego_proc)
    out_path = OUTPUT_DIR / "stego.png"
    image_ops.save_image(stego, str(out_path))
    print(f"[+] Embedded and saved stego image to: {out_path}")


def extract_text_from_image(stego_path: str, key: str, bits_per_pixel: int = 2):
    """
    Extract secret text using the same key and bits_per_pixel.
    - We always reconstruct the same shuffled-view of blue (by key)
      before reading header & payload, regardless of whether the saved
      stego was visually restored or left scrambled.
    """
    img = image_ops.load_image(stego_path)
    proc = image_ops.flip_transpose(img)
    r, g, b = image_ops.split_rgb(proc)

    perm = utils.generate_perm_from_key(key)
    shuffled_view_for_read = make_shuffled_blue(b, perm)

    # 4-byte header (cipher length)
    header_bits = 32
    header_bytes = utils.extract_bits_from_channel(
        shuffled_view_for_read, header_bits, bits_per_pixel=bits_per_pixel
    )
    cipher_len = int.from_bytes(header_bytes, "big")

    # Extract header+payload then slice
    total_bits_to_read = header_bits + cipher_len * 8
    combined = utils.extract_bits_from_channel(
        shuffled_view_for_read, total_bits_to_read, bits_per_pixel=bits_per_pixel
    )
    cipher_bytes = combined[4:4 + cipher_len]

    caldiff = encryption.mle_decrypt(cipher_bytes, key)

    # Reconstruct original message using RED channel
    red_flat = r.flatten()
    if len(caldiff) > red_flat.size:
        raise ValueError("Unexpected: decrypted payload larger than red pixel count used.")

    msg_bytes = bytes(((caldiff[i] + int(red_flat[i])) % 256) for i in range(len(caldiff)))
    text = utils.bytes_to_text(msg_bytes)

    # Save a copy to output for convenience
    out = OUTPUT_DIR / "decrypted.txt"
    with open(out, "w", encoding="utf-8") as f:
        f.write(text)

    print("[+] Recovered message:")
    print("--------------------------------------------------")
    print(text)
    print("--------------------------------------------------")
    print(f"[+] Also saved to: {out}")
    return text


# ---------------
# CLI main menu
# ---------------

def main_menu():
    print("=== Image Steganography (paper-style) ===")
    print("1) Encrypt text (save encrypted.bin)")
    print("2) Hide (embed) text in image")
    print("3) Extract hidden text from stego image")
    print("4) Decrypt file (encrypted.bin)")
    print("5) Exit")
    choice = input("Choose option (1-5): ").strip()
    return choice


def encrypt_text_only(secret_path: str, key: str):
    data = utils.text_to_bytes(secret_path)
    enc = encryption.mle_encrypt(data, key)
    out = OUTPUT_DIR / "encrypted.bin"
    with open(out, "wb") as f:
        f.write(enc)
    print(f"[+] Encrypted file saved to: {out}")


def decrypt_file_only(enc_path: str, key: str):
    with open(enc_path, "rb") as f:
        data = f.read()
    dec = encryption.mle_decrypt(data, key)
    try:
        text = dec.decode("utf-8")
    except Exception:
        text = dec.decode("latin1", errors="replace")
    out = OUTPUT_DIR / "decrypted.txt"
    with open(out, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"[+] Decrypted output saved to: {out}")
    print(text)


if __name__ == "__main__":
    while True:
        c = main_menu()
        if c == "1":
            secret = input(f"Secret text file path [{DEFAULT_SECRET}]: ").strip() or str(DEFAULT_SECRET)
            key = input("Secret key / password: ").strip()
            encrypt_text_only(secret, key)

        elif c == "2":
            cover = input(f"Cover image path [{DEFAULT_COVER}]: ").strip() or str(DEFAULT_COVER)
            secret = input(f"Secret text file path [{DEFAULT_SECRET}]: ").strip() or str(DEFAULT_SECRET)
            key = input("Secret key / password: ").strip()

            bpp_in = input("Bits per pixel to embed (1-4) [2]: ").strip() or "2"
            try:
                bpp = int(bpp_in)
                if bpp < 1 or bpp > 4:
                    raise ValueError
            except Exception:
                print("Invalid bits per pixel. Using 2.")
                bpp = 2

            visual_flag = input("Restore visual layout after embedding? (y/n) [y]: ").strip().lower() or "y"
            visual_restore = (visual_flag != "n")

            embed_text_into_image(cover, secret, key, bits_per_pixel=bpp, visual_restore=visual_restore)

        elif c == "3":
            stego = input("Stego image path [output/stego.png]: ").strip() or str(OUTPUT_DIR / "stego.png")
            key = input("Secret key / password: ").strip()

            bpp_in = input("Bits per pixel used when embedding (1-4) [2]: ").strip() or "2"
            try:
                bpp = int(bpp_in)
                if bpp < 1 or bpp > 4:
                    raise ValueError
            except Exception:
                print("Invalid bits per pixel. Using 2.")
                bpp = 2

            extract_text_from_image(stego, key, bits_per_pixel=bpp)

        elif c == "4":
            enc = input(f"Encrypted file path [{OUTPUT_DIR / 'encrypted.bin'}]: ").strip() or str(OUTPUT_DIR / "encrypted.bin")
            key = input("Secret key / password: ").strip()
            decrypt_file_only(enc, key)

        elif c == "5":
            print("Bye.")
            break
        else:
            print("Invalid choice. Try again.")
