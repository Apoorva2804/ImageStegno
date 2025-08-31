import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
import math
import os
from PIL import Image
import warnings

warnings.filterwarnings("ignore")


# ---- Quality Metrics ----
def mse(img1, img2):
    return np.mean((img1.astype("float") - img2.astype("float")) ** 2)

def rmse(img1, img2):
    return math.sqrt(mse(img1, img2))

def psnr(img1, img2):
    mse_val = mse(img1, img2)
    if mse_val == 0:  # Identical images
        return 100
    PIXEL_MAX = 255.0
    return 20 * math.log10(PIXEL_MAX / math.sqrt(mse_val))

def ncc(img1, img2):
    img1 = img1.astype(np.float64)
    img2 = img2.astype(np.float64)
    numerator = np.sum((img1 - img1.mean()) * (img2 - img2.mean()))
    denominator = np.sqrt(np.sum((img1 - img1.mean())**2) * np.sum((img2 - img2.mean())**2))
    return numerator / denominator if denominator != 0 else 0

def ssim_index(img1, img2):
    return ssim(img1, img2, channel_axis=-1)  # skimage handles RGB if channel_axis=-1

# ---- Resize and Compare ----
def evaluate_image_metrics(cover_path, stego_path, dimensions):
    cover = cv2.imread(cover_path)
    stego = cv2.imread(stego_path)

    # Resize both images to same dimensions
    cover_resized = cv2.resize(cover, (dimensions, dimensions))
    stego_resized = cv2.resize(stego, (dimensions, dimensions))

    return {
        "MSE": mse(cover_resized, stego_resized),
        "RMSE": rmse(cover_resized, stego_resized),
        "PSNR": psnr(cover_resized, stego_resized),
        "NCC": ncc(cover_resized, stego_resized),
        "SSIM": ssim_index(cover_resized, stego_resized),
    }

# ---- Run for different sizes ----
if __name__ == "__main__":
    cover_img = "input/cover.png"
    stego_img = "output/stego.png"

    dimensions = [128, 256, 512, 1024]
    results = {}

    for d in dimensions:
        metrics = evaluate_image_metrics(cover_img, stego_img, d)
        results[d] = metrics

    # Print results in table form
    print("Dimension |  MSE   |  RMSE  |  PSNR  |   NCC   |  SSIM")
    print("-"*60)
    for d, vals in results.items():
        print(f"{d}x{d} | {vals['MSE']:.2f} | {vals['RMSE']:.2f} | {vals['PSNR']:.2f} | {vals['NCC']:.4f} | {vals['SSIM']:.4f}")
    # for d, vals in results.items():
    #     print(f"{d}x{d} {vals['PSNR']:.2f} ")