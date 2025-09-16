from pathlib import Path
from steg_utils import image_ops, utils, encryption

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def embed_text_into_image(cover_path: str, secret_file: str, key: str, bits_per_pixel: int = 2):
    # Load and preprocess
    img = image_ops.load_image(cover_path)
    proc = image_ops.flip_transpose(img)
    r, g, b = image_ops.split_rgb(proc)

    # Read secret text from file
    text = Path(secret_file).read_text(encoding="utf-8").strip()

    # Convert text to bytes
    msg_bytes = utils.text_to_bytes(text)

    # Use red channel values
    red_flat = r.flatten()  # copy; safe for read-only usage
    if len(msg_bytes) > red_flat.size:
        raise ValueError("Message too large to hide using the chosen image's red channel length.")

    # calDiff = (msg[i] - r[i]) mod 256
    caldiff = bytes(((msg_bytes[i] - int(red_flat[i])) % 256) for i in range(len(msg_bytes)))

    # Encrypt
    cipher_bytes = encryption.mle_encrypt(caldiff, key)

    # payload = [len(cipher), cipher]
    cipher_len = len(cipher_bytes)
    header = cipher_len.to_bytes(4, "big")
    payload = header + cipher_bytes

    # Shuffle blue channel with key-derived permutation
    perm = utils.generate_perm_from_key(key)
    shuffled_blue = utils.make_shuffled_blue(b, perm)

    # Embed payload in shuffled blue channel
    new_shuffled_blue = utils.embed_payload_in_channel(
        shuffled_blue, payload, bits_per_pixel=bits_per_pixel
    )

    # Restore blue channel visually (undo shuffle for display)
    new_b = utils.unshuffle_to_visual(new_shuffled_blue, perm)

    # Combine channels and restore orientation
    stego_proc = image_ops.merge_rgb(r, g, new_b)
    stego_img = image_ops.inv_flip_transpose(stego_proc)

    # Save
    out_path = OUTPUT_DIR / "stego.png"
    image_ops.save_image(stego_img, out_path)

    print(f"[+] Stego image saved to {out_path}")
    return out_path


def extract_text_from_image(stego_path: str, key: str, bits_per_pixel: int = 2):
    # Load and preprocess
    img = image_ops.load_image(stego_path)
    proc = image_ops.flip_transpose(img)
    r, g, b = image_ops.split_rgb(proc)

    # Prepare shuffled view for reading
    perm = utils.generate_perm_from_key(key)
    shuffled_view_for_read = utils.make_shuffled_blue(b, perm)

    # Read 4-byte header (32 bits) to get cipher length
    header_bits = 32
    header_bytes = utils.extract_bits_from_channel(
        shuffled_view_for_read, header_bits, bits_per_pixel=bits_per_pixel
    )
    if len(header_bytes) != 4:
        raise ValueError("Failed to read header bytes from stego image.")
    cipher_len = int.from_bytes(header_bytes, "big")

    # Read full payload: header + cipher body, then slice out cipher
    total_bits_to_read = header_bits + cipher_len * 8
    combined = utils.extract_bits_from_channel(
        shuffled_view_for_read, total_bits_to_read, bits_per_pixel=bits_per_pixel
    )
    # combined begins with 4 header bytes, followed by cipher bytes
    cipher_bytes = combined[4:4 + cipher_len]
    if len(cipher_bytes) != cipher_len:
        raise ValueError("Cipher length mismatch when extracting from image.")

    # Decrypt to caldiff
    caldiff = encryption.mle_decrypt(cipher_bytes, key)

    # Recover original bytes using red channel
    red_flat = r.flatten()
    if len(caldiff) > red_flat.size:
        raise ValueError("Unexpected: decrypted payload larger than red pixel count used.")
    msg_bytes = bytes(((caldiff[i] + int(red_flat[i])) % 256) for i in range(len(caldiff)))

    # Decode text
    text = utils.bytes_to_text(msg_bytes)

    # Save recovered
    out = OUTPUT_DIR / "recovered.txt"
    out.write_text(text, encoding="utf-8")

    print("[+] Recovered message:")
    print("--------------------------------------------------")
    print(text)
    print("--------------------------------------------------")
    print(f"[+] Also saved to: {out}")
    return text


def main():
    print("=== Steganography with MLE Encryption ===")
    print("1. Embed message into image")
    print("2. Extract message from image")
    print("3. Encrypt text only")
    print("4. Decrypt text only")
    choice = input("Choose an option: ").strip()

    if choice == "1":
        cover = input("Cover image path [input/cover.png]: ").strip() or "input/cover.png"
        secret_file = "input/secret.txt"
        key = input("Secret key / password: ").strip()
        bpp_in = input("Bits per pixel to use (1-4) [2]: ").strip() or "2"
        try:
            bpp = int(bpp_in)
            if bpp < 1 or bpp > 4:
                raise ValueError
        except Exception:
            print("Invalid bits per pixel. Using 2.")
            bpp = 2
        embed_text_into_image(cover, secret_file, key, bits_per_pixel=bpp)

    elif choice == "2":
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
        extract_text_from_image(stego, key, bits_per_pixel=bpp)

    elif choice == "3":
        msg = input("Enter text to encrypt: ").strip()
        key = input("Secret key / password: ").strip()
        cipher = encryption.mle_encrypt(msg.encode("utf-8"), key)
        out = OUTPUT_DIR / "cipher.bin"
        out.write_bytes(cipher)
        print(f"[+] Cipher saved to {out}")

    elif choice == "4":
        cipher_path = input("Cipher file path [output/cipher.bin]: ").strip() or "output/cipher.bin"
        key = input("Secret key / password: ").strip()
        cipher_bytes = Path(cipher_path).read_bytes()
        plain = encryption.mle_decrypt(cipher_bytes, key)
        try:
            txt = plain.decode("utf-8")
        except UnicodeDecodeError:
            txt = str(plain)
        print("[+] Decrypted text:")
        print("--------------------------------------------------")
        print(txt)
        print("--------------------------------------------------")
    else:
        print("Invalid choice.")


if __name__ == "__main__":
    main()
