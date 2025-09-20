import cv2
import numpy as np
import matplotlib.pyplot as plt
import os

def plot_pdh(cover_path: str, stego_path: str, out_path="results/pdh.png"):
    cover = cv2.imread(cover_path, cv2.IMREAD_GRAYSCALE).astype(np.int16)
    stego = cv2.imread(stego_path, cv2.IMREAD_GRAYSCALE).astype(np.int16)

    if cover is None or stego is None:
        raise FileNotFoundError("Cover or stego image not found.")

    diff_cover = np.diff(cover.flatten())
    diff_stego = np.diff(stego.flatten())

    bins = np.arange(-40, 41)

    plt.figure(figsize=(10, 6))
    cover_hist, _ = np.histogram(diff_cover, bins=bins)
    stego_hist, _ = np.histogram(diff_stego, bins=bins)

    plt.plot(bins[:-1], cover_hist, label="Cover", color="blue", linewidth=1.5)
    plt.plot(bins[:-1], stego_hist, label="Stego", color="red", linewidth=1.5, linestyle="--")

    plt.title("Pixel Difference Histogram (PDH)")
    plt.xlabel("Pixel Difference")
    plt.ylabel("Frequency")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.6)

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.show()
    print(f"[+] Saved PDH plot to {out_path}")


if __name__ == "__main__":
    plot_pdh("input/cover.png", "output/stego.png")
