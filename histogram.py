import cv2
import numpy as np
import matplotlib.pyplot as plt
import os

def _to_gray_uint8(img):
    """Ensure image is grayscale and uint8 type."""
    if img is None:
        raise ValueError("Image not loaded properly (NoneType).")

    # Convert to grayscale if RGB/BGR
    if len(img.shape) == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Convert to uint8 if not already
    if img.dtype != np.uint8:
        img = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX)
        img = img.astype(np.uint8)

    return img


def _hist_gray(img):
    """Compute histogram for a grayscale image safely."""
    img = _to_gray_uint8(img)
    hist = cv2.calcHist([img], [0], None, [256], [0, 256])
    hist = hist.ravel().astype(np.float64)

    # Smooth out sharp peaks (optional but helps)
    hist = cv2.GaussianBlur(hist.reshape(-1, 1), (9, 9), 0).ravel()
    return hist


def plot_side_by_side_hist(cover_path, stego_path, save_path="histogram_comparison.png"):
    """Plot grayscale histograms of cover and stego images side by side."""
    if not os.path.exists(cover_path):
        raise FileNotFoundError(f"Cover image not found: {cover_path}")
    if not os.path.exists(stego_path):
        raise FileNotFoundError(f"Stego image not found: {stego_path}")

    cover = cv2.imread(cover_path)
    stego = cv2.imread(stego_path)

    cover_hist = _hist_gray(cover)
    stego_hist = _hist_gray(stego)

    plt.figure(figsize=(12, 5))
    plt.subplot(1, 2, 1)
    plt.plot(cover_hist, color='blue')
    plt.title("Cover Image Histogram")
    plt.xlabel("Pixel Intensity (0-255)")
    plt.ylabel("Frequency")
    plt.grid(True, linestyle='--', alpha=0.5)

    plt.subplot(1, 2, 2)
    plt.plot(stego_hist, color='red')
    plt.title("Stego Image Histogram")
    plt.xlabel("Pixel Intensity (0-255)")
    plt.ylabel("Frequency")
    plt.grid(True, linestyle='--', alpha=0.5)

    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()

    print(f"✅ Histogram comparison saved as: {save_path}")


# Example usage for testing (remove or comment out in main program)
if __name__ == "__main__":
    plot_side_by_side_hist(
        cover_path="cover.png",
        stego_path="stego.png"
    )
