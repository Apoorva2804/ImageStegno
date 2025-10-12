import cv2
import numpy as np
import matplotlib.pyplot as plt
import os
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

def _hist_gray(img: np.ndarray) -> np.ndarray:
    # 256-bin grayscale histogram, raw counts (no normalization) to match paper
    return cv2.calcHist([img], [0], None, [256], [0, 256]).ravel().astype(np.float64)

def _add_gray_strip(ax):
    # Small horizontal grayscale strip under each histogram (visual like paper)
    iax = inset_axes(ax, width="90%", height="7%", loc="lower center",
                     bbox_to_anchor=(0.5, -0.18, 0.0, 0.0), bbox_transform=ax.transAxes, borderpad=0)
    strip = np.tile(np.arange(256, dtype=np.uint8), (12, 1))
    iax.imshow(strip, cmap="gray", aspect="auto", extent=(0, 255, 0, 1))
    iax.set_xticks([]); iax.set_yticks([])
    for spine in iax.spines.values():
        spine.set_visible(False)

def plot_side_by_side_hist(cover_path: str, stego_path: str,
                           out_path: str = "results/hist_side_by_side.png"):
    cover = cv2.imread(cover_path, cv2.IMREAD_GRAYSCALE)
    stego = cv2.imread(stego_path, cv2.IMREAD_GRAYSCALE)
    if cover is None or stego is None:
        raise FileNotFoundError("Cover or stego image not found.")

    cov_h = _hist_gray(cover)
    stg_h = _hist_gray(stego)

    y_max = float(max(cov_h.max(), stg_h.max())) * 1.08

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4), sharey=True)

    # Cover
    axes[0].bar(np.arange(256), cov_h, color="#4f7bd3", edgecolor="#4f7bd3", width=1.0)
    axes[0].set_xlim(0, 255); axes[0].set_ylim(0, y_max)
    axes[0].set_title("Cover-Img Histograms")
    axes[0].set_xlabel("Pixel Intensity"); axes[0].set_ylabel("Frequency")
    _add_gray_strip(axes[0])

    # Stego
    axes[1].bar(np.arange(256), stg_h, color="#4f7bd3", edgecolor="#4f7bd3", width=1.0)
    axes[1].set_xlim(0, 255); axes[1].set_ylim(0, y_max)
    axes[1].set_title("Stego-Img Histograms")
    axes[1].set_xlabel("Pixel Intensity")
    _add_gray_strip(axes[1])

    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.show()
    print(f"[+] Histogram saved at {out_path}")
