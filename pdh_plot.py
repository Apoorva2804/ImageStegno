import cv2
import numpy as np
import matplotlib.pyplot as plt

def plot_pdh(cover_path, stego_path, out_path="results/pdh.png"):
    cover = cv2.imread(cover_path, cv2.IMREAD_GRAYSCALE).astype(np.int16)
    stego = cv2.imread(stego_path, cv2.IMREAD_GRAYSCALE).astype(np.int16)

    # difference arrays
    diff_cover = np.diff(cover.flatten())
    diff_stego = np.diff(stego.flatten())

    plt.figure(figsize=(10,5))
    plt.hist(diff_cover, bins=80, range=(-40,40), alpha=0.5, color="blue", label="Cover")
    plt.hist(diff_stego, bins=80, range=(-40,40), alpha=0.5, color="red", label="Stego")
    plt.title("Pixel Difference Histogram (PDH)")
    plt.xlabel("Pixel Difference")
    plt.ylabel("Frequency")
    plt.legend()
    plt.savefig(out_path, dpi=300)
    plt.show()


plot_pdh("input/cover.png", "output/stego.png")