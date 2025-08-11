import os
from pathlib import Path
from steg_utils import image_ops, encryption, utils

DEFAULT_COVER = Path("input/cover.png")
DEFAULT_SECRET = Path("input/secret.txt")
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def embed_text_into_image(cover_path: str, secret_path: str, key: str, bits_per_pixel: int = 4):
    import numpy as np

    img = image_ops.load_image(cover_path)
    # internal transform
    proc = image_ops.flip_transpose(img)

    r, g, b = image_ops.split_rgb(proc)
    h, w = b.shape

    # split blue into 4 blocks
    blocks = image_ops.split_blue_blocks(b)

    # permute blocks using key (magic + secret key in spirit of paper)
    perm = utils.generate_perm_from_key(key)
    # build shuffled blocks: new position i gets original block perm[i]
    shuffled_blocks = [blocks[perm[i]] for i in range(4)]
    shuffled_blue = image_ops.combine_blue_blocks(shuffled_blocks, (h, w))

    # read secret and build caldiff
    secret_bytes = utils.text_to_bytes(secret_path)
    msg_len = len(secret_bytes)
    red_flat = r.flatten()
    if msg_len > red_flat.size:
        raise ValueError("Secret is too large relative to image red-pixel availability.")

    # compute CalDiff bytes: (message_byte - red_pixel_value) mod 256
    caldiff = bytes(((secret_bytes[i] - int(red_flat[i])) % 256) for i in range(msg_len))

    # MLEA encrypt caldiff using key
    cipher = encryption.mle_encrypt(caldiff, key)

    # We'll store an UNENCRYPTED 4-byte header = len(cipher) so extractor knows how many bytes to read
    header = len(cipher).to_bytes(4, "big")
    payload = header + cipher

    # capacity check
    total_pixels = shuffled_blue.size
    capacity_bits = total_pixels * bits_per_pixel
    required_bits = len(payload) * 8 + 32  # we already included header in payload so +32 not needed; keep consistent
    # The header is already in payload, so required is len(payload)*8
    required_bits = len(payload) * 8
    if capacity_bits < required_bits:
        raise ValueError(f"Insufficient capacity: capacity {capacity_bits} bits, need {required_bits} bits. "
                         "Use larger image or reduce message size or use fewer bits in header scheme.")

    # embed payload
    new_shuffled_blue = utils.embed_payload_in_channel(shuffled_blue, payload, bits_per_pixel=bits_per_pixel)

    # merge back (note: the stego will contain shuffled blue blocks in position)
    # we must put blocks back in same layout as shuffled_blocks (we changed only blue)
    # Create blocks_by_position list (we used shuffled_blocks placed into TL,TR,BL,BR)
    blocks_after = image_ops.split_blue_blocks(new_shuffled_blue)
    # combine with original r,g
    new_b = image_ops.combine_blue_blocks(blocks_after, (h, w))
    stego_proc = image_ops.merge_rgb(r, g, new_b)

    # inverse transform to original orientation and save
    stego = image_ops.inv_flip_transpose(stego_proc)
    out_path = OUTPUT_DIR / "stego.png"
    image_ops.save_image(stego, str(out_path))
    print(f"[+] Embedded and saved stego image to: {out_path}")


def extract_text_from_image(stego_path: str, key: str, bits_per_pixel: int = 4):
    import numpy as np

    img = image_ops.load_image(stego_path)
    proc = image_ops.flip_transpose(img)  # bring to the internal processed form
    r, g, b = image_ops.split_rgb(proc)
    h, w = b.shape

    # The stego's blue channel already contains the shuffled blocks (BC1',BC2',...)
    # flatten blue in the same ordering used for embedding:
    # first extract header (first 32 bits -> 4 bytes) to know cipher length
    # But our embedding placed header as first 4 bytes of payload. So extract first 32 bits:
    total_pixels = b.size
    header_bits = 32
    header_bytes = utils.extract_bits_from_channel(b, header_bits, bits_per_pixel=bits_per_pixel)
    cipher_len = int.from_bytes(header_bytes, "big")

    # now get cipher_len bytes => bits needed:
    needed_bits = cipher_len * 8
    # extract next needed_bits bits (starting right after header)
    # To do that we extract (header_bits + needed_bits) and then slice off first 32 bits.
    combined_bits_total = header_bits + needed_bits
    combined_bytes = utils.extract_bits_from_channel(b, combined_bits_total, bits_per_pixel=bits_per_pixel)
    # remove header (first 4 bytes)
    cipher_bytes = combined_bytes[4:4 + cipher_len]

    # decrypt
    caldiff = encryption.mle_decrypt(cipher_bytes, key)

    # reconstruct message bytes: msg_byte = (caldiff + red_pixel_value) % 256
    red_flat = r.flatten()
    if len(caldiff) > red_flat.size:
        raise ValueError("Unexpected: decrypted payload larger than red pixel count used.")
    msg_bytes = bytes(( (caldiff[i] + int(red_flat[i])) % 256 ) for i in range(len(caldiff)))
    text = utils.bytes_to_text(msg_bytes)
    print("[+] Recovered message:")
    print("--------------------------------------------------")
    print(text)
    print("--------------------------------------------------")
    return text


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


def main_menu():
    print("=== Image Steganography (paper-style) ===")
    print("1) Encrypt text (save encrypted.bin)")
    print("2) Hide (embed) text in image")
    print("3) Extract hidden text from stego image")
    print("4) Decrypt file (encrypted.bin)")
    print("5) Exit")
    choice = input("Choose option (1-5): ").strip()
    return choice


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
            bpp = input("Bits per pixel to embed (1-4) [4]: ").strip() or "4"
            try:
                bpp = int(bpp)
                if bpp < 1 or bpp > 4:
                    raise ValueError
            except Exception:
                print("Invalid bits per pixel. Using 4.")
                bpp = 4
            embed_text_into_image(cover, secret, key, bits_per_pixel=bpp)
        elif c == "3":
            stego = input("Stego image path [output/stego.png]: ").strip() or str(OUTPUT_DIR / "stego.png")
            key = input("Secret key / password: ").strip()
            bpp = input("Bits per pixel used when embedding (1-4) [4]: ").strip() or "4"
            try:
                bpp = int(bpp)
                if bpp < 1 or bpp > 4:
                    raise ValueError
            except Exception:
                print("Invalid bits per pixel. Using 4.")
                bpp = 4
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
