import cv2
import numpy as np
import matplotlib.pyplot as plt
import os

def rs_analysis(image_path, out_path="results/rs_plot.png", block_size=2):
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(f"Image not found: {image_path}")

    pixels = img.flatten()
    n_blocks = len(pixels) // block_size
    pixels = pixels[:n_blocks * block_size].reshape(n_blocks, block_size)

    def f(block):
        return np.sum(np.abs(np.diff(block)))

    mask = np.array([1, -1] * (block_size // 2))

    R, Rm, S, Sm = [], [], [], []

    # embedding rate from 0 to 100%
    rates = list(range(0, 101, 10))
    for p in rates:
        n_flips = int((p / 100.0) * n_blocks)
        indices = np.random.choice(n_blocks, n_flips, replace=False)

        # positive flipping
        modified = pixels.copy()
        modified[indices] = np.clip(modified[indices] + mask, 0, 255)

        F_orig = np.array([f(b) for b in pixels])
        F_mod = np.array([f(b) for b in modified])

        R_count = np.sum(F_mod > F_orig)
        S_count = np.sum(F_mod < F_orig)

        R.append(R_count / n_blocks)
        S.append(S_count / n_blocks)

        # negative flipping
        modified_neg = pixels.copy()
        modified_neg[indices] = np.clip(modified_neg[indices] - mask, 0, 255)
        F_mod_neg = np.array([f(b) for b in modified_neg])

        Rm_count = np.sum(F_mod_neg > F_orig)
        Sm_count = np.sum(F_mod_neg < F_orig)

        Rm.append(Rm_count / n_blocks)
        Sm.append(Sm_count / n_blocks)

    plt.figure(figsize=(8, 6))
    plt.plot(rates, R, "r-", label="R(p)")
    plt.plot(rates, Rm, "r--", label="R(-p)")
    plt.plot(rates, S, "b-", label="S(p)")
    plt.plot(rates, Sm, "b--", label="S(-p)")

    plt.xlabel("Embedding Rate (%)")
    plt.ylabel("Fraction of Groups")
    plt.title("RS Steganalysis")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.6)

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.show()
    print(f"[+] Saved RS analysis plot to {out_path}")


if __name__ == "__main__":
    rs_analysis("output/stego.png")
