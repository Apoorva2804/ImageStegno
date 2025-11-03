import sys
from pathlib import Path
from steg_utils import encryption, image_ops, utils
from histogram import plot_side_by_side_hist
from rs_analysis import rs_analysis
from pdh_plot import plot_pdh
from metrics import run_single_pair, print_table, save_csv

OUTPUT_DIR = Path("output")
RESULTS_DIR = Path("results")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# ---------- Core Functions ----------

def encrypt_text_file(secret_path: str, key: str, out_file: str = "output/encrypted.bin"):
    secret_bytes = utils.text_to_bytes(secret_path)
    cipher = encryption.mle_encrypt(secret_bytes, key)
    Path(out_file).parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "wb") as f:
        f.write(cipher)
    print(f"[+] Encrypted text saved to {out_file}")
    return out_file

def decrypt_text_file(enc_file: str, key: str, out_file: str = "output/decrypted.txt"):
    with open(enc_file, "rb") as f:
        cipher = f.read()
    plain = encryption.mle_decrypt(cipher, key)
    text = utils.bytes_to_text(plain)
    Path(out_file).parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"[+] Decrypted text saved to {out_file}")
    print("--------------------------------------------------")
    print(text)
    print("--------------------------------------------------")
    return text

def embed_text_into_image(cover_path: str, enc_file: str, key: str, bits_per_pixel: int = 1):
    img = image_ops.load_image(cover_path)
    proc = image_ops.flip_transpose(img)
    r, g, b = image_ops.split_rgb(proc)
    h, w = b.shape

    # Split + shuffle blue
    blocks, split_indices = image_ops.split_blue_blocks(b)
    perm = utils.generate_perm_from_key(key)
    shuffled = [blocks[p] for p in perm]
    shuffled_blue = image_ops.combine_blue_blocks(shuffled, (h, w), split_indices)

    # Read encrypted payload
    with open(enc_file, "rb") as f:
        cipher = f.read()

    # Header + cipher
    header = len(cipher).to_bytes(4, "big")
    payload = header + cipher

    # Embed into shuffled blue using key-based pixel permutation
    stego_shuffled_blue = utils.embed_payload_in_channel(
        shuffled_blue, payload, bits_per_pixel=bits_per_pixel
    )

    # Unshuffle back to visual
    stego_blue = utils.unshuffle_to_visual_with_indices(stego_shuffled_blue, perm, split_indices)

    stego_proc = image_ops.merge_rgb(r, g, stego_blue)
    stego = image_ops.inv_flip_transpose(stego_proc)

    out_path = OUTPUT_DIR / "stego.png"
    image_ops.save_image(stego, str(out_path))
    print(f"[+] Stego image saved to {out_path}")
    return out_path

def extract_text_from_image(
    stego_path: str, key: str, bits_per_pixel: int = 1, out_file: str = "output/extracted.bin"
):
    img = image_ops.load_image(stego_path)
    proc = image_ops.flip_transpose(img)
    r, g, b = image_ops.split_rgb(proc)
    h, w = b.shape

    # Shuffle blue as embedding did
    perm = utils.generate_perm_from_key(key)
    shuffled_blue, split_indices = utils.make_shuffled_blue(b, perm)

    # Header (cipher length: 32 bits)
    header_bytes = utils.extract_bits_from_channel(
        shuffled_blue, 32, bits_per_pixel=bits_per_pixel
    )  # Removed key argument
    cipher_len = int.from_bytes(header_bytes, "big")

    # Cipher
    total_bits = (cipher_len * 8) + 32
    combined = utils.extract_bits_from_channel(
        shuffled_blue, total_bits, bits_per_pixel=bits_per_pixel
    )  # Removed key argument
    cipher_bytes = combined[4:4 + cipher_len]

    Path(out_file).parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "wb") as f:
        f.write(cipher_bytes)

    print(f"[+] Extracted encrypted data saved to {out_file}")
    return out_file

# ---------- Extra Features ----------

def run_histogram():
    plot_side_by_side_hist(
        "input/cover.png", "output/stego.png", "results/hist_side_by_side.png"
    )

def run_rs_analysis():
    rs_analysis("output/stego.png")

def run_pdh():
    plot_pdh("input/cover.png", "output/stego.png", "results/pdh.png")

# main.py — replace run_metrics()
def run_metrics():
    key = input("Secret key / password (same as embedding): ").strip()
    bpp_in = input("Bits per pixel (1-4) [1]: ").strip() or "1"
    bpp = int(bpp_in)
    dims = [128, 256, 512, 1024]
    enc_file = "output/encrypted.bin"
    if not Path(enc_file).exists():
        print("[!] Encrypted payload not found, run option 1 first."); return
    results = run_single_pair("input/cover.png", enc_file, key, bpp, dims)
    print_table(results)
    save_csv(results, "results/metrics_single_pair.csv")
    print("[+] Metrics saved to results/metrics_single_pair.csv")

# ---------- Interactive Menu ----------

def main():
    while True:
        print("\n===== Image Steganography Menu =====")
        print("1. Encrypt text")
        print("2. Embed encrypted text in image")
        print("3. Extract encrypted text from stego image")
        print("4. Decrypt text")
        print("5. Plot Histogram (Cover vs Stego)")
        print("6. RS Analysis (Stego)")
        print("7. Pixel Difference Histogram (Cover vs Stego)")
        print("8. Compute Metrics (MSE, RMSE, PSNR, SSIM, NCC)")
        print("9. Exit")
        choice = input("Enter choice (1-9): ").strip()

        if choice == "1":
            secret = input("Secret text file path [input/secret.txt]: ").strip() or "input/secret.txt"
            key = input("Secret key / password: ").strip()
            encrypt_text_file(secret, key)

        elif choice == "2":
            cover = input("Cover image path [input/cover.png]: ").strip() or "input/cover.png"
            enc_file = input("Encrypted file path [output/encrypted.bin]: ").strip() or "output/encrypted.bin"
            key = input("Secret key / password: ").strip()
            bpp_in = input("Bits per pixel (1-4) [1]: ").strip() or "1"
            bpp = int(bpp_in)
            embed_text_into_image(cover, enc_file, key, bpp)

        elif choice == "3":
            stego = input("Stego image path [output/stego.png]: ").strip() or "output/stego.png"
            key = input("Secret key / password: ").strip()
            bpp_in = input("Bits per pixel (1-4) [1]: ").strip() or "1"
            bpp = int(bpp_in)
            extract_text_from_image(stego, key, bpp)

        elif choice == "4":
            enc_file = input("Encrypted file path [output/extracted.bin]: ").strip() or "output/extracted.bin"
            key = input("Secret key / password: ").strip()
            decrypt_text_file(enc_file, key)

        elif choice == "5":
            run_histogram()

        elif choice == "6":
            run_rs_analysis()

        elif choice == "7":
            run_pdh()

        elif choice == "8":
            run_metrics()

        elif choice == "9":
            print("Exiting...")
            sys.exit(0)

        else:
            print("Invalid choice, try again.")

if __name__ == "__main__":
    main()
