from pathlib import Path
from steg_utils import image_ops, encryption, utils

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

<<<<<<< HEAD

def make_shuffled_blue(blue_channel, perm):
    blocks = image_ops.split_blue_blocks(blue_channel)
    shuffled_blocks = [blocks[perm[i]] for i in range(4)]
    return image_ops.combine_blue_blocks(shuffled_blocks, blue_channel.shape)


def extract_text_from_image(stego_path: str, key: str, bits_per_pixel: int = 2):
    img = image_ops.load_image(stego_path)
    proc = image_ops.flip_transpose(img)
    r, g, b = image_ops.split_rgb(proc)

    perm = utils.generate_perm_from_key(key)
    shuffled_view_for_read = make_shuffled_blue(b, perm)

    header_bits = 32
    header_bytes = utils.extract_bits_from_channel(
        shuffled_view_for_read, header_bits, bits_per_pixel=bits_per_pixel
    )
    cipher_len = int.from_bytes(header_bytes, "big")

    total_bits_to_read = header_bits + cipher_len * 8
    combined = utils.extract_bits_from_channel(
        shuffled_view_for_read, total_bits_to_read, bits_per_pixel=bits_per_pixel
    )
    cipher_bytes = combined[4:4 + cipher_len]

=======
def extract_text_from_image(stego_path: str, key: str, bits_per_pixel: int = 2):
    img = image_ops.load_image(stego_path)
    proc = image_ops.flip_transpose(img)
    r, g, b = image_ops.split_rgb(proc)

    perm = utils.generate_perm_from_key(key)
    shuffled_view_for_read = utils.make_shuffled_blue(b, perm)

    header_bits = 32
    header_bytes = utils.extract_bits_from_channel(shuffled_view_for_read, header_bits, bits_per_pixel=bits_per_pixel)
    cipher_len = int.from_bytes(header_bytes, "big")

    total_bits_to_read = header_bits + cipher_len * 8
    combined = utils.extract_bits_from_channel(shuffled_view_for_read, total_bits_to_read, bits_per_pixel=bits_per_pixel)
    cipher_bytes = combined[4:4 + cipher_len]

>>>>>>> origin/main
    caldiff = encryption.mle_decrypt(cipher_bytes, key)

    red_flat = r.flatten()
    if len(caldiff) > red_flat.size:
        raise ValueError("Unexpected: decrypted payload larger than red pixel count used.")

    msg_bytes = bytes(((caldiff[i] + int(red_flat[i])) % 256) for i in range(len(caldiff)))
    text = utils.bytes_to_text(msg_bytes)

    out = OUTPUT_DIR / "decrypted.txt"
    with open(out, "w", encoding="utf-8") as f:
        f.write(text)

    print("[+] Recovered message:")
    print("--------------------------------------------------")
    print(text)
    print("--------------------------------------------------")
    print(f"[+] Also saved to: {out}")
    return text

<<<<<<< HEAD

=======
>>>>>>> origin/main
if __name__ == "__main__":
    stego = input("Stego image path [output/stego.png]: ").strip() or "output/stego.png"
    key = input("Secret key / password: ").strip()
    bpp_in = input("Bits per pixel used when embedding (1-4) [2]: ").strip() or "2"
    try:
        bpp = int(bpp_in)
        if bpp < 1 or bpp > 4:
            raise ValueError
    except Exception:
        print("Invalid bits per pixel. Using 2.")
        bpp = 2
<<<<<<< HEAD

=======
>>>>>>> origin/main
    extract_text_from_image(stego, key, bits_per_pixel=bpp)
