import cv2
import numpy as np
import matplotlib.pyplot as plt
import os

def plot_side_by_side_hist(cover_path: str, stego_path: str, out_path: str = "results/hist_side_by_side.png"):
    # Load images in grayscale
    cover = cv2.imread(cover_path, cv2.IMREAD_GRAYSCALE)
    stego = cv2.imread(stego_path, cv2.IMREAD_GRAYSCALE)

    if cover is None or stego is None:
        raise FileNotFoundError("Cover or stego image not found.")

    # Compute histograms
    cover_hist = cv2.calcHist([cover], [0], None, [256], [0, 256]).ravel()
    stego_hist = cv2.calcHist([stego], [0], None, [256], [0, 256]).ravel()

    # Ensure output folder exists
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

    # Create figure with 1 row × 2 columns
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)

    # Left → Cover histogram
    axes[0].bar(range(256), cover_hist, color="blue", width=1)
    axes[0].set_title("Cover-Img Histogram")
    axes[0].set_xlabel("Pixel Intensity (0–255)")
    axes[0].set_ylabel("Frequency")
    axes[0].set_xlim([0, 255])

    # Right → Stego histogram
    axes[1].bar(range(256), stego_hist, color="blue", width=1)
    axes[1].set_title("Stego-Img Histogram")
    axes[1].set_xlabel("Pixel Intensity (0–255)")
    axes[1].set_xlim([0, 255])

    # Save & show
    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.show()

# Example usage
if __name__ == "__main__":
    plot_side_by_side_hist("input/cover.png", "output/stego.png")
